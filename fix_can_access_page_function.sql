-- Fix the can_access_page function to avoid parameter name conflicts
CREATE OR REPLACE FUNCTION public.can_access_page(p_page_key TEXT, p_org_id UUID, p_permission_type TEXT DEFAULT 'view')
RETURNS BOOLEAN
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    user_role public.user_role;
    has_permission BOOLEAN := false;
BEGIN
    -- Super admins can access everything
    IF public.is_super_admin() THEN
        RETURN true;
    END IF;
    
    -- Get user's role in the organization
    user_role := public.get_user_organization_role(p_org_id);
    
    -- If no role found, deny access
    IF user_role IS NULL THEN
        RETURN false;
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
    
    RETURN COALESCE(has_permission, false);
END;
$$;

-- Also fix the get_page_permissions function
CREATE OR REPLACE FUNCTION public.get_page_permissions(p_page_key TEXT, p_org_id UUID)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    user_role public.user_role;
    permissions JSONB;
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
