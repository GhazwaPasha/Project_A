-- Add missing RLS policies for organization owners on journal_entry_lines table
-- This script adds the missing policies that allow organization owners to manage journal entry lines

-- Add policy for organization owners to modify journal entry lines (INSERT, UPDATE, DELETE)
CREATE POLICY "journal_entry_lines_modify_owners" ON public.journal_entry_lines
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM public.journal_entries je
            WHERE je.id = journal_entry_id
            AND public.get_user_organization_role(je.organization_id) = 'organization_owner'
        )
    );

-- Add policy for organization owners and accountants to modify journal entry lines (broader policy)
-- This replaces the member-only policies with proper owner/accountant permissions
DROP POLICY IF EXISTS "journal_entry_lines_insert_members" ON public.journal_entry_lines;
DROP POLICY IF EXISTS "journal_entry_lines_update_members" ON public.journal_entry_lines;
DROP POLICY IF EXISTS "journal_entry_lines_delete_members" ON public.journal_entry_lines;

-- Create comprehensive policies for owners and accountants
CREATE POLICY "journal_entry_lines_insert_owners_accountants" ON public.journal_entry_lines
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.journal_entries je
            WHERE je.id = journal_entry_id
            AND public.get_user_organization_role(je.organization_id) IN ('organization_owner', 'accountant')
        )
    );

CREATE POLICY "journal_entry_lines_update_owners_accountants" ON public.journal_entry_lines
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM public.journal_entries je
            WHERE je.id = journal_entry_id
            AND public.get_user_organization_role(je.organization_id) IN ('organization_owner', 'accountant')
        )
    );

CREATE POLICY "journal_entry_lines_delete_owners_accountants" ON public.journal_entry_lines
    FOR DELETE USING (
        EXISTS (
            SELECT 1 FROM public.journal_entries je
            WHERE je.id = journal_entry_id
            AND public.get_user_organization_role(je.organization_id) IN ('organization_owner', 'accountant')
        )
    );

-- Verify the policies are in place
SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual
FROM pg_policies 
WHERE tablename = 'journal_entry_lines'
ORDER BY policyname;

COMMENT ON TABLE public.journal_entry_lines IS 'Journal entry line items with RLS policies for organization owners and accountants'; 