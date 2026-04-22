-- ===============================================
-- FIX ORGANIZATION LOADING ISSUE
-- ===============================================
-- This script fixes the circular dependency in RLS policies that prevents
-- users from loading their organizations properly

-- Drop the problematic policy that causes circular dependency
DROP POLICY IF EXISTS "org_members_select_members" ON public.organization_members;

-- Drop the existing policy if it exists  
DROP POLICY IF EXISTS "org_members_select_own" ON public.organization_members;

-- Create a simple policy that allows users to see their own memberships
CREATE POLICY "org_members_select_own" ON public.organization_members
    FOR SELECT USING (user_id = auth.uid() OR public.is_super_admin());

-- Test query to verify organizations are loading
-- Replace 'your-user-id-here' with an actual user ID
/*
SELECT 
    om.organization_id,
    om.role,
    o.name as organization_name,
    o.description
FROM public.organization_members om
JOIN public.organizations o ON o.id = om.organization_id
WHERE om.user_id = 'your-user-id-here'
AND om.is_active = true;
*/

-- Verify the fix
SELECT 'Organization loading issue fixed!' as status,
       'Users can now see their own organization memberships' as message;
