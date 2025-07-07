-- Fix RLS Policies for journal_entry_lines Table
-- This script adds missing policies for organization owners and accountants
-- Run this in your Supabase SQL Editor

-- ========================================
-- STEP 1: Remove restrictive member-only policies
-- ========================================

DROP POLICY IF EXISTS "journal_entry_lines_insert_members" ON public.journal_entry_lines;
DROP POLICY IF EXISTS "journal_entry_lines_update_members" ON public.journal_entry_lines;
DROP POLICY IF EXISTS "journal_entry_lines_delete_members" ON public.journal_entry_lines;

-- ========================================
-- STEP 2: Create proper role-based policies
-- ========================================

-- Organization owners and accountants can INSERT journal entry lines
CREATE POLICY "journal_entry_lines_insert_owners_accountants" ON public.journal_entry_lines
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.journal_entries je
            WHERE je.id = journal_entry_id
            AND public.get_user_organization_role(je.organization_id) IN ('organization_owner', 'accountant')
        )
    );

-- Organization owners and accountants can UPDATE journal entry lines
CREATE POLICY "journal_entry_lines_update_owners_accountants" ON public.journal_entry_lines
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM public.journal_entries je
            WHERE je.id = journal_entry_id
            AND public.get_user_organization_role(je.organization_id) IN ('organization_owner', 'accountant')
        )
    );

-- Organization owners and accountants can DELETE journal entry lines
CREATE POLICY "journal_entry_lines_delete_owners_accountants" ON public.journal_entry_lines
    FOR DELETE USING (
        EXISTS (
            SELECT 1 FROM public.journal_entries je
            WHERE je.id = journal_entry_id
            AND public.get_user_organization_role(je.organization_id) IN ('organization_owner', 'accountant')
        )
    );

-- ========================================
-- STEP 3: Verify the policies
-- ========================================

-- Check all current policies on journal_entry_lines table
SELECT 
    schemaname,
    tablename,
    policyname,
    permissive,
    roles,
    cmd,
    qual
FROM pg_policies 
WHERE tablename = 'journal_entry_lines'
ORDER BY policyname;

-- ========================================
-- SUMMARY
-- ========================================

-- After running this script, the access levels will be:
-- • Members: READ-ONLY access (via existing select policy)
-- • Accountants: FULL modify access (create, edit, delete)
-- • Organization Owners: FULL modify access (create, edit, delete)  
-- • Super Admins: FULL access (via existing super admin policy)

COMMENT ON TABLE public.journal_entry_lines IS 'Journal entry line items with proper role-based RLS policies for owners and accountants'; 