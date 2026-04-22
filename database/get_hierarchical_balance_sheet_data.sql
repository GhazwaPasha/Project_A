-- Function to get hierarchical balance sheet data with account details
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
    -- Get asset sections with hierarchical accounts
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
    ),
    asset_hierarchy AS (
        SELECT 
            CASE 
                WHEN "group" = 'current_asset' THEN 'Current Assets'
                WHEN "group" = 'fixed_asset' THEN 'Fixed Assets'
                WHEN "group" = 'other_asset' THEN 'Other Assets'
                ELSE 'Assets'
            END as section_name,
            "group" as section_group,
            json_agg(
                json_build_object(
                    'id', id,
                    'code', code,
                    'name', name,
                    'account_type', account_type,
                    'balance', balance,
                    'level', level,
                    'parent_id', parent_id
                ) ORDER BY code
            ) as accounts,
            SUM(balance) as section_total
        FROM asset_accounts
        WHERE balance != 0 OR "group" = 'current_asset' OR "group" = 'fixed_asset' OR "group" = 'other_asset'
        GROUP BY "group", 
            CASE 
                WHEN "group" = 'current_asset' THEN 'Current Assets'
                WHEN "group" = 'fixed_asset' THEN 'Fixed Assets'
                WHEN "group" = 'other_asset' THEN 'Other Assets'
                ELSE 'Assets'
            END
    )
    SELECT json_agg(
        json_build_object(
            'name', section_name,
            'group', section_group,
            'accounts', accounts,
            'total', section_total
        ) ORDER BY 
            CASE "section_group"
                WHEN 'current_asset' THEN 1
                WHEN 'fixed_asset' THEN 2
                WHEN 'other_asset' THEN 3
                ELSE 4
            END
    )
    INTO asset_sections
    FROM asset_hierarchy;

    -- Get liability sections with hierarchical accounts
    WITH liability_accounts AS (
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
        AND a."group" IN ('current_liability', 'long_term_liability', 'other_liability')
        AND a.is_active = true
        GROUP BY a.id, a.code, a.name, a.account_type, a."group", a.parent_id, a.level
    ),
    liability_hierarchy AS (
        SELECT 
            CASE 
                WHEN "group" = 'current_liability' THEN 'Current Liabilities'
                WHEN "group" = 'long_term_liability' THEN 'Long-term Liabilities'
                WHEN "group" = 'other_liability' THEN 'Other Liabilities'
                ELSE 'Liabilities'
            END as section_name,
            "group" as section_group,
            json_agg(
                json_build_object(
                    'id', id,
                    'code', code,
                    'name', name,
                    'account_type', account_type,
                    'balance', balance,
                    'level', level,
                    'parent_id', parent_id
                ) ORDER BY code
            ) as accounts,
            SUM(ABS(balance)) as section_total
        FROM liability_accounts
        WHERE balance != 0 OR "group" = 'current_liability' OR "group" = 'long_term_liability' OR "group" = 'other_liability'
        GROUP BY "group", 
            CASE 
                WHEN "group" = 'current_liability' THEN 'Current Liabilities'
                WHEN "group" = 'long_term_liability' THEN 'Long-term Liabilities'
                WHEN "group" = 'other_liability' THEN 'Other Liabilities'
                ELSE 'Liabilities'
            END
    )
    SELECT json_agg(
        json_build_object(
            'name', section_name,
            'group', section_group,
            'accounts', accounts,
            'total', section_total
        ) ORDER BY 
            CASE "section_group"
                WHEN 'current_liability' THEN 1
                WHEN 'long_term_liability' THEN 2
                WHEN 'other_liability' THEN 3
                ELSE 4
            END
    )
    INTO liability_sections
    FROM liability_hierarchy;

    -- Get equity sections with hierarchical accounts
    WITH equity_accounts AS (
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
        AND a."group" IN ('owners_equity', 'retained_earnings', 'other_equity')
        AND a.is_active = true
        GROUP BY a.id, a.code, a.name, a.account_type, a."group", a.parent_id, a.level
    ),
    equity_hierarchy AS (
        SELECT 
            CASE 
                WHEN "group" = 'owners_equity' THEN 'Owner''s Equity'
                WHEN "group" = 'retained_earnings' THEN 'Retained Earnings'
                WHEN "group" = 'other_equity' THEN 'Other Equity'
                ELSE 'Equity'
            END as section_name,
            "group" as section_group,
            json_agg(
                json_build_object(
                    'id', id,
                    'code', code,
                    'name', name,
                    'account_type', account_type,
                    'balance', balance,
                    'level', level,
                    'parent_id', parent_id
                ) ORDER BY code
            ) as accounts,
            SUM(balance) as section_total
        FROM equity_accounts
        WHERE balance != 0 OR "group" = 'owners_equity' OR "group" = 'retained_earnings' OR "group" = 'other_equity'
        GROUP BY "group", 
            CASE 
                WHEN "group" = 'owners_equity' THEN 'Owner''s Equity'
                WHEN "group" = 'retained_earnings' THEN 'Retained Earnings'
                WHEN "group" = 'other_equity' THEN 'Other Equity'
                ELSE 'Equity'
            END
    )
    SELECT json_agg(
        json_build_object(
            'name', section_name,
            'group', section_group,
            'accounts', accounts,
            'total', section_total
        ) ORDER BY 
            CASE "section_group"
                WHEN 'owners_equity' THEN 1
                WHEN 'retained_earnings' THEN 2
                WHEN 'other_equity' THEN 3
                ELSE 4
            END
    )
    INTO equity_sections
    FROM equity_hierarchy;

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