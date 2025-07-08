-- Database schema migration for multi-tenant support
-- Run this to create the new tables and modify existing ones

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Organizations table
CREATE TABLE IF NOT EXISTS organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    industry VARCHAR(100),
    fiscal_year_start DATE DEFAULT '01-01',
    base_currency VARCHAR(3) DEFAULT 'USD',
    settings JSONB DEFAULT '{
        "multi_currency": false,
        "tax_enabled": true,
        "audit_trail": true
    }',
    subscription_plan VARCHAR(50) DEFAULT 'basic',
    subscription_status VARCHAR(20) DEFAULT 'active',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Extended users table (connected to Supabase auth.users)
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    display_name VARCHAR(200),
    avatar_url TEXT,
    job_title VARCHAR(100),
    preferences JSONB DEFAULT '{
        "theme": "dark",
        "currency_display": "symbol",
        "date_format": "MM/DD/YYYY",
        "notifications": {
            "email": true,
            "in_app": true
        }
    }',
    last_login_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Organization membership (junction table)
CREATE TABLE IF NOT EXISTS organization_members (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL DEFAULT 'accountant',
    department VARCHAR(100),
    invited_by UUID REFERENCES users(id),
    invited_at TIMESTAMP WITH TIME ZONE,
    invitation_token VARCHAR(255),
    invitation_expires_at TIMESTAMP WITH TIME ZONE,
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_active_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(organization_id, user_id)
);

-- 4. System roles definition
CREATE TABLE IF NOT EXISTS roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(150) NOT NULL,
    description TEXT,
    permissions JSONB NOT NULL DEFAULT '{}',
    is_system_role BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert system roles
INSERT INTO roles (name, display_name, description, permissions, is_system_role) VALUES 
('super_admin', 'Super Administrator', 'Platform administrator with full access', '{
    "platform": {"manage": true, "view": true},
    "organizations": {"create": true, "delete": true, "manage": true, "view": true},
    "users": {"create": true, "delete": true, "manage": true, "view": true},
    "accounting": {"create": true, "read": true, "update": true, "delete": true}
}', true),
('organization_owner', 'Organization Owner', 'Full control over organization', '{
    "organization": {"manage": true, "delete": true, "billing": true},
    "users": {"invite": true, "remove": true, "manage_roles": true},
    "accounting": {"create": true, "read": true, "update": true, "delete": true}
}', true),
('organization_admin', 'Organization Administrator', 'Administrative access within organization', '{
    "organization": {"manage": true, "settings": true},
    "users": {"invite": true, "remove": true, "assign_accountant": true},
    "accounting": {"create": true, "read": true, "update": true, "delete": true}
}', true),
('accountant', 'Accountant', 'Full accounting operations access', '{
    "accounting": {"create": true, "read": true, "update": true, "delete": true},
    "reports": {"generate": true, "export": true}
}', true)
ON CONFLICT (name) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description,
    permissions = EXCLUDED.permissions,
    updated_at = NOW();

-- 8. Enable Row Level Security
ALTER TABLE accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE journal_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE organization_members ENABLE ROW LEVEL SECURITY;

-- First, drop all existing policies to avoid conflicts
DROP POLICY IF EXISTS "accounts_org_isolation" ON accounts;
DROP POLICY IF EXISTS "journal_entries_org_isolation" ON journal_entries;
DROP POLICY IF EXISTS "organizations_member_access" ON organizations;

DROP POLICY IF EXISTS "org_members_access" ON organization_members;
DROP POLICY IF EXISTS "org_members_select" ON organization_members;
DROP POLICY IF EXISTS "org_members_insert" ON organization_members;
DROP POLICY IF EXISTS "org_members_update" ON organization_members;
DROP POLICY IF EXISTS "org_members_delete" ON organization_members;

-- 9. Create RLS Policies with recursion fixes
-- First, create helper functions to avoid recursion
CREATE OR REPLACE FUNCTION set_app_context(
    user_id UUID,
    organization_id UUID DEFAULT NULL,
    role TEXT DEFAULT 'accountant'
)
RETURNS VOID AS $$
BEGIN
    PERFORM set_config('app.current_user_id', user_id::TEXT, false);
    PERFORM set_config('app.current_organization_id', COALESCE(organization_id::TEXT, ''), false);
    PERFORM set_config('app.user_role', role, false);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

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

-- Accounts: Users can only access accounts from their organization
CREATE POLICY "accounts_org_isolation" ON accounts
    FOR ALL USING (
        organization_id = current_setting('app.current_organization_id', true)::uuid
        OR current_setting('app.user_role', true) = 'super_admin'
    );

-- Journal entries: Users can only access entries from their organization  
CREATE POLICY "journal_entries_org_isolation" ON journal_entries
    FOR ALL USING (
        organization_id = current_setting('app.current_organization_id', true)::uuid
        OR current_setting('app.user_role', true) = 'super_admin'
    );

-- Organizations: Non-recursive policy using subquery
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

-- Organization members: Simple access policy - avoid recursion
CREATE POLICY "org_members_access" ON organization_members
    FOR ALL USING (
        current_setting('app.user_role', true) = 'super_admin'
        OR user_id = current_setting('app.current_user_id', true)::uuid
    );

-- 10. Create triggers for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply triggers to new tables
DROP TRIGGER IF EXISTS update_organizations_updated_at ON organizations;
CREATE TRIGGER update_organizations_updated_at 
    BEFORE UPDATE ON organizations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_org_members_updated_at ON organization_members;
CREATE TRIGGER update_org_members_updated_at 
    BEFORE UPDATE ON organization_members
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
