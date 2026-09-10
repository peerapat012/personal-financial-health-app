# Implementation Roadmap

This is a documentation-only roadmap. Do not perform these tasks during the planning pass. Each item should be one focused coding change where practical. `[ ]` means not started.

## Phase 0: foundation

- [x] Create the `apps/desktop` and `apps/api` workspace directories without moving useful existing files.
- [x] Add a minimal root README linking to the six planning documents.
- [x] Add root and app `.gitignore` entries for build output, virtual environments, local env files, and generated artifacts.
- [x] Set up Tauri 2 with React, TypeScript, and Vite. Dependency: none.
- [x] Set TypeScript strict mode and the initial desktop entry point. Dependency: Tauri/Vite setup.
- [x] Set up FastAPI with one app entry point and `/healthz`. Dependency: none.
- [x] Add backend configuration loading and `.env.example`. Dependency: FastAPI setup.
- [x] Add SQLAlchemy engine/session setup using the backend `DATABASE_URL`. Dependency: configuration.
- [x] Add Neon development/test connection checks. Dependency: SQLAlchemy setup.
- [x] Add Alembic configuration using the separate migration connection. Dependency: SQLAlchemy setup.
- [x] Add the initial migration for the V1 schema. Dependency: database design, Alembic setup.
- [x] Add the personal bearer-token dependency and `/api/v1/session`. Dependency: FastAPI setup, configuration.
- [x] Add the shared API error envelope and exception handlers. Dependency: FastAPI setup.
- [x] Add the desktop API client with base URL, in-memory token, timeout, JSON parsing, and error normalization. Dependency: desktop entry point, session contract.
- [x] Add the app shell, lock screen, navigation, and session clear behavior. Dependency: API client, session endpoint.

Phase 0 validation: desktop production build, API foundation checks, Python compile check, SQLAlchemy metadata load, Alembic offline PostgreSQL generation, and live Neon connectivity pass. Neon is migrated to revision `0001` with all eight MVP tables, `alembic_version`, and seven seed categories verified. Rust 1.98.1 is installed; native Tauri compilation awaits the MSVC linker from Visual Studio Build Tools with the Desktop development with C++ workload.

## Phase 1: shared desktop behavior

- [x] Add the post-install session flow around the existing lock screen: short privacy/API explanation, token validation feedback, successful redirect to Dashboard, and no token persistence. Dependency: API client and session endpoint.
- [x] Add route definitions for Dashboard, Finance, Health, Goals, and Settings. Dependency: app shell.
- [x] Add shared loading, empty, error, confirmation, and unsaved-form feedback components. Dependency: app shell.
- [x] Add date, THB, weight, duration, and unit formatters. Dependency: app shell.
- [x] Add frontend transport types from the FastAPI OpenAPI contract or a single maintained wire-type file. Dependency: API client and initial API schemas.
- [x] Add one focused frontend validation approach using native inputs and Zod only where it improves a boundary. Dependency: shared form patterns.

## Phase 2: finance data and screens

- [ ] Add SQLAlchemy models and schemas for accounts and categories if not completed in the initial migration. Dependency: initial migration.
- [ ] Add account and category services and REST routes. Dependency: models, schemas, auth.
- [ ] Add account/category API wrappers and query hooks. Dependency: finance routes.
- [ ] Add account list/create/edit/archive screens. Dependency: API wrappers and shared forms.
- [ ] Add category list/create/edit/archive screens. Dependency: API wrappers and shared forms.
- [ ] Add transaction model, schemas, service, and routes with income, expense, and transfer invariants. Dependency: accounts and categories.
- [ ] Add transaction API wrapper and `useTransactions.ts`. Dependency: transaction routes.
- [ ] Add `TransactionForm.tsx` and `TransactionTable.tsx`. Dependency: transaction hook and shared feedback.
- [ ] Add transaction filters, pagination, delete confirmation, and retry behavior. Dependency: transaction screen.
- [ ] Add budget model, schemas, service, and routes. Dependency: categories.
- [ ] Add budget API wrapper, hook, and monthly budget editor/list. Dependency: budget routes.
- [ ] Add finance balance calculation and monthly summary service functions. Dependency: transactions.
- [ ] Add finance summary response contract and tests for income, expense, transfers, and opening balances. Dependency: summary service.

## Phase 3: health data and screens

- [ ] Add `weight_logs` model, schemas, service, and date upsert/list routes. Dependency: initial migration, auth.
- [ ] Add weight-log API wrapper and hooks. Dependency: weight-log routes.
- [ ] Add weight-log form and history view with empty/error states. Dependency: hooks and shared forms.
- [ ] Add `workouts` model, schemas, service, and CRUD routes. Dependency: initial migration, auth.
- [ ] Add workout API wrapper and hooks. Dependency: workout routes.
- [ ] Add workout form and table with date/activity/duration validation. Dependency: hooks and shared forms.
- [ ] Add basic health summary functions for latest weight, recorded-value averages, and workout minutes. Dependency: weight logs and workouts.
- [ ] Add health summary response contract and focused tests for null values, date ranges, and duration totals. Dependency: summary functions.

## Phase 4: goals

- [ ] Add `financial_goals` model, schemas, service, and routes. Dependency: accounts and balance calculation.
- [ ] Add financial-goal API wrapper, hook, form, and list. Dependency: financial-goal routes.
- [ ] Add `health_goals` model, schemas, service, and routes. Dependency: weight logs and health summary functions.
- [ ] Add health-goal API wrapper, hook, form, and list. Dependency: health-goal routes.
- [ ] Add goal progress calculations and tests for increasing/decreasing weight goals, no-data state, clamping, and achieved state. Dependency: both goal services.

## Phase 5: Dashboard and experience

- [ ] Add the dashboard aggregation service and `/api/v1/dashboard?month=YYYY-MM`. Dependency: finance/health/goals services.
- [ ] Add Dashboard page cards for balances, monthly finance, budgets, health, goals, and recent transactions. Dependency: dashboard API.
- [ ] Add the month selector and correct Asia/Bangkok month boundaries. Dependency: Dashboard page.
- [ ] Add simple charts for expense by category, cash flow, and weight trend using one chart dependency only if needed. Dependency: dashboard/summary responses.
- [ ] Add dashboard loading, empty, error, and no-data states. Dependency: Dashboard page.
- [ ] Add quick-add actions that open existing finance and health forms. Dependency: feature forms.
- [ ] Add Settings page for units/timezone display, session lock, app version, and API status. Dependency: session and app shell.

## Phase 6: data protection and release readiness

- [ ] Add JSON export endpoint and desktop save-file flow. Dependency: auth, database snapshot, Tauri capability review.
- [ ] Add explicit export confirmation and verify secrets are excluded. Dependency: export flow.
- [ ] Add API tests for authentication, validation, 404/409/422 errors, and database rollback. Dependency: all implemented routes.
- [ ] Add PostgreSQL integration checks for transfer atomicity, category type rules, daily uniqueness, budget uniqueness, and goal references. Dependency: test database.
- [ ] Add frontend checks for preserving form data on network failure and retrying a mutation with the same ID. Dependency: API client and mutation screens.
- [ ] Add backup, restore, and migration runbook instructions to the README. Dependency: deployed test database.
- [ ] Configure production CORS, HTTPS, request limits, restricted Tauri capabilities, and CSP. Dependency: deployed API and desktop shell.
- [ ] Build the Windows installer and test CRUD on a machine without Node.js or Python. Dependency: all MVP screens.
- [ ] Verify the desktop bundle and logs contain no Neon credential or personal token. Dependency: release build.
- [ ] Perform a final MVP acceptance pass against `spec.md`, `database.md`, and `api.md`. Dependency: all prior phases.

## Dependency and scope rules

The initial migration must precede feature routes. Models, schemas, service rules, and endpoint contracts for a feature should land together. Dashboard work waits for finance, health, and goals summaries. Charts wait for stable summary responses. Packaging waits for the core CRUD flows.

Do not add mobile code, offline storage, recurring jobs, AI, OCR, bank integrations, health platform integrations, investment APIs, or new infrastructure during these phases. Add them only through a new design decision after V1 proves the need.
