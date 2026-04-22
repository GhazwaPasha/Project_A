-- Test script to see what columns are returned by the functions
-- Run this in Supabase SQL Editor to debug the column names

-- Test balance sheet function
SELECT generate_balance_sheet('0946405f-3b8a-4fe5-8c29-125b39d9ca8e', CURRENT_DATE);

-- Test income statement function  
SELECT generate_income_statement('0946405f-3b8a-4fe5-8c29-125b39d9ca8e', (CURRENT_DATE - INTERVAL '30 days')::DATE, CURRENT_DATE); 