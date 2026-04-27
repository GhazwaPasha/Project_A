-- Inventory + voucher tables (Neon / Postgres).
-- Run after 003_core_multitenant_user_org.sql and 004_ledger_core.sql (needs organizations, accounts, journal_entries, user_profiles).
-- Idempotent: safe to re-run; skips objects that already exist.

-- ---------------------------------------------------------------------------
-- Inventory core
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS public.inventory_categories (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  organization_id uuid NOT NULL REFERENCES public.organizations (id) ON DELETE CASCADE,
  name text NOT NULL,
  description text,
  inventory_account_id bigint NOT NULL REFERENCES public.accounts (id) ON DELETE RESTRICT,
  expense_account_id bigint NOT NULL REFERENCES public.accounts (id) ON DELETE RESTRICT,
  parent_id bigint REFERENCES public.inventory_categories (id) ON DELETE SET NULL,
  is_active boolean NOT NULL DEFAULT true,
  created_by uuid REFERENCES public.user_profiles (id) ON DELETE SET NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS inventory_categories_org
  ON public.inventory_categories (organization_id);

CREATE TABLE IF NOT EXISTS public.inventory_items (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  organization_id uuid NOT NULL REFERENCES public.organizations (id) ON DELETE CASCADE,
  category_id bigint NOT NULL REFERENCES public.inventory_categories (id) ON DELETE RESTRICT,
  sku text NOT NULL,
  name text NOT NULL,
  description text,
  unit_of_measure text NOT NULL DEFAULT 'pcs',
  quantity_in numeric(20, 4) NOT NULL DEFAULT 0,
  quantity_out numeric(20, 4) NOT NULL DEFAULT 0,
  quantity_available numeric(20, 4) NOT NULL DEFAULT 0,
  average_unit_cost numeric(20, 4) NOT NULL DEFAULT 0,
  total_value numeric(20, 2) NOT NULL DEFAULT 0,
  reorder_point numeric(20, 4) NOT NULL DEFAULT 0,
  reorder_quantity numeric(20, 4) NOT NULL DEFAULT 0,
  is_active boolean NOT NULL DEFAULT true,
  created_by uuid REFERENCES public.user_profiles (id) ON DELETE SET NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (organization_id, sku)
);

CREATE INDEX IF NOT EXISTS inventory_items_org
  ON public.inventory_items (organization_id);
CREATE INDEX IF NOT EXISTS inventory_items_category
  ON public.inventory_items (category_id);

CREATE TABLE IF NOT EXISTS public.inventory_transactions (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  organization_id uuid NOT NULL REFERENCES public.organizations (id) ON DELETE CASCADE,
  item_id bigint NOT NULL REFERENCES public.inventory_items (id) ON DELETE CASCADE,
  transaction_type text NOT NULL CHECK (transaction_type IN ('in', 'out', 'adjustment')),
  quantity numeric(20, 4) NOT NULL,
  unit_cost numeric(20, 4),
  total_cost numeric(20, 2),
  journal_entry_id bigint REFERENCES public.journal_entries (id) ON DELETE SET NULL,
  reference text,
  description text,
  transaction_date date NOT NULL,
  created_by uuid REFERENCES public.user_profiles (id) ON DELETE SET NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS inventory_transactions_org_date
  ON public.inventory_transactions (organization_id, transaction_date DESC);
CREATE INDEX IF NOT EXISTS inventory_transactions_item
  ON public.inventory_transactions (item_id);

-- ---------------------------------------------------------------------------
-- Vouchers (Inventory tab → Vouchers)
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS public.inventory_vouchers (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  organization_id uuid NOT NULL REFERENCES public.organizations (id) ON DELETE CASCADE,
  voucher_number text NOT NULL,
  voucher_type text NOT NULL,
  status text NOT NULL DEFAULT 'draft',
  requested_by uuid NOT NULL REFERENCES public.user_profiles (id) ON DELETE RESTRICT,
  requested_date date NOT NULL,
  vendor_name text,
  vendor_contact text,
  purchase_order_number text,
  expected_delivery_date date,
  purpose text,
  destination text,
  cost_center text,
  project_code text,
  destination_account_id bigint REFERENCES public.accounts (id) ON DELETE SET NULL,
  payment_type text NOT NULL DEFAULT 'credit',
  payment_account_id bigint REFERENCES public.accounts (id) ON DELETE SET NULL,
  deposit_amount double precision NOT NULL DEFAULT 0,
  payment_reference text,
  description text,
  notes text,
  total_estimated_cost double precision NOT NULL DEFAULT 0,
  total_actual_cost double precision,
  submitted_at timestamptz,
  approval_deadline timestamptz,
  expired_at timestamptz,
  renewed_at timestamptz,
  renewal_count integer NOT NULL DEFAULT 0,
  renewal_reason text,
  finance_approved_by uuid REFERENCES public.user_profiles (id) ON DELETE SET NULL,
  finance_approved_at timestamptz,
  finance_approval_notes text,
  rejected_by uuid REFERENCES public.user_profiles (id) ON DELETE SET NULL,
  rejected_at timestamptz,
  rejection_reason text,
  executed_by uuid REFERENCES public.user_profiles (id) ON DELETE SET NULL,
  executed_at timestamptz,
  journal_entry_id bigint REFERENCES public.journal_entries (id) ON DELETE SET NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS inventory_vouchers_org_number
  ON public.inventory_vouchers (organization_id, voucher_number);
CREATE INDEX IF NOT EXISTS inventory_vouchers_org_status
  ON public.inventory_vouchers (organization_id, status);

CREATE TABLE IF NOT EXISTS public.inventory_voucher_lines (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  voucher_id bigint NOT NULL REFERENCES public.inventory_vouchers (id) ON DELETE CASCADE,
  line_number int NOT NULL,
  item_id bigint NOT NULL REFERENCES public.inventory_items (id) ON DELETE RESTRICT,
  quantity_requested numeric(20, 4) NOT NULL,
  quantity_approved numeric(20, 4),
  quantity_actual numeric(20, 4),
  unit_cost_estimated numeric(20, 4),
  unit_cost_actual numeric(20, 4),
  total_cost numeric(20, 2) NOT NULL DEFAULT 0,
  notes text,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (voucher_id, line_number)
);

CREATE INDEX IF NOT EXISTS inventory_voucher_lines_voucher
  ON public.inventory_voucher_lines (voucher_id);

CREATE TABLE IF NOT EXISTS public.voucher_attachments (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  voucher_id bigint NOT NULL REFERENCES public.inventory_vouchers (id) ON DELETE CASCADE,
  file_name text NOT NULL,
  file_path text NOT NULL,
  file_type text,
  file_size bigint,
  file_data bytea,
  description text,
  uploaded_by uuid NOT NULL REFERENCES public.user_profiles (id) ON DELETE SET NULL,
  uploaded_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS voucher_attachments_voucher
  ON public.voucher_attachments (voucher_id);

CREATE TABLE IF NOT EXISTS public.voucher_approvals (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  voucher_id bigint NOT NULL REFERENCES public.inventory_vouchers (id) ON DELETE CASCADE,
  approver_id uuid NOT NULL REFERENCES public.user_profiles (id) ON DELETE CASCADE,
  action text NOT NULL,
  comments text,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS voucher_approvals_voucher
  ON public.voucher_approvals (voucher_id);

CREATE TABLE IF NOT EXISTS public.voucher_expiration_log (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  voucher_id bigint NOT NULL REFERENCES public.inventory_vouchers (id) ON DELETE CASCADE,
  status_when_expired text NOT NULL,
  expired_at timestamptz NOT NULL,
  approval_deadline timestamptz NOT NULL,
  items_count int NOT NULL DEFAULT 0,
  total_value double precision NOT NULL DEFAULT 0,
  renewed_at timestamptz,
  renewed_by uuid REFERENCES public.user_profiles (id) ON DELETE SET NULL,
  renewal_reason text,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS voucher_expiration_log_voucher
  ON public.voucher_expiration_log (voucher_id);
