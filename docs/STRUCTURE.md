# Repository Structure

## Target tree

```text
project-root/
├── apps/
│   ├── desktop/
│   │   ├── src/
│   │   │   ├── components/
│   │   │   ├── features/
│   │   │   │   ├── dashboard/
│   │   │   │   ├── finance/
│   │   │   │   ├── health/
│   │   │   │   └── goals/
│   │   │   ├── hooks/
│   │   │   ├── lib/
│   │   │   ├── routes/
│   │   │   ├── stores/
│   │   │   └── types/
│   │   └── src-tauri/
│   └── api/
│       ├── app/
│       │   ├── main.py
│       │   ├── routes/
│       │   ├── models/
│       │   ├── schemas/
│       │   ├── services/
│       │   ├── core/
│       │   └── db.py
│       └── migrations/
├── docs/
├── .gitignore
└── README.md
```

Create directories and files only when a feature needs them. This tree describes ownership, not a demand to scaffold empty folders now.

## Desktop directories

- `apps/desktop/src/components/`: shared UI primitives and shared feedback components used by at least two features.
- `apps/desktop/src/features/`: feature-owned screens and behavior. Keep Dashboard, Finance, Health, and Goals code close to its feature.
- `apps/desktop/src/hooks/`: hooks shared by multiple features. Feature hooks stay under their feature.
- `apps/desktop/src/lib/`: API client, formatting, query setup, and small stable infrastructure utilities.
- `apps/desktop/src/routes/`: route definitions and route-level composition.
- `apps/desktop/src/stores/`: truly global client state such as the in-memory session/lock state. Server data belongs in the query cache.
- `apps/desktop/src/types/`: cross-feature types only. Feature-only types belong beside the feature.
- `apps/desktop/src-tauri/`: Rust, Tauri configuration, capabilities, icons, and narrow native commands.

Recommended feature shape:

```text
features/finance/
├── api/finance.api.ts
├── components/
├── hooks/useTransactions.ts
├── pages/FinancePage.tsx
└── types.ts
```

The post-install welcome, token form, and session validation belong with the app-level session gate, not inside a business feature. Keep this small until it needs its own file; if extracted, use `apps/desktop/src/components/SessionGate.tsx`. First-account and first-entry prompts remain in the Dashboard and feature empty states.

## Backend directories

- `apps/api/app/main.py`: creates the FastAPI app, middleware, exception handlers, and route registration.
- `apps/api/app/routes/`: HTTP paths, dependencies, status codes, and response models. Routes do not contain business calculations.
- `apps/api/app/models/`: SQLAlchemy table mappings, constraints, and query relationships.
- `apps/api/app/schemas/`: Pydantic request, response, filter, and error schemas.
- `apps/api/app/services/`: business rules, calculations, and mutation transaction boundaries.
- `apps/api/app/core/`: configuration, authentication, errors, and small cross-cutting concerns when they have a clear owner.
- `apps/api/app/db.py`: engine creation, session lifecycle, and database dependency.
- `apps/api/migrations/`: Alembic history. Update a model and its migration together.

Examples:

| Item | Location | Purpose |
|---|---|---|
| `TransactionForm.tsx` | `apps/desktop/src/features/finance/components/` | Finance-specific form UI. |
| `TransactionTable.tsx` | `apps/desktop/src/features/finance/components/` | Finance-specific list and actions. |
| `useTransactions.ts` | `apps/desktop/src/features/finance/hooks/` | Finance queries, filters, and mutations. |
| `finance.api.ts` | `apps/desktop/src/features/finance/api/` | Typed calls to finance endpoints. |
| `Transaction` TypeScript type | `features/finance/types.ts` for view types; `lib/api-types.ts` for wire types | Keep local semantics close to usage. |
| FastAPI finance route | `apps/api/app/routes/finance.py` | HTTP contract and dependency wiring. |
| Finance service | `apps/api/app/services/finance.py` | Finance rules, balances, and transaction boundaries. |
| SQLAlchemy `Transaction` | `apps/api/app/models/transaction.py` | Database mapping and local constraints. |
| Pydantic transaction schemas | `apps/api/app/schemas/finance.py` | Request, response, and filter validation. |
| Budget route/service/model/schema | matching `routes`, `services`, `models`, and `schemas` files | Add only when monthly budgets are implemented. |

Health follows the same pattern: `features/health/pages/HealthPage.tsx`, health components, `useWeightLogs.ts` and `useWorkouts.ts`, `health.api.ts`, and matching backend health route/service/model/schema files.

The initial backend can keep related endpoints together:

| API resource | Route | Service | Model | Schema |
|---|---|---|---|---|
| accounts, categories, transactions, budgets | `app/routes/finance.py` | `app/services/finance.py` | matching finance model files | `app/schemas/finance.py` |
| weight logs, workouts | `app/routes/health.py` | `app/services/health.py` | matching health model files | `app/schemas/health.py` |
| financial goals, health goals | `app/routes/goals.py` | `app/services/goals.py` | matching goal model files | `app/schemas/goals.py` |
| dashboard summary | `app/routes/dashboard.py` | `app/services/dashboard.py` | reads existing models | `app/schemas/dashboard.py` |

## Shared versus feature-specific code

Keep a component inside its feature until a second feature needs the same behavior and semantics. A Button, Dialog, Input, Table, LoadingState, EmptyState, and ErrorState can be shared UI. A transaction table, budget editor, workout form, or goal progress card stays feature-specific.

The shared API client owns base URL, bearer header, timeout, JSON parsing, and error normalization. Feature API modules own endpoint paths and feature request/response types. Shared formatters may format currency, dates, and units; they must not calculate authoritative balances or goal progress.

## Naming conventions

- Python modules and variables use `snake_case`; Python classes use `PascalCase`.
- SQL tables and columns use `snake_case`; IDs end with `_id`, dates with `_date` or `_on`, and timestamps with `_at`.
- React components and type files use `PascalCase` where they export a component; hooks start with `use`.
- Frontend API modules end in `.api.ts`; backend modules use the owning domain name.
- HTTP collections are plural: `/accounts`, `/transactions`, `/budgets`, `/weight-logs`, `/workouts`, `/financial-goals`, and `/health-goals`.
- Use `Transaction` for one entity and `transactions` for a collection. Avoid aliases that hide domain meaning.

## File placement rules

1. Identify the owning feature or layer before creating a file.
2. Put feature behavior under that feature.
3. Put HTTP transport in `routes` and `schemas`, business rules in `services`, and table mappings in `models`.
4. Put app wiring, configuration, auth, errors, and DB lifecycle in `core` or `db.py`.
5. Move code to shared directories only after a second real consumer exists.
6. Do not create `utils`, `helpers`, `common`, or `shared` folders to avoid choosing an owner.

## Dependency boundaries

```text
route -> service -> model/db
feature UI -> feature API/hook -> shared API client
feature code -> shared UI/lib
Tauri native <-> explicit React bridge
```

Feature code may use shared code, but shared code may not import a feature. Routes may use schemas, services, auth, and DB dependencies. Services may use models and queries. Models never import routes or frontend code. Desktop may know the API URL and public JSON contract, but never Neon credentials. Tauri must not own product logic.

Dashboard may compose finance and health service functions; finance and health must not import Dashboard. Avoid circular imports and avoid a second abstraction layer for one implementation.

## Adding a feature

For a new V1 feature such as budgets:

1. Add the relevant database model and Alembic migration.
2. Add Pydantic schemas, service rules, and a focused FastAPI route.
3. Add the feature API wrapper, hook, page, and components as needed.
4. Wire the route and navigation entry.
5. Add focused validation and integration checks.
6. Update `docs/database.md`, `docs/api.md`, and `docs/tasks.md` when the contract changes.

Finance examples are `finance.api.ts`, `TransactionForm.tsx`, and `FinanceService`. Health examples are `health.api.ts`, `WeightLogForm.tsx`, and `HealthService`. Do not make a generic feature framework from these examples.

## When to split

Split a feature into subfolders when several screens make ownership hard to find. Split a backend module when it becomes difficult to review or contains independent rules. Add a new top-level layer only when a concrete requirement needs it. A file count alone is not a reason to split.

## Anti-over-engineering rules

- One FastAPI service, one database, one migration stream.
- No repository, CQRS, event bus, message broker, Redis, service locator, or dependency-injection container without a measured problem.
- Prefer PostgreSQL constraints, Pydantic, and direct service functions over duplicate validation frameworks.
- Do not add a local database or cache for a future mobile app.
- Do not add a shared package until a second client actually shares code and the build cost is justified.
- Preserve existing useful files during repository migration. Creating `apps/desktop` and `apps/api` is a later implementation step, not part of this documentation pass.
