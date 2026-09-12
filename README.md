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

FastAPI owns the single username/password account and its database sessions. After migrating, provision the owner once from `apps/api`; the command prompts without echoing the password:

```powershell
uv run python -m app.provision_owner owner
```

Passwords must be 12-128 characters. The command refuses to replace an existing owner. Migration `0002` removes legacy Better Auth tables, so back up the database and keep the new owner password ready before upgrading an activated installation.

### Backup, migration, and restore

Use the direct PostgreSQL URL for administration. Never put either database URL in the desktop environment or bundle.

```powershell
$env:PFH_DATABASE_URL = (Get-Content apps/api/.env | Select-String '^DATABASE_DIRECT_URL=').Line.Split('=', 2)[1].Replace('postgresql+psycopg://', 'postgresql://')
pg_dump --dbname $env:PFH_DATABASE_URL --format custom --no-owner --no-acl --file personal-health.backup
cd apps/api
uv run alembic current
uv run alembic upgrade head
```

Before migration `0002`, confirm the backup exists and the new owner password is available. After every migration, sign in and exercise one create/read/update/delete flow against a non-production record.

Restore into a new empty database first; do not overwrite the only production copy:

```powershell
pg_restore --dbname "postgresql://restore-user:password@host/empty_restore_db?sslmode=require" --no-owner --no-acl personal-health.backup
cd apps/api
$env:DATABASE_DIRECT_URL = "postgresql://restore-user:password@host/empty_restore_db?sslmode=require"
$env:DATABASE_URL = $env:DATABASE_DIRECT_URL
uv run alembic current
uv run python -m app.check_db
```

Point a test API at the restored database, sign in, verify record counts and CRUD, then schedule any production restore. Keep backups encrypted and restrict access because they contain finance, health, and notes.

### Production API

Set `APP_ENV=production`, an exact HTTPS desktop origin in `CORS_ORIGINS`, and the API hostname in `ALLOWED_HOSTS`. Terminate TLS at the hosting provider and forward HTTP to FastAPI only from that trusted proxy. Requests larger than 1 MiB are rejected. The release desktop CSP permits API connections over HTTPS only.

### Checks

Run `uv run python -m unittest discover -s tests -v` in `apps/api`, and `npm test` plus `npm run build` in `apps/desktop`. Set `TEST_DATABASE_URL` to a migrated, disposable PostgreSQL database to include the destructive rollback-only constraint checks.
