-- Consolidated Dashboard Data Function
-- Returns all dashboard data in a single call to reduce RPC overhead

CREATE OR REPLACE FUNCTION get_dashboard_data(
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
    balance_sheet_data JSON;
    income_statement_data JSON;
    ratios_data JSON;
    dashboard_data JSON;
BEGIN
    -- Get balance sheet data (already returns JSON)
    SELECT generate_balance_sheet(p_org_id, p_as_of_date) INTO balance_sheet_data;
    
    -- Get income statement data (already returns JSON)
    SELECT generate_income_statement(p_org_id, p_from_date, p_to_date) INTO income_statement_data;
    
    -- Get all ratios
    SELECT calculate_all_ratios(p_org_id, p_from_date, p_to_date, p_as_of_date) INTO ratios_data;
    
    -- Consolidate all data into a single response
    dashboard_data := json_build_object(
        'balance_sheet', COALESCE(balance_sheet_data, '{}'::json),
        'income_statement', COALESCE(income_statement_data, '{}'::json),
        'ratios', ratios_data,
        'period', json_build_object(
            'from_date', p_from_date,
            'to_date', p_to_date,
            'as_of_date', p_as_of_date
        ),
        'organization_id', p_org_id,
        'generated_at', NOW()
    );
    
    RETURN dashboard_data;
END;
$$; 