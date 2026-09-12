import unittest
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db import get_db
from app.main import create_app
from app.models.auth import AuthOwner, AuthSession
from app.provision_owner import provision_owner
from app.routes.auth import attempts


class NativeAuthTest(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine(
            "sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False}
        )
        AuthOwner.__table__.create(self.engine)
        AuthSession.__table__.create(self.engine)
        with Session(self.engine) as db:
            provision_owner(db, "Owner", "long-enough-password")

        def database():
            with Session(self.engine, expire_on_commit=False) as db:
                yield db

        app = create_app()
        app.dependency_overrides[get_db] = database
        self.client = TestClient(app)
        attempts.clear()

    def tearDown(self) -> None:
        self.client.close()
        self.engine.dispose()

    def sign_in(self):
        return self.client.post(
            "/api/v1/auth/sign-in",
            json={"username": "owner", "password": "long-enough-password"},
        )

    def test_sign_in_stores_only_hash_and_sign_out_revokes(self) -> None:
        response = self.sign_in()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["cache-control"], "no-store")
        token = response.json()["token"]
        with Session(self.engine) as db:
            stored = db.scalar(select(AuthSession))
            owner = db.get(AuthOwner, 1)
            self.assertTrue(owner.password_hash.startswith("$argon2"))
            self.assertNotIn("long-enough-password", owner.password_hash)
            self.assertNotEqual(stored.token_hash, token)
            self.assertEqual(len(stored.token_hash), 64)

        headers = {"Authorization": f"Bearer {token}"}
        self.assertEqual(self.client.get("/api/v1/session", headers=headers).status_code, 200)
        self.assertEqual(self.client.post("/api/v1/auth/sign-out", headers=headers).status_code, 204)
        self.assertEqual(self.client.get("/api/v1/session", headers=headers).status_code, 401)

    def test_invalid_expired_and_rate_limited_sessions(self) -> None:
        self.assertEqual(self.client.get("/api/v1/session").status_code, 401)
        self.assertEqual(
            self.client.post(
                "/api/v1/auth/sign-in",
                json={"username": "owner", "password": "wrong-password"},
            ).status_code,
            401,
        )
        attempts.clear()
        for _ in range(5):
            self.client.post(
                "/api/v1/auth/sign-in",
                json={"username": "missing", "password": "wrong-password"},
            )
        self.assertEqual(
            self.client.post(
                "/api/v1/auth/sign-in",
                json={"username": "owner", "password": "long-enough-password"},
            ).status_code,
            429,
        )
        attempts.clear()
        token = self.sign_in().json()["token"]
        with Session(self.engine) as db:
            session = db.scalar(select(AuthSession))
            session.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
            db.commit()
        self.assertEqual(
            self.client.get(
                "/api/v1/session", headers={"Authorization": f"Bearer {token}"}
            ).status_code,
            401,
        )

    def test_owner_is_singleton_and_inputs_are_validated(self) -> None:
        self.assertEqual(self.client.get("/api/v1/auth/config").status_code, 404)
        with Session(self.engine) as db, self.assertRaises(ValueError):
            provision_owner(db, "other", "another-long-password")
        self.assertEqual(
            self.client.post(
                "/api/v1/auth/sign-in", json={"username": "bad user", "password": "x"}
            ).status_code,
            422,
        )
        self.assertEqual(
            self.client.post(
                "/api/v1/auth/sign-in",
                json={
                    "username": "owner",
                    "password": "long-enough-password",
                    "admin": True,
                },
            ).status_code,
            422,
        )


if __name__ == "__main__":
    unittest.main()
