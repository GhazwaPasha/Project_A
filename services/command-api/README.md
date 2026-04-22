# Command API (event ledger)

TypeScript service (Hono) implementing **journal** commands against Neon (`DATABASE_URL`):

- `POST /journal/propose` — append `journal.proposed` + create `journal_proposals` row
- `POST /journal/approve` — append `journal.approved`
- `POST /journal/post` — append `journal.posted`, update `ledger_projection_account_balance`
- `POST /journal/reverse` — append `journal.reversed`, negate projection deltas
- `GET /journal/proposals?organization_id=…&status=pending|…`
- `GET /journal/projection/trial-balance?organization_id=…`

## Auth trust boundary

The Next.js app verifies **Auth.js** (`auth()`), then proxies with:

- `X-User-Id` — authenticated user id  
- `X-Command-Secret` — must match `COMMAND_API_SECRET` on this service  

Run the API on a **private network** in production; do not expose `COMMAND_API_SECRET` to browsers.

## Env

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | yes | Neon pooled connection string |
| `COMMAND_API_SECRET` | yes | Shared secret with Next.js BFF |
| `PORT` | no | Default `8787` |
| `DUAL_WRITE_LEGACY_JOURNAL` | no | Set `true` to also insert `journal_entries` / `journal_entry_lines` on post |
| `LOG_LEVEL` | no | Default `info` |

## Env

Variables are read from the **repository root** `.env` (same file as the Next.js app). `DATABASE_URL`, `COMMAND_API_SECRET`, etc. live there—no separate `services/command-api/.env` required.

## Run

```bash
cd services/command-api
npm install
npm run dev
```

Apply SQL under `../../database/migrations_v2/` before using commands:

```bash
npm run migrate:v2
```

## Build

```bash
npm run build && npm start
```

## Docker

From repository root:

```bash
docker build -t accountuitive-command-api -f services/command-api/Dockerfile services/command-api
docker run --rm -e DATABASE_URL -e COMMAND_API_SECRET -p 8787:8787 accountuitive-command-api
```
