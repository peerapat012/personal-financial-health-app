# Architecture

## System shape

```text
Tauri 2 Desktop
      |
React + TypeScript + Vite
      |
      | HTTPS / JSON
      v
FastAPI
      |
SQLAlchemy
      |
Neon PostgreSQL
```

There is one backend service and one database. The desktop client talks to the FastAPI HTTPS API only. It must never connect to Neon or bundle `DATABASE_URL`.

## Responsibilities

### Tauri 2

Tauri owns the native window, installer, capabilities, CSP, and narrowly scoped native actions such as choosing an export file path. It does not own business rules, API data access, SQL, balances, or goal calculations. Rust commands are added only when a browser capability is insufficient.

### React, TypeScript, and Vite

React owns screens, forms, navigation, view state, loading/empty/error states, and presentation. Feature API modules call the shared HTTP client. Server data lives in the query/cache mechanism selected during implementation; it is not copied into a second global store. Amounts remain strings in the client and are formatted for display.

Use Zod where it improves a form or untrusted response boundary. Do not create a duplicate schema for every TypeScript type when the OpenAPI contract is sufficient.

### FastAPI

FastAPI owns authentication, request validation, response shapes, business rules, calculations, transaction boundaries, and the public API. Keep it as a modular monolith:

```text
route -> service -> SQLAlchemy query/model -> session -> Neon
```

Routes handle HTTP concerns. Services handle business operations and calculations. SQLAlchemy models map tables and relationships. Pydantic schemas define transport contracts.

### PostgreSQL

Neon is the canonical store. PostgreSQL constraints enforce important invariants, indexes support known list and summary queries, and Alembic is the schema history. Do not add a cache, warehouse, materialized view, or second data store before measurement shows a need.

## Request and data flow

1. The user submits a React form.
2. The feature validates obvious input and calls its `.api.ts` module.
3. The shared client adds the in-memory bearer token, timeout, and JSON headers.
4. FastAPI authenticates the token before business handlers run.
5. Pydantic parses the request. The feature service loads related records and applies cross-row rules.
6. SQLAlchemy executes parameterized queries in one request session. Mutations commit once or roll back.
7. FastAPI returns a response model. Decimal money values are JSON strings.
8. React updates or invalidates affected server queries. It does not invent an authoritative total.

Dashboard and export reads should use a consistent read transaction so their component values come from one database snapshot where practical.

## Authentication

V1 uses one personal access token. The owner creates a high-entropy random token outside the app and keeps it in a password manager. The backend stores only its SHA-256 digest in `PERSONAL_API_TOKEN_SHA256`. The desktop asks for the token on launch, calls `/api/v1/session`, and holds the token in memory only.

The post-install flow is client-side session gating, not a persisted onboarding system. Successful `/api/v1/session` validation opens Dashboard; missing data is handled by normal feature empty states. No onboarding table, completion flag, or additional endpoint is required.

There is no signup, password reset, JWT, refresh token, session table, or user table in V1. Locking clears desktop memory; it does not revoke a stolen token. Rotation happens by changing the backend digest. Every business endpoint, including export, requires the token. Missing and invalid tokens return the same 401 shape.

Before multiple devices can edit data concurrently, add optimistic concurrency and a conflict policy. Before multi-user access, redesign identity, ownership, authorization, and database isolation.

## Configuration and secrets

Backend environment variables include `DATABASE_URL`, token digest, CORS origins, environment, log level, and host port. Runtime uses the Neon pooled URL. Alembic and backup operations use a separate direct URL and migration role. `.env.example` contains placeholders only.

The desktop may know only the public API base URL. A Vite environment variable containing the API URL is configuration, not a secret. No database URL, migration secret, token, or private key may enter the bundle, Tauri config, Rust source, or logs.

## Error handling

Use one error envelope:

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

Use 401 for authentication failure, 404 for missing resources, 409 for conflicts, 422 for validation/business input errors, 429 for rate limiting, 503 for unavailable dependencies, and 500 for unexpected failures. Never return stack traces or secrets. Map known database constraint failures to useful 409/422 responses and roll back failed mutations.

If a mutation times out after being sent, the client must say that the result is unknown and check the resource using the original client-generated ID before retrying. It must not silently create a second ID.

## Logging and observability

Log request ID, route template, status, duration, and safe error code. Do not log authorization headers, tokens, database URLs, notes, request bodies, or finance/health values. Use the hosting provider's logs and basic metrics. No analytics SDK or separate monitoring stack is required in V1.

## Network failure behavior

The app is usable only when the API is reachable. The shell may open while offline, but data screens show a clear connection error and preserve unsent form values. GET requests may retry once for a network failure or 503. Mutations require explicit retry after checking whether the original request committed. There is no offline queue or local write store.

## API versioning

Business endpoints use `/api/v1`. Breaking response or behavior changes require a new version. Additive fields are preferred within a version. The FastAPI OpenAPI document is the contract source for generated or maintained frontend transport types.

## Database and migration approach

Use SQLAlchemy 2 with synchronous `psycopg` and one session per request. Routes remain synchronous when using the synchronous database driver. Alembic migrations are reviewed and run explicitly; the API does not run migrations on startup. Runtime and migration roles are separate. Development, test, and production databases are separate.

## Future mobile architecture

A future mobile client consumes the same HTTPS JSON API and never connects to Neon. Stable UUIDs, platform-neutral JSON, server-owned calculations, and versioned routes are the only preparation required now. Do not create a mobile project, sync layer, or shared UI package in V1. When mobile editing becomes real, evaluate secure credential storage and add concurrency controls before allowing simultaneous edits.

## Key decisions

| Decision | Reason |
|---|---|
| FastAPI is the only remote data-access layer | Keeps Neon credentials server-side and leaves one business-rule boundary for desktop and future mobile. |
| One FastAPI service | The domain is small and one developer should deploy and debug one process. |
| Direct route-to-service-to-model flow | Avoids repository and use-case abstractions with no second implementation. |
| Neon is the only V1 store | Avoids sync, cache invalidation, and offline complexity. |
| Server-derived balances and summaries | Prevents duplicated money logic and stale cached totals. |
| Personal bearer token | Fits a single private user without inventing an identity system. |
| Calendar dates plus UTC timestamps | Makes personal daily records predictable in `Asia/Bangkok` while keeping audit timestamps unambiguous. |
