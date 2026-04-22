-- Append-only ledger events + idempotency + projection (trial balance slice)
-- Tenant: organization_id (UUID)

CREATE TABLE IF NOT EXISTS public.ledger_events (
  id                BIGSERIAL PRIMARY KEY,
  organization_id   UUID NOT NULL,
  event_type        TEXT NOT NULL,
  payload           JSONB NOT NULL DEFAULT '{}'::jsonb,
  correlation_id    UUID,
  idempotency_key   TEXT,
  created_by        TEXT NOT NULL,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT ledger_events_type_chk CHECK (char_length(event_type) > 0)
);

CREATE UNIQUE INDEX IF NOT EXISTS ledger_events_org_idem_uq
  ON public.ledger_events (organization_id, idempotency_key)
  WHERE idempotency_key IS NOT NULL;

CREATE INDEX IF NOT EXISTS ledger_events_org_created_idx
  ON public.ledger_events (organization_id, created_at DESC);

CREATE INDEX IF NOT EXISTS ledger_events_org_type_idx
  ON public.ledger_events (organization_id, event_type);

COMMENT ON TABLE public.ledger_events IS 'Append-only accounting event stream (system of record for v2 commands).';

-- Denormalized proposal queue (optional convenience; source of truth remains events)
CREATE TABLE IF NOT EXISTS public.journal_proposals (
  id                BIGSERIAL PRIMARY KEY,
  organization_id   UUID NOT NULL,
  proposal_key      UUID NOT NULL DEFAULT gen_random_uuid(),
  status            TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'posted', 'superseded')),
  payload           JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_by        TEXT NOT NULL,
  approved_by       TEXT,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS journal_proposals_org_status_idx
  ON public.journal_proposals (organization_id, status);

-- Projection: per-account balances from posted journal events (v2 path)
CREATE TABLE IF NOT EXISTS public.ledger_projection_account_balance (
  organization_id   UUID NOT NULL,
  account_id        BIGINT NOT NULL,
  debit_total       NUMERIC(24, 6) NOT NULL DEFAULT 0,
  credit_total      NUMERIC(24, 6) NOT NULL DEFAULT 0,
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (organization_id, account_id)
);

CREATE INDEX IF NOT EXISTS ledger_proj_bal_org_idx
  ON public.ledger_projection_account_balance (organization_id);

COMMENT ON TABLE public.ledger_projection_account_balance IS 'Derived balances from journal.posted / journal.reversed events (v2 projection).';
