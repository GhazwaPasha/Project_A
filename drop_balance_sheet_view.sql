-- ===============================================
-- DROP BALANCE SHEET ACCOUNTS VIEW
-- ===============================================
-- This script completely removes the balance_sheet_accounts view

-- Drop the view
DROP VIEW IF EXISTS public.balance_sheet_accounts;

-- ===============================================
-- VERIFY THE DROP
-- ===============================================
-- This should return an error if the view was successfully dropped
-- SELECT * FROM public.balance_sheet_accounts LIMIT 1;

-- ===============================================
-- VIEW DROPPED SUCCESSFULLY
-- ===============================================
-- The balance_sheet_accounts view no longer exists
-- You can recreate it later if needed using the original CREATE VIEW statement 