-- ===============================================
-- MIGRATION: Add Group Column to Accounts Table
-- ===============================================
-- This script adds a group column to the accounts table
-- and handles both fresh installations and existing databases

-- Drop old classification constraint if it exists
DO $$
BEGIN
    -- Check if the old classification_check constraint exists
    IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE table_name = 'accounts' 
        AND table_schema = 'public' 
        AND constraint_name = 'accounts_classification_check'
    ) THEN
        -- Drop the old constraint
        ALTER TABLE public.accounts DROP CONSTRAINT accounts_classification_check;
        RAISE NOTICE 'Dropped old accounts_classification_check constraint';
    ELSE
        RAISE NOTICE 'Old accounts_classification_check constraint does not exist';
    END IF;
END $$;

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
            ADD COLUMN "group" VARCHAR(50);
            RAISE NOTICE 'Added group column to accounts table';
        ELSE
            RAISE NOTICE 'Group column already exists';
        END IF;
    END IF;
END $$;

-- Add CHECK constraint if it doesn't exist
DO $$
BEGIN
    -- Check if the CHECK constraint already exists
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE table_name = 'accounts' 
        AND table_schema = 'public' 
        AND constraint_type = 'CHECK'
        AND constraint_name LIKE '%group%'
    ) THEN
        -- Add CHECK constraint
        ALTER TABLE public.accounts 
        ADD CONSTRAINT accounts_group_check 
        CHECK ("group" IN (
            'current_asset', 'fixed_asset', 'other_asset', 'prepaid_expense',
            'current_liability', 'long_term_liability', 'other_liability',
            'owners_equity', 'retained_earnings', 'other_equity',
            'sales_revenue', 'service_revenue', 'other_revenue', 'interest_income',
            'cogs', 'operating_expense', 'administrative_expense', 'selling_expense', 
            'financial_expense', 'other_expense', ''
        ));
        RAISE NOTICE 'Added CHECK constraint to group column';
    ELSE
        RAISE NOTICE 'CHECK constraint already exists on group column';
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
    
    -- Prepaid expenses
    LOWER(name) LIKE '%prepaid%' OR
    LOWER(name) LIKE '%advance%' OR
    
    -- Short-term investments
    LOWER(name) LIKE '%short term%' OR
    LOWER(name) LIKE '%temporary%' OR
    LOWER(name) LIKE '%marketable%'
);

-- Update inventory accounts as other assets
UPDATE public.accounts 
SET "group" = 'other_asset'
WHERE account_type = 'asset' 
AND ("group" IS NULL OR "group" = '')
AND (
    LOWER(name) LIKE '%inventory%' OR
    LOWER(name) LIKE '%stock%' OR
    LOWER(name) LIKE '%goods%'
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

-- Update equity accounts
UPDATE public.accounts 
SET "group" = 'owners_equity'
WHERE account_type = 'equity' 
AND ("group" IS NULL OR "group" = '')
AND (
    LOWER(name) LIKE '%owner%' OR
    LOWER(name) LIKE '%capital%' OR
    LOWER(name) LIKE '%investment%' OR
    LOWER(name) LIKE '%drawing%' OR
    LOWER(name) LIKE '%withdrawal%'
);

-- Update retained earnings
UPDATE public.accounts 
SET "group" = 'retained_earnings'
WHERE account_type = 'equity' 
AND ("group" IS NULL OR "group" = '')
AND (
    LOWER(name) LIKE '%retained%' OR
    LOWER(name) LIKE '%earnings%' OR
    LOWER(name) LIKE '%profit%'
);

-- Update other equity (remaining equity accounts)
UPDATE public.accounts 
SET "group" = 'other_equity'
WHERE account_type = 'equity' 
AND ("group" IS NULL OR "group" = '');

-- Update revenue accounts
UPDATE public.accounts 
SET "group" = 'sales_revenue'
WHERE account_type = 'revenue' 
AND ("group" IS NULL OR "group" = '')
AND (
    LOWER(name) LIKE '%sales%' OR
    LOWER(name) LIKE '%revenue%' OR
    LOWER(name) LIKE '%income%'
);

-- Update service revenue
UPDATE public.accounts 
SET "group" = 'service_revenue'
WHERE account_type = 'revenue' 
AND ("group" IS NULL OR "group" = '')
AND (
    LOWER(name) LIKE '%service%' OR
    LOWER(name) LIKE '%consulting%' OR
    LOWER(name) LIKE '%fees%'
);

-- Update interest income
UPDATE public.accounts 
SET "group" = 'interest_income'
WHERE account_type = 'revenue' 
AND ("group" IS NULL OR "group" = '')
AND (
    LOWER(name) LIKE '%interest%' OR
    LOWER(name) LIKE '%dividend%'
);

-- Update other revenue (remaining revenue accounts)
UPDATE public.accounts 
SET "group" = 'other_revenue'
WHERE account_type = 'revenue' 
AND ("group" IS NULL OR "group" = '');

-- Update additional expense groups
UPDATE public.accounts 
SET "group" = 'operating_expense'
WHERE account_type = 'expense' 
AND ("group" IS NULL OR "group" = '')
AND (
    LOWER(name) LIKE '%operating%' OR
    LOWER(name) LIKE '%general%' OR
    LOWER(name) LIKE '%overhead%'
);

UPDATE public.accounts 
SET "group" = 'administrative_expense'
WHERE account_type = 'expense' 
AND ("group" IS NULL OR "group" = '')
AND (
    LOWER(name) LIKE '%administrative%' OR
    LOWER(name) LIKE '%office%' OR
    LOWER(name) LIKE '%management%'
);

UPDATE public.accounts 
SET "group" = 'selling_expense'
WHERE account_type = 'expense' 
AND ("group" IS NULL OR "group" = '')
AND (
    LOWER(name) LIKE '%selling%' OR
    LOWER(name) LIKE '%marketing%' OR
    LOWER(name) LIKE '%advertising%' OR
    LOWER(name) LIKE '%promotion%'
);

UPDATE public.accounts 
SET "group" = 'financial_expense'
WHERE account_type = 'expense' 
AND ("group" IS NULL OR "group" = '')
AND (
    LOWER(name) LIKE '%interest expense%' OR
    LOWER(name) LIKE '%bank charges%' OR
    LOWER(name) LIKE '%finance%'
);

-- Update other expenses (remaining expense accounts)
UPDATE public.accounts 
SET "group" = 'other_expense'
WHERE account_type = 'expense' 
AND ("group" IS NULL OR "group" = '');

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
--   - current_asset, fixed_asset, other_asset, prepaid_expense (for assets)
--   - current_liability, long_term_liability, other_liability (for liabilities)
--   - owners_equity, retained_earnings, other_equity (for equity)
--   - sales_revenue, service_revenue, other_revenue, interest_income (for revenue)
--   - cogs, operating_expense, administrative_expense, selling_expense, 
--     financial_expense, other_expense (for expenses)
--   - empty string (for other account types)
-- 
-- Note: Inventory accounts are now classified as 'other_asset' instead of 'current_asset' 