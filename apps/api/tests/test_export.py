import unittest
from unittest.mock import patch

from sqlalchemy import MetaData
from sqlalchemy.exc import OperationalError

from app.models.finance import Budget, Category
from tests import test_goals


class ExportTest(unittest.TestCase):
    tearDown = test_goals.GoalsTest.tearDown
    request = test_goals.GoalsTest.request

    def setUp(self) -> None:
        test_goals.GoalsTest.setUp(self)
        metadata = MetaData()
        Category.__table__.to_metadata(metadata)
        table = Budget.__table__.to_metadata(metadata)
        table.constraints = {
            constraint
            for constraint in table.constraints
            if constraint.name != "budgets_month_start_check"
        }
        table.create(self.engine)

    def test_export_is_complete_and_excludes_authentication(self) -> None:
        result = self.request("GET", "/export")
        self.assertEqual(result["schema_version"], "1")
        self.assertTrue(result["exported_at"].endswith("Z"))
        self.assertEqual(
            set(result["data"]),
            {
                "accounts",
                "categories",
                "transactions",
                "budgets",
                "weight_logs",
                "workouts",
                "financial_goals",
                "health_goals",
            },
        )
        self.assertEqual(result["data"]["accounts"][0]["opening_balance"], "100.00")
        self.assertNotIn("auth_owner", result["data"])
        self.assertNotIn("auth_sessions", result["data"])

    def test_export_requires_auth_and_maps_database_failure(self) -> None:
        self.assertEqual(self.client.get("/api/v1/export").status_code, 401)
        with patch(
            "app.routes.export.get_export",
            side_effect=OperationalError("query", {}, Exception("offline")),
        ):
            result = self.request("GET", "/export", 503)
            self.assertEqual(result["error"]["code"], "DATABASE_UNAVAILABLE")


if __name__ == "__main__":
    unittest.main()
