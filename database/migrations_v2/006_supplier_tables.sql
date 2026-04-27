-- Suppliers, account mappings, contacts. Required for /suppliers and voucher supplier pickers.
-- Idempotent: safe to re-run.

CREATE TABLE IF NOT EXISTS public.suppliers (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  organization_id uuid NOT NULL REFERENCES public.organizations (id) ON DELETE CASCADE,
  supplier_code text NOT NULL,
  name text NOT NULL,
  legal_name text,
  description text,
  contact_person text,
  email text,
  phone text,
  fax text,
  website text,
  billing_address_line1 text,
  billing_address_line2 text,
  billing_city text,
  billing_state text,
  billing_postal_code text,
  billing_country text,
  shipping_address_line1 text,
  shipping_address_line2 text,
  shipping_city text,
  shipping_state text,
  shipping_postal_code text,
  shipping_country text,
  tax_id text,
  registration_number text,
  currency text NOT NULL DEFAULT 'USD',
  payment_terms text NOT NULL DEFAULT 'net_30',
  credit_limit double precision,
  current_balance double precision NOT NULL DEFAULT 0,
  status text NOT NULL DEFAULT 'active',
  is_preferred boolean NOT NULL DEFAULT false,
  notes text,
  created_by uuid REFERENCES public.user_profiles (id) ON DELETE SET NULL,
  updated_by uuid REFERENCES public.user_profiles (id) ON DELETE SET NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (organization_id, supplier_code)
);

CREATE TABLE IF NOT EXISTS public.supplier_account_mappings (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  supplier_id bigint NOT NULL REFERENCES public.suppliers (id) ON DELETE CASCADE,
  organization_id uuid NOT NULL REFERENCES public.organizations (id) ON DELETE CASCADE,
  payable_account_id bigint NOT NULL REFERENCES public.accounts (id) ON DELETE RESTRICT,
  cash_account_id bigint REFERENCES public.accounts (id) ON DELETE SET NULL,
  expense_account_id bigint REFERENCES public.accounts (id) ON DELETE SET NULL,
  inventory_account_id bigint REFERENCES public.accounts (id) ON DELETE SET NULL,
  freight_account_id bigint REFERENCES public.accounts (id) ON DELETE SET NULL,
  tax_account_id bigint REFERENCES public.accounts (id) ON DELETE SET NULL,
  discount_account_id bigint REFERENCES public.accounts (id) ON DELETE SET NULL,
  created_by uuid REFERENCES public.user_profiles (id) ON DELETE SET NULL,
  updated_by uuid REFERENCES public.user_profiles (id) ON DELETE SET NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (supplier_id)
);

CREATE TABLE IF NOT EXISTS public.supplier_contacts (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  supplier_id bigint NOT NULL REFERENCES public.suppliers (id) ON DELETE CASCADE,
  name text NOT NULL,
  title text,
  email text,
  phone text,
  mobile text,
  fax text,
  is_primary boolean NOT NULL DEFAULT false,
  is_billing boolean NOT NULL DEFAULT false,
  is_shipping boolean NOT NULL DEFAULT false,
  is_technical boolean NOT NULL DEFAULT false,
  created_by uuid REFERENCES public.user_profiles (id) ON DELETE SET NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS suppliers_org_name ON public.suppliers (organization_id, name);
CREATE INDEX IF NOT EXISTS supplier_account_mappings_org ON public.supplier_account_mappings (organization_id);
CREATE INDEX IF NOT EXISTS supplier_contacts_supplier ON public.supplier_contacts (supplier_id);
