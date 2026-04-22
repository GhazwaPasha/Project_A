-- Fix return types for existing functions
-- Drop and recreate functions with correct return types

-- Drop functions that need return type changes
DROP FUNCTION IF EXISTS generate_balance_sheet(UUID, DATE);
DROP FUNCTION IF EXISTS generate_income_statement(UUID, DATE, DATE);
DROP FUNCTION IF EXISTS get_trial_balance(UUID, DATE);

-- Recreate generate_balance_sheet with correct return type
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

-- Recreate generate_income_statement with correct return type
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

-- Recreate get_trial_balance with correct return type
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