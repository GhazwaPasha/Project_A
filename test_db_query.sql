-- Test query to check journal entries and lines data
-- Run this in your Supabase SQL Editor to see what's actually in the database

-- 1. Check journal entries table
SELECT 
    id,
    entry_number,
    entry_date,
    description,
    total_amount,
    organization_id
FROM journal_entries 
ORDER BY created_at DESC 
LIMIT 5;

-- 2. Check journal entry lines table
SELECT 
    jel.id,
    jel.journal_entry_id,
    jel.account_id,
    jel.debit_amount,
    jel.credit_amount,
    je.entry_number,
    je.description
FROM journal_entry_lines jel
JOIN journal_entries je ON jel.journal_entry_id = je.id
ORDER BY je.created_at DESC 
LIMIT 10;

-- 3. Check accounts table
SELECT 
    id,
    code,
    name,
    organization_id
FROM accounts 
ORDER BY code 
LIMIT 10;

-- 4. Test the full join query (same as what the app uses)
SELECT 
    je.*,
    json_agg(
        json_build_object(
            'id', jel.id,
            'account_id', jel.account_id,
            'debit_amount', jel.debit_amount,
            'credit_amount', jel.credit_amount,
            'line_order', jel.line_order,
            'accounts', json_build_object(
                'id', a.id,
                'code', a.code,
                'name', a.name
            )
        )
    ) as journal_entry_lines
FROM journal_entries je
LEFT JOIN journal_entry_lines jel ON je.id = jel.journal_entry_id
LEFT JOIN accounts a ON jel.account_id = a.id
GROUP BY je.id
ORDER BY je.entry_date DESC
LIMIT 5;

-- 5. Check RLS policies for journal_entry_lines
SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual 
FROM pg_policies 
WHERE tablename = 'journal_entry_lines';

-- 6. Check if there are any journal entry lines at all
SELECT COUNT(*) as total_lines FROM journal_entry_lines;

-- 7. Check if accounts have proper foreign key relationships
SELECT 
    COUNT(*) as entries_with_lines,
    AVG(line_count) as avg_lines_per_entry
FROM (
    SELECT 
        je.id,
        COUNT(jel.id) as line_count
    FROM journal_entries je
    LEFT JOIN journal_entry_lines jel ON je.id = jel.journal_entry_id
    GROUP BY je.id
) subquery; 