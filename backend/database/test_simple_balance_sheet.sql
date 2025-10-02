-- Simple test function to get basic account data
CREATE OR REPLACE FUNCTION test_simple_balance_sheet(
    p_org_id UUID,
    p_as_of_date DATE DEFAULT CURRENT_DATE
)
RETURNS JSON
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    result JSON;
    account_count INTEGER;
BEGIN
    -- Count accounts
    SELECT COUNT(*) INTO account_count
    FROM accounts 
    WHERE organization_id = p_org_id 
    AND is_active = true;

    -- Get sample account data
    SELECT json_agg(
        json_build_object(
            'id', id,
            'code', code,
            'name', name,
            'account_type', account_type,
            'group', "group",
            'level', level
        )
    )
    INTO result
    FROM accounts
    WHERE organization_id = p_org_id 
    AND is_active = true
    LIMIT 10;

    RETURN json_build_object(
        'account_count', account_count,
        'sample_accounts', COALESCE(result, '[]'::json),
        'org_id', p_org_id,
        'as_of_date', p_as_of_date
    );
END;
$$;
