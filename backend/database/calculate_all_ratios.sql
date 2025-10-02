-- Function to calculate all financial ratios
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
    current_assets DECIMAL(15,2) := 0;
    current_liabilities DECIMAL(15,2) := 0;
    inventory DECIMAL(15,2) := 0;
    total_assets DECIMAL(15,2) := 0;
    total_liabilities DECIMAL(15,2) := 0;
    total_equity DECIMAL(15,2) := 0;
    revenue DECIMAL(15,2) := 0;
    expenses DECIMAL(15,2) := 0;
    net_income DECIMAL(15,2) := 0;
    current_ratio DECIMAL(10,4) := 0;
    quick_ratio DECIMAL(10,4) := 0;
    working_capital DECIMAL(15,2) := 0;
    gross_profit_margin DECIMAL(10,4) := 0;
    net_profit_margin DECIMAL(10,4) := 0;
    roa DECIMAL(10,4) := 0;
    result JSON;
BEGIN
    -- Get current assets (accounts with group = 'current_asset')
    SELECT COALESCE(SUM(CASE WHEN account_balance > 0 THEN account_balance ELSE 0 END), 0)
    INTO current_assets
    FROM (
        SELECT a.id, a.account_type, a.group,
               COALESCE(SUM(CASE WHEN jel.debit_amount > 0 THEN jel.debit_amount ELSE -jel.credit_amount END), 0) as account_balance
        FROM accounts a
        LEFT JOIN journal_entry_lines jel ON a.id = jel.account_id
        LEFT JOIN journal_entries je ON jel.journal_entry_id = je.id 
            AND je.organization_id = p_org_id
            AND je.entry_date <= p_as_of_date
        WHERE a.organization_id = p_org_id 
        AND a.group = 'current_asset'
        AND a.is_active = true
        GROUP BY a.id, a.account_type, a.group
    ) account_balances;
    
    -- Get current liabilities (accounts with group = 'current_liability')
    SELECT COALESCE(SUM(CASE WHEN account_balance < 0 THEN ABS(account_balance) ELSE 0 END), 0)
    INTO current_liabilities
    FROM (
        SELECT a.id, a.account_type, a.group,
               COALESCE(SUM(CASE WHEN jel.debit_amount > 0 THEN jel.debit_amount ELSE -jel.credit_amount END), 0) as account_balance
        FROM accounts a
        LEFT JOIN journal_entry_lines jel ON a.id = jel.account_id
        LEFT JOIN journal_entries je ON jel.journal_entry_id = je.id 
            AND je.organization_id = p_org_id
            AND je.entry_date <= p_as_of_date
        WHERE a.organization_id = p_org_id 
        AND a.group = 'current_liability'
        AND a.is_active = true
        GROUP BY a.id, a.account_type, a.group
    ) account_balances;
    
    -- Get inventory (accounts with 'inventory' in name, regardless of group)
    SELECT COALESCE(SUM(CASE WHEN account_balance > 0 THEN account_balance ELSE 0 END), 0)
    INTO inventory
    FROM (
        SELECT a.id, a.account_type, a.group,
               COALESCE(SUM(CASE WHEN jel.debit_amount > 0 THEN jel.debit_amount ELSE -jel.credit_amount END), 0) as account_balance
        FROM accounts a
        LEFT JOIN journal_entry_lines jel ON a.id = jel.account_id
        LEFT JOIN journal_entries je ON jel.journal_entry_id = je.id 
            AND je.organization_id = p_org_id
            AND je.entry_date <= p_as_of_date
        WHERE a.organization_id = p_org_id 
        AND (a.name ILIKE '%inventory%' OR a.name ILIKE '%stock%' OR a.name ILIKE '%merchandise%')
        AND a.is_active = true
        GROUP BY a.id, a.account_type, a.group
    ) account_balances;
    
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
            AND je.entry_date <= p_as_of_date
        WHERE a.organization_id = p_org_id 
        AND a.account_type = 'asset'
        AND a.is_active = true
        GROUP BY a.id, a.account_type
    ) account_balances;
    
    -- Get total liabilities
    SELECT COALESCE(SUM(CASE WHEN account_balance < 0 THEN ABS(account_balance) ELSE 0 END), 0)
    INTO total_liabilities
    FROM (
        SELECT a.id, a.account_type,
               COALESCE(SUM(CASE WHEN jel.debit_amount > 0 THEN jel.debit_amount ELSE -jel.credit_amount END), 0) as account_balance
        FROM accounts a
        LEFT JOIN journal_entry_lines jel ON a.id = jel.account_id
        LEFT JOIN journal_entries je ON jel.journal_entry_id = je.id 
            AND je.organization_id = p_org_id
            AND je.entry_date <= p_as_of_date
        WHERE a.organization_id = p_org_id 
        AND a.account_type = 'liability'
        AND a.is_active = true
        GROUP BY a.id, a.account_type
    ) account_balances;
    
    -- Get total equity
    SELECT COALESCE(SUM(CASE WHEN account_balance > 0 THEN account_balance ELSE 0 END), 0)
    INTO total_equity
    FROM (
        SELECT a.id, a.account_type,
               COALESCE(SUM(CASE WHEN jel.debit_amount > 0 THEN jel.debit_amount ELSE -jel.credit_amount END), 0) as account_balance
        FROM accounts a
        LEFT JOIN journal_entry_lines jel ON a.id = jel.account_id
        LEFT JOIN journal_entries je ON jel.journal_entry_id = je.id 
            AND je.organization_id = p_org_id
            AND je.entry_date <= p_as_of_date
        WHERE a.organization_id = p_org_id 
        AND a.account_type = 'equity'
        AND a.is_active = true
        GROUP BY a.id, a.account_type
    ) account_balances;
    
    -- Get revenue for the period
    SELECT COALESCE(SUM(CASE WHEN jel.credit_amount > 0 THEN jel.credit_amount ELSE 0 END), 0)
    INTO revenue
    FROM journal_entries je
    JOIN journal_entry_lines jel ON je.id = jel.journal_entry_id
    JOIN accounts a ON jel.account_id = a.id
    WHERE je.organization_id = p_org_id
    AND je.entry_date BETWEEN p_from_date AND p_to_date
    AND a.account_type = 'revenue'
    AND a.is_active = true;
    
    -- Get expenses for the period
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
    
    -- Calculate liquidity ratios
    current_ratio := CASE WHEN current_liabilities > 0 THEN current_assets / current_liabilities ELSE 0 END;
    quick_ratio := CASE WHEN current_liabilities > 0 THEN (current_assets - inventory) / current_liabilities ELSE 0 END;
    working_capital := current_assets - current_liabilities;
    
    -- Calculate profitability ratios
    gross_profit_margin := CASE WHEN revenue > 0 THEN ((revenue - expenses) / revenue) * 100 ELSE 0 END;
    net_profit_margin := CASE WHEN revenue > 0 THEN (net_income / revenue) * 100 ELSE 0 END;
    roa := CASE WHEN total_assets > 0 THEN (net_income / total_assets) * 100 ELSE 0 END;
    
    -- Build and return JSON result
    result := json_build_object(
        'liquidity', json_build_object(
            'current_ratio', current_ratio,
            'quick_ratio', quick_ratio,
            'working_capital', working_capital
        ),
        'profitability', json_build_object(
            'gross_profit_margin', gross_profit_margin,
            'net_profit_margin', net_profit_margin,
            'roa', roa
        ),
        'calculation_date', CURRENT_TIMESTAMP,
        'organization_id', p_org_id,
        'debug_info', json_build_object(
            'current_assets', current_assets,
            'current_liabilities', current_liabilities,
            'inventory', inventory,
            'total_assets', total_assets,
            'total_liabilities', total_liabilities,
            'total_equity', total_equity,
            'revenue', revenue,
            'expenses', expenses,
            'net_income', net_income
        )
    );
    
    RETURN result;
END;
$$;
