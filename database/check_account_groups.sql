-- Check what account groups exist in the database
SELECT DISTINCT "group", COUNT(*) as count
FROM accounts 
WHERE organization_id = 'your-org-id-here'  -- Replace with actual org ID
AND is_active = true
GROUP BY "group"
ORDER BY "group";
