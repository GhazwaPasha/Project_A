-- Invoices and bills, tax, bank reconciliation, period closing, budgets, entry reversal, MCP sign-in and rate limits.
-- Additive only: adds tables and one nullable column. Idempotent: safe to re-run.

-- Reversing an entry links the pair, so it can't be reversed twice.
ALTER TABLE public.journal_entries
  ADD COLUMN IF NOT EXISTS reverses_entry_id bigint REFERENCES public.journal_entries (id) ON DELETE SET NULL;
CREATE UNIQUE INDEX IF NOT EXISTS journal_entries_reverses_once
  ON public.journal_entries (reverses_entry_id) WHERE reverses_entry_id IS NOT NULL;

CREATE TABLE IF NOT EXISTS public.customers (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  organization_id uuid NOT NULL REFERENCES public.organizations (id) ON DELETE CASCADE,
  name text NOT NULL,
  email text,
  phone text,
  address text,
  tax_id text,
  receivable_account_id bigint REFERENCES public.accounts (id) ON DELETE SET NULL,
  is_active boolean NOT NULL DEFAULT true,
  created_by uuid REFERENCES public.user_profiles (id) ON DELETE SET NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS customers_org ON public.customers (organization_id);

CREATE TABLE IF NOT EXISTS public.tax_rates (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  organization_id uuid NOT NULL REFERENCES public.organizations (id) ON DELETE CASCADE,
  name text NOT NULL,
  rate numeric(7, 4) NOT NULL CHECK (rate >= 0 AND rate <= 100),
  sales_account_id bigint NOT NULL REFERENCES public.accounts (id) ON DELETE RESTRICT,
  purchase_account_id bigint NOT NULL REFERENCES public.accounts (id) ON DELETE RESTRICT,
  is_active boolean NOT NULL DEFAULT true,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (organization_id, name)
);

CREATE TABLE IF NOT EXISTS public.trade_documents (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  organization_id uuid NOT NULL REFERENCES public.organizations (id) ON DELETE CASCADE,
  kind text NOT NULL CHECK (kind IN ('invoice', 'bill')),
  number text NOT NULL,
  status text NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'posted', 'partial', 'paid', 'void')),
  customer_id bigint REFERENCES public.customers (id) ON DELETE RESTRICT,
  supplier_id bigint REFERENCES public.suppliers (id) ON DELETE RESTRICT,
  party_name text NOT NULL,
  issue_date date NOT NULL,
  due_date date NOT NULL,
  control_account_id bigint REFERENCES public.accounts (id) ON DELETE RESTRICT,
  subtotal numeric(20, 2) NOT NULL DEFAULT 0,
  tax_total numeric(20, 2) NOT NULL DEFAULT 0,
  total numeric(20, 2) NOT NULL DEFAULT 0,
  amount_paid numeric(20, 2) NOT NULL DEFAULT 0,
  journal_entry_id bigint REFERENCES public.journal_entries (id) ON DELETE SET NULL,
  notes text,
  void_reason text,
  created_by uuid REFERENCES public.user_profiles (id) ON DELETE SET NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (organization_id, kind, number)
);
CREATE INDEX IF NOT EXISTS trade_documents_org_kind_status ON public.trade_documents (organization_id, kind, status);

CREATE TABLE IF NOT EXISTS public.trade_document_lines (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  document_id bigint NOT NULL REFERENCES public.trade_documents (id) ON DELETE CASCADE,
  line_order int NOT NULL,
  description text NOT NULL,
  account_id bigint NOT NULL REFERENCES public.accounts (id) ON DELETE RESTRICT,
  quantity numeric(20, 4) NOT NULL CHECK (quantity > 0),
  unit_price numeric(20, 4) NOT NULL CHECK (unit_price >= 0),
  tax_rate_id bigint REFERENCES public.tax_rates (id) ON DELETE RESTRICT,
  tax_rate numeric(7, 4) NOT NULL DEFAULT 0,
  amount numeric(20, 2) NOT NULL,
  tax_amount numeric(20, 2) NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS trade_document_lines_doc ON public.trade_document_lines (document_id);

CREATE TABLE IF NOT EXISTS public.trade_payments (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  organization_id uuid NOT NULL REFERENCES public.organizations (id) ON DELETE CASCADE,
  document_id bigint NOT NULL REFERENCES public.trade_documents (id) ON DELETE RESTRICT,
  payment_date date NOT NULL,
  amount numeric(20, 2) NOT NULL CHECK (amount > 0),
  bank_account_id bigint NOT NULL REFERENCES public.accounts (id) ON DELETE RESTRICT,
  reference text,
  journal_entry_id bigint REFERENCES public.journal_entries (id) ON DELETE SET NULL,
  created_by uuid REFERENCES public.user_profiles (id) ON DELETE SET NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS trade_payments_doc ON public.trade_payments (document_id);

CREATE TABLE IF NOT EXISTS public.tax_returns (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  organization_id uuid NOT NULL REFERENCES public.organizations (id) ON DELETE CASCADE,
  period_from date NOT NULL,
  period_to date NOT NULL,
  output_tax numeric(20, 2) NOT NULL,
  input_tax numeric(20, 2) NOT NULL,
  net_tax numeric(20, 2) NOT NULL,
  reference text,
  filed_by uuid REFERENCES public.user_profiles (id) ON DELETE SET NULL,
  filed_at timestamptz NOT NULL DEFAULT now(),
  CHECK (period_to >= period_from)
);
CREATE INDEX IF NOT EXISTS tax_returns_org ON public.tax_returns (organization_id, period_to DESC);

CREATE TABLE IF NOT EXISTS public.bank_statement_lines (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  organization_id uuid NOT NULL REFERENCES public.organizations (id) ON DELETE CASCADE,
  account_id bigint NOT NULL REFERENCES public.accounts (id) ON DELETE RESTRICT,
  statement_date date NOT NULL,
  description text NOT NULL,
  reference text,
  amount numeric(20, 2) NOT NULL,
  dedupe_key text NOT NULL,
  status text NOT NULL DEFAULT 'unmatched' CHECK (status IN ('unmatched', 'matched', 'ignored')),
  matched_journal_line_id bigint REFERENCES public.journal_entry_lines (id) ON DELETE SET NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (organization_id, account_id, dedupe_key)
);
CREATE UNIQUE INDEX IF NOT EXISTS bank_statement_line_matched_once
  ON public.bank_statement_lines (matched_journal_line_id) WHERE matched_journal_line_id IS NOT NULL;

CREATE TABLE IF NOT EXISTS public.bank_reconciliations (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  organization_id uuid NOT NULL REFERENCES public.organizations (id) ON DELETE CASCADE,
  account_id bigint NOT NULL REFERENCES public.accounts (id) ON DELETE RESTRICT,
  as_of date NOT NULL,
  statement_balance numeric(20, 2) NOT NULL,
  book_balance numeric(20, 2) NOT NULL,
  completed_by uuid REFERENCES public.user_profiles (id) ON DELETE SET NULL,
  completed_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.period_closes (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  organization_id uuid NOT NULL REFERENCES public.organizations (id) ON DELETE CASCADE,
  through_date date NOT NULL,
  notes text,
  closed_by uuid REFERENCES public.user_profiles (id) ON DELETE SET NULL,
  closed_at timestamptz NOT NULL DEFAULT now(),
  reopened_by uuid REFERENCES public.user_profiles (id) ON DELETE SET NULL,
  reopened_at timestamptz,
  reopen_reason text
);
CREATE INDEX IF NOT EXISTS period_closes_org ON public.period_closes (organization_id, through_date DESC);

CREATE TABLE IF NOT EXISTS public.budgets (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  organization_id uuid NOT NULL REFERENCES public.organizations (id) ON DELETE CASCADE,
  name text NOT NULL,
  year int NOT NULL CHECK (year BETWEEN 2000 AND 2100),
  created_by uuid REFERENCES public.user_profiles (id) ON DELETE SET NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (organization_id, name, year)
);

CREATE TABLE IF NOT EXISTS public.budget_lines (
  budget_id bigint NOT NULL REFERENCES public.budgets (id) ON DELETE CASCADE,
  account_id bigint NOT NULL REFERENCES public.accounts (id) ON DELETE CASCADE,
  month int NOT NULL CHECK (month BETWEEN 1 AND 12),
  amount numeric(20, 2) NOT NULL,
  PRIMARY KEY (budget_id, account_id, month)
);

-- MCP sign-in: apps register themselves, then a person approves them. Only hashes of codes are stored.
CREATE TABLE IF NOT EXISTS public.oauth_clients (
  client_id text PRIMARY KEY,
  name text NOT NULL,
  redirect_uris text[] NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.oauth_codes (
  code_hash text PRIMARY KEY,
  client_id text NOT NULL REFERENCES public.oauth_clients (client_id) ON DELETE CASCADE,
  user_id uuid NOT NULL REFERENCES public.user_profiles (id) ON DELETE CASCADE,
  organization_id uuid NOT NULL REFERENCES public.organizations (id) ON DELETE CASCADE,
  redirect_uri text NOT NULL,
  code_challenge text NOT NULL,
  can_record boolean NOT NULL DEFAULT false,
  expires_at timestamptz NOT NULL,
  used_at timestamptz
);

CREATE TABLE IF NOT EXISTS public.rate_limits (
  key text NOT NULL,
  window_start timestamptz NOT NULL,
  count int NOT NULL DEFAULT 0,
  PRIMARY KEY (key, window_start)
);
