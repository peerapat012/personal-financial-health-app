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
