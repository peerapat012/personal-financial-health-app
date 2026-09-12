# Private authentication service

Better Auth owns username/password hashing and sessions. FastAPI remains the only desktop-facing API and accepts only the configured `OWNER_USER_ID`. Public signup is blocked. The desktop keeps session tokens in memory and never connects to this service or PostgreSQL directly.

## Setup and activation

1. Install Node 22+ and run `npm ci` here.
2. Copy `.env.example` to `.env`. Set the runtime and direct PostgreSQL URLs, a randomly generated secret of at least 32 characters, and `BETTER_AUTH_URL`. Use HTTPS remotely, or loopback HTTP for a co-located service.
3. Run `npm run migrate` against development/test first. Better Auth manages only `auth_user`, `auth_session`, `auth_account`, and `auth_verification`; business tables stay under Alembic. Migration never runs at startup. Back up production before migrating and test the pinned lockfile version before upgrades.
4. Grant the auth runtime database role SELECT, INSERT, UPDATE, DELETE on those four tables only. Keep the direct migration URL out of the running service's environment.
5. Copy `.env.owner.example` to `.env.owner`, set the owner's details and a unique password of at least 12 characters, then run `npm run create-owner`. This local command refuses a second owner and prints the new `OWNER_USER_ID`. Store the password in your password manager and remove `.env.owner` afterward. Local env files are gitignored.
6. Run `npm start` or deploy `server.mjs` with runtime environment variables. The default host is `127.0.0.1`; use `HOST=0.0.0.0` only if your hosting platform requires it, with HTTPS and network access controls in front. Public `/api/auth/sign-up/email` must return 404.
7. Set FastAPI's `AUTH_MODE=better_auth`, `BETTER_AUTH_URL` to the service root URL, and `OWNER_USER_ID` to the provisioned ID. Remove the unused `PERSONAL_API_TOKEN_SHA256` variable, then restart FastAPI. The desktop discovers the sign-in mode automatically.

Until activation, `AUTH_MODE=personal_token` retains existing token sign-in. Better Auth mode never falls back to personal tokens. The app still contains one owner's shared business data, not a multi-user data model.

Lock clears local memory immediately and attempts remote revocation. If offline, the UI reports unconfirmed revocation. Sessions expire after 12 hours. Closing the desktop clears local memory but cannot guarantee remote revocation.

One auth process uses in-memory rate limits: five username login attempts per minute. Use shared/database rate limits before adding replicas. Never disable TLS verification. Do not log passwords, tokens, request bodies, authorization headers, or database URLs.

## Checks

`npm test` exercises the real Better Auth plugins with an in-memory test adapter: login, bearer session, revocation, blocked signup, configuration validation, and rate limiting. Production uses PostgreSQL. Live migration and owner login still require deployment configuration.

References: [username plugin](https://better-auth.com/docs/plugins/username), [bearer sessions](https://better-auth.com/docs/plugins/bearer), [PostgreSQL adapter](https://better-auth.com/docs/adapters/postgresql).
