-- Function to get financial metrics for dashboard (JSON version)
CREATE OR REPLACE FUNCTION get_financial_metrics_json(
    p_organization_id UUID
)
RETURNS JSON
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    revenue DECIMAL(15,2) := 0;
    expenses DECIMAL(15,2) := 0;
    net_income DECIMAL(15,2) := 0;
    assets DECIMAL(15,2) := 0;
    liabilities DECIMAL(15,2) := 0;
    equity DECIMAL(15,2) := 0;
    current_date DATE := CURRENT_DATE;
    result JSON;
BEGIN
    -- Get total revenue (all time)
    SELECT COALESCE(SUM(CASE WHEN jel.credit_amount > 0 THEN jel.credit_amount ELSE 0 END), 0)
    INTO revenue
    FROM journal_entries je
    JOIN journal_entry_lines jel ON je.id = jel.journal_entry_id
    JOIN accounts a ON jel.account_id = a.id
    WHERE je.organization_id = p_organization_id
    AND a.account_type = 'revenue'
    AND a.is_active = true;
    
    -- Get total expenses (all time)
    SELECT COALESCE(SUM(CASE WHEN jel.debit_amount > 0 THEN jel.debit_amount ELSE 0 END), 0)
    INTO expenses
    FROM journal_entries je
    JOIN journal_entry_lines jel ON je.id = jel.journal_entry_id
    JOIN accounts a ON jel.account_id = a.id
    WHERE je.organization_id = p_organization_id
    AND a.account_type = 'expense'
    AND a.is_active = true;
    
    -- Calculate net income
    net_income := revenue - expenses;
    
    -- Get total assets (current balance)
    SELECT COALESCE(SUM(CASE WHEN account_balance > 0 THEN account_balance ELSE 0 END), 0)
    INTO assets
    FROM (
        SELECT a.id,
               COALESCE(SUM(CASE WHEN jel.debit_amount > 0 THEN jel.debit_amount ELSE -jel.credit_amount END), 0) as account_balance
        FROM accounts a
        LEFT JOIN journal_entry_lines jel ON a.id = jel.account_id
        LEFT JOIN journal_entries je ON jel.journal_entry_id = je.id 
            AND je.organization_id = p_organization_id
            AND je.entry_date <= current_date
        WHERE a.organization_id = p_organization_id 
        AND a.account_type = 'asset'
        AND a.is_active = true
        GROUP BY a.id
    ) account_balances;
    
    -- Get total liabilities (current balance)
    SELECT COALESCE(SUM(CASE WHEN account_balance < 0 THEN ABS(account_balance) ELSE 0 END), 0)
    INTO liabilities
    FROM (
        SELECT a.id,
               COALESCE(SUM(CASE WHEN jel.debit_amount > 0 THEN jel.debit_amount ELSE -jel.credit_amount END), 0) as account_balance
        FROM accounts a
        LEFT JOIN journal_entry_lines jel ON a.id = jel.account_id
        LEFT JOIN journal_entries je ON jel.journal_entry_id = je.id 
            AND je.organization_id = p_organization_id
            AND je.entry_date <= current_date
        WHERE a.organization_id = p_organization_id 
        AND a.account_type = 'liability'
        AND a.is_active = true
        GROUP BY a.id
    ) account_balances;
    
    -- Get total equity (current balance)
    SELECT COALESCE(SUM(CASE WHEN account_balance > 0 THEN account_balance ELSE 0 END), 0)
    INTO equity
    FROM (
        SELECT a.id,
               COALESCE(SUM(CASE WHEN jel.debit_amount > 0 THEN jel.debit_amount ELSE -jel.credit_amount END), 0) as account_balance
        FROM accounts a
        LEFT JOIN journal_entry_lines jel ON a.id = jel.account_id
        LEFT JOIN journal_entries je ON jel.journal_entry_id = je.id 
            AND je.organization_id = p_organization_id
            AND je.entry_date <= current_date
        WHERE a.organization_id = p_organization_id 
        AND a.account_type = 'equity'
        AND a.is_active = true
        GROUP BY a.id
    ) account_balances;
    
    -- Build and return JSON result
    result := json_build_object(
        'totalRevenue', revenue,
        'totalExpenses', expenses,
        'netIncome', net_income,
        'totalAssets', assets,
        'totalLiabilities', liabilities,
        'totalEquity', equity
    );
    
    RETURN result;
END;
$$;
