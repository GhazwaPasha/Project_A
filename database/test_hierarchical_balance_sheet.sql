-- Test function to debug hierarchical balance sheet
CREATE OR REPLACE FUNCTION test_hierarchical_balance_sheet_data(
    p_org_id UUID,
    p_as_of_date DATE DEFAULT CURRENT_DATE
)
RETURNS JSON
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    result JSON;
BEGIN
    -- Simple test to get asset accounts
    WITH asset_accounts AS (
        SELECT 
            a.id,
            a.code,
            a.name,
            a.account_type,
            a."group",
            a.parent_id,
            a.level,
            COALESCE(SUM(CASE WHEN jel.debit_amount > 0 THEN jel.debit_amount ELSE -jel.credit_amount END), 0) as balance
        FROM accounts a
        LEFT JOIN journal_entry_lines jel ON a.id = jel.account_id
        LEFT JOIN journal_entries je ON jel.journal_entry_id = je.id 
            AND je.organization_id = p_org_id
            AND je.entry_date <= p_as_of_date
        WHERE a.organization_id = p_org_id 
        AND a."group" IN ('current_asset', 'fixed_asset', 'other_asset')
        AND a.is_active = true
        GROUP BY a.id, a.code, a.name, a.account_type, a."group", a.parent_id, a.level
    )
    SELECT json_agg(
        json_build_object(
            'id', id,
            'code', code,
            'name', name,
            'account_type', account_type,
            'group', "group",
            'balance', balance,
            'level', level,
            'parent_id', parent_id
        ) ORDER BY code
    )
    INTO result
    FROM asset_accounts;

    RETURN COALESCE(result, '[]'::json);
END;
$$;
