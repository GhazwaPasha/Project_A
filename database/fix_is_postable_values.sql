-- ===============================================
-- FIX is_postable VALUES
-- ===============================================
-- This script updates is_postable values for all accounts
-- based on whether they have children or not

-- Update: Accounts with NO children should be postable
UPDATE public.accounts 
SET is_postable = true
WHERE id IN (
    SELECT a.id 
    FROM public.accounts a
    LEFT JOIN public.accounts children ON children.parent_id = a.id
    WHERE children.id IS NULL
);

-- Update: Top-level parent accounts (with children) should NOT be postable
UPDATE public.accounts 
SET is_postable = false
WHERE id IN (
    SELECT a.id 
    FROM public.accounts a
    INNER JOIN public.accounts children ON children.parent_id = a.id
    WHERE a.parent_id IS NULL
);

-- Verify the results
SELECT 
    code,
    name,
    is_postable,
    parent_id,
    (SELECT COUNT(*) FROM public.accounts WHERE parent_id = a.id) as child_count
FROM public.accounts a
ORDER BY code;

