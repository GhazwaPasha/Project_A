-- FIFO cost layers, serial numbers, units of measure, bills of materials and assembly builds. Run after 010.
-- Adds tables and nullable or defaulted columns only. Every item stays on moving average until someone switches it,
-- so no existing figure changes. Idempotent: safe to re-run.

ALTER TABLE public.inventory_items
  ADD COLUMN IF NOT EXISTS costing_method text NOT NULL DEFAULT 'average' CHECK (costing_method IN ('average', 'fifo')),
  ADD COLUMN IF NOT EXISTS track_serials boolean NOT NULL DEFAULT false;

ALTER TABLE public.inventory_settings
  ADD COLUMN IF NOT EXISTS default_costing_method text NOT NULL DEFAULT 'average' CHECK (default_costing_method IN ('average', 'fifo'));

-- What's left of each purchase, oldest first. Layers belong to the item, not a warehouse: a transfer doesn't change cost.
CREATE TABLE IF NOT EXISTS public.stock_cost_layers (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  item_id bigint NOT NULL REFERENCES public.inventory_items (id) ON DELETE CASCADE,
  transaction_id bigint REFERENCES public.inventory_transactions (id) ON DELETE SET NULL,
  received_date date NOT NULL,
  quantity numeric(20, 4) NOT NULL,
  value numeric(20, 4) NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS stock_cost_layers_open ON public.stock_cost_layers (item_id, received_date, id) WHERE quantity > 0;

-- What each issue took from which layer, so undoing it puts stock back exactly where it came from.
CREATE TABLE IF NOT EXISTS public.stock_cost_layer_takes (
  transaction_id bigint NOT NULL REFERENCES public.inventory_transactions (id) ON DELETE CASCADE,
  layer_id bigint NOT NULL REFERENCES public.stock_cost_layers (id) ON DELETE CASCADE,
  quantity numeric(20, 4) NOT NULL,
  value numeric(20, 4) NOT NULL,
  PRIMARY KEY (transaction_id, layer_id)
);

CREATE TABLE IF NOT EXISTS public.stock_serials (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  item_id bigint NOT NULL REFERENCES public.inventory_items (id) ON DELETE CASCADE,
  warehouse_id bigint REFERENCES public.warehouses (id) ON DELETE RESTRICT,
  serial_number text NOT NULL,
  in_stock boolean NOT NULL DEFAULT true,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (item_id, serial_number)
);
CREATE INDEX IF NOT EXISTS stock_serials_number ON public.stock_serials (serial_number);
CREATE INDEX IF NOT EXISTS stock_serials_available ON public.stock_serials (item_id, warehouse_id, id) WHERE in_stock;

CREATE TABLE IF NOT EXISTS public.stock_serial_movements (
  transaction_id bigint NOT NULL REFERENCES public.inventory_transactions (id) ON DELETE CASCADE,
  serial_id bigint NOT NULL REFERENCES public.stock_serials (id) ON DELETE CASCADE,
  PRIMARY KEY (transaction_id, serial_id)
);
CREATE INDEX IF NOT EXISTS stock_serial_movements_serial ON public.stock_serial_movements (serial_id);

-- Other units an item is bought or sold in: 1 Box = 12 Each. The item's own unit is always the base.
CREATE TABLE IF NOT EXISTS public.item_units (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  item_id bigint NOT NULL REFERENCES public.inventory_items (id) ON DELETE CASCADE,
  name text NOT NULL,
  factor numeric(20, 6) NOT NULL CHECK (factor > 0),
  UNIQUE (item_id, name)
);

-- Lines keep the unit and factor used at the time, so changing a unit later can't rewrite history.
ALTER TABLE public.purchase_order_lines
  ADD COLUMN IF NOT EXISTS unit_name text,
  ADD COLUMN IF NOT EXISTS unit_factor numeric(20, 6) NOT NULL DEFAULT 1;
ALTER TABLE public.trade_document_lines
  ADD COLUMN IF NOT EXISTS unit_name text,
  ADD COLUMN IF NOT EXISTS unit_factor numeric(20, 6) NOT NULL DEFAULT 1,
  ADD COLUMN IF NOT EXISTS serial_numbers text[];

CREATE TABLE IF NOT EXISTS public.boms (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  organization_id uuid NOT NULL REFERENCES public.organizations (id) ON DELETE CASCADE,
  item_id bigint NOT NULL REFERENCES public.inventory_items (id) ON DELETE CASCADE,
  output_quantity numeric(20, 4) NOT NULL DEFAULT 1 CHECK (output_quantity > 0),
  notes text,
  created_by uuid REFERENCES public.user_profiles (id) ON DELETE SET NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (organization_id, item_id)
);

CREATE TABLE IF NOT EXISTS public.bom_lines (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  bom_id bigint NOT NULL REFERENCES public.boms (id) ON DELETE CASCADE,
  component_item_id bigint NOT NULL REFERENCES public.inventory_items (id) ON DELETE RESTRICT,
  quantity numeric(20, 4) NOT NULL CHECK (quantity > 0),
  UNIQUE (bom_id, component_item_id)
);

CREATE TABLE IF NOT EXISTS public.assemblies (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  organization_id uuid NOT NULL REFERENCES public.organizations (id) ON DELETE CASCADE,
  number text NOT NULL,
  status text NOT NULL DEFAULT 'built' CHECK (status IN ('built', 'reversed')),
  item_id bigint NOT NULL REFERENCES public.inventory_items (id) ON DELETE RESTRICT,
  warehouse_id bigint NOT NULL REFERENCES public.warehouses (id) ON DELETE RESTRICT,
  quantity numeric(20, 4) NOT NULL CHECK (quantity > 0),
  build_date date NOT NULL,
  components_cost numeric(20, 2) NOT NULL DEFAULT 0,
  extra_cost numeric(20, 2) NOT NULL DEFAULT 0,
  extra_account_id bigint REFERENCES public.accounts (id) ON DELETE SET NULL,
  journal_entry_id bigint REFERENCES public.journal_entries (id) ON DELETE SET NULL,
  reversal_entry_id bigint REFERENCES public.journal_entries (id) ON DELETE SET NULL,
  transaction_id bigint REFERENCES public.inventory_transactions (id) ON DELETE SET NULL,
  created_by uuid REFERENCES public.user_profiles (id) ON DELETE SET NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (organization_id, number)
);

CREATE TABLE IF NOT EXISTS public.assembly_lines (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  assembly_id bigint NOT NULL REFERENCES public.assemblies (id) ON DELETE CASCADE,
  item_id bigint NOT NULL REFERENCES public.inventory_items (id) ON DELETE RESTRICT,
  quantity numeric(20, 4) NOT NULL,
  cost numeric(20, 2) NOT NULL DEFAULT 0,
  transaction_id bigint REFERENCES public.inventory_transactions (id) ON DELETE SET NULL
);
