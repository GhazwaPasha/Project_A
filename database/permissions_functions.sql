-- Reverse migration: Drop the get_all_page_permissions function if it exists
DROP FUNCTION IF EXISTS public.get_all_page_permissions(UUID, TEXT[]);

-- Permission-related utility functions

-- Function to get all page permissions for a user in a single call
CREATE OR REPLACE FUNCTION public.get_all_page_permissions(p_org_id UUID, p_pages TEXT[])
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    user_role public.user_role;
    permissions JSONB := '{}'::JSONB;
    page_key TEXT;
    page_perms JSONB;
BEGIN
    -- Super admins get all permissions
    IF public.is_super_admin() THEN
        FOR page_key IN SELECT unnest(p_pages)
        LOOP
            permissions := permissions || jsonb_build_object(
                page_key, 
                '{"view": true, "create": true, "edit": true, "delete": true}'::JSONB
            );
        END LOOP;
        RETURN permissions;
    END IF;
    
    -- Get user's role in the organization
    user_role := public.get_user_organization_role(p_org_id);
    
    -- If no role found, return no permissions
    IF user_role IS NULL THEN
        FOR page_key IN SELECT unnest(p_pages)
        LOOP
            permissions := permissions || jsonb_build_object(
                page_key, 
                '{"view": false, "create": false, "edit": false, "delete": false}'::JSONB
            );
        END LOOP;
        RETURN permissions;
    END IF;
    
    -- Get permissions for each page
    FOR page_key IN SELECT unnest(p_pages)
    LOOP
        SELECT jsonb_build_object(
            'view', pp.can_view,
            'create', pp.can_create,
            'edit', pp.can_edit,
            'delete', pp.can_delete
        ) INTO page_perms
        FROM public.page_permissions pp
        WHERE pp.page_key = page_key 
        AND pp.role = user_role;
        
        -- If no permissions found for this page/role combination, default to false
        IF page_perms IS NULL THEN
            page_perms := '{"view": false, "create": false, "edit": false, "delete": false}'::JSONB;
        END IF;
        
        permissions := permissions || jsonb_build_object(page_key, page_perms);
    END LOOP;
    
    RETURN permissions;
END;
$$; 