import unittest
from datetime import date
from decimal import Decimal
from unittest.mock import patch
from uuid import uuid4

from sqlalchemy import MetaData
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.core.time import today_bangkok
from app.models.finance import Budget, Category
from app.models.health import WeightLog, Workout
from tests import test_goals


class DashboardTest(unittest.TestCase):
    setUp = test_goals.GoalsTest.setUp
    tearDown = test_goals.GoalsTest.tearDown
    request = test_goals.GoalsTest.request
    payload = test_goals.GoalsTest.payload

    def create_budget_table(self):
        # SQLite has no EXTRACT; production keeps the existing PostgreSQL constraint.
        metadata = MetaData()
        Category.__table__.to_metadata(metadata)
        table = Budget.__table__.to_metadata(metadata)
        table.constraints = {constraint for constraint in table.constraints if constraint.name != "budgets_month_start_check"}
        table.create(self.engine)

    def test_snapshot_month_boundaries_budgets_goals_and_missing_days(self):
        self.create_budget_table()
        month = date(2024, 2, 1)
        income = self.request("POST", "/categories", 201, json={"id": str(uuid4()), "name": "Pay", "kind": "income"})
        expense = self.request("POST", "/categories", 201, json={"id": str(uuid4()), "name": "Food", "kind": "expense"})
        account = self.request("POST", "/accounts", 201, json={"id": str(uuid4()), "name": "History", "kind": "bank", "opening_balance": "20.00", "opening_date": "2024-01-01"})
        for kind, category, amount, day in (("income", income, "300", "2024-02-01"), ("expense", expense, "80", "2024-02-29"), ("expense", expense, "12", "2024-03-01")):
            self.request("POST", "/transactions", 201, json={"id": str(uuid4()), "kind": kind, "account_id": account["id"], "category_id": category["id"], "amount": amount, "occurred_on": day})
        self.request("POST", "/transactions", 201, json={"id": str(uuid4()), "kind": "transfer", "account_id": account["id"], "to_account_id": str(self.account_id), "amount": "10", "occurred_on": self.today.isoformat()})
        goal = self.request("POST", "/financial-goals", 201, json=self.payload(True))
        self.request("PATCH", f"/financial-goals/{goal['id']}", json={"archived": True})
        self.request("POST", "/health-goals", 201, json=self.payload())
        self.request("POST", "/budgets", 201, json={"id": str(uuid4()), "category_id": expense["id"], "month": "2024-02", "amount": "60"})
        with Session(self.engine) as db:
            db.add_all([
                WeightLog(id=uuid4(), log_date=month, weight_kg=Decimal("80")),
                WeightLog(id=uuid4(), log_date=date(2024, 2, 3), weight_kg=Decimal("78")),
                WeightLog(id=uuid4(), log_date=date(2024, 3, 1), weight_kg=Decimal("77")),
                Workout(id=uuid4(), occurred_on=date(2024, 2, 29), activity_type="walk", duration_minutes=45),
                Workout(id=uuid4(), occurred_on=date(2024, 3, 1), activity_type="walk", duration_minutes=20),
            ])
            db.commit()
        result = self.request("GET", "/dashboard?month=2024-02")
        self.assertEqual(result["account_balances"]["as_of"], today_bangkok().isoformat())
        self.assertEqual(Decimal(result["account_balances"]["total"]), 328)
        self.assertEqual(Decimal(result["finance"]["income"]), 300)
        self.assertEqual(Decimal(result["finance"]["expense"]), 80)
        self.assertEqual(Decimal(result["finance"]["net_cash_flow"]), 220)
        self.assertEqual(Decimal(result["budgets"][0]["actual"]), 80)
        self.assertEqual(Decimal(result["budgets"][0]["remaining"]), -20)
        self.assertEqual(result["health"]["workout_minutes"], 45)
        self.assertEqual(result["health"]["recorded_weight_days"], 2)
        self.assertEqual(Decimal(result["health"]["average_weight_kg"]), 79)
        self.assertEqual(result["health"]["latest_weight_date"], "2024-03-01")
        self.assertEqual(len(result["health"]["weight_trend"]), 29)
        self.assertIsNone(result["health"]["weight_trend"][1]["weight_kg"])
        self.assertEqual(len(result["goals"]), 1)
        self.assertEqual(len(result["recent_transactions"]), 4)

    def test_validation_empty_future_month_and_database_failure(self):
        self.create_budget_table()
        self.assertEqual(self.client.get("/api/v1/dashboard?month=2024-01").status_code, 401)
        for value in ("", "2024-13", "2024-1", "2024-01-01", "nonsense"):
            self.request("GET", "/dashboard?month=" + value, 422)
        self.request("GET", "/dashboard", 422)
        result = self.request("GET", "/dashboard?month=9999-12")
        self.assertEqual(result["health"]["weight_trend"], [])
        self.assertIsNone(result["health"]["latest_weight_kg"])
        self.assertEqual(result["goals"], [])
        self.assertEqual(Decimal(result["finance"]["income"]), 0)
        with patch("app.routes.dashboard.get_dashboard", side_effect=OperationalError("query", {}, Exception("offline"))):
            result = self.request("GET", "/dashboard?month=2024-02", 503)
            self.assertEqual(result["error"]["code"], "DATABASE_UNAVAILABLE")


if __name__ == "__main__":
    unittest.main()
