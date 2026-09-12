import unittest
from unittest.mock import Mock
from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

from pydantic import ValidationError
from sqlalchemy import create_engine, event
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.finance import Account, Category, Transaction
from app.schemas.finance import AccountCreate, CategoryCreate, TransactionCreate
from app.services.finance import (
    _commit,
    create_account,
    create_category,
    create_transaction,
    finance_totals,
    get_account,
)


class FinanceRulesTest(unittest.TestCase):
    def test_failed_commit_rolls_back(self) -> None:
        db = Mock(spec=Session)
        db.commit.side_effect = IntegrityError("insert", {}, Exception("duplicate"))
        with self.assertRaises(AppError) as raised:
            _commit(db, "Already exists")
        self.assertEqual(raised.exception.status_code, 409)
        db.rollback.assert_called_once_with()

    def test_transaction_shape_and_monthly_totals(self) -> None:
        account_id = uuid4()
        category_id = uuid4()
        with self.assertRaises(ValidationError):
            TransactionCreate(
                id=uuid4(),
                kind="transfer",
                account_id=account_id,
                to_account_id=account_id,
                amount="10.00",
                occurred_on=date.today(),
            )
        with self.assertRaises(ValidationError):
            TransactionCreate(
                id=uuid4(),
                kind="income",
                account_id=account_id,
                category_id=uuid4(),
                amount=1e2,
                occurred_on=date.today(),
            )

        rows = [
            (SimpleNamespace(kind="income", amount=Decimal("100.00"), category_id=uuid4()), "Salary"),
            (SimpleNamespace(kind="expense", amount=Decimal("35.50"), category_id=category_id), "Food"),
            (SimpleNamespace(kind="transfer", amount=Decimal("20.00"), category_id=None), None),
        ]
        summary = finance_totals(rows, "2026-09")
        self.assertEqual(summary.income, Decimal("100.00"))
        self.assertEqual(summary.expense, Decimal("35.50"))
        self.assertEqual(summary.net_cash_flow, Decimal("64.50"))
        self.assertEqual(summary.expense_by_category[0].category_id, category_id)

    def test_balances_include_opening_money_and_atomic_transfer(self) -> None:
        engine = create_engine("sqlite:///:memory:")

        @event.listens_for(engine, "connect")
        def sqlite_functions(connection, _) -> None:
            connection.create_function("btrim", 1, lambda value: value.strip())
            connection.create_function("char_length", 1, len)

        Account.__table__.create(engine)
        Category.__table__.create(engine)
        Transaction.__table__.create(engine)
        with Session(engine, expire_on_commit=False) as db:
            cash_id, bank_id = uuid4(), uuid4()
            income_id, expense_id = uuid4(), uuid4()
            for account_id, name, opening in (
                (cash_id, "Cash", "100.00"),
                (bank_id, "Bank", "20.00"),
            ):
                create_account(db, AccountCreate(id=account_id, name=name, kind="cash", opening_balance=opening, opening_date=date.today()))
            create_category(db, CategoryCreate(id=income_id, name="Salary", kind="income"))
            create_category(db, CategoryCreate(id=expense_id, name="Food", kind="expense"))
            for transaction in (
                TransactionCreate(id=uuid4(), kind="income", account_id=cash_id, category_id=income_id, amount="50.00", occurred_on=date.today()),
                TransactionCreate(id=uuid4(), kind="expense", account_id=cash_id, category_id=expense_id, amount="10.00", occurred_on=date.today()),
                TransactionCreate(id=uuid4(), kind="transfer", account_id=cash_id, to_account_id=bank_id, amount="25.00", occurred_on=date.today()),
            ):
                create_transaction(db, transaction)
            self.assertEqual(get_account(db, cash_id).current_balance, Decimal("115.00"))
            self.assertEqual(get_account(db, bank_id).current_balance, Decimal("45.00"))
        engine.dispose()


if __name__ == "__main__":
    unittest.main()
