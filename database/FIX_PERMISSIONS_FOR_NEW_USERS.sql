-- ===============================================
-- FIX PERMISSIONS FOR NEW USERS
-- ===============================================
-- This script fixes permission issues for newly created users
-- by ensuring all necessary permissions are properly set up

-- 1. First, let's check what permissions exist
SELECT 'Current page permissions:' as info;
SELECT page_key, role, can_view, can_create, can_edit, can_delete 
FROM public.page_permissions 
ORDER BY page_key, role;

-- 2. Add missing permissions for all roles
-- First, let's ensure we have all the necessary page keys
INSERT INTO public.page_permissions (page_key, role, can_view, can_create, can_edit, can_delete) VALUES
-- Team Management (missing from original setup)
('team_management', 'super_admin', true, true, true, true),
('team_management', 'organization_owner', true, true, true, false),
('team_management', 'accountant', false, false, false, false),
('team_management', 'member', false, false, false, false),

-- Organization Settings (missing from original setup)
('organization_settings', 'super_admin', true, true, true, true),
('organization_settings', 'organization_owner', true, true, true, false),
('organization_settings', 'accountant', false, false, false, false),
('organization_settings', 'member', false, false, false, false),

-- Platform Overview (missing from original setup)
('platform_overview', 'super_admin', true, true, true, true),
('platform_overview', 'organization_owner', false, false, false, false),
('platform_overview', 'accountant', false, false, false, false),
('platform_overview', 'member', false, false, false, false),

-- Global Organizations (missing from original setup)
('global_organizations', 'super_admin', true, true, true, true),
('global_organizations', 'organization_owner', false, false, false, false),
('global_organizations', 'accountant', false, false, false, false),
('global_organizations', 'member', false, false, false, false),

-- Period Closing (missing from original setup)
('period_closing', 'super_admin', true, true, true, true),
('period_closing', 'organization_owner', true, true, true, false),
('period_closing', 'accountant', false, false, false, false),
('period_closing', 'member', false, false, false, false)
ON CONFLICT (page_key, role) DO NOTHING;

-- 3. Update existing permissions to ensure organization_owner has proper access
UPDATE public.page_permissions 
SET can_view = true, can_create = true, can_edit = true, can_delete = true
WHERE role = 'organization_owner' AND page_key IN ('dashboard', 'journal_entries', 'accounts', 'reports', 'settings');

-- 4. Drop existing functions first to avoid parameter name conflicts
DROP FUNCTION IF EXISTS public.can_access_page(TEXT, UUID, TEXT);
DROP FUNCTION IF EXISTS public.get_page_permissions(TEXT, UUID);
DROP FUNCTION IF EXISTS public.get_all_page_permissions(UUID, TEXT[]);

-- 5. Fix the can_access_page function to handle edge cases better
CREATE OR REPLACE FUNCTION public.can_access_page(p_page_key TEXT, p_org_id UUID, p_permission_type TEXT DEFAULT 'view')
RETURNS BOOLEAN
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    user_role public.user_role;
    has_permission BOOLEAN := false;
    org_type TEXT;
BEGIN
    -- Super admins can access everything
    IF public.is_super_admin() THEN
        RETURN true;
    END IF;
    
    -- Get user's role in the organization
    user_role := public.get_user_organization_role(p_org_id);
    
    -- If no role found, deny access
    IF user_role IS NULL THEN
        RAISE LOG 'No role found for user in organization %', p_org_id;
        RETURN false;
    END IF;
    
    -- Get organization type to handle personal workspace restrictions
    SELECT organization_type INTO org_type
    FROM public.organizations
    WHERE id = p_org_id;
    
    -- Personal workspace restrictions
    IF org_type = 'personal' THEN
        -- Hide team management, organization settings, and user management in personal workspaces
        IF p_page_key IN ('team_management', 'organization_settings', 'user_management') THEN
            RETURN false;
        END IF;
    END IF;
    
    -- Check page permissions based on permission type
    SELECT 
        CASE p_permission_type
            WHEN 'view' THEN pp.can_view
            WHEN 'create' THEN pp.can_create  
            WHEN 'edit' THEN pp.can_edit
            WHEN 'delete' THEN pp.can_delete
            ELSE false
        END INTO has_permission
    FROM public.page_permissions pp
    WHERE pp.page_key = p_page_key 
    AND pp.role = user_role;
    
    -- Log the permission check for debugging
    RAISE LOG 'Permission check: user_role=%, page_key=%, permission_type=%, result=%', 
              user_role, p_page_key, p_permission_type, COALESCE(has_permission, false);
    
    RETURN COALESCE(has_permission, false);
END;
$$;

-- 6. Fix the get_page_permissions function to handle edge cases better
CREATE OR REPLACE FUNCTION public.get_page_permissions(p_page_key TEXT, p_org_id UUID)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    user_role public.user_role;
    permissions JSONB;
    org_type TEXT;
BEGIN
    -- Super admins get all permissions
    IF public.is_super_admin() THEN
        RETURN '{"view": true, "create": true, "edit": true, "delete": true, "is_super_admin": true}'::JSONB;
    END IF;
    
    -- Get user's role in the organization
    user_role := public.get_user_organization_role(p_org_id);
    
    -- If no role found, return no permissions
    IF user_role IS NULL THEN
        RETURN '{"view": false, "create": false, "edit": false, "delete": false}'::JSONB;
    END IF;
    
    -- Get organization type to handle personal workspace restrictions
    SELECT organization_type INTO org_type
    FROM public.organizations
    WHERE id = p_org_id;
    
    -- Personal workspace restrictions
    IF org_type = 'personal' THEN
        -- Hide team management, organization settings, and user management in personal workspaces
        IF p_page_key IN ('team_management', 'organization_settings', 'user_management') THEN
            RETURN '{"view": false, "create": false, "edit": false, "delete": false, "hidden_in_personal": true}'::JSONB;
        END IF;
    END IF;
    
    -- Get permissions for the role and page
    SELECT jsonb_build_object(
        'view', pp.can_view,
        'create', pp.can_create,
        'edit', pp.can_edit,
        'delete', pp.can_delete,
        'role', user_role,
        'additional', pp.additional_permissions
    ) INTO permissions
    FROM public.page_permissions pp
    WHERE pp.page_key = p_page_key 
    AND pp.role = user_role;
    
    RETURN COALESCE(permissions, '{"view": false, "create": false, "edit": false, "delete": false}'::JSONB);
END;
$$;

-- 7. Create a function to get all page permissions in a single call (for performance)
CREATE OR REPLACE FUNCTION public.get_all_page_permissions(p_org_id UUID, p_pages TEXT[])
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    user_role public.user_role;
    permissions JSONB := '{}'::JSONB;
    current_page TEXT;
    page_perms JSONB;
    org_type TEXT;
BEGIN
    -- Super admins get all permissions
    IF public.is_super_admin() THEN
        FOR current_page IN SELECT unnest(p_pages)
        LOOP
            permissions := permissions || jsonb_build_object(
                current_page, 
                '{"view": true, "create": true, "edit": true, "delete": true}'::JSONB
            );
        END LOOP;
        RETURN permissions;
    END IF;
    
    -- Get user's role in the organization
    user_role := public.get_user_organization_role(p_org_id);
    
    -- If no role found, return no permissions
    IF user_role IS NULL THEN
        FOR current_page IN SELECT unnest(p_pages)
        LOOP
            permissions := permissions || jsonb_build_object(
                current_page, 
                '{"view": false, "create": false, "edit": false, "delete": false}'::JSONB
            );
        END LOOP;
        RETURN permissions;
    END IF;
    
    -- Get organization type to handle personal workspace restrictions
    SELECT organization_type INTO org_type
    FROM public.organizations
    WHERE id = p_org_id;
    
    -- Get permissions for each page
    FOR current_page IN SELECT unnest(p_pages)
    LOOP
        -- Personal workspace restrictions
        IF org_type = 'personal' AND current_page IN ('team_management', 'organization_settings', 'user_management') THEN
            page_perms := '{"view": false, "create": false, "edit": false, "delete": false, "hidden_in_personal": true}'::JSONB;
        ELSE
            SELECT jsonb_build_object(
                'view', pp.can_view,
                'create', pp.can_create,
                'edit', pp.can_edit,
                'delete', pp.can_delete
            ) INTO page_perms
            FROM public.page_permissions pp
            WHERE pp.page_key = current_page 
            AND pp.role = user_role;
        END IF;
        
        -- If no permissions found for this page/role combination, default to false
        IF page_perms IS NULL THEN
            page_perms := '{"view": false, "create": false, "edit": false, "delete": false}'::JSONB;
        END IF;
        
        permissions := permissions || jsonb_build_object(current_page, page_perms);
    END LOOP;
    
    RETURN permissions;
END;
$$;

-- 8. Grant necessary permissions
GRANT EXECUTE ON FUNCTION public.can_access_page(TEXT, UUID, TEXT) TO authenticated;
GRANT EXECUTE ON FUNCTION public.get_page_permissions(TEXT, UUID) TO authenticated;
GRANT EXECUTE ON FUNCTION public.get_all_page_permissions(UUID, TEXT[]) TO authenticated;

-- 9. Verify the setup
SELECT 'Permission setup completed!' as status;

-- Show final permission matrix
SELECT 'Final permission matrix:' as info;
SELECT 
    page_key,
    role,
    CASE WHEN can_view THEN '✓' ELSE '✗' END as view,
    CASE WHEN can_create THEN '✓' ELSE '✗' END as create,
    CASE WHEN can_edit THEN '✓' ELSE '✗' END as edit,
    CASE WHEN can_delete THEN '✓' ELSE '✗' END as delete
FROM public.page_permissions 
ORDER BY page_key, role;

-- Test the functions
SELECT 'Testing permission functions:' as info;
SELECT 
    'organization_owner dashboard view' as test,
    public.can_access_page('dashboard', (SELECT id FROM public.organizations LIMIT 1), 'view') as result;

-- Show organization types
SELECT 'Organization types:' as info;
SELECT organization_type, COUNT(*) as count 
FROM public.organizations 
GROUP BY organization_type; 