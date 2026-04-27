-- Core ledger: chart of accounts, journal header/lines. Required for trial balance, income statement, etc.
-- Idempotent: safe to re-run when objects already exist.

DO $$
BEGIN
  CREATE TYPE public.account_type AS ENUM (
    'asset', 'liability', 'equity', 'revenue', 'expense'
  );
EXCEPTION
  WHEN duplicate_object THEN NULL;
END $$;

CREATE TABLE IF NOT EXISTS public.accounts (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  organization_id uuid NOT NULL REFERENCES public.organizations (id) ON DELETE CASCADE,
  code text NOT NULL,
  name text NOT NULL,
  account_type public.account_type NOT NULL,
  parent_id bigint REFERENCES public.accounts (id) ON DELETE SET NULL,
  description text,
  is_active boolean NOT NULL DEFAULT true,
  "group" text,
  is_postable boolean NOT NULL DEFAULT true,
  created_by uuid REFERENCES public.user_profiles (id) ON DELETE SET NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (organization_id, code)
);

CREATE TABLE IF NOT EXISTS public.journal_entries (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  organization_id uuid NOT NULL REFERENCES public.organizations (id) ON DELETE CASCADE,
  entry_number text NOT NULL,
  entry_date date NOT NULL,
  description text NOT NULL DEFAULT '',
  reference text,
  total_amount numeric(20, 2) NOT NULL DEFAULT 0,
  is_posted boolean NOT NULL DEFAULT false,
  created_by uuid REFERENCES public.user_profiles (id) ON DELETE SET NULL,
  posted_by uuid REFERENCES public.user_profiles (id) ON DELETE SET NULL,
  posted_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.journal_entry_lines (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  journal_entry_id bigint NOT NULL REFERENCES public.journal_entries (id) ON DELETE CASCADE,
  account_id bigint NOT NULL REFERENCES public.accounts (id) ON DELETE RESTRICT,
  description text,
  debit_amount numeric(20, 2) NOT NULL DEFAULT 0,
  credit_amount numeric(20, 2) NOT NULL DEFAULT 0,
  line_order int NOT NULL DEFAULT 1
);

CREATE INDEX IF NOT EXISTS journal_entries_org_date
  ON public.journal_entries (organization_id, entry_date DESC);
CREATE INDEX IF NOT EXISTS journal_entry_lines_entry
  ON public.journal_entry_lines (journal_entry_id, line_order);
CREATE INDEX IF NOT EXISTS journal_entry_lines_account
  ON public.journal_entry_lines (account_id);
