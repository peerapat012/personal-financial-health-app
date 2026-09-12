import os
import unittest
from datetime import date
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import create_engine, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.finance import Account, Budget, Category, Transaction
from app.models.goals import FinancialGoal
from app.models.health import WeightLog
from app.schemas.finance import TransactionCreate
from app.services.finance import create_transaction

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")


@unittest.skipUnless(TEST_DATABASE_URL, "Set TEST_DATABASE_URL for PostgreSQL checks")
class PostgreSQLConstraintTest(unittest.TestCase):
    def setUp(self) -> None:
        url = TEST_DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)
        self.engine = create_engine(url)
        self.connection = self.engine.connect()
        self.transaction = self.connection.begin()
        self.db = Session(bind=self.connection, join_transaction_mode="rollback_only")
        self.source_id, self.destination_id = uuid4(), uuid4()
        self.income_id, self.expense_id = uuid4(), uuid4()
        self.db.add_all(
            [
                Account(id=self.source_id, name=f"test-{self.source_id}", kind="bank", opening_balance=Decimal("100"), opening_date=date(2000, 1, 1)),
                Account(id=self.destination_id, name=f"test-{self.destination_id}", kind="bank", opening_balance=Decimal("0"), opening_date=date(2000, 1, 1)),
                Category(id=self.income_id, name=f"test-{self.income_id}", kind="income"),
                Category(id=self.expense_id, name=f"test-{self.expense_id}", kind="expense"),
            ]
        )
        self.db.flush()

    def tearDown(self) -> None:
        self.db.close()
        self.transaction.rollback()
        self.connection.close()
        self.engine.dispose()

    def test_transfer_is_one_atomic_row(self) -> None:
        transaction_id = uuid4()
        create_transaction(
            self.db,
            TransactionCreate(
                id=transaction_id,
                kind="transfer",
                account_id=self.source_id,
                to_account_id=self.destination_id,
                amount="25.00",
                occurred_on=date(2000, 1, 2),
            ),
        )
        self.assertEqual(
            self.db.scalar(
                select(func.count()).select_from(Transaction).where(Transaction.id == transaction_id)
            ),
            1,
        )

    def test_category_type_constraint(self) -> None:
        self.db.add(Transaction(id=uuid4(), kind="expense", account_id=self.source_id, category_id=self.income_id, amount=Decimal("1"), occurred_on=date(2000, 1, 2)))
        with self.assertRaises(IntegrityError):
            self.db.flush()

    def test_daily_weight_uniqueness(self) -> None:
        self.db.add_all(
            [
                WeightLog(id=uuid4(), log_date=date(1900, 1, 1), weight_kg=Decimal("70")),
                WeightLog(id=uuid4(), log_date=date(1900, 1, 1), weight_kg=Decimal("71")),
            ]
        )
        with self.assertRaises(IntegrityError):
            self.db.flush()

    def test_budget_uniqueness(self) -> None:
        self.db.add_all(
            [
                Budget(id=uuid4(), category_id=self.expense_id, month=date(1900, 1, 1), amount=Decimal("1")),
                Budget(id=uuid4(), category_id=self.expense_id, month=date(1900, 1, 1), amount=Decimal("2")),
            ]
        )
        with self.assertRaises(IntegrityError):
            self.db.flush()

    def test_goal_account_reference(self) -> None:
        self.db.add(
            FinancialGoal(
                id=uuid4(), name="test", account_id=uuid4(), baseline_amount=Decimal("0"),
                target_amount=Decimal("1"), start_date=date(2000, 1, 1),
            )
        )
        with self.assertRaises(IntegrityError):
            self.db.flush()


if __name__ == "__main__":
    unittest.main()
