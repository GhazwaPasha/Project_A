# Migrations v2 (event ledger + command API)

Numbered SQL migrations for the **append-only event log** and related projections. Apply after `DATABASE_URL` points at your Neon (or Postgres) branch.

**Order:** run files in lexical order (e.g. `001_...sql`, then `002_...sql`).

**Neon branches:** use a dedicated dev/preview branch URL in CI and local `.env`; production uses the production branch connection string. Document each environment’s `DATABASE_URL` in the repo root `.env.example`.

**Optional extension:** `002_enable_pgvector.sql` enables `vector` when your Neon Postgres version supports it (Phase 3).
