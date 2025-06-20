"""
Quick Multi-Tenant Database Setup Script
Run this to create the multi-tenant schema in your Supabase database
"""
import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

def run_migration():
    """Run the multi-tenant migration"""
    try:
        # Load environment variables
        load_dotenv()
        
        # Database connection parameters from environment
        conn_params = {
            'host': os.getenv('POSTGRES_HOST'),
            'port': int(os.getenv('POSTGRES_PORT', 5432)),
            'database': os.getenv('POSTGRES_DB'),
            'user': os.getenv('POSTGRES_USER'),
            'password': os.getenv('POSTGRES_PASSWORD')
        }
        
        # Validate required parameters
        if not all([conn_params['host'], conn_params['database'], 
                   conn_params['user'], conn_params['password']]):
            print("❌ Missing required database connection parameters in .env file")
            print("Required: POSTGRES_HOST, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD")
            return False
        
        print("Connecting to Supabase database...")
        conn = psycopg2.connect(**conn_params)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Read the migration script
        migration_file = os.path.join(os.path.dirname(__file__), 'create_multitenant_schema.sql')
        
        if not os.path.exists(migration_file):
            print(f"Migration file not found: {migration_file}")
            print("Creating basic multi-tenant tables...")
            
            # Basic multi-tenant schema
            migration_sql = """
            -- Create organizations table
            CREATE TABLE IF NOT EXISTS organizations (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name VARCHAR(255) NOT NULL,
                slug VARCHAR(100) UNIQUE NOT NULL,
                settings JSONB DEFAULT '{}',
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            
            -- Create roles table
            CREATE TABLE IF NOT EXISTS roles (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name VARCHAR(50) UNIQUE NOT NULL,
                description TEXT,
                permissions JSONB DEFAULT '{}',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            
            -- Insert default roles
            INSERT INTO roles (name, description, permissions) VALUES
            ('super_admin', 'Super Administrator', '{"all": true}'),
            ('org_owner', 'Organization Owner', '{"org_admin": true, "user_management": true, "billing": true}'),
            ('org_admin', 'Organization Administrator', '{"user_management": true, "settings": true}'),
            ('accountant', 'Accountant', '{"accounting": true, "reports": true}')
            ON CONFLICT (name) DO NOTHING;
            
            -- Create users table (extending Supabase auth.users)
            CREATE TABLE IF NOT EXISTS users (
                id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
                first_name VARCHAR(100),
                last_name VARCHAR(100),
                avatar_url TEXT,
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            
            -- Create organization_members table
            CREATE TABLE IF NOT EXISTS organization_members (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                role_id UUID NOT NULL REFERENCES roles(id),
                is_active BOOLEAN DEFAULT true,
                invited_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                joined_at TIMESTAMP WITH TIME ZONE,
                invited_by UUID REFERENCES users(id),
                UNIQUE(organization_id, user_id)
            );
            
            -- Add organization context to existing tables
            ALTER TABLE accounts ADD COLUMN IF NOT EXISTS organization_id UUID REFERENCES organizations(id);
            ALTER TABLE accounts ADD COLUMN IF NOT EXISTS created_by UUID REFERENCES users(id);
            ALTER TABLE accounts ADD COLUMN IF NOT EXISTS updated_by UUID REFERENCES users(id);
            
            ALTER TABLE journal_entries ADD COLUMN IF NOT EXISTS organization_id UUID REFERENCES organizations(id);
            ALTER TABLE journal_entries ADD COLUMN IF NOT EXISTS created_by UUID REFERENCES users(id);
            ALTER TABLE journal_entries ADD COLUMN IF NOT EXISTS updated_by UUID REFERENCES users(id);
            
            -- Create indexes
            CREATE INDEX IF NOT EXISTS idx_accounts_organization ON accounts(organization_id);
            CREATE INDEX IF NOT EXISTS idx_journal_entries_organization ON journal_entries(organization_id);
            CREATE INDEX IF NOT EXISTS idx_organization_members_org ON organization_members(organization_id);
            CREATE INDEX IF NOT EXISTS idx_organization_members_user ON organization_members(user_id);
            
            -- Enable RLS
            ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;
            ALTER TABLE users ENABLE ROW LEVEL SECURITY;
            ALTER TABLE organization_members ENABLE ROW LEVEL SECURITY;
            ALTER TABLE accounts ENABLE ROW LEVEL SECURITY;
            ALTER TABLE journal_entries ENABLE ROW LEVEL SECURITY;
            
            -- Basic RLS policies
            CREATE POLICY "Users can view their own profile" ON users
                FOR SELECT USING (auth.uid() = id);
            
            CREATE POLICY "Users can view their organizations" ON organizations
                FOR SELECT USING (
                    id IN (
                        SELECT organization_id FROM organization_members 
                        WHERE user_id = auth.uid() AND is_active = true
                    )
                );
            
            CREATE POLICY "Organization members can view accounts" ON accounts
                FOR SELECT USING (
                    organization_id IN (
                        SELECT organization_id FROM organization_members 
                        WHERE user_id = auth.uid() AND is_active = true
                    )
                );
            
            CREATE POLICY "Organization members can view journal entries" ON journal_entries
                FOR SELECT USING (
                    organization_id IN (
                        SELECT organization_id FROM organization_members 
                        WHERE user_id = auth.uid() AND is_active = true
                    )
                );
            
            -- Create default organization for existing data
            INSERT INTO organizations (name, slug) VALUES ('Default Organization', 'default-org')
            ON CONFLICT (slug) DO NOTHING;
            
            COMMIT;
            """
        else:
            with open(migration_file, 'r') as f:
                migration_sql = f.read()
        
        print("Running migration...")
        cursor.execute(migration_sql)
        conn.commit()
        
        print("✅ Multi-tenant schema created successfully!")
        print("✅ Default roles created: super_admin, org_owner, org_admin, accountant")
        print("✅ Row Level Security enabled")
        print("✅ Default organization created")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 Setting up Multi-Tenant Accounting Database...")
    if run_migration():
        print("\n✅ Setup complete! You can now run the application with: python main_auth.py")
    else:
        print("\n❌ Setup failed. Please check your database connection and try again.")
        sys.exit(1)
