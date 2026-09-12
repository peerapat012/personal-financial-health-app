import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.config import Settings, get_settings
from app.core.errors import AppError
from app.main import create_app


class BetterAuthTest(unittest.TestCase):
    def setUp(self):
        self.settings = Settings(
            database_url="postgresql://user:pass@localhost/test", database_direct_url="postgresql://user:pass@localhost/test",
            auth_mode="better_auth", better_auth_url="http://127.0.0.1:3001", owner_user_id="owner-id",
        )
        app = create_app()
        app.dependency_overrides[get_settings] = lambda: self.settings
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()

    def session(self, user="owner-id", expired=False):
        return {"user": {"id": user}, "session": {"userId": user, "expiresAt": (datetime.now(timezone.utc) + timedelta(hours=-1 if expired else 1)).isoformat()}}

    def test_owner_only_expiry_and_missing_credentials(self):
        self.assertEqual(self.client.get("/api/v1/auth/config").json(), {"mode": "better_auth"})
        self.assertEqual(self.client.get("/api/v1/session").status_code, 401)
        for payload, expected in ((self.session(), 200), (self.session("other"), 401), (self.session(expired=True), 401), (None, 401), ({}, 401)):
            with self.subTest(expected=expected), patch("app.core.better_auth.auth_request", return_value=payload):
                self.assertEqual(self.client.get("/api/v1/session", headers={"Authorization": "Bearer opaque-session"}).status_code, expected)
        with patch("app.core.better_auth.auth_request", side_effect=AppError(503, "AUTH_UNAVAILABLE", "Unavailable")):
            self.assertEqual(self.client.get("/api/v1/session", headers={"Authorization": "Bearer opaque-session"}).status_code, 503)

    def test_sign_in_returns_only_verified_token_and_sign_out_revokes(self):
        with patch("app.routes.auth.auth_request", return_value={"token": "opaque-session"}) as request, patch("app.core.better_auth.auth_request", return_value=self.session()):
            response = self.client.post("/api/v1/auth/sign-in", json={"username": "owner", "password": "long-enough-password"})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), {"token": "opaque-session"})
            self.assertEqual(response.headers["cache-control"], "no-store")
            self.assertEqual(self.client.post("/api/v1/auth/sign-out", headers={"Authorization": "Bearer opaque-session"}).status_code, 204)
            self.assertEqual(request.call_args.args[1], "sign-out")
        with patch("app.routes.auth.auth_request", return_value={"token": "someone-else"}), patch("app.core.better_auth.auth_request", return_value=self.session("other")):
            self.assertEqual(self.client.post("/api/v1/auth/sign-in", json={"username": "other", "password": "long-enough-password"}).status_code, 401)
        self.assertEqual(self.client.post("/api/v1/auth/sign-in", json={"username": "bad user", "password": "x"}).status_code, 422)

    def test_auth_configuration_fails_closed(self):
        values = self.settings.model_dump()
        for changes in ({"owner_user_id": None}, {"better_auth_url": None}, {"better_auth_url": "http://remote.example.com"}, {"better_auth_url": "https://user:pass@example.com"}):
            with self.assertRaises(ValidationError):
                Settings(**(values | changes))


if __name__ == "__main__":
    unittest.main()
