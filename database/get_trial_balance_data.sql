-- Function to get trial balance data
CREATE OR REPLACE FUNCTION get_trial_balance_data(
    p_org_id UUID,
    p_as_of_date DATE DEFAULT CURRENT_DATE
)
RETURNS JSON
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    total_debits DECIMAL(15,2) := 0;
    total_credits DECIMAL(15,2) := 0;
    is_balanced BOOLEAN := false;
    accounts_data JSON;
    result JSON;
BEGIN
    -- Get all accounts with their balances
    SELECT 
        json_agg(
            json_build_object(
                'accountId', a.id,
                'accountName', a.name,
                'accountType', a.account_type,
                'debitBalance', CASE 
                    WHEN account_balance > 0 THEN account_balance 
                    ELSE 0 
                END,
                'creditBalance', CASE 
                    WHEN account_balance < 0 THEN ABS(account_balance) 
                    ELSE 0 
                END
            )
        ),
        COALESCE(SUM(CASE WHEN account_balance > 0 THEN account_balance ELSE 0 END), 0),
        COALESCE(SUM(CASE WHEN account_balance < 0 THEN ABS(account_balance) ELSE 0 END), 0)
    INTO accounts_data, total_debits, total_credits
    FROM (
        SELECT 
            a.id, 
            a.name, 
            a.account_type,
            COALESCE(SUM(CASE WHEN jel.debit_amount > 0 THEN jel.debit_amount ELSE -jel.credit_amount END), 0) as account_balance
        FROM accounts a
        LEFT JOIN journal_entry_lines jel ON a.id = jel.account_id
        LEFT JOIN journal_entries je ON jel.journal_entry_id = je.id 
            AND je.organization_id = p_org_id
            AND je.entry_date <= p_as_of_date
        WHERE a.organization_id = p_org_id 
        AND a.is_active = true
        GROUP BY a.id, a.name, a.account_type
        ORDER BY a.account_type, a.name
    ) account_balances;
    
    -- Check if balanced
    is_balanced := (total_debits = total_credits);
    
    -- Handle null accounts data
    IF accounts_data IS NULL THEN
        accounts_data := '[]'::json;
    END IF;
    
    -- Build and return JSON result
    result := json_build_object(
        'accounts', accounts_data,
        'totalDebits', total_debits,
        'totalCredits', total_credits,
        'isBalanced', is_balanced,
        'generatedAt', CURRENT_TIMESTAMP,
        'organization_id', p_org_id,
        'asOfDate', p_as_of_date
    );
    
    RETURN result;
END;
$$;
