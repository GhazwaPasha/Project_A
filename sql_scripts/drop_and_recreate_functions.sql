-- Drop existing functions to allow recreation with new return types
DROP FUNCTION IF EXISTS calculate_current_ratio(UUID, DATE);
DROP FUNCTION IF EXISTS calculate_quick_ratio(UUID, DATE);
DROP FUNCTION IF EXISTS calculate_gross_profit_margin(UUID, DATE, DATE);
DROP FUNCTION IF EXISTS calculate_net_profit_margin(UUID, DATE, DATE);
DROP FUNCTION IF EXISTS calculate_roa(UUID, DATE, DATE);
DROP FUNCTION IF EXISTS calculate_net_income(UUID, DATE, DATE);
DROP FUNCTION IF EXISTS generate_balance_sheet(UUID, DATE);
DROP FUNCTION IF EXISTS generate_income_statement(UUID, DATE, DATE);
DROP FUNCTION IF EXISTS get_trial_balance(UUID, DATE);
DROP FUNCTION IF EXISTS calculate_working_capital(UUID, DATE);
DROP FUNCTION IF EXISTS calculate_all_ratios(UUID, DATE, DATE, DATE);

-- Now recreate all functions with correct return types and fixed logic

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
    net_profit DECIMAL(15,2) := 0;
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
    
    -- Calculate net profit and margin
    net_profit := revenue - total_expenses;
    
    IF revenue > 0 THEN
        margin := (net_profit / revenue) * 100;
    ELSE
        margin := 0;
    END IF;
    
    RETURN margin;
END;
$$;

-- Function to calculate Return on Assets (ROA)
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
    as_of_date DATE := p_to_date;
BEGIN
    -- Get net income for the period
    SELECT COALESCE(SUM(CASE WHEN jel.credit_amount > 0 THEN jel.credit_amount ELSE 0 END), 0) -
           COALESCE(SUM(CASE WHEN jel.debit_amount > 0 THEN jel.debit_amount ELSE 0 END), 0)
    INTO net_income
    FROM journal_entries je
    JOIN journal_entry_lines jel ON je.id = jel.journal_entry_id
    JOIN accounts a ON jel.account_id = a.id
    WHERE je.organization_id = p_org_id
    AND je.entry_date BETWEEN p_from_date AND p_to_date
    AND a.account_type IN ('revenue', 'expense')
    AND a.is_active = true;
    
    -- Get total assets as of the end date
    SELECT COALESCE(SUM(CASE WHEN account_balance > 0 THEN account_balance ELSE 0 END), 0)
    INTO total_assets
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
    
    -- Calculate ROA
    IF total_assets > 0 THEN
        roa := (net_income / total_assets) * 100;
    ELSE
        roa := 0;
    END IF;
    
    RETURN roa;
END;
$$;

-- Function to calculate net income
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

-- Function to generate balance sheet
CREATE OR REPLACE FUNCTION generate_balance_sheet(
    p_org_id UUID,
    p_as_of_date DATE DEFAULT CURRENT_DATE
)
RETURNS JSON
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    balance_sheet JSON;
    as_of_date DATE := p_as_of_date;
BEGIN
    -- Get balance sheet data
    WITH account_balances AS (
        SELECT 
            a.id,
            a.name,
            a.account_type,
            a.group,
            COALESCE(SUM(CASE WHEN jel.debit_amount > 0 THEN jel.debit_amount ELSE -jel.credit_amount END), 0) as balance
        FROM accounts a
        LEFT JOIN journal_entry_lines jel ON a.id = jel.account_id
        LEFT JOIN journal_entries je ON jel.journal_entry_id = je.id 
            AND je.organization_id = p_org_id
            AND je.entry_date <= as_of_date
        WHERE a.organization_id = p_org_id 
        AND a.is_active = true
        GROUP BY a.id, a.name, a.account_type, a.group
    )
    SELECT json_build_object(
        'as_of_date', as_of_date,
        'total_assets', COALESCE(SUM(CASE WHEN account_type = 'asset' AND balance > 0 THEN balance ELSE 0 END), 0),
        'total_liabilities', COALESCE(SUM(CASE WHEN account_type = 'liability' AND balance < 0 THEN ABS(balance) ELSE 0 END), 0),
        'total_equity', COALESCE(SUM(CASE WHEN account_type = 'equity' AND balance < 0 THEN ABS(balance) ELSE 0 END), 0),
        'accounts', json_agg(
            json_build_object(
                'id', id,
                'name', name,
                'account_type', account_type,
                'group', "group",
                'balance', balance
            )
        )
    ) INTO balance_sheet
    FROM account_balances;
    
    RETURN balance_sheet;
END;
$$;

-- Function to generate income statement
CREATE OR REPLACE FUNCTION generate_income_statement(
    p_org_id UUID,
    p_from_date DATE,
    p_to_date DATE
)
RETURNS JSON
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    income_statement JSON;
BEGIN
    -- Get income statement data
    WITH period_activity AS (
        SELECT 
            a.id,
            a.name,
            a.account_type,
            a.group,
            COALESCE(SUM(CASE WHEN jel.credit_amount > 0 THEN jel.credit_amount ELSE 0 END), 0) as credits,
            COALESCE(SUM(CASE WHEN jel.debit_amount > 0 THEN jel.debit_amount ELSE 0 END), 0) as debits
        FROM accounts a
        LEFT JOIN journal_entry_lines jel ON a.id = jel.account_id
        LEFT JOIN journal_entries je ON jel.journal_entry_id = je.id 
            AND je.organization_id = p_org_id
            AND je.entry_date BETWEEN p_from_date AND p_to_date
        WHERE a.organization_id = p_org_id 
        AND a.account_type IN ('revenue', 'expense')
        AND a.is_active = true
        GROUP BY a.id, a.name, a.account_type, a.group
    )
    SELECT json_build_object(
        'from_date', p_from_date,
        'to_date', p_to_date,
        'total_revenue', COALESCE(SUM(CASE WHEN account_type = 'revenue' THEN credits ELSE 0 END), 0),
        'total_expenses', COALESCE(SUM(CASE WHEN account_type = 'expense' THEN debits ELSE 0 END), 0),
        'net_income', COALESCE(SUM(CASE WHEN account_type = 'revenue' THEN credits ELSE 0 END), 0) - 
                     COALESCE(SUM(CASE WHEN account_type = 'expense' THEN debits ELSE 0 END), 0),
        'accounts', json_agg(
            json_build_object(
                'id', id,
                'name', name,
                'account_type', account_type,
                'group', "group",
                'credits', credits,
                'debits', debits,
                'net_amount', CASE WHEN account_type = 'revenue' THEN credits ELSE -debits END
            )
        )
    ) INTO income_statement
    FROM period_activity;
    
    RETURN income_statement;
END;
$$;

-- Function to get trial balance
CREATE OR REPLACE FUNCTION get_trial_balance(
    p_org_id UUID,
    p_as_of_date DATE DEFAULT CURRENT_DATE
)
RETURNS JSON
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    trial_balance JSON;
    as_of_date DATE := p_as_of_date;
BEGIN
    -- Get trial balance data
    WITH account_balances AS (
        SELECT 
            a.id,
            a.name,
            a.account_type,
            a.group,
            COALESCE(SUM(CASE WHEN jel.debit_amount > 0 THEN jel.debit_amount ELSE -jel.credit_amount END), 0) as balance
        FROM accounts a
        LEFT JOIN journal_entry_lines jel ON a.id = jel.account_id
        LEFT JOIN journal_entries je ON jel.journal_entry_id = je.id 
            AND je.organization_id = p_org_id
            AND je.entry_date <= as_of_date
        WHERE a.organization_id = p_org_id 
        AND a.is_active = true
        GROUP BY a.id, a.name, a.account_type, a.group
    )
    SELECT json_build_object(
        'as_of_date', as_of_date,
        'total_debits', COALESCE(SUM(CASE WHEN balance > 0 THEN balance ELSE 0 END), 0),
        'total_credits', COALESCE(SUM(CASE WHEN balance < 0 THEN ABS(balance) ELSE 0 END), 0),
        'accounts', json_agg(
            json_build_object(
                'id', id,
                'name', name,
                'account_type', account_type,
                'group', "group",
                'balance', balance
            )
        )
    ) INTO trial_balance
    FROM account_balances;
    
    RETURN trial_balance;
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
    
    -- Calculate working capital
    working_capital := current_assets - current_liabilities;
    
    RETURN working_capital;
END;
$$;

-- Optimized function to calculate all ratios using existing balance sheet and income statement data
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
    -- Financial data from balance sheet and income statement
    balance_sheet_data JSON;
    income_statement_data JSON;
    
    -- Extracted values
    current_assets DECIMAL(15,2) := 0;
    current_liabilities DECIMAL(15,2) := 0;
    total_assets DECIMAL(15,2) := 0;
    total_liabilities DECIMAL(15,2) := 0;
    total_equity DECIMAL(15,2) := 0;
    cash DECIMAL(15,2) := 0;
    inventory DECIMAL(15,2) := 0;
    receivables DECIMAL(15,2) := 0;
    payables DECIMAL(15,2) := 0;
    long_term_debt DECIMAL(15,2) := 0;
    total_revenue DECIMAL(15,2) := 0;
    total_cogs DECIMAL(15,2) := 0;
    gross_profit DECIMAL(15,2) := 0;
    total_expenses DECIMAL(15,2) := 0;
    net_income DECIMAL(15,2) := 0;
    
    -- Calculated ratios
    current_ratio DECIMAL(10,4) := 0;
    quick_ratio DECIMAL(10,4) := 0;
    debt_to_equity DECIMAL(10,4) := 0;
    gross_profit_margin DECIMAL(10,4) := 0;
    net_profit_margin DECIMAL(10,4) := 0;
    roa DECIMAL(10,4) := 0;
    
    ratios JSON;
BEGIN
    -- Get balance sheet data
    SELECT generate_balance_sheet(p_org_id, p_as_of_date) INTO balance_sheet_data;
    
    -- Get income statement data
    SELECT generate_income_statement(p_org_id, p_from_date, p_to_date) INTO income_statement_data;
    
    -- Extract values from balance sheet
    current_assets := COALESCE((balance_sheet_data->>'total_assets')::DECIMAL, 0);
    total_assets := COALESCE((balance_sheet_data->>'total_assets')::DECIMAL, 0);
    total_liabilities := COALESCE((balance_sheet_data->>'total_liabilities')::DECIMAL, 0);
    total_equity := COALESCE((balance_sheet_data->>'total_equity')::DECIMAL, 0);
    
    -- Extract values from income statement
    total_revenue := COALESCE((income_statement_data->>'total_revenue')::DECIMAL, 0);
    total_expenses := COALESCE((income_statement_data->>'total_expenses')::DECIMAL, 0);
    net_income := COALESCE((income_statement_data->>'net_income')::DECIMAL, 0);
    
    -- Calculate current liabilities (simplified - all liabilities for now)
    current_liabilities := total_liabilities;
    
    -- Calculate ratios
    -- Current Ratio
    IF current_liabilities > 0 THEN
        current_ratio := current_assets / current_liabilities;
    ELSE
        current_ratio := 0;
    END IF;
    
    -- Quick Ratio (excluding inventory)
    IF current_liabilities > 0 THEN
        quick_ratio := (current_assets - inventory) / current_liabilities;
    ELSE
        quick_ratio := 0;
    END IF;
    
    -- Debt-to-Equity Ratio
    IF total_equity > 0 THEN
        debt_to_equity := total_liabilities / total_equity;
    ELSE
        debt_to_equity := 0;
    END IF;
    
    -- Gross Profit Margin
    gross_profit := total_revenue - total_cogs;
    IF total_revenue > 0 THEN
        gross_profit_margin := (gross_profit / total_revenue) * 100;
    ELSE
        gross_profit_margin := 0;
    END IF;
    
    -- Net Profit Margin
    IF total_revenue > 0 THEN
        net_profit_margin := (net_income / total_revenue) * 100;
    ELSE
        net_profit_margin := 0;
    END IF;
    
    -- Return on Assets (ROA)
    IF total_assets > 0 THEN
        roa := (net_income / total_assets) * 100;
    ELSE
        roa := 0;
    END IF;
    
    -- Build ratios JSON
    ratios := json_build_object(
        'financial_data', json_build_object(
            'current_assets', current_assets,
            'current_liabilities', current_liabilities,
            'total_assets', total_assets,
            'total_liabilities', total_liabilities,
            'total_equity', total_equity,
            'cash', cash,
            'inventory', inventory,
            'receivables', receivables,
            'payables', payables,
            'long_term_debt', long_term_debt,
            'total_revenue', total_revenue,
            'total_cogs', total_cogs,
            'gross_profit', gross_profit,
            'total_expenses', total_expenses,
            'net_income', net_income
        ),
        'ratios', json_build_object(
            'liquidity', json_build_object(
                'current_ratio', json_build_object('value', current_ratio, 'label', 'Current Ratio'),
                'quick_ratio', json_build_object('value', quick_ratio, 'label', 'Quick Ratio')
            ),
            'leverage', json_build_object(
                'debt_to_equity', json_build_object('value', debt_to_equity, 'label', 'Debt-to-Equity Ratio')
            ),
            'profitability', json_build_object(
                'gross_profit_margin', json_build_object('value', gross_profit_margin, 'label', 'Gross Profit Margin (%)'),
                'net_profit_margin', json_build_object('value', net_profit_margin, 'label', 'Net Profit Margin (%)'),
                'roa', json_build_object('value', roa, 'label', 'Return on Assets (%)')
            )
        ),
        'as_of_date', p_as_of_date,
        'period', json_build_object('from_date', p_from_date, 'to_date', p_to_date)
    );
    
    RETURN ratios;
END;
$$; 