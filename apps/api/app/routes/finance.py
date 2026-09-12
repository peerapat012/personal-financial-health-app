from datetime import date
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.auth import require_session
from app.core.errors import AppError
from app.db import get_db
from app.models.finance import Budget, Transaction
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
    ListResponse,
    TransactionCreate,
    TransactionPatch,
    TransactionResponse,
)
from app.services import finance

router = APIRouter(
    prefix="/api/v1",
    dependencies=[Depends(require_session)],
)
Db = Annotated[Session, Depends(get_db)]
PageLimit = Annotated[int, Query(ge=1, le=200)]
PageOffset = Annotated[int, Query(ge=0)]


def month_date(value: str) -> date:
    try:
        parsed = date.fromisoformat(f"{value}-01")
    except ValueError as error:
        raise AppError(422, "VALIDATION_ERROR", "Month must use YYYY-MM") from error
    if parsed.strftime("%Y-%m") != value:
        raise AppError(422, "VALIDATION_ERROR", "Month must use YYYY-MM")
    return parsed


@router.get("/accounts", response_model=ListResponse[AccountResponse])
def accounts(db: Db, include_archived: bool = False, limit: PageLimit = 50, offset: PageOffset = 0):
    items, total = finance.list_accounts(db, include_archived, limit, offset)
    return ListResponse[AccountResponse](items=items, total=total, limit=limit, offset=offset)


@router.post("/accounts", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
def create_account(data: AccountCreate, db: Db):
    return finance.create_account(db, data)


@router.get("/accounts/{account_id}", response_model=AccountResponse)
def account(account_id: UUID, db: Db):
    return finance.get_account(db, account_id)


@router.patch("/accounts/{account_id}", response_model=AccountResponse)
def update_account(account_id: UUID, data: AccountPatch, db: Db):
    return finance.update_account(db, account_id, data)


@router.delete("/accounts/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(account_id: UUID, db: Db) -> Response:
    finance.delete_account(db, account_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/categories", response_model=ListResponse[CategoryResponse])
def categories(
    db: Db,
    kind: Literal["income", "expense"] | None = None,
    include_archived: bool = False,
    limit: PageLimit = 50,
    offset: PageOffset = 0,
):
    items, total = finance.list_categories(db, kind, include_archived, limit, offset)
    return ListResponse[CategoryResponse](items=items, total=total, limit=limit, offset=offset)


@router.post("/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(data: CategoryCreate, db: Db):
    return finance.create_category(db, data)


@router.get("/categories/{category_id}", response_model=CategoryResponse)
def category(category_id: UUID, db: Db):
    return finance.get_category(db, category_id)


@router.patch("/categories/{category_id}", response_model=CategoryResponse)
def update_category(category_id: UUID, data: CategoryPatch, db: Db):
    return finance.update_category(db, category_id, data)


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: UUID, db: Db) -> Response:
    finance.delete_category(db, category_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/transactions", response_model=ListResponse[TransactionResponse])
def transactions(
    db: Db,
    from_: Annotated[date | None, Query(alias="from")] = None,
    to: date | None = None,
    account_id: UUID | None = None,
    category_id: UUID | None = None,
    kind: Literal["income", "expense", "transfer"] | None = None,
    q: Annotated[str | None, Query(max_length=100)] = None,
    limit: PageLimit = 50,
    offset: PageOffset = 0,
):
    if from_ and to and from_ > to:
        raise AppError(422, "INVALID_DATE_RANGE", "From date cannot be after to date")
    filters = []
    if from_:
        filters.append(Transaction.occurred_on >= from_)
    if to:
        filters.append(Transaction.occurred_on <= to)
    if account_id:
        filters.append(or_(Transaction.account_id == account_id, Transaction.to_account_id == account_id))
    if category_id:
        filters.append(Transaction.category_id == category_id)
    if kind:
        filters.append(Transaction.kind == kind)
    if q:
        filters.append(Transaction.note.ilike(f"%{q}%"))
    items, total = finance.list_transactions(db, filters, limit, offset)
    return ListResponse[TransactionResponse](items=items, total=total, limit=limit, offset=offset)


@router.post("/transactions", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def create_transaction(data: TransactionCreate, db: Db):
    return finance.create_transaction(db, data)


@router.get("/transactions/{transaction_id}", response_model=TransactionResponse)
def transaction(transaction_id: UUID, db: Db):
    return finance.get_transaction(db, transaction_id)


@router.patch("/transactions/{transaction_id}", response_model=TransactionResponse)
def update_transaction(transaction_id: UUID, data: TransactionPatch, db: Db):
    return finance.update_transaction(db, transaction_id, data)


@router.delete("/transactions/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(transaction_id: UUID, db: Db) -> Response:
    finance.delete_transaction(db, transaction_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/budgets", response_model=ListResponse[BudgetResponse])
def budgets(
    db: Db,
    month: str | None = None,
    category_id: UUID | None = None,
    limit: PageLimit = 50,
    offset: PageOffset = 0,
):
    filters = []
    if month:
        filters.append(Budget.month == month_date(month))
    if category_id:
        filters.append(Budget.category_id == category_id)
    items, total = finance.list_budgets(db, filters, limit, offset)
    return ListResponse[BudgetResponse](items=items, total=total, limit=limit, offset=offset)


@router.post("/budgets", response_model=BudgetResponse, status_code=status.HTTP_201_CREATED)
def create_budget(data: BudgetCreate, db: Db):
    return finance.create_budget(db, data)


@router.get("/budgets/{budget_id}", response_model=BudgetResponse)
def budget(budget_id: UUID, db: Db):
    return finance.get_budget(db, budget_id)


@router.patch("/budgets/{budget_id}", response_model=BudgetResponse)
def update_budget(budget_id: UUID, data: BudgetPatch, db: Db):
    return finance.update_budget(db, budget_id, data)


@router.delete("/budgets/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_budget(budget_id: UUID, db: Db) -> Response:
    finance.delete_budget(db, budget_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
