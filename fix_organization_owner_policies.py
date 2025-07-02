#!/usr/bin/env python3
"""
Fix Organization Owner Policies Migration
This script adds missing RLS policies for organization owners on journal_entry_lines table.
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.supabase_manager import SupabaseManager

def read_sql_file(filename):
    """Read SQL file content."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"❌ SQL file not found: {filename}")
        return None
    except Exception as e:
        print(f"❌ Error reading SQL file: {e}")
        return None

def run_migration():
    """Run the organization owner policies migration."""
    print("🔧 Running Organization Owner Policies Migration...")
    
    # Read the SQL migration file
    sql_content = read_sql_file('add_organization_owner_policies.sql')
    if not sql_content:
        return False
    
    try:
        # Initialize database manager (this will use the service role)
        db_manager = SupabaseManager()
        
        # Execute the migration SQL
        print("📝 Executing migration SQL...")
        result = db_manager.supabase.rpc('exec_sql', {'sql': sql_content}).execute()
        
        if result.data:
            print("✅ Migration executed successfully!")
            print("📊 Policy verification results:")
            if isinstance(result.data, list):
                for row in result.data:
                    print(f"   - {row}")
            return True
        else:
            print("⚠️  Migration completed but no verification data returned")
            return True
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        print("\n💡 Alternative approach:")
        print("1. Connect to your Supabase SQL editor")
        print("2. Run the contents of 'add_organization_owner_policies.sql' manually")
        return False

def main():
    """Main function."""
    print("=" * 60)
    print("🚀 Organization Owner Policies Fix")
    print("=" * 60)
    
    # Check if SQL file exists
    if not os.path.exists('add_organization_owner_policies.sql'):
        print("❌ add_organization_owner_policies.sql file not found!")
        print("Please make sure the SQL file is in the current directory.")
        return
    
    # Run the migration
    success = run_migration()
    
    if success:
        print("\n✅ Migration completed successfully!")
        print("🎉 Organization owners should now have proper access to journal entry lines.")
    else:
        print("\n❌ Migration failed. Please check the error messages above.")
        print("💡 You can also run the SQL manually in your Supabase dashboard.")

if __name__ == "__main__":
    main() 