-- ===============================================
-- RENAME CLASSIFICATION COLUMN TO GROUP
-- ===============================================
-- This script renames the classification column to group in the accounts table
-- for better consistency with the frontend naming

-- Rename the column from classification to group
ALTER TABLE public.accounts 
RENAME COLUMN classification TO "group";

-- ===============================================
-- VERIFY THE CHANGE
-- ===============================================
-- Check that the column was renamed successfully
SELECT 
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns 
WHERE table_name = 'accounts' 
AND table_schema = 'public'
AND column_name IN ('group', 'classification')
ORDER BY column_name;

-- ===============================================
-- COLUMN RENAMED SUCCESSFULLY
-- ===============================================
-- The classification column has been renamed to "group"
-- The frontend will now work with consistent naming throughout 