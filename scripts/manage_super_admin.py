#!/usr/bin/env python3
"""
Super Admin Management Tool
Use this script to promote users to super admin or revoke super admin status
"""
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client, Client

REPO_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(REPO_ROOT / ".env")

def get_supabase_client() -> Client:
    """Initialize Supabase client"""
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')  # Use service role key for admin operations
    
    if not url or not key:
        raise Exception("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in .env file")
    
    return create_client(url, key)

def list_super_admins():
    """List all current super admins"""
    supabase = get_supabase_client()
    
    try:
        result = supabase.table('user_profiles')\
            .select('email, full_name, created_at')\
            .eq('is_super_admin', True)\
            .execute()
        
        if result.data:
            print("\n🔐 Current Super Admins:")
            print("-" * 50)
            for admin in result.data:
                print(f"📧 {admin['email']}")
                print(f"👤 {admin.get('full_name', 'N/A')}")
                print(f"📅 Created: {admin['created_at'][:10]}")
                print("-" * 30)
        else:
            print("❌ No super admins found!")
            
    except Exception as e:
        print(f"❌ Error listing super admins: {e}")

def promote_user(email: str):
    """Promote a user to super admin"""
    supabase = get_supabase_client()
    
    try:
        # First check if user exists
        user_check = supabase.table('user_profiles')\
            .select('email, full_name, is_super_admin')\
            .eq('email', email)\
            .execute()
        
        if not user_check.data:
            print(f"❌ User with email {email} not found!")
            return False
        
        user = user_check.data[0]
        if user['is_super_admin']:
            print(f"ℹ️  User {email} is already a super admin!")
            return True
        
        # Promote to super admin
        result = supabase.table('user_profiles')\
            .update({'is_super_admin': True})\
            .eq('email', email)\
            .execute()
        
        if result.data:
            print(f"✅ Successfully promoted {user['full_name']} ({email}) to super admin!")
            return True
        else:
            print(f"❌ Failed to promote {email} to super admin")
            return False
            
    except Exception as e:
        print(f"❌ Error promoting user: {e}")
        return False

def revoke_user(email: str):
    """Revoke super admin status from a user"""
    supabase = get_supabase_client()
    
    try:
        # Check how many super admins exist
        admin_count = supabase.table('user_profiles')\
            .select('id', count='exact')\
            .eq('is_super_admin', True)\
            .execute()
        
        if admin_count.count <= 1:
            print("❌ Cannot revoke super admin status - at least one super admin must remain!")
            return False
        
        # Check if user exists and is super admin
        user_check = supabase.table('user_profiles')\
            .select('email, full_name, is_super_admin')\
            .eq('email', email)\
            .execute()
        
        if not user_check.data:
            print(f"❌ User with email {email} not found!")
            return False
        
        user = user_check.data[0]
        if not user['is_super_admin']:
            print(f"ℹ️  User {email} is not a super admin!")
            return True
        
        # Revoke super admin status
        result = supabase.table('user_profiles')\
            .update({'is_super_admin': False})\
            .eq('email', email)\
            .execute()
        
        if result.data:
            print(f"✅ Successfully revoked super admin status from {user['full_name']} ({email})")
            return True
        else:
            print(f"❌ Failed to revoke super admin status from {email}")
            return False
            
    except Exception as e:
        print(f"❌ Error revoking super admin: {e}")
        return False

def main():
    """Main function"""
    print("🚀 Super Admin Management Tool")
    print("=" * 40)
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python manage_super_admin.py list                    # List all super admins")
        print("  python manage_super_admin.py promote user@email.com  # Promote user to super admin")
        print("  python manage_super_admin.py revoke user@email.com   # Revoke super admin status")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "list":
        list_super_admins()
    elif command == "promote":
        if len(sys.argv) < 3:
            print("❌ Please provide user email to promote")
            sys.exit(1)
        email = sys.argv[2]
        promote_user(email)
    elif command == "revoke":
        if len(sys.argv) < 3:
            print("❌ Please provide user email to revoke")
            sys.exit(1)
        email = sys.argv[2]
        revoke_user(email)
    else:
        print(f"❌ Unknown command: {command}")
        print("Available commands: list, promote, revoke")
        sys.exit(1)

if __name__ == "__main__":
    main()
