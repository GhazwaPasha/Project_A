-- Fix RLS policies to eliminate infinite recursion
-- This script completely removes the circular dependency

-- Drop all existing policies that might cause recursion
DROP POLICY IF EXISTS "accounts_org_isolation" ON accounts;
DROP POLICY IF EXISTS "journal_entries_org_isolation" ON journal_entries;
DROP POLICY IF EXISTS "organizations_member_access" ON organizations;
DROP POLICY IF EXISTS "org_members_access" ON organization_members;
DROP POLICY IF EXISTS "org_members_select" ON organization_members;
DROP POLICY IF EXISTS "org_members_insert" ON organization_members;
DROP POLICY IF EXISTS "org_members_update" ON organization_members;
DROP POLICY IF EXISTS "org_members_delete" ON organization_members;

-- Simple, direct policies without circular references

-- 1. Organization members policy - This is the base policy, no dependencies
CREATE POLICY "org_members_simple" ON organization_members
    FOR ALL USING (
        -- Super admin can access everything
        current_setting('app.user_role', true) = 'super_admin'
        -- Users can access their own membership records
        OR user_id = current_setting('app.current_user_id', true)::uuid
        -- Organization owners/admins can access members of their organizations
        -- We use a direct subquery without referencing the same table
        OR (
            current_setting('app.current_organization_id', true)::uuid IS NOT NULL
            AND organization_id = current_setting('app.current_organization_id', true)::uuid
            AND current_setting('app.user_role', true) IN ('organization_owner', 'organization_admin')
        )
    );

-- 2. Organizations policy - Uses app.current_user_organizations setting instead of subquery
CREATE POLICY "organizations_simple" ON organizations
    FOR ALL USING (
        -- Super admin can access everything
        current_setting('app.user_role', true) = 'super_admin'
        -- Users can only access organizations they belong to
        -- This will be set by the application based on cached memberships
        OR id::text = ANY(string_to_array(current_setting('app.user_organizations', true), ','))
    );

-- 3. Accounts policy - Simple organization isolation
CREATE POLICY "accounts_simple" ON accounts
    FOR ALL USING (
        -- Super admin can access everything
        current_setting('app.user_role', true) = 'super_admin'
        -- Users can access accounts from their current organization
        OR organization_id = current_setting('app.current_organization_id', true)::uuid
    );

-- 4. Journal entries policy - Simple organization isolation
CREATE POLICY "journal_entries_simple" ON journal_entries
    FOR ALL USING (
        -- Super admin can access everything
        current_setting('app.user_role', true) = 'super_admin'
        -- Users can access entries from their current organization
        OR organization_id = current_setting('app.current_organization_id', true)::uuid
    );

-- Create a function to help set user context (to be called by the application)
CREATE OR REPLACE FUNCTION set_user_context(
    p_user_id UUID,
    p_user_role TEXT,
    p_current_org_id UUID DEFAULT NULL,
    p_user_orgs TEXT DEFAULT NULL
)
RETURNS void AS $$
BEGIN
    -- Set the user context for RLS policies
    PERFORM set_config('app.current_user_id', p_user_id::text, true);
    PERFORM set_config('app.user_role', p_user_role, true);
    
    IF p_current_org_id IS NOT NULL THEN
        PERFORM set_config('app.current_organization_id', p_current_org_id::text, true);
    END IF;
    
    IF p_user_orgs IS NOT NULL THEN
        PERFORM set_config('app.user_organizations', p_user_orgs, true);
    END IF;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
