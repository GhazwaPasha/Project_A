-- Function to get aged receivables data
CREATE OR REPLACE FUNCTION get_aged_receivables_data(
    p_org_id UUID,
    p_as_of_date DATE DEFAULT CURRENT_DATE
)
RETURNS JSON
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    receivables_data JSON;
    totals_data JSON;
    result JSON;
BEGIN
    -- Get aged receivables data
    -- Note: This is a simplified version. In a real system, you'd need customer/vendor tables
    -- and proper aging logic based on invoice dates and payment terms.
    
    WITH aged_data AS (
        SELECT 
            'Sample Customer' as customer_name,
            CASE 
                WHEN EXTRACT(DAYS FROM (p_as_of_date - je.entry_date)) <= 30 THEN COALESCE(SUM(CASE WHEN jel.credit_amount > 0 THEN jel.credit_amount ELSE 0 END), 0)
                ELSE 0
            END as current_amount,
            CASE 
                WHEN EXTRACT(DAYS FROM (p_as_of_date - je.entry_date)) BETWEEN 31 AND 60 THEN COALESCE(SUM(CASE WHEN jel.credit_amount > 0 THEN jel.credit_amount ELSE 0 END), 0)
                ELSE 0
            END as days_30_amount,
            CASE 
                WHEN EXTRACT(DAYS FROM (p_as_of_date - je.entry_date)) BETWEEN 61 AND 90 THEN COALESCE(SUM(CASE WHEN jel.credit_amount > 0 THEN jel.credit_amount ELSE 0 END), 0)
                ELSE 0
            END as days_60_amount,
            CASE 
                WHEN EXTRACT(DAYS FROM (p_as_of_date - je.entry_date)) > 90 THEN COALESCE(SUM(CASE WHEN jel.credit_amount > 0 THEN jel.credit_amount ELSE 0 END), 0)
                ELSE 0
            END as days_90_amount
        FROM accounts a
        JOIN journal_entry_lines jel ON a.id = jel.account_id
        JOIN journal_entries je ON jel.journal_entry_id = je.id
        WHERE je.organization_id = p_org_id
        AND je.entry_date <= p_as_of_date
        AND a.account_type = 'asset'
        AND (a.name ILIKE '%receivable%' OR a.name ILIKE '%customer%')
        AND a.is_active = true
        GROUP BY je.entry_date
    )
    SELECT 
        json_agg(
            json_build_object(
                'customerName', customer_name,
                'current', current_amount,
                'days30', days_30_amount,
                'days60', days_60_amount,
                'days90', days_90_amount,
                'total', current_amount + days_30_amount + days_60_amount + days_90_amount
            )
        ) FILTER (WHERE (current_amount + days_30_amount + days_60_amount + days_90_amount) > 0),
        json_build_object(
            'current', COALESCE(SUM(current_amount), 0),
            'days30', COALESCE(SUM(days_30_amount), 0),
            'days60', COALESCE(SUM(days_60_amount), 0),
            'days90', COALESCE(SUM(days_90_amount), 0),
            'total', COALESCE(SUM(current_amount + days_30_amount + days_60_amount + days_90_amount), 0)
        )
    INTO receivables_data, totals_data
    FROM aged_data;
    
    -- Handle null data
    IF receivables_data IS NULL THEN
        receivables_data := '[]'::json;
    END IF;
    
    IF totals_data IS NULL THEN
        totals_data := json_build_object(
            'current', 0,
            'days30', 0,
            'days60', 0,
            'days90', 0,
            'total', 0
        );
    END IF;
    
    -- Build and return JSON result
    result := json_build_object(
        'receivables', receivables_data,
        'totals', totals_data,
        'generatedAt', CURRENT_TIMESTAMP,
        'organization_id', p_org_id,
        'asOfDate', p_as_of_date
    );
    
    RETURN result;
END;
$$;
