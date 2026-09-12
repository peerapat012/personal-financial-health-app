# Personal Finance + Health Desktop App

Status: V1 product specification and planning baseline. This document defines what the first usable release must do. It does not authorize application implementation by itself.

## Product overview

This is a desktop-first personal app for recording finances and health data, viewing small useful summaries, and tracking a few concrete goals. It is designed for one person and one developer. The first client is a Windows desktop app built with Tauri 2, React, TypeScript, and Vite. A single FastAPI service is the only path from the desktop client to Neon PostgreSQL.

The app is online-required in V1. Desktop-first describes the user experience and packaging; it does not mean offline-first. Neon is the source of truth. The desktop app never contains database credentials and never connects to Neon directly.

## Target user

The target user is the owner of the app, using it privately to maintain a simple record of personal money and health. Phase 5 adds one provisioned sign-in identity. There is no public registration, multi-user access, tenant model, sharing, or administrator role.

## Goals

- Record an income, expense, weight entry, or workout quickly after opening the relevant screen.
- Make monthly finance and basic health trends understandable without a complex analytics system.
- Keep balances, summaries, dashboard cards, and goal progress derived from the same canonical data.
- Make data easy to correct, export, back up, and restore operationally.
- Keep the backend and contracts usable by a future mobile client.
- Keep the codebase small enough for one developer to maintain.

## Non-goals

- Multi-user identity, roles, sharing, household finance, or multi-tenancy.
- Offline writes, local database sync, conflict resolution, real-time subscriptions, or background synchronization.
- Bank connections, OCR, receipt scanning, AI advice, investment market APIs, tax accounting, double-entry accounting, credit-card interest, or multiple currencies.
- Medical records, diagnosis, treatment recommendations, nutrition plans, or a health score.
- Notifications, recurring transactions, scheduled jobs, complex automation, or a plugin system.
- Microservices, CQRS, event sourcing, message brokers, Redis, GraphQL, or a generic repository layer.

## MVP scope

The V1 navigation is Dashboard, Finance, Health, Goals, and Settings.

### Finance

- Accounts: cash, bank, and e-wallet accounts; opening balance/date; archive and unarchive.
- Categories: one level, separately typed as income or expense; create, rename, archive, and unarchive.
- Transactions: income, expense, and transfers; positive amounts; date, account, optional category, and note.
- Monthly budgets: one budget amount per expense category and calendar month.
- Monthly summary: income, expense, net cash flow, spending by category, and account balances.

Balances are derived from opening balance and transactions. No stored `current_balance` or balance cache is needed in V1. Transfers are excluded from income and expense totals. A transfer is one transaction row with a source and destination account so create, edit, and delete are atomic.

### Health

- Weight logs: one optional weight value per day, with an optional note.
- Workout logs: multiple workouts per day with activity type, duration, and note.
- Basic summaries: latest weight, weight trend, workout minutes, and simple date-range totals.

### Goals

- Financial goals tied to an account balance target.
- Weight goals tied to a baseline and target weight.
- Start date, optional due date, progress, achieved state, and archive state.

Goal progress is calculated from current canonical data. A goal is a milestone and does not reserve money or alter account balances.

### Settings

- Display the fixed V1 currency, units, and timezone.
- Lock the session and clear the in-memory token and client data.
- Export a JSON snapshot through a user-selected file path.
- Display app version and API connectivity status.

## Main user flows

1. After installation, the app connects to the deployed API and discovers its sign-in mode. With Better Auth activated, the owner enters username/password; the API verifies the session and owner ID. Legacy token mode remains available until activation. Both modes hold tokens only in memory.
2. The user opens Dashboard, chooses a month, and sees finance, health, and active-goal summaries.
3. The user creates an account and categories, then records income, expenses, and transfers from Finance.
4. The user creates a monthly category budget and compares actual expense totals with the budget.
5. The user records today's weight or a workout from Health and reviews a date-range summary.
6. The user creates a financial or weight goal and reviews calculated progress on Dashboard or Goals.
7. The user edits or deletes a record after confirmation. A failed request keeps the form values available for retry.
8. The user locks the app or closes it; the token and client-side data are cleared.

### Recommended post-install flow

Keep first run short: welcome and privacy note, configured sign-in form, connection/authentication result, then Dashboard. If no finance data exists, Dashboard shows one primary action to create the first account and a secondary option to begin with Health. After an account exists, the next empty-state action is to record the first transaction. Goals remain optional. Do not require a profile, tutorial carousel, sample data, or preference wizard; V1 already fixes THB, kilograms, and `Asia/Bangkok`.

## Dashboard requirements

Dashboard accepts a selected calendar month and defaults to the current month in `Asia/Bangkok`. It displays:

- Total account balance as of today, clearly labelled with its date.
- Income, expense, and net cash flow for the selected month.
- Actual expense by category and budget-versus-actual values for configured budgets.
- Latest recorded weight and its date, plus workout minutes in the selected month.
- Active financial and weight goals with progress and optional due date.
- The five most recent transactions.
- Quick actions for adding a transaction, weight log, or workout.

Empty cards explain what to record next. Loading and error states are visible and do not silently show stale-looking zeroes. Gaps in health data remain gaps; missing data is not treated as zero.

## Finance requirements

Accounts allow a name, kind, opening balance, opening date, and archive state. Negative opening balances are allowed. An account with transactions cannot change its opening balance or opening date. Archived accounts remain in historical reports but cannot receive new transactions. An account can be deleted only when nothing references it.

Transactions use a positive `amount` and a `kind` of `income`, `expense`, or `transfer`. Income and expense require a matching category type. Transfers require different source and destination accounts and no category. Transaction dates cannot be in the future or before the relevant account opening date. V1 uses hard delete after confirmation and has no audit history or trash.

Budgets use a calendar month (`YYYY-MM`) and one positive amount per expense category. A category can have at most one budget for a month. Budgets are guidance only; they do not block spending. Archived categories remain usable for historical calculations but cannot receive a new budget or transaction.

Monthly summaries exclude opening balances and transfers from income and expense. The API is the owner of money calculations; the frontend formats decimal strings and does not calculate authoritative totals with JavaScript floating point.

## Health requirements

Weight log dates and workout dates are calendar dates in `Asia/Bangkok`, stored as PostgreSQL `date`. Future dates are rejected. A weight log has at most one row per day. Weight is optional on a row only when another supported value or note is present.

Workout duration is an integer number of minutes. V1 activity types are `walk`, `run`, `cycle`, `strength`, and `other`. Calories, routes, wearable data, medical interpretation, and exercise plans are deferred.

Basic summaries use only available values. A seven-day weight view may show the latest value and average of recorded values; it must also show how many days had data. Workout summaries show total minutes for a selected range and month.

## Goals requirements

Financial goals store an account, baseline amount, target amount, start date, and optional due date. The target must be greater than the baseline. Current progress uses the account balance as of today. Weight goals store baseline and target weight; the target may be higher or lower but cannot equal the baseline. Current progress uses the latest weight on or after the start date.

Progress is clamped to 0–100% for display while the raw ratio remains available to the API. Achieved is calculated, so a goal can return to in-progress after later data changes. Archived goals are hidden from the dashboard. Editing a goal's type, baseline, target, account, or start date requires creating a new goal; name and due date are editable.

## Functional requirements

- All business requests use `/api/v1` and require the personal bearer token.
- Forms validate obvious errors before sending and display field errors near the field.
- The backend validates every request with Pydantic and service rules, then relies on PostgreSQL constraints for invariants.
- Money uses decimal strings over JSON. Amounts accept at most two decimal places and must be greater than zero where specified.
- Dates use `YYYY-MM-DD`; timestamps use ISO 8601 UTC.
- Lists support pagination only where useful, with a default limit of 50 and maximum of 200.
- Delete actions require confirmation. Unsaved form changes warn before navigation.
- Dashboard and goal calculations reuse backend finance and health logic rather than duplicating formulas in React.
- Export includes business tables and a schema version, but never credentials or configuration secrets.

## Basic non-functional requirements

- Windows is the first build and test target; the installer must run without Node.js or Python installed.
- Production API traffic uses HTTPS. The desktop release uses a restricted Tauri capability set and production CSP.
- A warm backend with ordinary V1 data should return list and summary requests promptly; measure before adding infrastructure.
- Use one FastAPI business API, one small Better Auth service, one Neon database, and one desktop client. Alembic manages business tables; Better Auth manages only its prefixed auth tables through an explicit command.
- Use strict TypeScript, Pydantic validation, SQLAlchemy, and Alembic. Use Zod where it improves a frontend boundary, not for every type.
- Keep API errors predictable with an error code, human-readable message, optional field details, and request ID.
- Loading, empty, network failure, and server error states are part of every data screen.

## Security and privacy expectations

- Neon credentials exist only in backend environment variables. They must never appear in Vite variables, Tauri assets, Rust constants, logs, or API responses.
- Phase 5 authentication uses Better Auth with one provisioned owner, disabled public signup, and owner-ID verification in FastAPI. Legacy personal-token mode is retained until activation; the modes never silently fall back to each other.
- Locking or closing clears local token and client data. Lock also attempts Better Auth session revocation; unconfirmed revocation is reported. The backend rejects expired/revoked sessions. In legacy mode, revoke a compromised token by rotating the digest.
- Production database runtime credentials use a restricted role. Migration credentials are separate and are never shipped to the desktop.
- Logs exclude authorization headers, tokens, database URLs, notes, request bodies, and personal finance or health values.
- The app does not claim that a client-side lock protects data from malware or a user who already controls the machine.
- Export is treated as sensitive personal data and requires an explicit save action.

## Future features

Add these only after V1 usage demonstrates a need and each feature gets its own small design:

- Recurring transactions and reminders.
- CSV import with preview, mapping, duplicate detection, and rollback.
- Secure token persistence using the operating system credential store.
- Multi-currency, investments, debt, and richer accounting.
- Wearable integrations, nutrition, attachments, and additional health metrics.
- Notifications, tray behavior, signed auto-update, and improved backup automation.
- A mobile client consuming the same versioned API.

## Explicitly deferred features

AI, OCR, bank integrations, Apple Health, Google Health Connect, investment market APIs, offline mode, sync, multi-user identity, social features, medical guidance, server-side job infrastructure, and real-time updates are outside MVP. They require new security, data ownership, or operational decisions and must not be smuggled into the first implementation.

## Decisions carried from the existing repository draft

The existing draft's useful decisions are retained: Windows-first delivery, online-required operation, `THB` and `Asia/Bangkok`, UTC system timestamps, memory-only token storage, no SQLite, derived account balances, simple feature folders, a single FastAPI service, and no infrastructure added for hypothetical scale. The current request changes monthly budgets from deferred work to MVP work and uses separate `financial_goals` and `health_goals` tables for clearer contracts.
