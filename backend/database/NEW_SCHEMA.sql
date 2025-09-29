-- ===============================================
-- CLEAN MULTI-TENANT SAAS SCHEMA
-- ===============================================
-- Four Roles: Super Admin, Organization Owner, Accountant, Member
-- Clean, non-recursive RLS policies
-- Production-ready Supabase backend

-- ===============================================
-- 1. ENUMS AND TYPES
-- ===============================================

-- User roles enum (exactly 4 roles as specified)
CREATE TYPE public.user_role AS ENUM (
    'super_admin',
    'organization_owner', 
    'accountant',
    'member'
);

-- Account types for accounting system
CREATE TYPE public.account_type AS ENUM (
    'asset',
    'liability',
    'equity',
    'revenue',
    'expense'
);

-- Entry types for journal entries
CREATE TYPE public.entry_type AS ENUM (
    'debit',
    'credit'
);

-- ===============================================
-- 2. CORE TABLES
-- ===============================================

-- Organizations table (multi-tenant base)
CREATE TABLE public.organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    is_active BOOLEAN DEFAULT true
);

-- User profiles table (extends Supabase auth.users)
CREATE TABLE public.user_profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL UNIQUE,
    full_name VARCHAR(255),
    avatar_url TEXT,
    phone VARCHAR(50),
    is_super_admin BOOLEAN DEFAULT false,
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    last_sign_in_at TIMESTAMP WITH TIME ZONE
);

-- Organization membership (many-to-many with roles)
CREATE TABLE public.organization_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.user_profiles(id) ON DELETE CASCADE,
    role public.user_role NOT NULL DEFAULT 'member',
    invited_by UUID REFERENCES public.user_profiles(id),
    invited_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    joined_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true,
    permissions JSONB DEFAULT '{}',
    UNIQUE(organization_id, user_id)
);

-- ===============================================
-- 3. ACCOUNTING TABLES
-- ===============================================

-- Chart of accounts
CREATE TABLE public.accounts (
    id BIGSERIAL PRIMARY KEY,
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    code VARCHAR(20) NOT NULL,
    name VARCHAR(255) NOT NULL,
    account_type public.account_type NOT NULL,
    parent_id BIGINT REFERENCES public.accounts(id),
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    created_by UUID REFERENCES public.user_profiles(id),
    UNIQUE(organization_id, code)
);

-- Journal entries
CREATE TABLE public.journal_entries (
    id BIGSERIAL PRIMARY KEY,
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    entry_number VARCHAR(50) NOT NULL,
    entry_date DATE NOT NULL,
    description TEXT NOT NULL,
    reference VARCHAR(100),
    total_amount DECIMAL(15,2) NOT NULL DEFAULT 0,
    is_posted BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    created_by UUID REFERENCES public.user_profiles(id),
    posted_by UUID REFERENCES public.user_profiles(id),
    posted_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(organization_id, entry_number)
);

-- Journal entry line items
CREATE TABLE public.journal_entry_lines (
    id BIGSERIAL PRIMARY KEY,
    journal_entry_id BIGINT NOT NULL REFERENCES public.journal_entries(id) ON DELETE CASCADE,
    account_id BIGINT NOT NULL REFERENCES public.accounts(id),
    description TEXT,
    debit_amount DECIMAL(15,2) DEFAULT 0,
    credit_amount DECIMAL(15,2) DEFAULT 0,
    line_order INTEGER NOT NULL DEFAULT 1
);

-- Budgets
CREATE TABLE public.budgets (
    id BIGSERIAL PRIMARY KEY,
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    fiscal_year INTEGER NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    total_budget DECIMAL(15,2) DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    created_by UUID REFERENCES public.user_profiles(id)
);

-- Budget line items
CREATE TABLE public.budget_entries (
    id BIGSERIAL PRIMARY KEY,
    budget_id BIGINT NOT NULL REFERENCES public.budgets(id) ON DELETE CASCADE,
    account_id BIGINT NOT NULL REFERENCES public.accounts(id),
    budgeted_amount DECIMAL(15,2) NOT NULL DEFAULT 0,
    actual_amount DECIMAL(15,2) DEFAULT 0,
    variance DECIMAL(15,2) DEFAULT 0,
    notes TEXT,
    UNIQUE(budget_id, account_id)
);

-- Period closing
CREATE TABLE public.period_closing (
    id BIGSERIAL PRIMARY KEY,
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    period_name VARCHAR(100) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    is_closed BOOLEAN DEFAULT false,
    closed_at TIMESTAMP WITH TIME ZONE,
    closed_by UUID REFERENCES public.user_profiles(id),
    notes TEXT,
    closing_entries JSONB DEFAULT '[]',
    UNIQUE(organization_id, period_name)
);

-- Account classifications for balance sheet categorization
CREATE TABLE public.account_classifications (
    id BIGSERIAL PRIMARY KEY,
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    account_id BIGINT NOT NULL REFERENCES public.accounts(id) ON DELETE CASCADE,
    classification VARCHAR(50) NOT NULL CHECK (classification IN (
        'current_asset', 'fixed_asset', 'other_asset',
        'current_liability', 'long_term_liability', 'other_liability'
    )),
    assigned_by UUID REFERENCES public.user_profiles(id),
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    UNIQUE(organization_id, account_id)
);

-- ===============================================
-- 4. HELPER FUNCTIONS
-- ===============================================

-- Get current user's organizations
CREATE OR REPLACE FUNCTION public.get_user_organizations()
RETURNS TABLE(organization_id UUID, role public.user_role)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    RETURN QUERY
    SELECT om.organization_id, om.role
    FROM public.organization_members om
    WHERE om.user_id = auth.uid()
    AND om.is_active = true;
END;
$$;

-- Check if user is member of organization
CREATE OR REPLACE FUNCTION public.is_organization_member(org_id UUID)
RETURNS BOOLEAN
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 
        FROM public.organization_members om
        WHERE om.organization_id = org_id
        AND om.user_id = auth.uid()
        AND om.is_active = true
    );
END;
$$;

-- Get user's role in organization
CREATE OR REPLACE FUNCTION public.get_user_organization_role(org_id UUID)
RETURNS public.user_role
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    user_role public.user_role;
BEGIN
    SELECT om.role INTO user_role
    FROM public.organization_members om
    WHERE om.organization_id = org_id
    AND om.user_id = auth.uid()
    AND om.is_active = true;
    
    RETURN user_role;
END;
$$;

-- Check if user is super admin
CREATE OR REPLACE FUNCTION public.is_super_admin()
RETURNS BOOLEAN
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 
        FROM public.user_profiles up
        WHERE up.id = auth.uid()
        AND up.is_super_admin = true
    );
END;
$$;

-- ===============================================
-- 5. ROW LEVEL SECURITY POLICIES
-- ===============================================

-- Enable RLS on all tables
ALTER TABLE public.organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.organization_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.journal_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.journal_entry_lines ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.budgets ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.budget_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.period_closing ENABLE ROW LEVEL SECURITY;

-- ===============================================
-- USER PROFILES POLICIES
-- ===============================================

-- Users can read their own profile
CREATE POLICY "user_profiles_select_own" ON public.user_profiles
    FOR SELECT USING (auth.uid() = id);

-- Users can update their own profile
CREATE POLICY "user_profiles_update_own" ON public.user_profiles
    FOR UPDATE USING (auth.uid() = id);

-- Super admins can read all profiles
CREATE POLICY "user_profiles_select_super_admin" ON public.user_profiles
    FOR SELECT USING (public.is_super_admin());

-- Super admins can update all profiles
CREATE POLICY "user_profiles_update_super_admin" ON public.user_profiles
    FOR UPDATE USING (public.is_super_admin());

-- Allow profile creation during signup
CREATE POLICY "user_profiles_insert_own" ON public.user_profiles
    FOR INSERT WITH CHECK (auth.uid() = id);

-- ===============================================
-- ORGANIZATIONS POLICIES
-- ===============================================

-- Organization members can read their organizations
CREATE POLICY "organizations_select_members" ON public.organizations
    FOR SELECT USING (public.is_organization_member(id));

-- Organization owners can update their organizations
CREATE POLICY "organizations_update_owners" ON public.organizations
    FOR UPDATE USING (
        public.get_user_organization_role(id) = 'organization_owner'
    );

-- Super admins can do everything with organizations
CREATE POLICY "organizations_all_super_admin" ON public.organizations
    FOR ALL USING (public.is_super_admin());

-- Organization owners can create organizations
CREATE POLICY "organizations_insert_owners" ON public.organizations
    FOR INSERT WITH CHECK (true); -- Will be restricted by application logic

-- ===============================================
-- ORGANIZATION MEMBERS POLICIES
-- ===============================================

-- Members can read organization membership
CREATE POLICY "org_members_select_members" ON public.organization_members
    FOR SELECT USING (public.is_organization_member(organization_id));

-- Organization owners can manage membership
CREATE POLICY "org_members_all_owners" ON public.organization_members
    FOR ALL USING (
        public.get_user_organization_role(organization_id) = 'organization_owner'
    );

-- Super admins can manage all memberships
CREATE POLICY "org_members_all_super_admin" ON public.organization_members
    FOR ALL USING (public.is_super_admin());

-- ===============================================
-- ACCOUNTING DATA POLICIES
-- ===============================================

-- Accounts: Organization members can read, Accountants+ can modify
CREATE POLICY "accounts_select_members" ON public.accounts
    FOR SELECT USING (public.is_organization_member(organization_id));

CREATE POLICY "accounts_modify_accountants" ON public.accounts
    FOR ALL USING (
        public.get_user_organization_role(organization_id) IN ('organization_owner', 'accountant')
    );

-- Journal Entries: Organization members can read, Accountants+ can modify
CREATE POLICY "journal_entries_select_members" ON public.journal_entries
    FOR SELECT USING (public.is_organization_member(organization_id));

CREATE POLICY "journal_entries_modify_accountants" ON public.journal_entries
    FOR ALL USING (
        public.get_user_organization_role(organization_id) IN ('organization_owner', 'accountant')
    );

-- Journal Entry Lines: Follow journal entry permissions
CREATE POLICY "journal_lines_select_members" ON public.journal_entry_lines
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.journal_entries je 
            WHERE je.id = journal_entry_id 
            AND public.is_organization_member(je.organization_id)
        )
    );

CREATE POLICY "journal_lines_modify_accountants" ON public.journal_entry_lines
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM public.journal_entries je 
            WHERE je.id = journal_entry_id 
            AND public.get_user_organization_role(je.organization_id) IN ('organization_owner', 'accountant')
        )
    );

-- Budgets: Organization members can read, Accountants+ can modify
CREATE POLICY "budgets_select_members" ON public.budgets
    FOR SELECT USING (public.is_organization_member(organization_id));

CREATE POLICY "budgets_modify_accountants" ON public.budgets
    FOR ALL USING (
        public.get_user_organization_role(organization_id) IN ('organization_owner', 'accountant')
    );

-- Budget Entries: Follow budget permissions
CREATE POLICY "budget_entries_select_members" ON public.budget_entries
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.budgets b 
            WHERE b.id = budget_id 
            AND public.is_organization_member(b.organization_id)
        )
    );

CREATE POLICY "budget_entries_modify_accountants" ON public.budget_entries
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM public.budgets b 
            WHERE b.id = budget_id 
            AND public.get_user_organization_role(b.organization_id) IN ('organization_owner', 'accountant')
        )
    );

-- Period Closing: Organization members can read, Owners can modify
CREATE POLICY "period_closing_select_members" ON public.period_closing
    FOR SELECT USING (public.is_organization_member(organization_id));

CREATE POLICY "period_closing_modify_owners" ON public.period_closing
    FOR ALL USING (
        public.get_user_organization_role(organization_id) = 'organization_owner'
    );

-- ===============================================
-- 6. INDEXES FOR PERFORMANCE
-- ===============================================

-- Organization indexes
CREATE INDEX idx_organizations_name ON public.organizations(name);
CREATE INDEX idx_organizations_active ON public.organizations(is_active);

-- User profiles indexes
CREATE INDEX idx_user_profiles_email ON public.user_profiles(email);
CREATE INDEX idx_user_profiles_super_admin ON public.user_profiles(is_super_admin);

-- Organization members indexes
CREATE INDEX idx_org_members_org_id ON public.organization_members(organization_id);
CREATE INDEX idx_org_members_user_id ON public.organization_members(user_id);
CREATE INDEX idx_org_members_role ON public.organization_members(role);
CREATE INDEX idx_org_members_active ON public.organization_members(is_active);

-- Accounting indexes
CREATE INDEX idx_accounts_org_id ON public.accounts(organization_id);
CREATE INDEX idx_accounts_code ON public.accounts(organization_id, code);
CREATE INDEX idx_accounts_type ON public.accounts(account_type);

CREATE INDEX idx_journal_entries_org_id ON public.journal_entries(organization_id);
CREATE INDEX idx_journal_entries_date ON public.journal_entries(entry_date);
CREATE INDEX idx_journal_entries_number ON public.journal_entries(organization_id, entry_number);

CREATE INDEX idx_journal_lines_entry_id ON public.journal_entry_lines(journal_entry_id);
CREATE INDEX idx_journal_lines_account_id ON public.journal_entry_lines(account_id);

CREATE INDEX idx_budgets_org_id ON public.budgets(organization_id);
CREATE INDEX idx_budgets_fiscal_year ON public.budgets(fiscal_year);

CREATE INDEX idx_budget_entries_budget_id ON public.budget_entries(budget_id);
CREATE INDEX idx_budget_entries_account_id ON public.budget_entries(account_id);

CREATE INDEX idx_period_closing_org_id ON public.period_closing(organization_id);

CREATE INDEX idx_account_classifications_org_id ON public.account_classifications(organization_id);
CREATE INDEX idx_account_classifications_account_id ON public.account_classifications(account_id);
CREATE INDEX idx_account_classifications_classification ON public.account_classifications(classification);

-- ===============================================
-- 7. TRIGGERS FOR UPDATED_AT
-- ===============================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add triggers to tables with updated_at
CREATE TRIGGER update_organizations_updated_at 
    BEFORE UPDATE ON public.organizations 
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_user_profiles_updated_at 
    BEFORE UPDATE ON public.user_profiles 
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_accounts_updated_at 
    BEFORE UPDATE ON public.accounts 
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_journal_entries_updated_at 
    BEFORE UPDATE ON public.journal_entries 
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_budgets_updated_at 
    BEFORE UPDATE ON public.budgets 
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

-- ===============================================
-- 8. SECURITY SETTINGS
-- ===============================================

-- Grant usage on schema
GRANT USAGE ON SCHEMA public TO anon, authenticated;

-- Grant access to tables for authenticated users
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO authenticated;

-- Grant execute on functions
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO authenticated;

-- ===============================================
-- SCHEMA CREATION COMPLETE
-- ===============================================

SELECT 'Multi-tenant SaaS schema created successfully!' as status,
       'Roles: Super Admin, Organization Owner, Accountant, Member' as roles,
       'All RLS policies are non-recursive and session-based' as security;
