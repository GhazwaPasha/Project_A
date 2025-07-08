-- ===============================================
-- MIGRATION: Add Classification to Accounts Table
-- ===============================================
-- This script adds a classification column to the accounts table
-- and populates it with intelligent default classifications

-- Add classification column to accounts table
ALTER TABLE public.accounts 
ADD COLUMN classification VARCHAR(50) CHECK (classification IN (
    'current_asset', 'fixed_asset', 'other_asset',
    'current_liability', 'long_term_liability', 'other_liability'
));

-- Create index for better performance
CREATE INDEX idx_accounts_classification ON public.accounts(classification);

-- ===============================================
-- POPULATE INITIAL CLASSIFICATIONS
-- ===============================================

-- Update asset accounts based on account names and types
UPDATE public.accounts 
SET classification = 'current_asset'
WHERE account_type = 'asset' 
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
SET classification = 'fixed_asset'
WHERE account_type = 'asset' 
AND classification IS NULL
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
SET classification = 'other_asset'
WHERE account_type = 'asset' 
AND classification IS NULL;

-- Update liability accounts
UPDATE public.accounts 
SET classification = 'current_liability'
WHERE account_type = 'liability' 
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
SET classification = 'long_term_liability'
WHERE account_type = 'liability' 
AND classification IS NULL
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
SET classification = 'other_liability'
WHERE account_type = 'liability' 
AND classification IS NULL;

-- ===============================================
-- CREATE VIEW FOR BALANCE SHEET CLASSIFICATIONS
-- ===============================================

CREATE OR REPLACE VIEW public.balance_sheet_accounts AS
SELECT 
    a.id,
    a.organization_id,
    a.code,
    a.name,
    a.account_type,
    a.parent_id,
    a.classification,
    a.is_active,
    CASE 
        WHEN a.classification = 'current_asset' THEN 1
        WHEN a.classification = 'fixed_asset' THEN 2
        WHEN a.classification = 'other_asset' THEN 3
        WHEN a.classification = 'current_liability' THEN 4
        WHEN a.classification = 'long_term_liability' THEN 5
        WHEN a.classification = 'other_liability' THEN 6
        ELSE 7
    END as sort_order
FROM public.accounts a
WHERE a.account_type IN ('asset', 'liability')
AND a.is_active = true
ORDER BY sort_order, a.code;

-- ===============================================
-- MIGRATION COMPLETE
-- ===============================================
-- The accounts table now has a classification column
-- All existing accounts have been classified based on their names
-- Users can update classifications through the UI
-- The balance_sheet_accounts view provides sorted accounts for reporting 