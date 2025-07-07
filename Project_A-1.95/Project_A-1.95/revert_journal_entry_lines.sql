-- Migration to revert journal_entry_lines table to original structure
-- This script will restore the original field names and structure

-- First, backup any existing data (if needed)
-- CREATE TABLE journal_entry_lines_backup AS SELECT * FROM journal_entry_lines;

-- Drop the current table (this will also drop any foreign key constraints)
DROP TABLE IF EXISTS public.journal_entry_lines CASCADE;

-- Recreate the table with the original structure
CREATE TABLE public.journal_entry_lines (
    id BIGSERIAL PRIMARY KEY,
    journal_entry_id BIGINT NOT NULL REFERENCES public.journal_entries(id) ON DELETE CASCADE,
    account_id BIGINT NOT NULL REFERENCES public.accounts(id),
    description TEXT,
    debit_amount DECIMAL(15,2) DEFAULT 0,
    credit_amount DECIMAL(15,2) DEFAULT 0,
    line_order INTEGER NOT NULL DEFAULT 1
);

-- Re-enable RLS
ALTER TABLE public.journal_entry_lines ENABLE ROW LEVEL SECURITY;

-- Recreate the indexes
CREATE INDEX idx_journal_lines_entry_id ON public.journal_entry_lines(journal_entry_id);
CREATE INDEX idx_journal_lines_account_id ON public.journal_entry_lines(account_id);

-- Add RLS policies for journal_entry_lines
-- Organization members can read journal entry lines for their organization
CREATE POLICY "journal_entry_lines_select_members" ON public.journal_entry_lines
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.journal_entries je
            WHERE je.id = journal_entry_id
            AND public.is_organization_member(je.organization_id)
        )
    );

-- Organization members can insert journal entry lines for their organization
CREATE POLICY "journal_entry_lines_insert_members" ON public.journal_entry_lines
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.journal_entries je
            WHERE je.id = journal_entry_id
            AND public.is_organization_member(je.organization_id)
        )
    );

-- Organization members can update journal entry lines for their organization
CREATE POLICY "journal_entry_lines_update_members" ON public.journal_entry_lines
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM public.journal_entries je
            WHERE je.id = journal_entry_id
            AND public.is_organization_member(je.organization_id)
        )
    );

-- Organization members can delete journal entry lines for their organization
CREATE POLICY "journal_entry_lines_delete_members" ON public.journal_entry_lines
    FOR DELETE USING (
        EXISTS (
            SELECT 1 FROM public.journal_entries je
            WHERE je.id = journal_entry_id
            AND public.is_organization_member(je.organization_id)
        )
    );

-- Super admins can do everything
CREATE POLICY "journal_entry_lines_all_super_admin" ON public.journal_entry_lines
    FOR ALL USING (public.is_super_admin());

-- Add constraint to ensure only one of debit_amount or credit_amount is set
ALTER TABLE public.journal_entry_lines 
ADD CONSTRAINT check_debit_or_credit 
CHECK (
    (debit_amount > 0 AND credit_amount = 0) OR 
    (credit_amount > 0 AND debit_amount = 0) OR 
    (debit_amount = 0 AND credit_amount = 0)
);

-- Add constraint to ensure account_id is not null
ALTER TABLE public.journal_entry_lines 
ALTER COLUMN account_id SET NOT NULL;

-- Add constraint to ensure line_order is positive
ALTER TABLE public.journal_entry_lines 
ADD CONSTRAINT check_line_order_positive 
CHECK (line_order > 0);

-- Add unique constraint to prevent duplicate line orders within the same journal entry
ALTER TABLE public.journal_entry_lines 
ADD CONSTRAINT unique_line_order_per_entry 
UNIQUE (journal_entry_id, line_order);

-- Add trigger to update updated_at column (if you have this function)
-- CREATE TRIGGER update_journal_entry_lines_updated_at 
--     BEFORE UPDATE ON public.journal_entry_lines 
--     FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

-- Grant necessary permissions
GRANT ALL ON public.journal_entry_lines TO authenticated;
GRANT USAGE, SELECT ON SEQUENCE public.journal_entry_lines_id_seq TO authenticated;

-- Insert a sample record to verify the structure (optional - remove after testing)
-- INSERT INTO public.journal_entry_lines (journal_entry_id, account_id, description, debit_amount, credit_amount, line_order)
-- VALUES (1, 1, 'Sample debit line', 100.00, 0, 1);

COMMENT ON TABLE public.journal_entry_lines IS 'Journal entry line items with original structure: account_id, debit_amount, credit_amount';
COMMENT ON COLUMN public.journal_entry_lines.account_id IS 'Reference to the account being debited or credited';
COMMENT ON COLUMN public.journal_entry_lines.debit_amount IS 'Amount to debit (positive value)';
COMMENT ON COLUMN public.journal_entry_lines.credit_amount IS 'Amount to credit (positive value)';
COMMENT ON COLUMN public.journal_entry_lines.line_order IS 'Order of the line within the journal entry'; 