# Personal Financial Health App

Single-user desktop app for personal finance and health tracking.

## Documentation

- [Product specification](docs/spec.md)
- [Architecture](docs/architecture.md)
- [Repository structure](docs/STRUCTURE.md)
- [Database design](docs/database.md)
- [API contract](docs/api.md)
- [Implementation roadmap](docs/tasks.md)
- [Frontend and UI guidelines](docs/frontend.md)

## Development

### Desktop

```powershell
cd apps/desktop
npm install
npm run dev
```

Install the [Tauri prerequisites](https://v2.tauri.app/start/prerequisites/) before running `npm run tauri dev`.

### API

Copy `apps/api/.env.example` to `apps/api/.env`, replace placeholders, then run:

```powershell
cd apps/api
uv sync
uv run fastapi dev app/main.py
```

Check database connectivity with `uv run python -m app.check_db`. Run migrations with `uv run alembic upgrade head`.

### Username/password sign-in

Phase 5 adds a private Better Auth service in [`apps/auth`](apps/auth/README.md). Follow its setup instructions to migrate auth tables, provision the single owner, and activate `AUTH_MODE=better_auth` in FastAPI. Existing token sign-in remains active until that configuration changes. The desktop discovers the configured sign-in mode automatically.

### Checks

Run `uv run python -m unittest discover -s tests -v` in `apps/api`, `npm test` in `apps/auth`, and `npm test` plus `npm run build` in `apps/desktop`.
