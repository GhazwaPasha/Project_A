-- Function to get income statement data
CREATE OR REPLACE FUNCTION get_income_statement_data(
    p_org_id UUID,
    p_from_date DATE,
    p_to_date DATE
)
RETURNS JSON
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    revenue_total DECIMAL(15,2) := 0;
    expenses_total DECIMAL(15,2) := 0;
    net_income DECIMAL(15,2) := 0;
    gross_profit DECIMAL(15,2) := 0;
    operating_income DECIMAL(15,2) := 0;
    revenue_breakdown JSON := '[]'::json;
    expenses_breakdown JSON := '[]'::json;
    result JSON;
BEGIN
    -- Get revenue breakdown
    SELECT 
        COALESCE(SUM(CASE WHEN jel.credit_amount > 0 THEN jel.credit_amount ELSE 0 END), 0),
        json_agg(
            json_build_object(
                'account', a.name,
                'amount', COALESCE(SUM(CASE WHEN jel.credit_amount > 0 THEN jel.credit_amount ELSE 0 END), 0)
            )
        ) FILTER (WHERE COALESCE(SUM(CASE WHEN jel.credit_amount > 0 THEN jel.credit_amount ELSE 0 END), 0) > 0)
    INTO revenue_total, revenue_breakdown
    FROM accounts a
    JOIN journal_entry_lines jel ON a.id = jel.account_id
    JOIN journal_entries je ON jel.journal_entry_id = je.id
    WHERE je.organization_id = p_org_id
    AND je.entry_date BETWEEN p_from_date AND p_to_date
    AND a.account_type = 'revenue'
    AND a.is_active = true
    GROUP BY a.id, a.name;
    
    -- Get expenses breakdown
    SELECT 
        COALESCE(SUM(CASE WHEN jel.debit_amount > 0 THEN jel.debit_amount ELSE 0 END), 0),
        json_agg(
            json_build_object(
                'account', a.name,
                'amount', COALESCE(SUM(CASE WHEN jel.debit_amount > 0 THEN jel.debit_amount ELSE 0 END), 0)
            )
        ) FILTER (WHERE COALESCE(SUM(CASE WHEN jel.debit_amount > 0 THEN jel.debit_amount ELSE 0 END), 0) > 0)
    INTO expenses_total, expenses_breakdown
    FROM accounts a
    JOIN journal_entry_lines jel ON a.id = jel.account_id
    JOIN journal_entries je ON jel.journal_entry_id = je.id
    WHERE je.organization_id = p_org_id
    AND je.entry_date BETWEEN p_from_date AND p_to_date
    AND a.account_type = 'expense'
    AND a.is_active = true
    GROUP BY a.id, a.name;
    
    -- Calculate derived values
    net_income := revenue_total - expenses_total;
    gross_profit := revenue_total - expenses_total; -- Simplified for now
    operating_income := revenue_total - expenses_total; -- Simplified for now
    
    -- Handle null breakdowns
    IF revenue_breakdown IS NULL THEN
        revenue_breakdown := '[]'::json;
    END IF;
    
    IF expenses_breakdown IS NULL THEN
        expenses_breakdown := '[]'::json;
    END IF;
    
    -- Build and return JSON result
    result := json_build_object(
        'revenue', json_build_object(
            'total', revenue_total,
            'breakdown', revenue_breakdown
        ),
        'expenses', json_build_object(
            'total', expenses_total,
            'breakdown', expenses_breakdown
        ),
        'netIncome', net_income,
        'grossProfit', gross_profit,
        'operatingIncome', operating_income,
        'generatedAt', CURRENT_TIMESTAMP,
        'organization_id', p_org_id,
        'fromDate', p_from_date,
        'toDate', p_to_date
    );
    
    RETURN result;
END;
$$;
