-- Adds accounts.report_category (+ enum) if missing. Idempotent; duplicate of 005_account_report_category.sql
-- with a unique number so ordered migrations do not skip it when multiple "005_*.sql" files exist.

DO $$
BEGIN
  CREATE TYPE public.account_report_category AS ENUM (
    'current_asset',
    'fixed_asset',
    'other_asset',
    'current_liability',
    'long_term_liability',
    'other_liability',
    'owners_equity',
    'retained_earnings',
    'other_equity',
    'operating_revenue',
    'other_revenue',
    'cost_of_sales',
    'operating_expense',
    'other_expense'
  );
EXCEPTION
  WHEN duplicate_object THEN NULL;
END $$;

ALTER TABLE public.accounts
  ADD COLUMN IF NOT EXISTS report_category public.account_report_category NULL;

COMMENT ON COLUMN public.accounts.report_category IS
  'Optional FS/P&L bucket; must align with account_type. When NULL, reports infer defaults.';
