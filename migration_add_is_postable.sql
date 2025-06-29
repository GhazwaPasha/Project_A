-- Migration: Add is_postable column to accounts table
-- This field determines whether transactions can be posted to an account
-- Level 1 accounts (category headers) are typically not postable
-- Level 2+ accounts can be postable based on business needs

ALTER TABLE public.accounts 
ADD COLUMN is_postable BOOLEAN DEFAULT true;

-- Set Level 1 accounts (category headers) to not postable by default
-- These are typically accounts with no parent (parent_id IS NULL)
UPDATE public.accounts 
SET is_postable = false 
WHERE parent_id IS NULL;

-- Create index for performance
CREATE INDEX idx_accounts_postable ON public.accounts(is_postable) WHERE is_postable = true;

COMMENT ON COLUMN public.accounts.is_postable IS 'Determines if transactions can be posted to this account. Level 1 accounts (category headers) are typically false, while Level 2+ accounts can be true or false based on business needs.';
