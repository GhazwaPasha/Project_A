# Neon event ledger cutover (shadow / dual-write / backfill)

This document captures the **operational choices** for moving from legacy Supabase-shaped tables to the **append-only** `ledger_events` model and `services/command-api`.

## Modes

1. **Shadow (recommended early):** append `journal.posted` (and projections) **without** writing legacy `journal_entries`. Compare projection balances vs legacy trial balance in an admin report until parity is proven.
2. **Dual-write:** set `DUAL_WRITE_LEGACY_JOURNAL=true` on **command-api** so `POST /journal/post` also inserts `journal_entries` / `journal_entry_lines` in the same database transaction as the event + projection updates. Higher cost, faster UI parity for screens still reading legacy tables.
3. **Cutover:** freeze legacy writers; point UI reads at projections; optionally **backfill** historical rows into `ledger_events` if policy requires a single auditable stream.

## Backfill strategy (sketch)

- Export historical `journal_entries` + lines ordered by `(organization_id, posted_at, id)`.
- Emit synthetic `journal.posted` events (or `journal.migrated` if you prefer a distinct type) with `payload` mirroring the historical lines.
- Rebuild `ledger_projection_account_balance` from events (batch job) and reconcile totals.

## Web app status

- **Browser:** Supabase Auth helpers and `createClientComponentClient` are removed; **Auth.js** drives sessions.
- **Server:** `app-data-authorize` and voucher org checks use **Neon** via `getSql()`. `DataServiceAdmin` still uses the **service-role Supabase client** as an interim bridge for broad CRUD until those reads/writes are ported to SQL.

## Checklist before production cutover

- [ ] Apply `database/migrations_v2/*.sql` on the target Neon branch.
- [ ] Run `services/command-api` with `COMMAND_API_SECRET` and private networking where possible.
- [ ] Configure `COMMAND_API_URL` + `COMMAND_API_SECRET` on the Next.js host.
- [ ] Choose shadow vs dual-write; document the decision per tenant.
- [ ] Add monitoring for command-api latency, idempotency conflicts (`23505`), and projection drift vs legacy reports.
