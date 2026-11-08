-- What each account is for, beyond its type. The reports, the cash flow and the posting rules read these
-- instead of guessing from account names. Run after 013. Additive: adds nullable columns and fills them in.
-- Idempotent: safe to re-run. Values set by hand are never overwritten.
--
-- system_role         the job the account does: receivable, payable, inventory, grni, output_tax, input_tax,
--                     bank, cash, retained_earnings, opening_balance, price_variance
-- is_control          kept by a subledger (invoices, bills, stock), so manual entries can't post to it
-- cash_flow_category  cash (the account IS cash), operating, investing or financing
-- pl_category         IFRS 18 income statement category: operating, investing, financing or income_tax
-- is_contra           reduces its section, like sales returns or accumulated depreciation

ALTER TABLE public.accounts ADD COLUMN IF NOT EXISTS system_role text;
ALTER TABLE public.accounts ADD COLUMN IF NOT EXISTS is_control boolean NOT NULL DEFAULT false;
ALTER TABLE public.accounts ADD COLUMN IF NOT EXISTS cash_flow_category text;
ALTER TABLE public.accounts ADD COLUMN IF NOT EXISTS pl_category text;
ALTER TABLE public.accounts ADD COLUMN IF NOT EXISTS is_contra boolean NOT NULL DEFAULT false;

DO $$
BEGIN
  ALTER TABLE public.accounts ADD CONSTRAINT accounts_system_role_valid CHECK (system_role IS NULL OR system_role IN
    ('receivable', 'payable', 'inventory', 'grni', 'output_tax', 'input_tax', 'bank', 'cash', 'retained_earnings', 'opening_balance', 'price_variance'));
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE public.accounts ADD CONSTRAINT accounts_cash_flow_category_valid CHECK (cash_flow_category IS NULL OR cash_flow_category IN ('cash', 'operating', 'investing', 'financing'));
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE public.accounts ADD CONSTRAINT accounts_pl_category_valid CHECK (pl_category IS NULL OR pl_category IN ('operating', 'investing', 'financing', 'income_tax'));
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- Roles there can only be one of.
CREATE UNIQUE INDEX IF NOT EXISTS accounts_single_roles ON public.accounts (organization_id, system_role)
  WHERE system_role IN ('grni', 'retained_earnings', 'opening_balance', 'price_variance');

-- Fill in what the system already knows. Each statement only touches accounts with no role yet.
UPDATE public.accounts a SET system_role = 'receivable', is_control = true
WHERE a.system_role IS NULL AND a.account_type = 'asset' AND (
  a.id IN (SELECT receivable_account_id FROM public.customers WHERE receivable_account_id IS NOT NULL)
  OR a.id IN (SELECT control_account_id FROM public.trade_documents WHERE kind = 'invoice' AND control_account_id IS NOT NULL));

UPDATE public.accounts a SET system_role = 'payable', is_control = true
WHERE a.system_role IS NULL AND a.account_type = 'liability' AND (
  a.id IN (SELECT payable_account_id FROM public.supplier_account_mappings WHERE payable_account_id IS NOT NULL)
  OR a.id IN (SELECT control_account_id FROM public.trade_documents WHERE kind = 'bill' AND control_account_id IS NOT NULL));

UPDATE public.accounts a SET system_role = 'inventory', is_control = true
WHERE a.system_role IS NULL AND a.account_type = 'asset'
  AND a.id IN (SELECT inventory_account_id FROM public.inventory_categories WHERE inventory_account_id IS NOT NULL);

UPDATE public.accounts a SET system_role = 'grni', is_control = true
WHERE a.system_role IS NULL
  AND a.id IN (SELECT grni_account_id FROM public.inventory_settings WHERE grni_account_id IS NOT NULL)
  AND NOT EXISTS (SELECT 1 FROM public.accounts b WHERE b.organization_id = a.organization_id AND b.system_role = 'grni');

-- Tax accounts stay open to manual entries: paying the tax authority is a manual entry.
UPDATE public.accounts a SET system_role = 'output_tax'
WHERE a.system_role IS NULL AND a.id IN (SELECT sales_account_id FROM public.tax_rates);
UPDATE public.accounts a SET system_role = 'input_tax'
WHERE a.system_role IS NULL AND a.id IN (SELECT purchase_account_id FROM public.tax_rates);

UPDATE public.accounts a SET system_role = 'bank'
WHERE a.system_role IS NULL AND a.account_type = 'asset' AND (
  a.id IN (SELECT account_id FROM public.bank_statement_lines)
  OR a.id IN (SELECT bank_account_id FROM public.trade_payments WHERE bank_account_id IS NOT NULL));

UPDATE public.accounts a SET system_role = CASE WHEN a.name ~* 'bank' THEN 'bank' ELSE 'cash' END
WHERE a.system_role IS NULL AND a.account_type = 'asset' AND a.name ~* '(^|[^a-z])(cash|bank|petty)([^a-z]|$)'
  AND a.name !~* '(receiv|loan|deposit|equivalent fund|clearing)';

UPDATE public.accounts SET system_role = 'retained_earnings'
WHERE id IN (
  SELECT DISTINCT ON (organization_id) id FROM public.accounts
  WHERE account_type = 'equity' AND (report_category = 'retained_earnings' OR name ~* 'retained')
  ORDER BY organization_id, code)
AND NOT EXISTS (SELECT 1 FROM public.accounts b WHERE b.organization_id = accounts.organization_id AND b.system_role = 'retained_earnings');

-- Cash flow: cash accounts, then what the report category or the name says.
UPDATE public.accounts SET cash_flow_category = 'cash'
WHERE cash_flow_category IS NULL AND system_role IN ('bank', 'cash');
UPDATE public.accounts SET cash_flow_category = CASE
    WHEN account_type = 'asset' AND report_category IN ('fixed_asset', 'other_asset') THEN 'investing'
    WHEN account_type = 'liability' AND (report_category = 'long_term_liability' OR name ~* '(loan|borrow|mortgage|debenture|overdraft|lease liab)') THEN 'financing'
    WHEN account_type = 'equity' THEN 'financing'
    ELSE 'operating' END
WHERE cash_flow_category IS NULL AND account_type IN ('asset', 'liability', 'equity');

-- Income statement categories for finance lines and tax. Everything else is operating, the IFRS 18 default.
UPDATE public.accounts SET pl_category = CASE
    WHEN account_type = 'expense' AND name ~* '(income tax|corporation tax|tax expense)' THEN 'income_tax'
    WHEN name ~* '(interest|finance cost|finance charge|bank charge on loan)' THEN 'financing'
    ELSE NULL END
WHERE pl_category IS NULL AND account_type IN ('revenue', 'expense');

UPDATE public.accounts SET is_contra = true
WHERE NOT is_contra AND (
  (account_type = 'revenue' AND name ~* '(return|discount|allowance|refund)')
  OR (account_type = 'asset' AND name ~* '(accumulated|allowance for|provision for|impairment)'));

-- From now on, an account takes its role the first time the system uses it for one, whichever screen or
-- service does it. A role set by hand is never replaced.
CREATE OR REPLACE FUNCTION public.mark_account_role(account bigint, role text) RETURNS void LANGUAGE plpgsql AS $$
BEGIN
  IF account IS NULL THEN RETURN; END IF;
  UPDATE public.accounts a SET
    system_role = role,
    is_control = a.is_control OR role IN ('receivable', 'payable', 'inventory', 'grni'),
    cash_flow_category = CASE WHEN role IN ('bank', 'cash') THEN 'cash' ELSE a.cash_flow_category END
  WHERE a.id = account AND a.system_role IS NULL
    AND a.account_type::text = CASE WHEN role IN ('payable', 'grni', 'output_tax') THEN 'liability' ELSE 'asset' END
    AND NOT (role = 'grni' AND EXISTS (SELECT 1 FROM public.accounts b WHERE b.organization_id = a.organization_id AND b.system_role = 'grni'));
END;
$$;

CREATE OR REPLACE FUNCTION public.mark_account_roles_from_use() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  CASE TG_TABLE_NAME
    WHEN 'customers' THEN PERFORM public.mark_account_role(NEW.receivable_account_id, 'receivable');
    WHEN 'supplier_account_mappings' THEN PERFORM public.mark_account_role(NEW.payable_account_id, 'payable');
    WHEN 'inventory_categories' THEN PERFORM public.mark_account_role(NEW.inventory_account_id, 'inventory');
    WHEN 'inventory_settings' THEN PERFORM public.mark_account_role(NEW.grni_account_id, 'grni');
    WHEN 'trade_documents' THEN PERFORM public.mark_account_role(NEW.control_account_id, CASE WHEN NEW.kind = 'invoice' THEN 'receivable' ELSE 'payable' END);
    WHEN 'trade_payments' THEN PERFORM public.mark_account_role(NEW.bank_account_id, 'bank');
    WHEN 'bank_statement_lines' THEN PERFORM public.mark_account_role(NEW.account_id, 'bank');
    WHEN 'tax_rates' THEN
      PERFORM public.mark_account_role(NEW.sales_account_id, 'output_tax');
      PERFORM public.mark_account_role(NEW.purchase_account_id, 'input_tax');
  END CASE;
  RETURN NEW;
END;
$$;

DO $$
DECLARE t text;
BEGIN
  FOREACH t IN ARRAY ARRAY['customers', 'supplier_account_mappings', 'inventory_categories', 'inventory_settings', 'trade_documents', 'trade_payments', 'bank_statement_lines', 'tax_rates'] LOOP
    EXECUTE format('DROP TRIGGER IF EXISTS mark_account_roles ON public.%I', t);
    EXECUTE format('CREATE TRIGGER mark_account_roles AFTER INSERT OR UPDATE ON public.%I FOR EACH ROW EXECUTE FUNCTION public.mark_account_roles_from_use()', t);
  END LOOP;
END $$;
