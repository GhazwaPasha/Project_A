#!/usr/bin/env python3
"""
Fix the organization_members policy to avoid infinite recursion
"""
import os
from supabase import create_client, Client

def fix_policy():
    """Fix the organization members policy"""
    # Get Supabase credentials
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_ANON_KEY')
    
    if not url or not key:
        print("❌ Supabase credentials not found. Please set SUPABASE_URL and SUPABASE_ANON_KEY.")
        return False
    
    try:
        # Create Supabase client
        supabase: Client = create_client(url, key)
        
        print("🔧 Fixing organization_members policy...")
        
        # Drop the existing policy
        drop_policy_sql = """
        DROP POLICY IF EXISTS "org_members_access" ON organization_members;
        """
        
        # Create the new fixed policy
        create_policy_sql = """
        CREATE POLICY "org_members_access" ON organization_members
        FOR ALL USING (
            current_setting('app.user_role', true) = 'super_admin'
            OR user_id = current_setting('app.current_user_id', true)::uuid
            OR organization_id = current_setting('app.current_organization_id', true)::uuid
        );
        """
        
        # Execute the SQL commands
        result = supabase.rpc('exec_sql', {'sql': drop_policy_sql})
        print("✅ Dropped old policy")
        
        result = supabase.rpc('exec_sql', {'sql': create_policy_sql})
        print("✅ Created new policy")
        
        print("🎉 Policy fixed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing policy: {e}")
        return False

if __name__ == "__main__":
    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    
    fix_policy()
