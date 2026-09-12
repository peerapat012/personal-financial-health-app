import hashlib
import unittest
from datetime import timedelta
from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.config import Settings, get_settings
from app.core.time import today_bangkok
from app.db import get_db
from app.main import create_app
from app.models.finance import Account, Category, Transaction
from app.models.goals import FinancialGoal, HealthGoal
from app.models.health import WeightLog, Workout
from app.services.goals import progress


class GoalsTest(unittest.TestCase):
    def setUp(self):
        # Local service/HTTP checks only; PostgreSQL integration remains a release check.
        self.engine = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})

        @event.listens_for(self.engine, "connect")
        def functions(connection, _):
            connection.create_function("btrim", 1, lambda value: value.strip() if value else value)
            connection.create_function("char_length", 1, lambda value: len(value) if value else 0)
            connection.execute("PRAGMA foreign_keys=ON")

        for model in (Account, Category, Transaction, WeightLog, Workout, FinancialGoal, HealthGoal):
            model.__table__.create(self.engine)
        self.today = today_bangkok()
        self.start = self.today - timedelta(days=7)
        self.account_id = uuid4()
        with Session(self.engine) as db:
            db.add(Account(id=self.account_id, name="Cash", kind="cash", opening_balance=Decimal("100.00"), opening_date=self.start))
            db.commit()
        app = create_app()
        settings = Settings(
            app_env="test", database_url="postgresql+psycopg://user:pass@localhost/test",
            database_direct_url="postgresql+psycopg://user:pass@localhost/test",
            personal_api_token_sha256=hashlib.sha256(b"secret").hexdigest(),
        )

        def database():
            with Session(self.engine, expire_on_commit=False) as db:
                yield db

        app.dependency_overrides[get_settings] = lambda: settings
        app.dependency_overrides[get_db] = database
        self.client = TestClient(app)
        self.headers = {"Authorization": "Bearer secret"}

    def tearDown(self):
        self.client.close()
        self.engine.dispose()

    def payload(self, financial=False):
        body = {"id": str(uuid4()), "name": " Milestone ", "start_date": self.start.isoformat(), "due_date": None}
        return body | ({"account_id": str(self.account_id), "baseline_amount": "0.00", "target_amount": "200.00"} if financial else {"baseline_weight_kg": "80.00", "target_weight_kg": "70.00"})

    def request(self, method, path, expected=200, **kwargs):
        response = self.client.request(method, f"/api/v1{path}", headers=self.headers, **kwargs)
        self.assertEqual(response.status_code, expected, response.text)
        return response.json() if expected != 204 else None

    def test_progress_in_both_directions_clamping_and_no_data(self):
        for baseline, target, current, ratio, percent, achieved in (
            (80, 70, 75, ".5", "50", False), (70, 80, 75, ".5", "50", False),
            (80, 70, 85, "-.5", "0", False), (70, 80, 65, "-.5", "0", False),
            (80, 70, 65, "1.5", "100", True), (70, 80, 85, "1.5", "100", True),
            (80, 70, 70, "1", "100", True), (70, 80, 80, "1", "100", True),
        ):
            with self.subTest(baseline=baseline, target=target, current=current):
                self.assertEqual(progress(Decimal(baseline), Decimal(target), Decimal(current)), {
                    "progress_ratio": Decimal(ratio), "progress_percent": Decimal(percent), "achieved": achieved,
                })
        self.assertEqual(progress(Decimal(80), Decimal(70), None), {"progress_ratio": None, "progress_percent": None, "achieved": False})

    def test_goal_lifecycle_validation_and_auth(self):
        for financial in (False, True):
            path = "/financial-goals" if financial else "/health-goals"
            body = self.payload(financial)
            item_path = f"{path}/{body['id']}"
            for method, suffix in (("GET", ""), ("POST", ""), ("GET", "/missing"), ("PATCH", "/missing"), ("DELETE", "/missing")):
                denied = self.client.request(method, f"/api/v1{path}{suffix}")
                self.assertEqual(denied.status_code, 401)
            created = self.request("POST", path, 201, json=body)
            self.assertEqual(created["name"], "Milestone")
            self.assertIsInstance(created["target_amount" if financial else "target_weight_kg"], str)
            self.request("POST", path, 201, json=body)  # Same ID/payload recovers a committed request.
            self.request("POST", path, 409, json=body | {"name": "Other"})
            self.assertEqual(self.request("GET", path)["total"], 1)
            self.request("PATCH", item_path, 422, json={"start_date": self.today.isoformat()})
            self.request("PATCH", item_path, 422, json={"name": None})
            self.request("PATCH", item_path, 422, json={})
            self.request("PATCH", item_path, 422, json={"name": "Must not persist", "due_date": (self.start - timedelta(days=1)).isoformat()})
            self.assertEqual(self.request("GET", item_path)["name"], "Milestone")
            self.request("PATCH", item_path, json={"due_date": self.today.isoformat(), "archived": True})
            self.assertEqual(self.request("GET", path)["total"], 0)
            self.assertEqual(self.request("GET", path + "?include_archived=true")["total"], 1)
            updated = self.request("PATCH", item_path, json={"due_date": None, "archived": False, "name": "Renamed"})
            self.assertIsNone(updated["due_date"])
            self.assertIsNone(updated["archived_at"])
            self.request("POST", path, 201, json=self.payload(financial))
            self.assertEqual(len(self.request("GET", path + "?limit=1&offset=1")["items"]), 1)
            self.assertEqual(self.request("GET", path + "?offset=99")["items"], [])
            for query in ("limit=201", "offset=-1", "include_archived=invalid"):
                self.request("GET", path + "?" + query, 422)
            if financial:
                self.request("DELETE", f"/accounts/{self.account_id}", 409)
            self.request("DELETE", item_path, 204)
            self.request("GET", item_path, 404)
            for invalid in ({"name": " "}, {"start_date": (self.today + timedelta(days=1)).isoformat()}, {"due_date": (self.start - timedelta(days=1)).isoformat()}, {"unknown": True}):
                self.request("POST", path, 422, json=self.payload(financial) | invalid)
            target = "target_amount" if financial else "target_weight_kg"
            for invalid in ("NaN", "1e2", "1.001", 20):
                self.request("POST", path, 422, json=self.payload(financial) | {target: invalid})
            self.request("POST", path, 422, json=self.payload(financial) | {target: "0" if financial else "80"})
        self.request("POST", "/financial-goals", 422, json=self.payload(True) | {"account_id": str(uuid4())})
        self.request("POST", "/health-goals", 422, json=self.payload() | {"baseline_weight_kg": "501"})

    def test_latest_weight_respects_start_skips_notes_and_reverses_achievement(self):
        body = self.payload()
        path = f"/health-goals/{body['id']}"
        with Session(self.engine) as db:
            db.add_all([
                WeightLog(id=uuid4(), log_date=self.start - timedelta(days=1), weight_kg=Decimal("70")),
                WeightLog(id=uuid4(), log_date=self.today, weight_kg=None, note="Note only"),
            ])
            db.commit()
        result = self.request("POST", "/health-goals", 201, json=body)
        self.assertIsNone(result["current_weight_kg"])
        self.assertIsNone(result["progress_percent"])
        with Session(self.engine) as db:
            weight_id = uuid4()
            db.add(WeightLog(id=weight_id, log_date=self.start, weight_kg=Decimal("69")))
            db.commit()
        self.assertTrue(self.request("GET", path)["achieved"])
        with Session(self.engine) as db:
            db.get(WeightLog, weight_id).weight_kg = Decimal("75")
            db.commit()
        result = self.request("GET", path)
        self.assertFalse(result["achieved"])
        self.assertEqual(Decimal(result["progress_percent"]), 50)
        self.assertEqual(result["current_weight_date"], self.start.isoformat())

    def test_financial_goal_uses_current_balance_and_transaction_changes(self):
        body = self.payload(True)
        result = self.request("POST", "/financial-goals", 201, json=body)
        self.assertEqual(Decimal(result["progress_percent"]), 50)
        income = self.request("POST", "/categories", 201, json={"id": str(uuid4()), "name": "Income", "kind": "income"})
        transaction = self.request("POST", "/transactions", 201, json={
            "id": str(uuid4()), "kind": "income", "account_id": str(self.account_id), "category_id": income["id"],
            "amount": "120.00", "occurred_on": self.today.isoformat(),
        })
        path = f"/financial-goals/{body['id']}"
        result = self.request("GET", path)
        self.assertEqual(Decimal(result["progress_ratio"]), Decimal("1.1"))
        self.assertTrue(result["achieved"])
        self.request("DELETE", f"/transactions/{transaction['id']}", 204)
        self.assertFalse(self.request("GET", path)["achieved"])


if __name__ == "__main__":
    unittest.main()
