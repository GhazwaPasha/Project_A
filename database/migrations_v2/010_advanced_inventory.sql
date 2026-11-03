-- Warehouses, batches, transfers, purchase orders, goods receipts and stock counts, and links from invoices to stock.
-- Adds tables and nullable or defaulted columns, and widens one check. Existing stock moves into a "Main" warehouse
-- for each organization that has items; item totals and journal entries are untouched. Idempotent: safe to re-run.

CREATE TABLE IF NOT EXISTS public.warehouses (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  organization_id uuid NOT NULL REFERENCES public.organizations (id) ON DELETE CASCADE,
  name text NOT NULL,
  code text,
  address text,
  is_default boolean NOT NULL DEFAULT false,
  is_active boolean NOT NULL DEFAULT true,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (organization_id, name)
);
CREATE UNIQUE INDEX IF NOT EXISTS warehouses_one_default ON public.warehouses (organization_id) WHERE is_default;

ALTER TABLE public.inventory_items
  ADD COLUMN IF NOT EXISTS barcode text,
  ADD COLUMN IF NOT EXISTS selling_price numeric(20, 4),
  ADD COLUMN IF NOT EXISTS income_account_id bigint REFERENCES public.accounts (id) ON DELETE SET NULL,
  ADD COLUMN IF NOT EXISTS preferred_supplier_id bigint REFERENCES public.suppliers (id) ON DELETE SET NULL,
  ADD COLUMN IF NOT EXISTS lead_time_days int NOT NULL DEFAULT 14,
  ADD COLUMN IF NOT EXISTS track_lots boolean NOT NULL DEFAULT false;
CREATE INDEX IF NOT EXISTS inventory_items_barcode ON public.inventory_items (organization_id, barcode) WHERE barcode IS NOT NULL;

CREATE TABLE IF NOT EXISTS public.stock_levels (
  item_id bigint NOT NULL REFERENCES public.inventory_items (id) ON DELETE CASCADE,
  warehouse_id bigint NOT NULL REFERENCES public.warehouses (id) ON DELETE RESTRICT,
  quantity numeric(20, 4) NOT NULL DEFAULT 0,
  PRIMARY KEY (item_id, warehouse_id)
);

CREATE TABLE IF NOT EXISTS public.stock_lots (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  item_id bigint NOT NULL REFERENCES public.inventory_items (id) ON DELETE CASCADE,
  warehouse_id bigint NOT NULL REFERENCES public.warehouses (id) ON DELETE RESTRICT,
  lot_number text NOT NULL,
  expiry_date date,
  quantity numeric(20, 4) NOT NULL DEFAULT 0,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (item_id, warehouse_id, lot_number)
);
CREATE INDEX IF NOT EXISTS stock_lots_expiry ON public.stock_lots (expiry_date) WHERE quantity > 0;

ALTER TABLE public.inventory_transactions DROP CONSTRAINT IF EXISTS inventory_transactions_transaction_type_check;
ALTER TABLE public.inventory_transactions
  ADD CONSTRAINT inventory_transactions_transaction_type_check
  CHECK (transaction_type IN ('in', 'out', 'adjustment', 'transfer_in', 'transfer_out'));
ALTER TABLE public.inventory_transactions
  ADD COLUMN IF NOT EXISTS warehouse_id bigint REFERENCES public.warehouses (id) ON DELETE RESTRICT,
  ADD COLUMN IF NOT EXISTS source_type text,
  ADD COLUMN IF NOT EXISTS source_id bigint;

CREATE TABLE IF NOT EXISTS public.stock_lot_movements (
  transaction_id bigint NOT NULL REFERENCES public.inventory_transactions (id) ON DELETE CASCADE,
  lot_id bigint NOT NULL REFERENCES public.stock_lots (id) ON DELETE CASCADE,
  quantity numeric(20, 4) NOT NULL,
  PRIMARY KEY (transaction_id, lot_id)
);

CREATE TABLE IF NOT EXISTS public.inventory_settings (
  organization_id uuid PRIMARY KEY REFERENCES public.organizations (id) ON DELETE CASCADE,
  grni_account_id bigint REFERENCES public.accounts (id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS public.purchase_orders (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  organization_id uuid NOT NULL REFERENCES public.organizations (id) ON DELETE CASCADE,
  number text NOT NULL,
  status text NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'approved', 'partial', 'received', 'cancelled')),
  supplier_id bigint REFERENCES public.suppliers (id) ON DELETE SET NULL,
  supplier_name text NOT NULL,
  warehouse_id bigint NOT NULL REFERENCES public.warehouses (id) ON DELETE RESTRICT,
  order_date date NOT NULL,
  expected_date date,
  notes text,
  created_by uuid REFERENCES public.user_profiles (id) ON DELETE SET NULL,
  approved_by uuid REFERENCES public.user_profiles (id) ON DELETE SET NULL,
  approved_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (organization_id, number)
);
CREATE INDEX IF NOT EXISTS purchase_orders_org_status ON public.purchase_orders (organization_id, status);

CREATE TABLE IF NOT EXISTS public.purchase_order_lines (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  purchase_order_id bigint NOT NULL REFERENCES public.purchase_orders (id) ON DELETE CASCADE,
  item_id bigint NOT NULL REFERENCES public.inventory_items (id) ON DELETE RESTRICT,
  quantity numeric(20, 4) NOT NULL CHECK (quantity > 0),
  quantity_received numeric(20, 4) NOT NULL DEFAULT 0,
  unit_cost numeric(20, 4) NOT NULL CHECK (unit_cost >= 0),
  tax_rate_id bigint REFERENCES public.tax_rates (id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS purchase_order_lines_po ON public.purchase_order_lines (purchase_order_id);

CREATE TABLE IF NOT EXISTS public.goods_receipts (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  organization_id uuid NOT NULL REFERENCES public.organizations (id) ON DELETE CASCADE,
  purchase_order_id bigint NOT NULL REFERENCES public.purchase_orders (id) ON DELETE RESTRICT,
  number text NOT NULL,
  receipt_date date NOT NULL,
  warehouse_id bigint NOT NULL REFERENCES public.warehouses (id) ON DELETE RESTRICT,
  total numeric(20, 2) NOT NULL DEFAULT 0,
  journal_entry_id bigint REFERENCES public.journal_entries (id) ON DELETE SET NULL,
  bill_id bigint REFERENCES public.trade_documents (id) ON DELETE SET NULL,
  created_by uuid REFERENCES public.user_profiles (id) ON DELETE SET NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (organization_id, number)
);
CREATE INDEX IF NOT EXISTS goods_receipts_po ON public.goods_receipts (purchase_order_id);

CREATE TABLE IF NOT EXISTS public.goods_receipt_lines (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  goods_receipt_id bigint NOT NULL REFERENCES public.goods_receipts (id) ON DELETE CASCADE,
  purchase_order_line_id bigint NOT NULL REFERENCES public.purchase_order_lines (id) ON DELETE RESTRICT,
  item_id bigint NOT NULL REFERENCES public.inventory_items (id) ON DELETE RESTRICT,
  quantity numeric(20, 4) NOT NULL CHECK (quantity > 0),
  unit_cost numeric(20, 4) NOT NULL,
  lot_number text,
  expiry_date date
);

CREATE TABLE IF NOT EXISTS public.stock_counts (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  organization_id uuid NOT NULL REFERENCES public.organizations (id) ON DELETE CASCADE,
  number text NOT NULL,
  status text NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'posted', 'cancelled')),
  warehouse_id bigint NOT NULL REFERENCES public.warehouses (id) ON DELETE RESTRICT,
  count_date date NOT NULL,
  notes text,
  journal_entry_id bigint REFERENCES public.journal_entries (id) ON DELETE SET NULL,
  created_by uuid REFERENCES public.user_profiles (id) ON DELETE SET NULL,
  posted_by uuid REFERENCES public.user_profiles (id) ON DELETE SET NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (organization_id, number)
);

CREATE TABLE IF NOT EXISTS public.stock_count_lines (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  stock_count_id bigint NOT NULL REFERENCES public.stock_counts (id) ON DELETE CASCADE,
  item_id bigint NOT NULL REFERENCES public.inventory_items (id) ON DELETE CASCADE,
  expected numeric(20, 4) NOT NULL,
  counted numeric(20, 4),
  UNIQUE (stock_count_id, item_id)
);

ALTER TABLE public.trade_document_lines
  ADD COLUMN IF NOT EXISTS item_id bigint REFERENCES public.inventory_items (id) ON DELETE RESTRICT,
  ADD COLUMN IF NOT EXISTS warehouse_id bigint REFERENCES public.warehouses (id) ON DELETE RESTRICT,
  ADD COLUMN IF NOT EXISTS cost_amount numeric(20, 2);

-- Existing stock goes to a Main warehouse, so warehouse quantities add up to item totals from the start.
INSERT INTO public.warehouses (organization_id, name, is_default)
SELECT DISTINCT i.organization_id, 'Main', true
FROM public.inventory_items i
WHERE NOT EXISTS (SELECT 1 FROM public.warehouses w WHERE w.organization_id = i.organization_id)
ON CONFLICT DO NOTHING;

INSERT INTO public.stock_levels (item_id, warehouse_id, quantity)
SELECT i.id, w.id, i.quantity_available
FROM public.inventory_items i
JOIN public.warehouses w ON w.organization_id = i.organization_id AND w.is_default
WHERE NOT EXISTS (SELECT 1 FROM public.stock_levels s WHERE s.item_id = i.id)
ON CONFLICT DO NOTHING;

UPDATE public.inventory_transactions t
SET warehouse_id = w.id
FROM public.warehouses w
WHERE t.warehouse_id IS NULL AND w.organization_id = t.organization_id AND w.is_default;
