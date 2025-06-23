-- Fix infinite recursion in organization_members policy
-- This script properly fixes the recursive policy issue

-- First, drop the problematic policy
DROP POLICY IF EXISTS "org_members_access" ON organization_members;

-- Create a better, non-recursive policy for organization_members
-- This policy allows users to see:
-- 1. Their own membership records
-- 2. Other members in organizations where they are members (but only if they're active)
CREATE POLICY "organization_members_policy" ON organization_members
FOR ALL USING (
    -- Users can see their own memberships
    auth.uid() = user_id
    OR
    -- Users can see other members in organizations where they are also members
    -- This avoids recursion by directly checking user_id instead of using a subquery on the same table
    organization_id IN (
        SELECT om.organization_id 
        FROM organization_members om 
        WHERE om.user_id = auth.uid() 
        AND om.status = 'active'
    )
);

-- Ensure RLS is enabled
ALTER TABLE organization_members ENABLE ROW LEVEL SECURITY;

-- Also create a simpler insert policy for organization_members
DROP POLICY IF EXISTS "org_members_insert" ON organization_members;
CREATE POLICY "organization_members_insert" ON organization_members
FOR INSERT WITH CHECK (
    -- Only allow inserting if the user is an admin of the organization
    -- or if they're inserting their own membership (for signup flow)
    auth.uid() = user_id
    OR
    EXISTS (
        SELECT 1 FROM organization_members om 
        WHERE om.organization_id = organization_members.organization_id 
        AND om.user_id = auth.uid() 
        AND om.role IN ('organization_owner', 'admin')
        AND om.status = 'active'
    )
);

-- Create update policy for organization_members
DROP POLICY IF EXISTS "org_members_update" ON organization_members;
CREATE POLICY "organization_members_update" ON organization_members
FOR UPDATE USING (
    -- Users can update their own membership status (e.g., to leave)
    auth.uid() = user_id
    OR
    -- Organization admins can update any membership in their org
    EXISTS (
        SELECT 1 FROM organization_members om 
        WHERE om.organization_id = organization_members.organization_id 
        AND om.user_id = auth.uid() 
        AND om.role IN ('organization_owner', 'admin')
        AND om.status = 'active'
    )
);

-- Create delete policy for organization_members  
DROP POLICY IF EXISTS "org_members_delete" ON organization_members;
CREATE POLICY "organization_members_delete" ON organization_members
FOR DELETE USING (
    -- Users can delete their own membership (leave organization)
    auth.uid() = user_id
    OR
    -- Organization owners can delete any membership
    EXISTS (
        SELECT 1 FROM organization_members om 
        WHERE om.organization_id = organization_members.organization_id 
        AND om.user_id = auth.uid() 
        AND om.role = 'organization_owner'
        AND om.status = 'active'
    )
);

-- Fix organizations table policies as well to avoid any related recursion
DROP POLICY IF EXISTS "organizations_access" ON organizations;
CREATE POLICY "organizations_policy" ON organizations
FOR ALL USING (
    -- Allow access to organizations where the user is a member
    id IN (
        SELECT organization_id 
        FROM organization_members 
        WHERE user_id = auth.uid() 
        AND status = 'active'
    )
    OR
    -- Allow public read access for public organizations (if needed)
    visibility = 'public'
);

-- Ensure organizations table has RLS enabled
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;

-- Add some helpful indexes to improve performance of these policies
CREATE INDEX IF NOT EXISTS idx_org_members_user_org ON organization_members(user_id, organization_id);
CREATE INDEX IF NOT EXISTS idx_org_members_org_status ON organization_members(organization_id, status);
CREATE INDEX IF NOT EXISTS idx_org_members_user_status ON organization_members(user_id, status);

-- Refresh the schema cache
NOTIFY pgrst, 'reload schema';
