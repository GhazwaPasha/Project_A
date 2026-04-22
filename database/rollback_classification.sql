-- ===============================================
-- ROLLBACK: Remove Classification from Accounts Table
-- ===============================================
-- This script removes the classification column and related changes
-- Use this if you need to undo the classification migration

-- Drop the balance sheet accounts view
DROP VIEW IF EXISTS public.balance_sheet_accounts;

-- Drop the index on classification column
DROP INDEX IF EXISTS idx_accounts_classification;

-- Remove the classification column from accounts table
ALTER TABLE public.accounts DROP COLUMN IF EXISTS classification;

-- ===============================================
-- ROLLBACK COMPLETE
-- ===============================================
-- The accounts table has been restored to its original state
-- without the classification column 