# Services

## `command-api/` (TypeScript / Hono)

Event-sourced **journal** commands against Neon. See [command-api/README.md](command-api/README.md).

**Quick start**

```bash
cd services/command-api
npm install
npm run dev
```

Apply SQL migrations in [../database/migrations_v2/](../database/migrations_v2/) first.

The Next.js app proxies authenticated requests to this service via `/api/commands/*` using `COMMAND_API_URL` and `COMMAND_API_SECRET`.

## Other

The main UI remains in `web-app/`. Database artifacts live in `database/`. Operational scripts live in `scripts/`.
