import re
from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Generic, Literal, TypeVar
from uuid import UUID

from pydantic import (
    AfterValidator,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    PlainSerializer,
    model_validator,
)

from app.core.time import today_bangkok

AccountKind = Literal["cash", "bank", "ewallet"]
CategoryKind = Literal["income", "expense"]
TransactionKind = Literal["income", "expense", "transfer"]
Name = Annotated[
    str,
    BeforeValidator(lambda value: value.strip() if isinstance(value, str) else value),
    Field(min_length=1, max_length=100),
]
Note = Annotated[str, Field(max_length=2000)]


def parse_money(value: object) -> object:
    if isinstance(value, Decimal):
        return value
    if not isinstance(value, str) or not re.fullmatch(r"-?\d+(?:\.\d{1,2})?", value):
        raise ValueError("Money must be a plain decimal string with at most two decimal places")
    return value


Money = Annotated[Decimal, BeforeValidator(parse_money), Field(max_digits=14, decimal_places=2)]
PositiveMoney = Annotated[Decimal, BeforeValidator(parse_money), Field(gt=0, max_digits=14, decimal_places=2)]


def not_future(value: date) -> date:
    if value > today_bangkok():
        raise ValueError("Date cannot be in the future")
    return value


def parse_month(value: object) -> object:
    if isinstance(value, str):
        if not re.fullmatch(r"\d{4}-\d{2}", value):
            raise ValueError("Month must use YYYY-MM")
        return date.fromisoformat(f"{value}-01")
    return value


def first_day(value: date) -> date:
    if value.day != 1:
        raise ValueError("Month must use its first day")
    return value


PastDate = Annotated[date, AfterValidator(not_future)]
Month = Annotated[
    date,
    BeforeValidator(parse_month),
    AfterValidator(first_day),
    PlainSerializer(lambda value: value.strftime("%Y-%m"), return_type=str),
]


class WireModel(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)


class AccountCreate(WireModel):
    id: UUID
    name: Name
    kind: AccountKind
    opening_balance: Money
    opening_date: PastDate


class AccountPatch(WireModel):
    name: Name | None = None
    archived: bool | None = None

    @model_validator(mode="after")
    def require_change(self) -> "AccountPatch":
        if not self.model_fields_set:
            raise ValueError("At least one field is required")
        if any(getattr(self, field) is None for field in self.model_fields_set):
            raise ValueError("Updated account fields cannot be null")
        return self


class AccountResponse(WireModel):
    id: UUID
    name: str
    kind: AccountKind
    opening_balance: Decimal
    opening_date: date
    archived_at: datetime | None
    current_balance: Decimal
    created_at: datetime
    updated_at: datetime


class CategoryCreate(WireModel):
    id: UUID
    name: Name
    kind: CategoryKind


class CategoryPatch(WireModel):
    name: Name | None = None
    archived: bool | None = None

    @model_validator(mode="after")
    def require_change(self) -> "CategoryPatch":
        if not self.model_fields_set:
            raise ValueError("At least one field is required")
        if any(getattr(self, field) is None for field in self.model_fields_set):
            raise ValueError("Updated category fields cannot be null")
        return self


class CategoryResponse(WireModel):
    id: UUID
    name: str
    kind: CategoryKind
    archived_at: datetime | None
    created_at: datetime
    updated_at: datetime


class TransactionCreate(WireModel):
    id: UUID
    kind: TransactionKind
    account_id: UUID
    to_account_id: UUID | None = None
    category_id: UUID | None = None
    amount: PositiveMoney
    occurred_on: PastDate
    note: Note | None = None

    @model_validator(mode="after")
    def valid_shape(self) -> "TransactionCreate":
        if self.kind == "transfer":
            if not self.to_account_id or self.to_account_id == self.account_id or self.category_id:
                raise ValueError("Transfers require different source and destination accounts and no category")
        elif not self.category_id or self.to_account_id:
            raise ValueError("Income and expenses require a category and no destination account")
        return self


class TransactionPatch(WireModel):
    kind: TransactionKind | None = None
    account_id: UUID | None = None
    to_account_id: UUID | None = None
    category_id: UUID | None = None
    amount: PositiveMoney | None = None
    occurred_on: PastDate | None = None
    note: Note | None = None

    @model_validator(mode="after")
    def require_change(self) -> "TransactionPatch":
        if not self.model_fields_set:
            raise ValueError("At least one field is required")
        required = {"kind", "account_id", "amount", "occurred_on"}
        if any(getattr(self, field) is None for field in self.model_fields_set & required):
            raise ValueError("Required transaction fields cannot be null")
        return self


class TransactionResponse(WireModel):
    id: UUID
    kind: TransactionKind
    account_id: UUID
    account_name: str
    to_account_id: UUID | None
    to_account_name: str | None
    category_id: UUID | None
    category_name: str | None
    amount: Decimal
    occurred_on: date
    note: str | None
    created_at: datetime
    updated_at: datetime


class BudgetCreate(WireModel):
    id: UUID
    category_id: UUID
    month: Month
    amount: PositiveMoney


class BudgetPatch(WireModel):
    amount: PositiveMoney


class BudgetResponse(WireModel):
    id: UUID
    category_id: UUID
    category_name: str
    month: Month
    amount: Decimal
    created_at: datetime
    updated_at: datetime


T = TypeVar("T")


class ListResponse(WireModel, Generic[T]):
    items: list[T]
    total: int
    limit: int
    offset: int


class CategoryTotal(WireModel):
    category_id: UUID
    category_name: str
    amount: Decimal


class FinanceSummaryResponse(WireModel):
    month: str
    income: Decimal
    expense: Decimal
    net_cash_flow: Decimal
    expense_by_category: list[CategoryTotal]
