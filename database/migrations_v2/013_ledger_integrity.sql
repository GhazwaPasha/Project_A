-- Ledger rules the database enforces itself, so no code path, script or AI connection can break them. Run after 012.
-- Idempotent: safe to re-run. Existing figures are not changed. The one data change: an entry number used twice
-- in an organization gets its row id appended, so each number is unique before the unique index is added.

-- Where an entry came from: manual, invoice, payment, agent, mcp and so on, with the id of the thing that made it.
ALTER TABLE public.journal_entries ADD COLUMN IF NOT EXISTS source text;
ALTER TABLE public.journal_entries ADD COLUMN IF NOT EXISTS source_id text;

-- 1. Amounts are never negative, and a line is a debit or a credit, not both.
-- NOT VALID checks new rows only, so an old bad row can't block the migration. VALIDATE then checks old rows when it can.
DO $$
BEGIN
  ALTER TABLE public.journal_entry_lines ADD CONSTRAINT journal_line_amounts_valid
    CHECK (debit_amount >= 0 AND credit_amount >= 0 AND NOT (debit_amount > 0 AND credit_amount > 0)) NOT VALID;
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
DO $$
BEGIN
  ALTER TABLE public.journal_entry_lines VALIDATE CONSTRAINT journal_line_amounts_valid;
EXCEPTION WHEN check_violation THEN
  RAISE WARNING 'Some existing journal lines have negative or two-sided amounts. New lines are checked; fix the old ones by reversing their entries.';
END $$;

-- 2. Entry numbers are unique in an organization.
UPDATE public.journal_entries e SET entry_number = e.entry_number || '-' || e.id
WHERE EXISTS (
  SELECT 1 FROM public.journal_entries o
  WHERE o.organization_id = e.organization_id AND o.entry_number = e.entry_number AND o.id < e.id
);
CREATE UNIQUE INDEX IF NOT EXISTS journal_entries_number_unique ON public.journal_entries (organization_id, entry_number);

-- 3. Every entry balances. Checked when the transaction commits, after all its lines are in.
CREATE OR REPLACE FUNCTION public.journal_entry_must_balance() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
  entry bigint := COALESCE(NEW.journal_entry_id, OLD.journal_entry_id);
  dr numeric;
  cr numeric;
  n int;
BEGIN
  SELECT COALESCE(SUM(debit_amount), 0), COALESCE(SUM(credit_amount), 0), COUNT(*) INTO dr, cr, n
  FROM public.journal_entry_lines WHERE journal_entry_id = entry;
  IF n > 0 AND dr <> cr THEN
    RAISE EXCEPTION 'Journal entry % does not balance: debits % and credits %.', entry, dr, cr USING ERRCODE = 'check_violation';
  END IF;
  RETURN NULL;
END;
$$;
DROP TRIGGER IF EXISTS journal_entry_balances ON public.journal_entry_lines;
CREATE CONSTRAINT TRIGGER journal_entry_balances AFTER INSERT OR UPDATE OR DELETE ON public.journal_entry_lines
  DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION public.journal_entry_must_balance();

-- 4. Posted entries are corrected by reversing them, never by editing or deleting.
-- Allowed: relinking who created or posted an entry, linking a reversal once, and deletes that cascade from
-- deleting a whole organization. Database maintenance can opt out for one transaction with
--   SET LOCAL app.ledger_maintenance = 'on';
CREATE OR REPLACE FUNCTION public.journal_entry_is_permanent() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF current_setting('app.ledger_maintenance', true) = 'on' THEN
    RETURN COALESCE(NEW, OLD);
  END IF;
  IF TG_OP = 'DELETE' THEN
    -- An organization being deleted takes its books with it.
    IF NOT EXISTS (SELECT 1 FROM public.organizations WHERE id = OLD.organization_id) THEN
      RETURN OLD;
    END IF;
    RAISE EXCEPTION 'Journal entry % cannot be deleted. Reverse it instead.', OLD.entry_number;
  END IF;
  IF NEW.organization_id IS DISTINCT FROM OLD.organization_id
     OR NEW.entry_number IS DISTINCT FROM OLD.entry_number
     OR NEW.entry_date IS DISTINCT FROM OLD.entry_date
     OR NEW.description IS DISTINCT FROM OLD.description
     OR NEW.reference IS DISTINCT FROM OLD.reference
     OR NEW.total_amount IS DISTINCT FROM OLD.total_amount
     OR NEW.is_posted IS DISTINCT FROM OLD.is_posted
     OR NEW.source IS DISTINCT FROM OLD.source
     OR NEW.source_id IS DISTINCT FROM OLD.source_id
     OR (OLD.reverses_entry_id IS NOT NULL AND NEW.reverses_entry_id IS DISTINCT FROM OLD.reverses_entry_id) THEN
    RAISE EXCEPTION 'Journal entry % cannot be changed. Reverse it and record a new one.', OLD.entry_number;
  END IF;
  RETURN NEW;
END;
$$;
DROP TRIGGER IF EXISTS journal_entries_permanent ON public.journal_entries;
CREATE TRIGGER journal_entries_permanent BEFORE UPDATE OR DELETE ON public.journal_entries
  FOR EACH ROW EXECUTE FUNCTION public.journal_entry_is_permanent();

CREATE OR REPLACE FUNCTION public.journal_line_is_permanent() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF current_setting('app.ledger_maintenance', true) = 'on' THEN
    RETURN COALESCE(NEW, OLD);
  END IF;
  IF TG_OP = 'DELETE' THEN
    -- Only as part of deleting the entry itself, which the rule above allows only for a deleted organization.
    IF NOT EXISTS (SELECT 1 FROM public.journal_entries WHERE id = OLD.journal_entry_id) THEN
      RETURN OLD;
    END IF;
    RAISE EXCEPTION 'Journal lines cannot be deleted. Reverse the entry instead.';
  END IF;
  RAISE EXCEPTION 'Journal lines cannot be changed. Reverse the entry and record a new one.';
END;
$$;
DROP TRIGGER IF EXISTS journal_lines_permanent ON public.journal_entry_lines;
CREATE TRIGGER journal_lines_permanent BEFORE UPDATE OR DELETE ON public.journal_entry_lines
  FOR EACH ROW EXECUTE FUNCTION public.journal_line_is_permanent();
