-- Invite links, an audit log and credit notes. Run after 011.
-- Adds tables and one nullable column, and relaxes one NOT NULL. No existing figure changes. Idempotent: safe to re-run.

CREATE TABLE IF NOT EXISTS public.organization_invites (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  organization_id uuid NOT NULL REFERENCES public.organizations (id) ON DELETE CASCADE,
  email text NOT NULL,
  role text NOT NULL,
  token_hash text NOT NULL UNIQUE,
  invited_by uuid REFERENCES public.user_profiles (id) ON DELETE SET NULL,
  expires_at timestamptz NOT NULL,
  accepted_at timestamptz,
  accepted_by uuid REFERENCES public.user_profiles (id) ON DELETE SET NULL,
  revoked_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS organization_invites_org ON public.organization_invites (organization_id, created_at DESC);

-- Who did what. No foreign keys on purpose, so the record outlives what it describes.
CREATE TABLE IF NOT EXISTS public.audit_log (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  organization_id uuid NOT NULL,
  user_id uuid,
  source text NOT NULL DEFAULT 'app',
  action text NOT NULL,
  target_type text,
  target_id text,
  details jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS audit_log_org_time ON public.audit_log (organization_id, created_at DESC, id DESC);

-- History can be added to, never rewritten.
CREATE OR REPLACE FUNCTION public.audit_log_is_append_only() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'The audit log cannot be changed.';
END;
$$;
DROP TRIGGER IF EXISTS audit_log_append_only ON public.audit_log;
CREATE TRIGGER audit_log_append_only BEFORE UPDATE OR DELETE ON public.audit_log
  FOR EACH ROW EXECUTE FUNCTION public.audit_log_is_append_only();

CREATE TABLE IF NOT EXISTS public.credit_notes (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  organization_id uuid NOT NULL REFERENCES public.organizations (id) ON DELETE CASCADE,
  document_id bigint NOT NULL REFERENCES public.trade_documents (id) ON DELETE RESTRICT,
  number text NOT NULL,
  credit_date date NOT NULL,
  reason text NOT NULL,
  subtotal numeric(20, 2) NOT NULL,
  tax_total numeric(20, 2) NOT NULL DEFAULT 0,
  total numeric(20, 2) NOT NULL,
  applied numeric(20, 2) NOT NULL DEFAULT 0,
  refund numeric(20, 2) NOT NULL DEFAULT 0,
  refund_account_id bigint REFERENCES public.accounts (id) ON DELETE RESTRICT,
  journal_entry_id bigint REFERENCES public.journal_entries (id) ON DELETE SET NULL,
  created_by uuid REFERENCES public.user_profiles (id) ON DELETE SET NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (organization_id, number)
);
CREATE INDEX IF NOT EXISTS credit_notes_document ON public.credit_notes (document_id);

CREATE TABLE IF NOT EXISTS public.credit_note_lines (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  credit_note_id bigint NOT NULL REFERENCES public.credit_notes (id) ON DELETE CASCADE,
  document_line_id bigint NOT NULL REFERENCES public.trade_document_lines (id) ON DELETE RESTRICT,
  quantity numeric(20, 4) NOT NULL CHECK (quantity > 0),
  amount numeric(20, 2) NOT NULL,
  tax_amount numeric(20, 2) NOT NULL DEFAULT 0,
  cost_amount numeric(20, 2) NOT NULL DEFAULT 0,
  restocked boolean NOT NULL DEFAULT false
);
CREATE INDEX IF NOT EXISTS credit_note_lines_line ON public.credit_note_lines (document_line_id);

-- A credit reduces what's owed the way a payment does, so it's recorded alongside them, with no bank account.
ALTER TABLE public.trade_payments ALTER COLUMN bank_account_id DROP NOT NULL;
ALTER TABLE public.trade_payments
  ADD COLUMN IF NOT EXISTS credit_note_id bigint REFERENCES public.credit_notes (id) ON DELETE RESTRICT;
