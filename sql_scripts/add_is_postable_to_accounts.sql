-- ===============================================
-- MIGRATION: Add is_postable Column to Accounts Table
-- ===============================================
-- This script adds an is_postable column to the accounts table
-- to store user's choice for postable status

-- Add is_postable column to accounts table
ALTER TABLE public.accounts 
ADD COLUMN is_postable BOOLEAN DEFAULT false;

-- Create index for better performance
CREATE INDEX idx_accounts_is_postable ON public.accounts(is_postable);

-- ===============================================
-- POPULATE INITIAL is_postable VALUES
-- ===============================================
-- Set initial values based on the new hierarchy rules:
-- 1. If account has no children, it is postable
-- 2. If account has children and is level 1, it is NOT postable  
-- 3. If account has children and is level 2 or higher, it is postable (user can choose)

-- First, let's create a temporary function to calculate levels
CREATE OR REPLACE FUNCTION calculate_account_level(account_id BIGINT)
RETURNS INTEGER AS $$
DECLARE
    level INTEGER := 1;
    current_parent_id BIGINT;
BEGIN
    -- Calculate level by counting parents
    current_parent_id := account_id;
    
    WHILE current_parent_id IS NOT NULL LOOP
        SELECT parent_id INTO current_parent_id 
        FROM public.accounts 
        WHERE id = current_parent_id;
        
        IF current_parent_id IS NOT NULL THEN
            level := level + 1;
        END IF;
    END LOOP;
    
    RETURN level;
END;
$$ LANGUAGE plpgsql;

-- Update is_postable based on hierarchy rules
UPDATE public.accounts 
SET is_postable = true
WHERE id IN (
    -- Accounts with no children (leaf accounts)
    SELECT a.id 
    FROM public.accounts a
    LEFT JOIN public.accounts children ON children.parent_id = a.id
    WHERE children.id IS NULL
);

-- Set level 1 accounts with children to NOT postable
UPDATE public.accounts 
SET is_postable = false
WHERE id IN (
    SELECT a.id 
    FROM public.accounts a
    INNER JOIN public.accounts children ON children.parent_id = a.id
    WHERE calculate_account_level(a.id) = 1
);

-- For level 2+ accounts with children, set to true (user can choose)
UPDATE public.accounts 
SET is_postable = true
WHERE id IN (
    SELECT a.id 
    FROM public.accounts a
    INNER JOIN public.accounts children ON children.parent_id = a.id
    WHERE calculate_account_level(a.id) >= 2
);

-- Drop the temporary function
DROP FUNCTION calculate_account_level(BIGINT);

-- ===============================================
-- VERIFY THE CHANGE
-- ===============================================
-- Check that the column exists and has data
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'accounts' 
AND table_schema = 'public'
AND column_name = 'is_postable';

-- Show sample of accounts with is_postable data
SELECT 
    code,
    name,
    account_type,
    is_postable,
    (SELECT COUNT(*) FROM public.accounts WHERE parent_id = a.id) as child_count
FROM public.accounts a
ORDER BY code
LIMIT 10;

-- ===============================================
-- MIGRATION COMPLETE
-- ===============================================
-- The accounts table now has an is_postable column
-- All existing accounts have been set based on the new hierarchy rules:
-- - Leaf accounts (no children): postable = true
-- - Level 1 accounts with children: postable = false  
-- - Level 2+ accounts with children: postable = true (user can choose)
-- Users can now control the postable status through the UI 