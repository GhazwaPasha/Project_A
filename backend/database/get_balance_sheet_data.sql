-- Function to get balance sheet data
CREATE OR REPLACE FUNCTION get_balance_sheet_data(
    p_org_id UUID,
    p_as_of_date DATE DEFAULT CURRENT_DATE
)
RETURNS JSON
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    current_assets DECIMAL(15,2) := 0;
    fixed_assets DECIMAL(15,2) := 0;
    other_assets DECIMAL(15,2) := 0;
    total_assets DECIMAL(15,2) := 0;
    current_liabilities DECIMAL(15,2) := 0;
    long_term_liabilities DECIMAL(15,2) := 0;
    other_liabilities DECIMAL(15,2) := 0;
    total_liabilities DECIMAL(15,2) := 0;
    owners_equity DECIMAL(15,2) := 0;
    retained_earnings DECIMAL(15,2) := 0;
    other_equity DECIMAL(15,2) := 0;
    total_equity DECIMAL(15,2) := 0;
    is_balanced BOOLEAN := false;
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
    
    -- Get fixed assets (accounts with group = 'fixed_asset')
    SELECT COALESCE(SUM(CASE WHEN account_balance > 0 THEN account_balance ELSE 0 END), 0)
    INTO fixed_assets
    FROM (
        SELECT a.id, a.account_type, a.group,
               COALESCE(SUM(CASE WHEN jel.debit_amount > 0 THEN jel.debit_amount ELSE -jel.credit_amount END), 0) as account_balance
        FROM accounts a
        LEFT JOIN journal_entry_lines jel ON a.id = jel.account_id
        LEFT JOIN journal_entries je ON jel.journal_entry_id = je.id 
            AND je.organization_id = p_org_id
            AND je.entry_date <= p_as_of_date
        WHERE a.organization_id = p_org_id 
        AND a.group = 'fixed_asset'
        AND a.is_active = true
        GROUP BY a.id, a.account_type, a.group
    ) account_balances;
    
    -- Get other assets (accounts with group = 'other_asset')
    SELECT COALESCE(SUM(CASE WHEN account_balance > 0 THEN account_balance ELSE 0 END), 0)
    INTO other_assets
    FROM (
        SELECT a.id, a.account_type, a.group,
               COALESCE(SUM(CASE WHEN jel.debit_amount > 0 THEN jel.debit_amount ELSE -jel.credit_amount END), 0) as account_balance
        FROM accounts a
        LEFT JOIN journal_entry_lines jel ON a.id = jel.account_id
        LEFT JOIN journal_entries je ON jel.journal_entry_id = je.id 
            AND je.organization_id = p_org_id
            AND je.entry_date <= p_as_of_date
        WHERE a.organization_id = p_org_id 
        AND a.group = 'other_asset'
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
    
    -- Get long-term liabilities (accounts with group = 'long_term_liability')
    SELECT COALESCE(SUM(CASE WHEN account_balance < 0 THEN ABS(account_balance) ELSE 0 END), 0)
    INTO long_term_liabilities
    FROM (
        SELECT a.id, a.account_type, a.group,
               COALESCE(SUM(CASE WHEN jel.debit_amount > 0 THEN jel.debit_amount ELSE -jel.credit_amount END), 0) as account_balance
        FROM accounts a
        LEFT JOIN journal_entry_lines jel ON a.id = jel.account_id
        LEFT JOIN journal_entries je ON jel.journal_entry_id = je.id 
            AND je.organization_id = p_org_id
            AND je.entry_date <= p_as_of_date
        WHERE a.organization_id = p_org_id 
        AND a.group = 'long_term_liability'
        AND a.is_active = true
        GROUP BY a.id, a.account_type, a.group
    ) account_balances;
    
    -- Get other liabilities (accounts with group = 'other_liability')
    SELECT COALESCE(SUM(CASE WHEN account_balance < 0 THEN ABS(account_balance) ELSE 0 END), 0)
    INTO other_liabilities
    FROM (
        SELECT a.id, a.account_type, a.group,
               COALESCE(SUM(CASE WHEN jel.debit_amount > 0 THEN jel.debit_amount ELSE -jel.credit_amount END), 0) as account_balance
        FROM accounts a
        LEFT JOIN journal_entry_lines jel ON a.id = jel.account_id
        LEFT JOIN journal_entries je ON jel.journal_entry_id = je.id 
            AND je.organization_id = p_org_id
            AND je.entry_date <= p_as_of_date
        WHERE a.organization_id = p_org_id 
        AND a.group = 'other_liability'
        AND a.is_active = true
        GROUP BY a.id, a.account_type, a.group
    ) account_balances;
    
    -- Get owner's equity (accounts with group = 'owners_equity')
    SELECT COALESCE(SUM(CASE WHEN account_balance > 0 THEN account_balance ELSE 0 END), 0)
    INTO owners_equity
    FROM (
        SELECT a.id, a.account_type, a.group,
               COALESCE(SUM(CASE WHEN jel.debit_amount > 0 THEN jel.debit_amount ELSE -jel.credit_amount END), 0) as account_balance
        FROM accounts a
        LEFT JOIN journal_entry_lines jel ON a.id = jel.account_id
        LEFT JOIN journal_entries je ON jel.journal_entry_id = je.id 
            AND je.organization_id = p_org_id
            AND je.entry_date <= p_as_of_date
        WHERE a.organization_id = p_org_id 
        AND a.group = 'owners_equity'
        AND a.is_active = true
        GROUP BY a.id, a.account_type, a.group
    ) account_balances;
    
    -- Get retained earnings (accounts with group = 'retained_earnings')
    SELECT COALESCE(SUM(CASE WHEN account_balance > 0 THEN account_balance ELSE 0 END), 0)
    INTO retained_earnings
    FROM (
        SELECT a.id, a.account_type, a.group,
               COALESCE(SUM(CASE WHEN jel.debit_amount > 0 THEN jel.debit_amount ELSE -jel.credit_amount END), 0) as account_balance
        FROM accounts a
        LEFT JOIN journal_entry_lines jel ON a.id = jel.account_id
        LEFT JOIN journal_entries je ON jel.journal_entry_id = je.id 
            AND je.organization_id = p_org_id
            AND je.entry_date <= p_as_of_date
        WHERE a.organization_id = p_org_id 
        AND a.group = 'retained_earnings'
        AND a.is_active = true
        GROUP BY a.id, a.account_type, a.group
    ) account_balances;
    
    -- Get other equity (accounts with group = 'other_equity')
    SELECT COALESCE(SUM(CASE WHEN account_balance > 0 THEN account_balance ELSE 0 END), 0)
    INTO other_equity
    FROM (
        SELECT a.id, a.account_type, a.group,
               COALESCE(SUM(CASE WHEN jel.debit_amount > 0 THEN jel.debit_amount ELSE -jel.credit_amount END), 0) as account_balance
        FROM accounts a
        LEFT JOIN journal_entry_lines jel ON a.id = jel.account_id
        LEFT JOIN journal_entries je ON jel.journal_entry_id = je.id 
            AND je.organization_id = p_org_id
            AND je.entry_date <= p_as_of_date
        WHERE a.organization_id = p_org_id 
        AND a.group = 'other_equity'
        AND a.is_active = true
        GROUP BY a.id, a.account_type, a.group
    ) account_balances;
    
    -- Calculate totals
    total_assets := current_assets + fixed_assets + other_assets;
    total_liabilities := current_liabilities + long_term_liabilities + other_liabilities;
    total_equity := owners_equity + retained_earnings + other_equity;
    
    -- Check if balanced
    is_balanced := (total_assets = (total_liabilities + total_equity));
    
    -- Build and return JSON result
    result := json_build_object(
        'assets', json_build_object(
            'current', current_assets,
            'fixed', fixed_assets,
            'other', other_assets,
            'total', total_assets
        ),
        'liabilities', json_build_object(
            'current', current_liabilities,
            'longTerm', long_term_liabilities,
            'other', other_liabilities,
            'total', total_liabilities
        ),
        'equity', json_build_object(
            'owners', owners_equity,
            'retained', retained_earnings,
            'other', other_equity,
            'total', total_equity
        ),
        'isBalanced', is_balanced,
        'generatedAt', CURRENT_TIMESTAMP,
        'organization_id', p_org_id,
        'asOfDate', p_as_of_date
    );
    
    RETURN result;
END;
$$;
