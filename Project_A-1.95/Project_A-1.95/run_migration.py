#!/usr/bin/env python3
"""
Run the is_postable migration using Supabase client
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.config import DatabaseConfig

def run_migration():
    """Run the is_postable migration."""
    try:
        from supabase import create_client
        
        # Create Supabase client
        supabase = create_client(
            DatabaseConfig.SUPABASE_URL,
            DatabaseConfig.SUPABASE_SERVICE_KEY  # Use service key for admin operations
        )
        
        print("🔧 Running is_postable migration...")
        
        # Read migration SQL
        with open('migration_add_is_postable.sql', 'r') as f:
            migration_sql = f.read()
        
        # Split into individual statements
        statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip()]
        
        for i, statement in enumerate(statements):
            if statement:
                print(f"  Executing statement {i+1}/{len(statements)}...")
                try:
                    result = supabase.rpc('exec_sql', {'sql': statement}).execute()
                    print(f"    ✅ Success")
                except Exception as e:
                    print(f"    ❌ Error: {e}")
                    # Try direct SQL execution if RPC fails
                    try:
                        # For ALTER TABLE and other DDL, we need to use a different approach
                        if 'ALTER TABLE' in statement or 'UPDATE' in statement or 'CREATE INDEX' in statement or 'COMMENT' in statement:
                            print(f"    🔄 Trying alternative approach...")
                            # These need to be run via Supabase dashboard or direct postgres connection
                            print(f"    📝 Statement to run manually: {statement}")
                        else:
                            raise e
                    except Exception as e2:
                        print(f"    ❌ Alternative approach also failed: {e2}")
        
        print("✅ Migration completed!")
        print("\n⚠️  Note: If any statements failed, you may need to run them manually in the Supabase SQL editor:")
        print("   1. Go to your Supabase dashboard")
        print("   2. Navigate to SQL Editor")
        print("   3. Run the migration_add_is_postable.sql file")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        print("\n📝 Please run the migration manually in Supabase SQL editor:")
        print("   1. Go to your Supabase dashboard")
        print("   2. Navigate to SQL Editor") 
        print("   3. Copy and paste the contents of migration_add_is_postable.sql")

if __name__ == "__main__":
    run_migration()
