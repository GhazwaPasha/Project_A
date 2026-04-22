-- Function to get hierarchical balance sheet data with account details (flexible version)
CREATE OR REPLACE FUNCTION get_hierarchical_balance_sheet_data(
    p_org_id UUID,
    p_as_of_date DATE DEFAULT CURRENT_DATE
)
RETURNS JSON
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    result JSON;
    asset_sections JSON;
    liability_sections JSON;
    equity_sections JSON;
    total_assets DECIMAL(15,2) := 0;
    total_liabilities DECIMAL(15,2) := 0;
    total_equity DECIMAL(15,2) := 0;
    is_balanced BOOLEAN := false;
BEGIN
    -- Get all accounts with their balances
    WITH account_balances AS (
        SELECT 
            a.id,
            a.code,
            a.name,
            a.account_type,
            a."group",
            a.parent_id,
            COALESCE(SUM(CASE WHEN jel.debit_amount > 0 THEN jel.debit_amount ELSE -jel.credit_amount END), 0) as balance
        FROM accounts a
        LEFT JOIN journal_entry_lines jel ON a.id = jel.account_id
        LEFT JOIN journal_entries je ON jel.journal_entry_id = je.id 
            AND je.organization_id = p_org_id
            AND je.entry_date <= p_as_of_date
        WHERE a.organization_id = p_org_id 
        AND a.is_active = true
        GROUP BY a.id, a.code, a.name, a.account_type, a."group", a.parent_id
    ),
    -- Group accounts by their group and create sections
    grouped_accounts AS (
        SELECT 
            "group",
            CASE 
                WHEN "group" LIKE '%asset%' OR "group" = 'current_asset' OR "group" = 'fixed_asset' THEN 'Assets'
                WHEN "group" LIKE '%liability%' OR "group" = 'current_liability' OR "group" = 'long_term_liability' THEN 'Liabilities'
                WHEN "group" LIKE '%equity%' OR "group" = 'owners_equity' OR "group" = 'retained_earnings' THEN 'Equity'
                ELSE 'Other'
            END as category,
            json_agg(
                json_build_object(
                    'id', id,
                    'code', code,
                    'name', name,
                    'account_type', account_type,
                    'balance', balance,
                    'parent_id', parent_id
                ) ORDER BY code
            ) as accounts,
            SUM(CASE 
                WHEN "group" LIKE '%liability%' OR "group" = 'current_liability' OR "group" = 'long_term_liability' 
                THEN ABS(balance) 
                ELSE balance 
            END) as section_total
        FROM account_balances
        WHERE balance != 0
        GROUP BY "group"
    ),
    -- Create asset sections
    asset_sections_data AS (
        SELECT 
            "group" as section_name,
            "group" as section_group,
            accounts,
            section_total
        FROM grouped_accounts
        WHERE category = 'Assets'
    ),
    -- Create liability sections
    liability_sections_data AS (
        SELECT 
            "group" as section_name,
            "group" as section_group,
            accounts,
            section_total
        FROM grouped_accounts
        WHERE category = 'Liabilities'
    ),
    -- Create equity sections
    equity_sections_data AS (
        SELECT 
            "group" as section_name,
            "group" as section_group,
            accounts,
            section_total
        FROM grouped_accounts
        WHERE category = 'Equity'
    )
    -- Get asset sections
    SELECT COALESCE(json_agg(
        json_build_object(
            'name', section_name,
            'group', section_group,
            'accounts', accounts,
            'total', section_total
        )
    ), '[]'::json)
    INTO asset_sections
    FROM asset_sections_data;

    -- Get liability sections
    SELECT COALESCE(json_agg(
        json_build_object(
            'name', section_name,
            'group', section_group,
            'accounts', accounts,
            'total', section_total
        )
    ), '[]'::json)
    INTO liability_sections
    FROM liability_sections_data;

    -- Get equity sections
    SELECT COALESCE(json_agg(
        json_build_object(
            'name', section_name,
            'group', section_group,
            'accounts', accounts,
            'total', section_total
        )
    ), '[]'::json)
    INTO equity_sections
    FROM equity_sections_data;

    -- Calculate totals
    SELECT COALESCE(SUM((section->>'total')::DECIMAL), 0) INTO total_assets
    FROM json_array_elements(COALESCE(asset_sections, '[]'::json));

    SELECT COALESCE(SUM((section->>'total')::DECIMAL), 0) INTO total_liabilities
    FROM json_array_elements(COALESCE(liability_sections, '[]'::json));

    SELECT COALESCE(SUM((section->>'total')::DECIMAL), 0) INTO total_equity
    FROM json_array_elements(COALESCE(equity_sections, '[]'::json));

    -- Check if balanced
    is_balanced := (total_assets = (total_liabilities + total_equity));

    -- Build result
    result := json_build_object(
        'is_group_based', true,
        'asset_sections', COALESCE(asset_sections, '[]'::json),
        'liability_sections', COALESCE(liability_sections, '[]'::json),
        'equity_sections', COALESCE(equity_sections, '[]'::json),
        'total_assets', total_assets,
        'total_liabilities', total_liabilities,
        'total_equity', total_equity,
        'is_balanced', is_balanced,
        'generated_at', NOW()::text
    );

    RETURN result;
END;
$$;
