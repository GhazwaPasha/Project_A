#!/usr/bin/env python3
"""
Database Setup Guide
Complete setup guide for the clean multi-tenant schema
"""
import os
import sys

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️  Warning: python-dotenv not installed, using system environment")

def main():
    print("🗃️ Database Setup Guide")
    print("=" * 50)
    print()
    
    supabase_url = os.getenv('SUPABASE_URL', '')
    supabase_key = os.getenv('SUPABASE_ANON_KEY', '')
    
    if supabase_url and supabase_key:
        project_name = supabase_url.replace('https://', '').split('.')[0]
        print(f"🎯 Your Supabase project: {project_name}")
        print(f"🔗 Dashboard: https://supabase.com/dashboard/project/{project_name}")
    else:
        print("❌ Supabase credentials not found!")
        print("   Check your .env file has SUPABASE_URL and SUPABASE_ANON_KEY")
        return 1
    
    print()
    print("📋 STEP 1: Apply the main schema")
    print("-" * 30)
    print("1. Open your Supabase dashboard")
    print("2. Go to SQL Editor")
    print("3. Copy ALL contents of: NEW_SCHEMA.sql")
    print("4. Paste and click 'Run'")
    print("5. Wait for: 'Multi-tenant SaaS schema created successfully!'")
    print()
    
    print("📋 STEP 2: Apply the user profile trigger")
    print("-" * 30)
    print("1. Still in SQL Editor")
    print("2. Copy ALL contents of: USER_PROFILE_TRIGGER.sql")
    print("3. Paste and click 'Run'")
    print("4. Wait for: 'User profile trigger created successfully!'")
    print()
    
    print("✅ VERIFICATION: Check your tables")
    print("-" * 30)
    print("In Supabase, go to 'Table Editor' and verify you see:")
    print("  - organizations")
    print("  - user_profiles") 
    print("  - organization_members")
    print("  - accounts")
    print("  - journal_entries")
    print("  - journal_entry_lines")
    print("  - budgets")
    print("  - budget_entries")
    print("  - period_closing")
    print()
    
    print("🧪 TESTING")
    print("-" * 30)
    print("After both scripts run successfully:")
    print("1. Run: python run.py")
    print("2. Click 'Sign up'")
    print("3. Create a new account")
    print("4. Should work without database errors!")
    print()
    
    # Check if files exist
    print("📁 Required files:")
    files = ['NEW_SCHEMA.sql', 'USER_PROFILE_TRIGGER.sql']
    for file in files:
        if os.path.exists(file):
            print(f"  ✅ {file}")
        else:
            print(f"  ❌ {file} - Missing!")
    
    print()
    print("🚀 Ready to set up your database!")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
