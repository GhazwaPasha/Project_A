"""
Database schema migration for multi-tenant support
Run this to create the new tables and modify existing ones
"""

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

-- 5. Modify existing accounts table
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'accounts' AND column_name = 'organization_id') THEN
        ALTER TABLE accounts ADD COLUMN organization_id UUID REFERENCES organizations(id);
        ALTER TABLE accounts ADD COLUMN created_by UUID REFERENCES users(id);
        ALTER TABLE accounts ADD COLUMN updated_by UUID REFERENCES users(id);
    END IF;
END $$;

-- 6. Modify existing journal_entries table  
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'journal_entries' AND column_name = 'organization_id') THEN
        ALTER TABLE journal_entries ADD COLUMN organization_id UUID REFERENCES organizations(id);
        ALTER TABLE journal_entries ADD COLUMN created_by UUID REFERENCES users(id);
        ALTER TABLE journal_entries ADD COLUMN updated_by UUID REFERENCES users(id);
    END IF;
END $$;

-- 7. Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_accounts_organization_id ON accounts(organization_id);
CREATE INDEX IF NOT EXISTS idx_journal_entries_organization_id ON journal_entries(organization_id);
CREATE INDEX IF NOT EXISTS idx_organization_members_user_id ON organization_members(user_id);
CREATE INDEX IF NOT EXISTS idx_organization_members_org_id ON organization_members(organization_id);
CREATE INDEX IF NOT EXISTS idx_users_last_login ON users(last_login_at);

-- 8. Enable Row Level Security
ALTER TABLE accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE journal_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE organization_members ENABLE ROW LEVEL SECURITY;

-- 9. Create RLS Policies
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

-- Organizations: Users can only see organizations they belong to
CREATE POLICY "organizations_member_access" ON organizations
    FOR ALL USING (
        current_setting('app.user_role', true) = 'super_admin'
        OR id IN (
            SELECT organization_id FROM organization_members 
            WHERE user_id = current_setting('app.current_user_id', true)::uuid 
            AND is_active = true
        )
    );

-- Organization members: Users can see members of their organizations
CREATE POLICY "org_members_access" ON organization_members
    FOR ALL USING (
        current_setting('app.user_role', true) = 'super_admin'
        OR organization_id IN (
            SELECT organization_id FROM organization_members 
            WHERE user_id = current_setting('app.current_user_id', true)::uuid 
            AND is_active = true
        )
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

-- 11. Create default organization for existing data migration
INSERT INTO organizations (name, slug, description) 
VALUES ('Default Organization', 'default', 'Migrated from single-tenant setup')
ON CONFLICT (slug) DO NOTHING;

-- 12. Update existing data with default organization (if any exists)
DO $$ 
DECLARE
    default_org_id UUID;
BEGIN
    SELECT id INTO default_org_id FROM organizations WHERE slug = 'default';
    
    IF default_org_id IS NOT NULL THEN
        UPDATE accounts SET organization_id = default_org_id WHERE organization_id IS NULL;
        UPDATE journal_entries SET organization_id = default_org_id WHERE organization_id IS NULL;
    END IF;
END $$;
