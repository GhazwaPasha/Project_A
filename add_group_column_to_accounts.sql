-- ===============================================
-- MIGRATION: Add Group Column to Accounts Table
-- ===============================================
-- This script adds a group column to the accounts table
-- and handles both fresh installations and existing databases

-- Check if classification column exists and rename it to group
DO $$
BEGIN
    -- Check if classification column exists
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'accounts' 
        AND table_schema = 'public' 
        AND column_name = 'classification'
    ) THEN
        -- Rename classification to group
        ALTER TABLE public.accounts RENAME COLUMN classification TO "group";
        RAISE NOTICE 'Renamed classification column to group';
    ELSE
        -- Check if group column already exists
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'accounts' 
            AND table_schema = 'public' 
            AND column_name = 'group'
        ) THEN
            -- Add group column
            ALTER TABLE public.accounts 
            ADD COLUMN "group" VARCHAR(50) CHECK ("group" IN (
                'current_asset', 'fixed_asset', 'other_asset',
                'current_liability', 'long_term_liability', 'other_liability',
                'cogs', ''
            ));
            RAISE NOTICE 'Added group column to accounts table';
        ELSE
            RAISE NOTICE 'Group column already exists';
        END IF;
    END IF;
END $$;

-- Create index for better performance (if it doesn't exist)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE tablename = 'accounts' 
        AND indexname = 'idx_accounts_group'
    ) THEN
        CREATE INDEX idx_accounts_group ON public.accounts("group");
        RAISE NOTICE 'Created index on group column';
    ELSE
        RAISE NOTICE 'Group index already exists';
    END IF;
END $$;

-- ===============================================
-- POPULATE INITIAL GROUP VALUES (if column is empty)
-- ===============================================

-- Update asset accounts based on account names and types
UPDATE public.accounts 
SET "group" = 'current_asset'
WHERE account_type = 'asset' 
AND ("group" IS NULL OR "group" = '')
AND (
    -- Cash and cash equivalents
    LOWER(name) LIKE '%cash%' OR
    LOWER(name) LIKE '%bank%' OR
    LOWER(name) LIKE '%checking%' OR
    LOWER(name) LIKE '%savings%' OR
    LOWER(name) LIKE '%money market%' OR
    LOWER(name) LIKE '%petty cash%' OR
    
    -- Accounts receivable
    LOWER(name) LIKE '%accounts receivable%' OR
    LOWER(name) LIKE '%ar%' OR
    LOWER(name) LIKE '%receivable%' OR
    
    -- Inventory
    LOWER(name) LIKE '%inventory%' OR
    LOWER(name) LIKE '%stock%' OR
    LOWER(name) LIKE '%goods%' OR
    
    -- Prepaid expenses
    LOWER(name) LIKE '%prepaid%' OR
    LOWER(name) LIKE '%advance%' OR
    
    -- Short-term investments
    LOWER(name) LIKE '%short term%' OR
    LOWER(name) LIKE '%temporary%' OR
    LOWER(name) LIKE '%marketable%'
);

-- Update fixed assets
UPDATE public.accounts 
SET "group" = 'fixed_asset'
WHERE account_type = 'asset' 
AND ("group" IS NULL OR "group" = '')
AND (
    -- Property, plant, and equipment
    LOWER(name) LIKE '%equipment%' OR
    LOWER(name) LIKE '%machinery%' OR
    LOWER(name) LIKE '%vehicle%' OR
    LOWER(name) LIKE '%building%' OR
    LOWER(name) LIKE '%land%' OR
    LOWER(name) LIKE '%property%' OR
    LOWER(name) LIKE '%furniture%' OR
    LOWER(name) LIKE '%computer%' OR
    LOWER(name) LIKE '%software%' OR
    LOWER(name) LIKE '%accumulated depreciation%' OR
    LOWER(name) LIKE '%depreciation%' OR
    LOWER(name) LIKE '%amortization%'
);

-- Update other assets (remaining asset accounts)
UPDATE public.accounts 
SET "group" = 'other_asset'
WHERE account_type = 'asset' 
AND ("group" IS NULL OR "group" = '');

-- Update liability accounts
UPDATE public.accounts 
SET "group" = 'current_liability'
WHERE account_type = 'liability' 
AND ("group" IS NULL OR "group" = '')
AND (
    -- Accounts payable
    LOWER(name) LIKE '%accounts payable%' OR
    LOWER(name) LIKE '%ap%' OR
    LOWER(name) LIKE '%payable%' OR
    
    -- Short-term loans
    LOWER(name) LIKE '%short term%' OR
    LOWER(name) LIKE '%current portion%' OR
    
    -- Accrued expenses
    LOWER(name) LIKE '%accrued%' OR
    LOWER(name) LIKE '%wages payable%' OR
    LOWER(name) LIKE '%taxes payable%' OR
    LOWER(name) LIKE '%interest payable%' OR
    
    -- Unearned revenue
    LOWER(name) LIKE '%unearned%' OR
    LOWER(name) LIKE '%deferred revenue%' OR
    LOWER(name) LIKE '%advance payment%'
);

-- Update long-term liabilities
UPDATE public.accounts 
SET "group" = 'long_term_liability'
WHERE account_type = 'liability' 
AND ("group" IS NULL OR "group" = '')
AND (
    -- Long-term loans
    LOWER(name) LIKE '%long term%' OR
    LOWER(name) LIKE '%mortgage%' OR
    LOWER(name) LIKE '%bonds%' OR
    LOWER(name) LIKE '%notes payable%' OR
    
    -- Deferred taxes
    LOWER(name) LIKE '%deferred tax%' OR
    
    -- Pension obligations
    LOWER(name) LIKE '%pension%' OR
    LOWER(name) LIKE '%retirement%'
);

-- Update other liabilities (remaining liability accounts)
UPDATE public.accounts 
SET "group" = 'other_liability'
WHERE account_type = 'liability' 
AND ("group" IS NULL OR "group" = '');

-- Update expense accounts for COGS
UPDATE public.accounts 
SET "group" = 'cogs'
WHERE account_type = 'expense' 
AND ("group" IS NULL OR "group" = '')
AND (
    LOWER(name) LIKE '%cost of goods sold%' OR
    LOWER(name) LIKE '%cogs%' OR
    LOWER(name) LIKE '%cost of sales%' OR
    LOWER(name) LIKE '%direct cost%' OR
    LOWER(name) LIKE '%material cost%' OR
    LOWER(name) LIKE '%labor cost%'
);

-- ===============================================
-- VERIFY THE CHANGE
-- ===============================================
-- Check that the column exists and has data
SELECT 
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns 
WHERE table_name = 'accounts' 
AND table_schema = 'public'
AND column_name = 'group';

-- Show sample of accounts with group data
SELECT 
    code,
    name,
    account_type,
    "group"
FROM public.accounts 
WHERE "group" IS NOT NULL AND "group" != ''
ORDER BY account_type, code
LIMIT 10;

-- ===============================================
-- MIGRATION COMPLETE
-- ===============================================
-- The accounts table now has a group column
-- All existing accounts have been classified based on their names
-- Users can update groups through the UI
-- The group column supports the following values:
--   - current_asset, fixed_asset, other_asset (for assets)
--   - current_liability, long_term_liability, other_liability (for liabilities)
--   - cogs (for cost of goods sold expenses)
--   - empty string (for other account types) 