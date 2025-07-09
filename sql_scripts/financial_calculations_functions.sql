-- Financial Calculations Database Functions
-- These functions will replace Python calculations for better performance and consistency

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Function to calculate current ratio
CREATE OR REPLACE FUNCTION calculate_current_ratio(
    p_org_id UUID,
    p_as_of_date DATE DEFAULT CURRENT_DATE
)
RETURNS DECIMAL(10,4)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    current_assets DECIMAL(15,2) := 0;
    current_liabilities DECIMAL(15,2) := 0;
    ratio DECIMAL(10,4) := 0;
    as_of_date DATE := p_as_of_date;
BEGIN
    -- Get current assets (Asset accounts with positive balances)
    SELECT COALESCE(SUM(CASE WHEN account_balance > 0 THEN account_balance ELSE 0 END), 0)
    INTO current_assets
    FROM (
        SELECT a.id, a.account_type,
               COALESCE(SUM(CASE WHEN jel.debit_amount > 0 THEN jel.debit_amount ELSE -jel.credit_amount END), 0) as account_balance
        FROM accounts a
        LEFT JOIN journal_entry_lines jel ON a.id = jel.account_id
        LEFT JOIN journal_entries je ON jel.journal_entry_id = je.id 
            AND je.organization_id = p_org_id
            AND je.entry_date <= as_of_date
        WHERE a.organization_id = p_org_id 
        AND a.account_type = 'asset'
        AND a.is_active = true
        GROUP BY a.id, a.account_type
    ) account_balances;
    
    -- Get current liabilities (Liability accounts with negative balances)
    SELECT COALESCE(SUM(CASE WHEN account_balance < 0 THEN ABS(account_balance) ELSE 0 END), 0)
    INTO current_liabilities
    FROM (
        SELECT a.id, a.account_type,
               COALESCE(SUM(CASE WHEN jel.debit_amount > 0 THEN jel.debit_amount ELSE -jel.credit_amount END), 0) as account_balance
        FROM accounts a
        LEFT JOIN journal_entry_lines jel ON a.id = jel.account_id
        LEFT JOIN journal_entries je ON jel.journal_entry_id = je.id 
            AND je.organization_id = p_org_id
            AND je.entry_date <= as_of_date
        WHERE a.organization_id = p_org_id 
        AND a.account_type = 'liability'
        AND a.is_active = true
        GROUP BY a.id, a.account_type
    ) account_balances;
    
    -- Calculate ratio (avoid division by zero)
    IF current_liabilities > 0 THEN
        ratio := current_assets / current_liabilities;
    ELSE
        ratio := 0;
    END IF;
    
    RETURN ratio;
END;
$$;

-- Function to calculate quick ratio (excluding inventory)
CREATE OR REPLACE FUNCTION calculate_quick_ratio(
    p_org_id UUID,
    p_as_of_date DATE DEFAULT CURRENT_DATE
)
RETURNS DECIMAL(10,4)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    current_assets DECIMAL(15,2) := 0;
    inventory DECIMAL(15,2) := 0;
    current_liabilities DECIMAL(15,2) := 0;
    ratio DECIMAL(10,4) := 0;
    as_of_date DATE := p_as_of_date;
BEGIN
    -- Get current assets
    SELECT COALESCE(SUM(CASE WHEN account_balance > 0 THEN account_balance ELSE 0 END), 0)
    INTO current_assets
    FROM (
        SELECT a.id, a.account_type,
               COALESCE(SUM(CASE WHEN jel.debit_amount > 0 THEN jel.debit_amount ELSE -jel.credit_amount END), 0) as account_balance
        FROM accounts a
        LEFT JOIN journal_entry_lines jel ON a.id = jel.account_id
        LEFT JOIN journal_entries je ON jel.journal_entry_id = je.id 
            AND je.organization_id = p_org_id
            AND je.entry_date <= as_of_date
        WHERE a.organization_id = p_org_id 
        AND a.account_type = 'asset'
        AND a.is_active = true
        GROUP BY a.id, a.account_type
    ) account_balances;
    
    -- Get inventory (specific inventory accounts)
    SELECT COALESCE(SUM(CASE WHEN account_balance > 0 THEN account_balance ELSE 0 END), 0)
    INTO inventory
    FROM (
        SELECT a.id, a.account_type,
               COALESCE(SUM(CASE WHEN jel.debit_amount > 0 THEN jel.debit_amount ELSE -jel.credit_amount END), 0) as account_balance
        FROM accounts a
        LEFT JOIN journal_entry_lines jel ON a.id = jel.account_id
        LEFT JOIN journal_entries je ON jel.journal_entry_id = je.id 
            AND je.organization_id = p_org_id
            AND je.entry_date <= as_of_date
        WHERE a.organization_id = p_org_id 
        AND (a.name ILIKE '%inventory%' OR a.name ILIKE '%stock%')
        AND a.is_active = true
        GROUP BY a.id, a.account_type
    ) account_balances;
    
    -- Get current liabilities
    SELECT COALESCE(SUM(CASE WHEN account_balance < 0 THEN ABS(account_balance) ELSE 0 END), 0)
    INTO current_liabilities
    FROM (
        SELECT a.id, a.account_type,
               COALESCE(SUM(CASE WHEN jel.debit_amount > 0 THEN jel.debit_amount ELSE -jel.credit_amount END), 0) as account_balance
        FROM accounts a
        LEFT JOIN journal_entry_lines jel ON a.id = jel.account_id
        LEFT JOIN journal_entries je ON jel.journal_entry_id = je.id 
            AND je.organization_id = p_org_id
            AND je.entry_date <= as_of_date
        WHERE a.organization_id = p_org_id 
        AND a.account_type = 'liability'
        AND a.is_active = true
        GROUP BY a.id, a.account_type
    ) account_balances;
    
    -- Calculate ratio
    IF current_liabilities > 0 THEN
        ratio := (current_assets - inventory) / current_liabilities;
    ELSE
        ratio := 0;
    END IF;
    
    RETURN ratio;
END;
$$;

-- Function to calculate gross profit margin
CREATE OR REPLACE FUNCTION calculate_gross_profit_margin(
    p_org_id UUID,
    p_from_date DATE,
    p_to_date DATE
)
RETURNS DECIMAL(10,4)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    revenue DECIMAL(15,2) := 0;
    cogs DECIMAL(15,2) := 0;
    gross_profit DECIMAL(15,2) := 0;
    margin DECIMAL(10,4) := 0;
BEGIN
    -- Get total revenue
    SELECT COALESCE(SUM(CASE WHEN jel.credit_amount > 0 THEN jel.credit_amount ELSE 0 END), 0)
    INTO revenue
    FROM journal_entries je
    JOIN journal_entry_lines jel ON je.id = jel.journal_entry_id
    JOIN accounts a ON jel.account_id = a.id
    WHERE je.organization_id = p_org_id
    AND je.entry_date BETWEEN p_from_date AND p_to_date
    AND a.account_type = 'revenue'
    AND a.is_active = true;
    
    -- Get cost of goods sold
    SELECT COALESCE(SUM(CASE WHEN jel.debit_amount > 0 THEN jel.debit_amount ELSE 0 END), 0)
    INTO cogs
    FROM journal_entries je
    JOIN journal_entry_lines jel ON je.id = jel.journal_entry_id
    JOIN accounts a ON jel.account_id = a.id
    WHERE je.organization_id = p_org_id
    AND je.entry_date BETWEEN p_from_date AND p_to_date
    AND a.account_type = 'expense'
    AND (a.name ILIKE '%cost%' OR a.name ILIKE '%cogs%')
    AND a.is_active = true;
    
    -- Calculate gross profit and margin
    gross_profit := revenue - cogs;
    
    IF revenue > 0 THEN
        margin := (gross_profit / revenue) * 100;
    ELSE
        margin := 0;
    END IF;
    
    RETURN margin;
END;
$$;

-- Function to calculate net profit margin
CREATE OR REPLACE FUNCTION calculate_net_profit_margin(
    p_org_id UUID,
    p_from_date DATE,
    p_to_date DATE
)
RETURNS DECIMAL(10,4)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    revenue DECIMAL(15,2) := 0;
    total_expenses DECIMAL(15,2) := 0;
    net_income DECIMAL(15,2) := 0;
    margin DECIMAL(10,4) := 0;
BEGIN
    -- Get total revenue
    SELECT COALESCE(SUM(CASE WHEN jel.credit_amount > 0 THEN jel.credit_amount ELSE 0 END), 0)
    INTO revenue
    FROM journal_entries je
    JOIN journal_entry_lines jel ON je.id = jel.journal_entry_id
    JOIN accounts a ON jel.account_id = a.id
    WHERE je.organization_id = p_org_id
    AND je.entry_date BETWEEN p_from_date AND p_to_date
    AND a.account_type = 'revenue'
    AND a.is_active = true;
    
    -- Get total expenses
    SELECT COALESCE(SUM(CASE WHEN jel.debit_amount > 0 THEN jel.debit_amount ELSE 0 END), 0)
    INTO total_expenses
    FROM journal_entries je
    JOIN journal_entry_lines jel ON je.id = jel.journal_entry_id
    JOIN accounts a ON jel.account_id = a.id
    WHERE je.organization_id = p_org_id
    AND je.entry_date BETWEEN p_from_date AND p_to_date
    AND a.account_type = 'expense'
    AND a.is_active = true;
    
    -- Calculate net income and margin
    net_income := revenue - total_expenses;
    
    IF revenue > 0 THEN
        margin := (net_income / revenue) * 100;
    ELSE
        margin := 0;
    END IF;
    
    RETURN margin;
END;
$$;

-- Function to calculate ROA (Return on Assets)
CREATE OR REPLACE FUNCTION calculate_roa(
    p_org_id UUID,
    p_from_date DATE,
    p_to_date DATE
)
RETURNS DECIMAL(10,4)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    net_income DECIMAL(15,2) := 0;
    total_assets DECIMAL(15,2) := 0;
    roa DECIMAL(10,4) := 0;
BEGIN
    -- Get net income
    SELECT calculate_net_income(p_org_id, p_from_date, p_to_date)
    INTO net_income;
    
    -- Get total assets
    SELECT COALESCE(SUM(CASE WHEN account_balance > 0 THEN account_balance ELSE 0 END), 0)
    INTO total_assets
    FROM (
        SELECT a.id, a.account_type,
               COALESCE(SUM(CASE WHEN jel.debit_amount > 0 THEN jel.debit_amount ELSE -jel.credit_amount END), 0) as account_balance
        FROM accounts a
        LEFT JOIN journal_entry_lines jel ON a.id = jel.account_id
        LEFT JOIN journal_entries je ON jel.journal_entry_id = je.id 
            AND je.organization_id = p_org_id
            AND je.entry_date <= p_to_date
        WHERE a.organization_id = p_org_id 
        AND a.account_type = 'asset'
        AND a.is_active = true
        GROUP BY a.id, a.account_type
    ) account_balances;
    
    -- Calculate ROA
    IF total_assets > 0 THEN
        roa := (net_income / total_assets) * 100;
    ELSE
        roa := 0;
    END IF;
    
    RETURN roa;
END;
$$;

-- Helper function to calculate net income
CREATE OR REPLACE FUNCTION calculate_net_income(
    p_org_id UUID,
    p_from_date DATE,
    p_to_date DATE
)
RETURNS DECIMAL(15,2)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    revenue DECIMAL(15,2) := 0;
    expenses DECIMAL(15,2) := 0;
    net_income DECIMAL(15,2) := 0;
BEGIN
    -- Get total revenue
    SELECT COALESCE(SUM(CASE WHEN jel.credit_amount > 0 THEN jel.credit_amount ELSE 0 END), 0)
    INTO revenue
    FROM journal_entries je
    JOIN journal_entry_lines jel ON je.id = jel.journal_entry_id
    JOIN accounts a ON jel.account_id = a.id
    WHERE je.organization_id = p_org_id
    AND je.entry_date BETWEEN p_from_date AND p_to_date
    AND a.account_type = 'revenue'
    AND a.is_active = true;
    
    -- Get total expenses
    SELECT COALESCE(SUM(CASE WHEN jel.debit_amount > 0 THEN jel.debit_amount ELSE 0 END), 0)
    INTO expenses
    FROM journal_entries je
    JOIN journal_entry_lines jel ON je.id = jel.journal_entry_id
    JOIN accounts a ON jel.account_id = a.id
    WHERE je.organization_id = p_org_id
    AND je.entry_date BETWEEN p_from_date AND p_to_date
    AND a.account_type = 'expense'
    AND a.is_active = true;
    
    -- Calculate net income
    net_income := revenue - expenses;
    
    RETURN net_income;
END;
$$;

-- Function to generate balance sheet data
CREATE OR REPLACE FUNCTION generate_balance_sheet(
    p_org_id UUID,
    p_as_of_date DATE DEFAULT CURRENT_DATE
)
RETURNS TABLE(
    account_type TEXT,
    account_name TEXT,
    balance DECIMAL(15,2),
    account_id TEXT
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        a.account_type::TEXT,
        a.name::TEXT,
        COALESCE(SUM(CASE WHEN jel.debit_amount > 0 THEN jel.debit_amount ELSE -jel.credit_amount END), 0) as balance,
        a.id::TEXT as account_id
    FROM accounts a
    LEFT JOIN journal_entry_lines jel ON a.id = jel.account_id
    LEFT JOIN journal_entries je ON jel.journal_entry_id = je.id 
        AND je.organization_id = p_org_id
        AND je.entry_date <= p_as_of_date
    WHERE a.organization_id = p_org_id
    AND a.is_active = true
    GROUP BY a.id, a.account_type, a.name
    ORDER BY a.account_type, a.name;
END;
$$;

-- Function to generate income statement data
CREATE OR REPLACE FUNCTION generate_income_statement(
    p_org_id UUID,
    p_from_date DATE,
    p_to_date DATE
)
RETURNS TABLE(
    account_type TEXT,
    account_name TEXT,
    amount DECIMAL(15,2),
    account_id TEXT
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        a.account_type::TEXT,
        a.name::TEXT,
        COALESCE(SUM(CASE WHEN jel.credit_amount > 0 THEN jel.credit_amount ELSE -jel.debit_amount END), 0) as amount,
        a.id::TEXT as account_id
    FROM accounts a
    LEFT JOIN journal_entry_lines jel ON a.id = jel.account_id
    LEFT JOIN journal_entries je ON jel.journal_entry_id = je.id 
        AND je.organization_id = p_org_id
        AND je.entry_date BETWEEN p_from_date AND p_to_date
    WHERE a.organization_id = p_org_id
    AND a.is_active = true
    AND a.account_type IN ('revenue', 'expense')
    GROUP BY a.id, a.account_type, a.name
    HAVING COALESCE(SUM(CASE WHEN jel.credit_amount > 0 THEN jel.credit_amount ELSE -jel.debit_amount END), 0) != 0
    ORDER BY a.account_type, a.name;
END;
$$;

-- Function to get trial balance
CREATE OR REPLACE FUNCTION get_trial_balance(
    p_org_id UUID,
    p_as_of_date DATE DEFAULT CURRENT_DATE
)
RETURNS TABLE(
    account_name TEXT,
    account_type TEXT,
    debit_balance DECIMAL(15,2),
    credit_balance DECIMAL(15,2),
    net_balance DECIMAL(15,2),
    account_id TEXT
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        account_balances.name::TEXT,
        account_balances.account_type::TEXT,
        CASE WHEN account_balances.account_balance > 0 THEN account_balances.account_balance ELSE 0 END as debit_balance,
        CASE WHEN account_balances.account_balance < 0 THEN ABS(account_balances.account_balance) ELSE 0 END as credit_balance,
        account_balances.account_balance as net_balance,
        account_balances.id::TEXT as account_id
    FROM (
        SELECT a.id, a.name, a.account_type,
               COALESCE(SUM(CASE WHEN jel.debit_amount > 0 THEN jel.debit_amount ELSE -jel.credit_amount END), 0) as account_balance
        FROM accounts a
        LEFT JOIN journal_entry_lines jel ON a.id = jel.account_id
        LEFT JOIN journal_entries je ON jel.journal_entry_id = je.id 
            AND je.organization_id = p_org_id
            AND je.entry_date <= p_as_of_date
        WHERE a.organization_id = p_org_id
        AND a.is_active = true
        GROUP BY a.id, a.name, a.account_type
    ) account_balances
    ORDER BY account_balances.account_type, account_balances.name;
END;
$$;

-- Function to calculate working capital
CREATE OR REPLACE FUNCTION calculate_working_capital(
    p_org_id UUID,
    p_as_of_date DATE DEFAULT CURRENT_DATE
)
RETURNS DECIMAL(15,2)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    current_assets DECIMAL(15,2) := 0;
    current_liabilities DECIMAL(15,2) := 0;
    working_capital DECIMAL(15,2) := 0;
    as_of_date DATE := p_as_of_date;
BEGIN
    -- Get current assets
    SELECT COALESCE(SUM(CASE WHEN account_balance > 0 THEN account_balance ELSE 0 END), 0)
    INTO current_assets
    FROM (
        SELECT a.id, a.account_type,
               COALESCE(SUM(CASE WHEN jel.debit_amount > 0 THEN jel.debit_amount ELSE -jel.credit_amount END), 0) as account_balance
        FROM accounts a
        LEFT JOIN journal_entry_lines jel ON a.id = jel.account_id
        LEFT JOIN journal_entries je ON jel.journal_entry_id = je.id 
            AND je.organization_id = p_org_id
            AND je.entry_date <= as_of_date
        WHERE a.organization_id = p_org_id 
        AND a.account_type = 'asset'
        AND a.is_active = true
        GROUP BY a.id, a.account_type
    ) account_balances;
    
    -- Get current liabilities
    SELECT COALESCE(SUM(CASE WHEN account_balance < 0 THEN ABS(account_balance) ELSE 0 END), 0)
    INTO current_liabilities
    FROM (
        SELECT a.id, a.account_type,
               COALESCE(SUM(CASE WHEN jel.debit_amount > 0 THEN jel.debit_amount ELSE -jel.credit_amount END), 0) as account_balance
        FROM accounts a
        LEFT JOIN journal_entry_lines jel ON a.id = jel.account_id
        LEFT JOIN journal_entries je ON jel.journal_entry_id = je.id 
            AND je.organization_id = p_org_id
            AND je.entry_date <= as_of_date
        WHERE a.organization_id = p_org_id 
        AND a.account_type = 'liability'
        AND a.is_active = true
        GROUP BY a.id, a.account_type
    ) account_balances;
    
    -- Calculate working capital
    working_capital := current_assets - current_liabilities;
    
    RETURN working_capital;
END;
$$;

-- Function to get all financial ratios at once
CREATE OR REPLACE FUNCTION calculate_all_ratios(
    p_org_id UUID,
    p_from_date DATE,
    p_to_date DATE,
    p_as_of_date DATE DEFAULT CURRENT_DATE
)
RETURNS JSON
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    result JSON;
BEGIN
    SELECT json_build_object(
        'liquidity', json_build_object(
            'current_ratio', calculate_current_ratio(p_org_id, p_as_of_date),
            'quick_ratio', calculate_quick_ratio(p_org_id, p_as_of_date),
            'working_capital', calculate_working_capital(p_org_id, p_as_of_date)
        ),
        'profitability', json_build_object(
            'gross_profit_margin', calculate_gross_profit_margin(p_org_id, p_from_date, p_to_date),
            'net_profit_margin', calculate_net_profit_margin(p_org_id, p_from_date, p_to_date),
            'roa', calculate_roa(p_org_id, p_from_date, p_to_date)
        ),
        'calculation_date', CURRENT_TIMESTAMP,
        'organization_id', p_org_id
    ) INTO result;
    
    RETURN result;
END;
$$;

-- Grant permissions to authenticated users
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO authenticated; 