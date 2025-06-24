-- Supabase Edge Function for setting database context
-- This needs to be created in Supabase SQL Editor

-- Create function to set app context for RLS policies
CREATE OR REPLACE FUNCTION set_app_context(
    user_id UUID,
    organization_id UUID DEFAULT NULL,
    role TEXT DEFAULT 'accountant'
)
RETURNS VOID AS $$
BEGIN
    -- Set the context variables for RLS policies
    PERFORM set_config('app.current_user_id', user_id::TEXT, false);
    PERFORM set_config('app.current_organization_id', COALESCE(organization_id::TEXT, ''), false);
    PERFORM set_config('app.user_role', role, false);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create improved RLS policies that avoid recursion
-- First drop all existing policies
DROP POLICY IF EXISTS "organizations_member_access" ON organizations;
DROP POLICY IF EXISTS "org_members_select" ON organization_members;
DROP POLICY IF EXISTS "org_members_insert" ON organization_members;
DROP POLICY IF EXISTS "org_members_update" ON organization_members;
DROP POLICY IF EXISTS "org_members_delete" ON organization_members;

-- Create non-recursive policies
-- Organizations: Simple policy that doesn't cause recursion
CREATE POLICY "organizations_access" ON organizations
    FOR ALL USING (
        current_setting('app.user_role', true) = 'super_admin'
        OR current_setting('app.current_user_id', true)::uuid = ANY(
            SELECT DISTINCT om.user_id 
            FROM organization_members om 
            WHERE om.organization_id = organizations.id 
            AND om.is_active = true
        )
    );

-- Organization members: Simple user-based access
CREATE POLICY "org_members_access" ON organization_members
    FOR ALL USING (
        current_setting('app.user_role', true) = 'super_admin'
        OR user_id = current_setting('app.current_user_id', true)::uuid
        OR organization_id = current_setting('app.current_organization_id', true)::uuid
    );

-- Helper function to get user organizations (bypasses RLS)
CREATE OR REPLACE FUNCTION get_user_organizations(p_user_id UUID)
RETURNS TABLE (
    organization_id UUID,
    organization_name TEXT,
    user_role TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        o.id as organization_id,
        o.name as organization_name,
        om.role as user_role
    FROM organizations o
    INNER JOIN organization_members om ON o.id = om.organization_id
    WHERE om.user_id = p_user_id 
    AND om.is_active = true
    AND o.is_active = true;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to safely check if user can access organization
CREATE OR REPLACE FUNCTION can_access_organization(p_user_id UUID, p_org_id UUID)
RETURNS BOOLEAN AS $$
DECLARE
    has_access BOOLEAN := false;
BEGIN
    SELECT EXISTS(
        SELECT 1 FROM organization_members om
        WHERE om.user_id = p_user_id 
        AND om.organization_id = p_org_id
        AND om.is_active = true
    ) INTO has_access;
    
    RETURN has_access;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
