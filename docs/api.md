# HTTP API Contract

## Common contract

The API is JSON over HTTPS in production. Business endpoints use `/api/v1` and require `Authorization: Bearer <token>`. The token is an opaque database session for the single provisioned owner. `GET /healthz` and sign-in are unauthenticated. IDs are UUID strings, dates are `YYYY-MM-DD`, timestamps are ISO 8601 UTC, and money and weight values are decimal strings.

List responses use:

```json
{"items": [], "total": 0, "limit": 50, "offset": 0}
```

`limit` defaults to 50 and is capped at 200. `offset` defaults to 0. Create responses use 201, successful reads/updates use 200, and successful deletes use 204.

Errors use:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request is invalid",
    "fields": {"amount": "Must be greater than zero"},
    "request_id": "uuid"
  }
}
```

Common errors are 401 authentication failure, 404 missing ID, 409 duplicate/reference/archive conflict, 422 invalid input or business rule, 429 rate limit, 503 database/network unavailable, and 500 unexpected server error.

## System endpoints

`POST /api/v1/auth/sign-in` is public, accepts `{"username":"owner","password":"..."}`, and returns only `{"token":"..."}` with `Cache-Control: no-store`. `POST /api/v1/auth/sign-out` requires and revokes the bearer session, returning 204. Public signup is not exposed. Invalid credentials or sessions return 401 and the in-process sign-in limit returns 429. Desktop credentials and tokens are never persisted.

| Method | Path | Purpose | Request/query | Response |
|---|---|---|---|---|
| GET | `/healthz` | Liveness check. Must not expose database details. | None | `{ "status": "ok" }` |
| POST | `/api/v1/auth/sign-in` | Verify the owner and create a session. | `{ "username": "owner", "password": "..." }` | `{ "token": "..." }` |
| POST | `/api/v1/auth/sign-out` | Revoke the current session. | Bearer token | 204 |
| GET | `/api/v1/session` | Validate the token and return V1 display settings. | None | `{ "authenticated": true, "currency": "THB", "timezone": "Asia/Bangkok", "units": {"weight": "kg", "water": "ml"} }` |
| GET | `/api/v1/export` | Return a consistent JSON snapshot for user export. | None | `{ "schema_version": "1", "exported_at": "...", "data": { ... } }` |

Export includes all business tables and no credentials, configuration, or request metadata. It is a read-only operation and may return 503 if the database is unavailable.

## Accounts

| Method | Path | Purpose | Request/query | Response |
|---|---|---|---|---|
| GET | `/api/v1/accounts` | List accounts. | `include_archived` optional boolean; pagination. | Items contain `id`, `name`, `kind`, `opening_balance`, `opening_date`, `archived_at`, and derived `current_balance`. |
| POST | `/api/v1/accounts` | Create an account. | `{ "id": "uuid", "name": "Cash", "kind": "cash", "opening_balance": "0.00", "opening_date": "2026-09-10" }` | Account resource, 201. |
| GET | `/api/v1/accounts/{id}` | Read an account and derived balance. | Path UUID. | Account resource. |
| PATCH | `/api/v1/accounts/{id}` | Rename, archive, or unarchive. | Any of `{ "name": "...", "archived": true }`. Opening fields are immutable after creation and should not be accepted in this operation. | Updated account. |
| DELETE | `/api/v1/accounts/{id}` | Delete an unused account. | Path UUID. | 204. |

Names are trimmed and non-empty. Kind must be `cash`, `bank`, or `ewallet`. Opening date cannot be future. New transactions cannot use archived accounts. Delete returns 409 if transactions or financial goals reference the account.

## Categories

| Method | Path | Purpose | Request/query | Response |
|---|---|---|---|---|
| GET | `/api/v1/categories` | List categories for forms and reports. | `kind=income|expense`, `include_archived`, pagination. | Items contain `id`, `name`, `kind`, and `archived_at`. |
| POST | `/api/v1/categories` | Create a category. | `{ "id": "uuid", "name": "Food", "kind": "expense" }` | Category resource, 201. |
| GET | `/api/v1/categories/{id}` | Read a category. | Path UUID. | Category resource. |
| PATCH | `/api/v1/categories/{id}` | Rename, archive, or unarchive. | `{ "name": "..." }` or `{ "archived": true }`. Kind is immutable. | Updated category. |
| DELETE | `/api/v1/categories/{id}` | Delete an unreferenced category. | Path UUID. | 204. |

Names are unique within a kind. A referenced category cannot change kind or be deleted. Archived categories cannot be selected for new transactions or budgets.

## Transactions

| Method | Path | Purpose | Request/query | Response |
|---|---|---|---|---|
| GET | `/api/v1/transactions` | List transactions newest first. | `from`, `to` inclusive dates; `account_id`; `category_id`; `kind`; `q` note search max 100 chars; pagination. | Items contain transaction fields plus account/category display data. |
| POST | `/api/v1/transactions` | Create income, expense, or transfer. | Income/expense: `{ "id": "uuid", "kind": "expense", "account_id": "uuid", "category_id": "uuid", "amount": "85.00", "occurred_on": "2026-09-10", "note": "Lunch" }`. Transfer replaces category with `to_account_id`. | Transaction resource, 201. |
| GET | `/api/v1/transactions/{id}` | Read one transaction. | Path UUID. | Transaction resource. |
| PATCH | `/api/v1/transactions/{id}` | Edit mutable transaction fields. | Partial transaction body; omitted fields keep their values and nullable fields may be cleared. | Updated transaction. |
| DELETE | `/api/v1/transactions/{id}` | Hard-delete a transaction after UI confirmation. | Path UUID. | 204. |

Amount must be positive, finite, plain decimal with at most two fractional digits. Kind/category shape, account archive state, account opening dates, future date, and transfer source/destination rules are validated before commit. `from <= to`; no silent truncation. A client-supplied duplicate ID with the same payload may return the existing resource; a different payload returns 409.

## Budgets

| Method | Path | Purpose | Request/query | Response |
|---|---|---|---|---|
| GET | `/api/v1/budgets` | List monthly category budgets. | `month=YYYY-MM` optional; `category_id` optional; pagination. | Items contain `id`, `category_id`, `month`, `amount`, and category name. |
| POST | `/api/v1/budgets` | Create a monthly budget. | `{ "id": "uuid", "category_id": "uuid", "month": "2026-09", "amount": "5000.00" }` | Budget resource, 201. |
| GET | `/api/v1/budgets/{id}` | Read a budget. | Path UUID. | Budget resource. |
| PATCH | `/api/v1/budgets/{id}` | Change amount. | `{ "amount": "5500.00" }`. Category and month are immutable. | Updated budget. |
| DELETE | `/api/v1/budgets/{id}` | Delete a budget. | Path UUID. | 204. |

Month is a calendar month represented by its first day in the wire format. Amount must be greater than zero. The category must be an expense category. `(category_id, month)` duplicates return 409.

## Weight logs

| Method | Path | Purpose | Request/query | Response |
|---|---|---|---|---|
| GET | `/api/v1/weight-logs` | List weight logs by date. | `from`, `to` inclusive dates; pagination. | Items contain `id`, `log_date`, `weight_kg`, `note`, timestamps. |
| PUT | `/api/v1/weight-logs/{date}` | Replace or create the one log for a date. | `{ "weight_kg": "82.40", "note": "Morning" }`; omitted values become null. | Weight-log resource, 200. |
| GET | `/api/v1/weight-logs/{date}` | Read the log for a date. | Date path. | Weight-log resource. |
| DELETE | `/api/v1/weight-logs/{date}` | Delete a date's log. | Date path. | 204. |

Date cannot be future. Weight is optional but must be 1.00–500.00 when present; at least weight or non-empty note is required. `PUT` is an atomic upsert and concurrent requests leave one row for the date.

## Workouts

| Method | Path | Purpose | Request/query | Response |
|---|---|---|---|---|
| GET | `/api/v1/workouts` | List workouts newest first. | `from`, `to`, `activity_type`, pagination. | Items contain workout fields and timestamps. |
| POST | `/api/v1/workouts` | Create a workout. | `{ "id": "uuid", "occurred_on": "2026-09-10", "activity_type": "walk", "duration_minutes": 30, "note": "Park" }` | Workout resource, 201. |
| GET | `/api/v1/workouts/{id}` | Read a workout. | Path UUID. | Workout resource. |
| PATCH | `/api/v1/workouts/{id}` | Edit a workout. | Partial mutable fields. | Updated workout. |
| DELETE | `/api/v1/workouts/{id}` | Delete a workout. | Path UUID. | 204. |

Activity type must be `walk`, `run`, `cycle`, `strength`, or `other`. Duration is an integer from 1 through 1,440 minutes. Date cannot be future.

## Goals

### Financial goals

| Method | Path | Purpose | Request/query | Response |
|---|---|---|---|---|
| GET | `/api/v1/financial-goals` | List financial goals with progress. | `include_archived` and pagination. | Items contain stored fields plus `current_amount`, `progress_ratio`, `progress_percent`, and `achieved`. |
| POST | `/api/v1/financial-goals` | Create an account balance goal. | `{ "id": "uuid", "name": "Emergency fund", "account_id": "uuid", "baseline_amount": "10000.00", "target_amount": "30000.00", "start_date": "2026-09-10", "due_date": null }` | Goal resource, 201. |
| GET | `/api/v1/financial-goals/{id}` | Read a goal with progress. | Path UUID. | Goal resource. |
| PATCH | `/api/v1/financial-goals/{id}` | Rename, change due date, archive, or unarchive. | `{ "name": "...", "due_date": "...", "archived": true }`. | Updated goal. |
| DELETE | `/api/v1/financial-goals/{id}` | Delete a goal. | Path UUID. | 204. |

### Health goals

| Method | Path | Purpose | Request/query | Response |
|---|---|---|---|---|
| GET | `/api/v1/health-goals` | List weight goals with progress. | `include_archived` and pagination. | Items contain stored fields plus `current_weight_kg`, `progress_ratio`, `progress_percent`, and `achieved`. |
| POST | `/api/v1/health-goals` | Create a weight goal. | `{ "id": "uuid", "name": "Target weight", "baseline_weight_kg": "82.00", "target_weight_kg": "75.00", "start_date": "2026-09-10", "due_date": null }` | Goal resource, 201. |
| GET | `/api/v1/health-goals/{id}` | Read a goal with progress. | Path UUID. | Goal resource. |
| PATCH | `/api/v1/health-goals/{id}` | Rename, change due date, archive, or unarchive. | Metadata fields only. | Updated goal. |
| DELETE | `/api/v1/health-goals/{id}` | Delete a goal. | Path UUID. | 204. |

Goal names are required. Due date cannot precede start date. Financial target must be greater than baseline. Weight target must differ from baseline and both weights must be 1.00–500.00. Progress is clamped for display but the raw ratio is returned. Archived goals are excluded from Dashboard by default.

Start dates cannot be future. Goal type, account, baseline, target, and start date are immutable; create a new goal to change them. Financial responses also include `account_name`. Current amount is the account balance as of today, including opening balance and transfers; archived accounts remain reportable. Health responses include `current_weight_date` and use the latest non-null weight on or after the start date through today. With no qualifying weight, `current_weight_kg`, `current_weight_date`, `progress_ratio`, and `progress_percent` are null, and `achieved` is false. Ratios and percentages are decimal strings when present. Achieved state is recalculated and can reverse after records change.

Both goal collections support stable pagination and default to excluding archived goals. A repeated create with the same client ID and payload returns the existing goal; a different payload returns 409.

## Dashboard summary

| Method | Path | Purpose | Request/query | Response |
|---|---|---|---|---|
| GET | `/api/v1/dashboard` | Return the Dashboard snapshot for one month. | Required `month=YYYY-MM`. | `{ "month": "2026-09", "account_balances": {...}, "finance": {...}, "budgets": [...], "health": {...}, "goals": [...], "recent_transactions": [...] }` |

The response includes total balance as of today, selected-month income/expense/net cash flow, expense-by-category, budget actuals, latest weight and date, workout minutes, active goals, and five recent transactions. Month boundaries use `Asia/Bangkok`. The service computes these values from one consistent read snapshot. Invalid month format returns 422; database failure returns 503.

Phase 5 concrete response fields:

- `account_balances`: `as_of`, decimal `total`, and all account resources in `items` (including archived accounts).
- `finance`: `month`, decimal `income`, `expense`, `net_cash_flow`, and `expense_by_category` entries containing `category_id`, `category_name`, and decimal `amount`.
- `budgets`: `id`, `category_id`, `category_name`, decimal `amount`, `actual`, and `remaining`. Negative remaining means over budget.
- `health`: latest non-null `latest_weight_kg` and `latest_weight_date` through today, selected-month `workout_minutes`, `recorded_weight_days`, `average_weight_kg`, and `weight_trend` entries (`date`, nullable decimal `weight_kg`). Trend includes every calendar day through today within the selected month, with null gaps. Latest weight is not limited to the reporting month.
- `goals`: active financial/health goal resources, with current progress; `recent_transactions`: the latest five transaction resources across all months.

Money, weights, ratios, and percentages remain decimal strings. Missing weights remain null. PostgreSQL dashboard reads use REPEATABLE READ set before the first query.

## Filtering and validation rules

All date ranges are inclusive. List filters reject malformed dates, `from > to`, invalid UUIDs, and unsupported enum values. A list with no rows returns an empty `items` array and 200. PATCH validates the complete resulting resource, not only the fields supplied. Unknown request fields are rejected by Pydantic. Authentication happens before resource lookup so unauthorized requests do not reveal whether an ID exists.
