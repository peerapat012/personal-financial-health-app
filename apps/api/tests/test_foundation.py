import unittest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.config import Settings
from app.db import get_db
from app.main import create_app
from app.models.auth import AuthOwner, AuthSession
from app.provision_owner import provision_owner


class FoundationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.engine = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
        AuthOwner.__table__.create(cls.engine)
        AuthSession.__table__.create(cls.engine)
        with Session(cls.engine) as db:
            provision_owner(db, "owner", "long-enough-password")

        def database():
            with Session(cls.engine, expire_on_commit=False) as db:
                yield db

        app = create_app()
        app.dependency_overrides[get_db] = database
        cls.client = TestClient(app)
        cls.token = cls.client.post("/api/v1/auth/sign-in", json={"username": "owner", "password": "long-enough-password"}).json()["token"]

    @classmethod
    def tearDownClass(cls) -> None:
        cls.client.close()
        cls.engine.dispose()

    def test_healthcheck(self) -> None:
        response = self.client.get("/healthz")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})
        self.assertIn("X-Request-ID", response.headers)

    def test_neon_url_uses_installed_psycopg_driver(self) -> None:
        settings = Settings(
            database_url="postgresql://user:pass@localhost/test",
            database_direct_url="postgresql://user:pass@localhost/test",
        )
        self.assertTrue(settings.database_url.startswith("postgresql+psycopg://"))

    def test_session_requires_valid_token(self) -> None:
        denied = self.client.get(
            "/api/v1/session", headers={"Authorization": "Bearer wrong"}
        )
        self.assertEqual(denied.status_code, 401)
        self.assertEqual(denied.json()["error"]["code"], "UNAUTHORIZED")

        allowed = self.client.get(
            "/api/v1/session", headers={"Authorization": f"Bearer {self.token}"}
        )
        self.assertEqual(allowed.status_code, 200)
        self.assertEqual(allowed.json()["currency"], "THB")

    def test_session_allows_desktop_origin(self) -> None:
        response = self.client.get(
            "/api/v1/session",
            headers={
                "Authorization": f"Bearer {self.token}",
                "Origin": "http://localhost:5173",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["access-control-allow-origin"], "http://localhost:5173")

    def test_session_preflight_allows_tauri_dev_origin(self) -> None:
        response = self.client.options(
            "/api/v1/session",
            headers={
                "Origin": "http://localhost:1420",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "authorization",
            },
        )
        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
