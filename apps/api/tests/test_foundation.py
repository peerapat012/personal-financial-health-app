import hashlib
import unittest

from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.main import create_app


class FoundationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        app = create_app()
        settings = Settings(
            app_env="test",
            database_url="postgresql+psycopg://user:pass@localhost/test",
            database_direct_url="postgresql+psycopg://user:pass@localhost/test",
            personal_api_token_sha256=hashlib.sha256(b"secret").hexdigest(),
        )
        app.dependency_overrides[get_settings] = lambda: settings
        cls.client = TestClient(app)

    def test_healthcheck(self) -> None:
        response = self.client.get("/healthz")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})
        self.assertIn("X-Request-ID", response.headers)

    def test_neon_url_uses_installed_psycopg_driver(self) -> None:
        settings = Settings(
            database_url="postgresql://user:pass@localhost/test",
            database_direct_url="postgresql://user:pass@localhost/test",
            personal_api_token_sha256=hashlib.sha256(b"secret").hexdigest(),
        )
        self.assertTrue(settings.database_url.startswith("postgresql+psycopg://"))

    def test_session_requires_valid_token(self) -> None:
        denied = self.client.get(
            "/api/v1/session", headers={"Authorization": "Bearer wrong"}
        )
        self.assertEqual(denied.status_code, 401)
        self.assertEqual(denied.json()["error"]["code"], "UNAUTHORIZED")

        allowed = self.client.get(
            "/api/v1/session", headers={"Authorization": "Bearer secret"}
        )
        self.assertEqual(allowed.status_code, 200)
        self.assertEqual(allowed.json()["currency"], "THB")


if __name__ == "__main__":
    unittest.main()
