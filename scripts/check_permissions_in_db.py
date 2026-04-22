#!/usr/bin/env python3
"""
Check permissions in database
"""
import os
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client, Client

REPO_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(REPO_ROOT / ".env")

def check_permissions_in_db():
    """Check if permissions are set up correctly in the database"""
    
    # Initialize Supabase client
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_ANON_KEY')
    
    if not url or not key:
        print("❌ Supabase credentials not found in .env file")
        return
    
    supabase: Client = create_client(url, key)
    
    print("🔍 Checking permissions in database...")
    print("=" * 50)
    
    # Check 1: Page permissions table
    print("\n1. Checking page_permissions table...")
    try:
        result = supabase.table('page_permissions').select('*').execute()
        print(f"✅ Found {len(result.data)} page permissions:")
        for perm in result.data:
            print(f"   {perm['page_key']} - {perm['role']}: view={perm['can_view']}, create={perm['can_create']}, edit={perm['can_edit']}, delete={perm['can_delete']}")
    except Exception as e:
        print(f"❌ Error checking page_permissions: {e}")
    
    # Check 2: Organization members
    print("\n2. Checking organization_members table...")
    try:
        result = supabase.table('organization_members').select('*').limit(5).execute()
        print(f"✅ Found {len(result.data)} organization members:")
        for member in result.data:
            print(f"   User {member['user_id']} in org {member['organization_id']}: role={member['role']}, active={member['is_active']}")
    except Exception as e:
        print(f"❌ Error checking organization_members: {e}")
    
    # Check 3: Organizations
    print("\n3. Checking organizations table...")
    try:
        result = supabase.table('organizations').select('*').limit(5).execute()
        print(f"✅ Found {len(result.data)} organizations:")
        for org in result.data:
            print(f"   {org['name']} (ID: {org['id']}): type={org.get('organization_type', 'unknown')}")
    except Exception as e:
        print(f"❌ Error checking organizations: {e}")
    
    # Check 4: Users
    print("\n4. Checking users table...")
    try:
        result = supabase.table('users').select('*').limit(5).execute()
        print(f"✅ Found {len(result.data)} users:")
        for user in result.data:
            print(f"   {user.get('email', 'No email')} (ID: {user['id']})")
    except Exception as e:
        print(f"❌ Error checking users: {e}")
    
    print("\n" + "=" * 50)
    print("Database check completed!")

if __name__ == "__main__":
    check_permissions_in_db() 