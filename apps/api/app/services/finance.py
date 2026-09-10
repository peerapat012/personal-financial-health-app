from collections import defaultdict
from collections.abc import Iterable
from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, aliased

from app.core.errors import AppError
from app.models.finance import Account, Budget, Category, Transaction
from app.models.goals import FinancialGoal
from app.schemas.finance import (
    AccountCreate,
    AccountPatch,
    AccountResponse,
    BudgetCreate,
    BudgetPatch,
    BudgetResponse,
    CategoryCreate,
    CategoryPatch,
    CategoryResponse,
    CategoryTotal,
    FinanceSummaryResponse,
    TransactionCreate,
    TransactionPatch,
    TransactionResponse,
    today_bangkok,
)

ZERO = Decimal("0.00")


def _commit(db: Session, message: str) -> None:
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise AppError(409, "CONFLICT", message) from error


def _account_balance():
    credits = (
        select(func.coalesce(func.sum(Transaction.amount), ZERO))
        .where(
            Transaction.occurred_on <= today_bangkok(),
            or_(
                and_(Transaction.kind == "income", Transaction.account_id == Account.id),
                and_(Transaction.kind == "transfer", Transaction.to_account_id == Account.id),
            ),
        )
        .correlate(Account)
        .scalar_subquery()
    )
    debits = (
        select(func.coalesce(func.sum(Transaction.amount), ZERO))
        .where(
            Transaction.occurred_on <= today_bangkok(),
            or_(
                and_(Transaction.kind == "expense", Transaction.account_id == Account.id),
                and_(Transaction.kind == "transfer", Transaction.account_id == Account.id),
            ),
        )
        .correlate(Account)
        .scalar_subquery()
    )
    return Account.opening_balance + credits - debits


def _account_response(account: Account, balance: Decimal) -> AccountResponse:
    return AccountResponse(
        id=account.id,
        name=account.name,
        kind=account.kind,
        opening_balance=account.opening_balance,
        opening_date=account.opening_date,
        archived_at=account.archived_at,
        current_balance=balance,
        created_at=account.created_at,
        updated_at=account.updated_at,
    )


def list_accounts(db: Session, include_archived: bool, limit: int, offset: int):
    filters = [] if include_archived else [Account.archived_at.is_(None)]
    total = db.scalar(select(func.count()).select_from(Account).where(*filters)) or 0
    rows = db.execute(
        select(Account, _account_balance().label("current_balance"))
        .where(*filters)
        .order_by(Account.archived_at.nulls_first(), Account.name)
        .limit(limit)
        .offset(offset)
    ).all()
    return [_account_response(account, balance) for account, balance in rows], total


def get_account(db: Session, account_id: UUID) -> AccountResponse:
    row = db.execute(
        select(Account, _account_balance().label("current_balance")).where(Account.id == account_id)
    ).one_or_none()
    if not row:
        raise AppError(404, "NOT_FOUND", "Account not found")
    return _account_response(*row)


def create_account(db: Session, data: AccountCreate) -> AccountResponse:
    existing = db.get(Account, data.id)
    if existing:
        same = all(getattr(existing, field) == value for field, value in data.model_dump().items())
        if same:
            return get_account(db, existing.id)
        raise AppError(409, "CONFLICT", "Account ID is already in use")
    account = Account(**data.model_dump())
    db.add(account)
    _commit(db, "An account with this name already exists")
    return get_account(db, account.id)


def update_account(db: Session, account_id: UUID, data: AccountPatch) -> AccountResponse:
    account = db.get(Account, account_id)
    if not account:
        raise AppError(404, "NOT_FOUND", "Account not found")
    if data.name is not None:
        account.name = data.name
    if data.archived is not None:
        account.archived_at = datetime.now(timezone.utc) if data.archived else None
    _commit(db, "An account with this name already exists")
    return get_account(db, account.id)


def delete_account(db: Session, account_id: UUID) -> None:
    account = db.get(Account, account_id)
    if not account:
        raise AppError(404, "NOT_FOUND", "Account not found")
    referenced = db.scalar(
        select(func.count()).select_from(Transaction).where(
            or_(Transaction.account_id == account_id, Transaction.to_account_id == account_id)
        )
    ) or db.scalar(
        select(func.count()).select_from(FinancialGoal).where(FinancialGoal.account_id == account_id)
    )
    if referenced:
        raise AppError(409, "ACCOUNT_IN_USE", "Account is referenced and cannot be deleted")
    db.delete(account)
    _commit(db, "Account could not be deleted")


def list_categories(db: Session, kind: str | None, include_archived: bool, limit: int, offset: int):
    filters = []
    if kind:
        filters.append(Category.kind == kind)
    if not include_archived:
        filters.append(Category.archived_at.is_(None))
    total = db.scalar(select(func.count()).select_from(Category).where(*filters)) or 0
    items = list(db.scalars(select(Category).where(*filters).order_by(Category.kind, Category.name).limit(limit).offset(offset)))
    return [CategoryResponse.model_validate(item) for item in items], total


def get_category(db: Session, category_id: UUID) -> CategoryResponse:
    category = db.get(Category, category_id)
    if not category:
        raise AppError(404, "NOT_FOUND", "Category not found")
    return CategoryResponse.model_validate(category)


def create_category(db: Session, data: CategoryCreate) -> CategoryResponse:
    existing = db.get(Category, data.id)
    if existing:
        if existing.name == data.name and existing.kind == data.kind:
            return CategoryResponse.model_validate(existing)
        raise AppError(409, "CONFLICT", "Category ID is already in use")
    category = Category(**data.model_dump())
    db.add(category)
    _commit(db, "A category with this name and type already exists")
    return CategoryResponse.model_validate(category)


def update_category(db: Session, category_id: UUID, data: CategoryPatch) -> CategoryResponse:
    category = db.get(Category, category_id)
    if not category:
        raise AppError(404, "NOT_FOUND", "Category not found")
    if data.name is not None:
        category.name = data.name
    if data.archived is not None:
        category.archived_at = datetime.now(timezone.utc) if data.archived else None
    _commit(db, "A category with this name and type already exists")
    return CategoryResponse.model_validate(category)


def delete_category(db: Session, category_id: UUID) -> None:
    category = db.get(Category, category_id)
    if not category:
        raise AppError(404, "NOT_FOUND", "Category not found")
    referenced = db.scalar(select(func.count()).select_from(Transaction).where(Transaction.category_id == category_id)) or db.scalar(
        select(func.count()).select_from(Budget).where(Budget.category_id == category_id)
    )
    if referenced:
        raise AppError(409, "CATEGORY_IN_USE", "Category is referenced and cannot be deleted")
    db.delete(category)
    _commit(db, "Category could not be deleted")


def _transaction_query():
    source = aliased(Account)
    destination = aliased(Account)
    return (
        select(Transaction, source.name, destination.name, Category.name)
        .join(source, Transaction.account_id == source.id)
        .outerjoin(destination, Transaction.to_account_id == destination.id)
        .outerjoin(Category, Transaction.category_id == Category.id)
    )


def _transaction_response(row) -> TransactionResponse:
    transaction, account_name, to_account_name, category_name = row
    return TransactionResponse(
        **{column.name: getattr(transaction, column.name) for column in Transaction.__table__.columns},
        account_name=account_name,
        to_account_name=to_account_name,
        category_name=category_name,
    )


def list_transactions(db: Session, filters: list, limit: int, offset: int):
    total = db.scalar(select(func.count()).select_from(Transaction).where(*filters)) or 0
    rows = db.execute(
        _transaction_query().where(*filters).order_by(Transaction.occurred_on.desc(), Transaction.created_at.desc()).limit(limit).offset(offset)
    ).all()
    return [_transaction_response(row) for row in rows], total


def get_transaction(db: Session, transaction_id: UUID) -> TransactionResponse:
    row = db.execute(_transaction_query().where(Transaction.id == transaction_id)).one_or_none()
    if not row:
        raise AppError(404, "NOT_FOUND", "Transaction not found")
    return _transaction_response(row)


def _validate_transaction(db: Session, data: TransactionCreate, existing: Transaction | None = None) -> None:
    account_ids = {data.account_id}
    if data.to_account_id:
        account_ids.add(data.to_account_id)
    accounts = {account.id: account for account in db.scalars(select(Account).where(Account.id.in_(account_ids)))}
    if len(accounts) != len(account_ids):
        raise AppError(422, "INVALID_ACCOUNT", "One or more accounts do not exist")
    existing_accounts = {existing.account_id, existing.to_account_id} if existing else set()
    for account in accounts.values():
        if account.archived_at and account.id not in existing_accounts:
            raise AppError(422, "ARCHIVED_ACCOUNT", "Archived accounts cannot receive new transactions")
        if data.occurred_on < account.opening_date:
            raise AppError(422, "BEFORE_OPENING_DATE", "Transaction date cannot precede an account opening date")
    if data.category_id:
        category = db.get(Category, data.category_id)
        if not category or category.kind != data.kind:
            raise AppError(422, "INVALID_CATEGORY", "Category type must match the transaction type")
        if category.archived_at and (not existing or category.id != existing.category_id):
            raise AppError(422, "ARCHIVED_CATEGORY", "Archived categories cannot receive new transactions")


def create_transaction(db: Session, data: TransactionCreate) -> TransactionResponse:
    existing = db.get(Transaction, data.id)
    if existing:
        if all(getattr(existing, field) == value for field, value in data.model_dump().items()):
            return get_transaction(db, existing.id)
        raise AppError(409, "CONFLICT", "Transaction ID is already in use")
    _validate_transaction(db, data)
    transaction = Transaction(**data.model_dump())
    db.add(transaction)
    _commit(db, "Transaction conflicts with existing data")
    return get_transaction(db, transaction.id)


def update_transaction(db: Session, transaction_id: UUID, data: TransactionPatch) -> TransactionResponse:
    transaction = db.get(Transaction, transaction_id)
    if not transaction:
        raise AppError(404, "NOT_FOUND", "Transaction not found")
    values = {column.name: getattr(transaction, column.name) for column in Transaction.__table__.columns}
    values.update(data.model_dump(exclude_unset=True))
    complete = TransactionCreate(**{field: values[field] for field in TransactionCreate.model_fields})
    _validate_transaction(db, complete, transaction)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(transaction, field, value)
    _commit(db, "Transaction conflicts with existing data")
    return get_transaction(db, transaction.id)


def delete_transaction(db: Session, transaction_id: UUID) -> None:
    transaction = db.get(Transaction, transaction_id)
    if not transaction:
        raise AppError(404, "NOT_FOUND", "Transaction not found")
    db.delete(transaction)
    _commit(db, "Transaction could not be deleted")


def _budget_response(row) -> BudgetResponse:
    budget, category_name = row
    return BudgetResponse(
        **{column.name: getattr(budget, column.name) for column in Budget.__table__.columns},
        category_name=category_name,
    )


def list_budgets(db: Session, filters: list, limit: int, offset: int):
    total = db.scalar(select(func.count()).select_from(Budget).where(*filters)) or 0
    rows = db.execute(select(Budget, Category.name).join(Category).where(*filters).order_by(Budget.month.desc(), Category.name).limit(limit).offset(offset)).all()
    return [_budget_response(row) for row in rows], total


def get_budget(db: Session, budget_id: UUID) -> BudgetResponse:
    row = db.execute(select(Budget, Category.name).join(Category).where(Budget.id == budget_id)).one_or_none()
    if not row:
        raise AppError(404, "NOT_FOUND", "Budget not found")
    return _budget_response(row)


def create_budget(db: Session, data: BudgetCreate) -> BudgetResponse:
    existing = db.get(Budget, data.id)
    if existing:
        if all(getattr(existing, field) == value for field, value in data.model_dump().items()):
            return get_budget(db, existing.id)
        raise AppError(409, "CONFLICT", "Budget ID is already in use")
    category = db.get(Category, data.category_id)
    if not category or category.kind != "expense" or category.archived_at:
        raise AppError(422, "INVALID_CATEGORY", "Budget category must be an active expense category")
    budget = Budget(**data.model_dump())
    db.add(budget)
    _commit(db, "A budget already exists for this category and month")
    return get_budget(db, budget.id)


def update_budget(db: Session, budget_id: UUID, data: BudgetPatch) -> BudgetResponse:
    budget = db.get(Budget, budget_id)
    if not budget:
        raise AppError(404, "NOT_FOUND", "Budget not found")
    budget.amount = data.amount
    _commit(db, "Budget could not be updated")
    return get_budget(db, budget.id)


def delete_budget(db: Session, budget_id: UUID) -> None:
    budget = db.get(Budget, budget_id)
    if not budget:
        raise AppError(404, "NOT_FOUND", "Budget not found")
    db.delete(budget)
    _commit(db, "Budget could not be deleted")


def finance_totals(rows: Iterable[tuple[Transaction, str | None]], month: str) -> FinanceSummaryResponse:
    income = ZERO
    expense = ZERO
    categories: dict[tuple[UUID, str], Decimal] = defaultdict(lambda: ZERO)
    for transaction, category_name in rows:
        if transaction.kind == "income":
            income += transaction.amount
        elif transaction.kind == "expense":
            expense += transaction.amount
            categories[(transaction.category_id, category_name or "Unknown")] += transaction.amount
    return FinanceSummaryResponse(
        month=month,
        income=income,
        expense=expense,
        net_cash_flow=income - expense,
        expense_by_category=[
            CategoryTotal(category_id=category_id, category_name=name, amount=amount)
            for (category_id, name), amount in sorted(categories.items(), key=lambda item: item[1], reverse=True)
        ],
    )


def get_finance_summary(db: Session, month: date) -> FinanceSummaryResponse:
    next_month = date(month.year + (month.month == 12), month.month % 12 + 1, 1)
    rows = db.execute(
        select(Transaction, Category.name)
        .outerjoin(Category, Transaction.category_id == Category.id)
        .where(Transaction.occurred_on >= month, Transaction.occurred_on < next_month)
    ).all()
    # ponytail: one personal month is aggregated in memory; move this to SQL if profiling shows a limit.
    return finance_totals(rows, month.strftime("%Y-%m"))
