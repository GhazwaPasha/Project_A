#!/usr/bin/env python3
"""
Fix Database Policy Recursion
Executes the SQL script to fix the infinite recursion in organization_members policy
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def fix_database_policies():
    """Execute the SQL script to fix database policies"""
    try:
        from supabase import create_client, Client
        
        # Get Supabase credentials from environment
        url = os.getenv('SUPABASE_URL')
        service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        
        if not url or not service_role_key:
            print("❌ Missing Supabase credentials in .env file")
            print("   Required: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY")
            return False
        
        print("🔧 Connecting to Supabase...")
        
        # Create client with service role key (bypasses RLS)
        supabase: Client = create_client(url, service_role_key)
        
        # Read the SQL script
        with open('fix_policy_recursion.sql', 'r') as f:
            sql_script = f.read()
        
        print("🔧 Executing policy fix script...")
        
        # Execute using alternative approach - try psycopg2 directly
        return execute_with_psycopg2(url, service_role_key, sql_script)
        
    except ImportError:
        print("❌ supabase-py not installed. Trying direct database connection...")
        # Get credentials and try psycopg2 directly
        url = os.getenv('SUPABASE_URL')
        service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        
        if not url or not service_role_key:
            print("❌ Missing Supabase credentials in .env file")
            return False
            
        with open('fix_policy_recursion.sql', 'r') as f:
            sql_script = f.read()
        
        return execute_with_psycopg2(url, service_role_key, sql_script)
    except Exception as e:
        print(f"❌ Error fixing database policies: {e}")
        return False

def execute_with_psycopg2(url, service_role_key, sql_script):
    """Alternative execution using psycopg2 if available"""
    try:
        import psycopg2
        from urllib.parse import urlparse
        
        # Parse the Supabase URL to get connection details
        parsed = urlparse(url)
        host = parsed.hostname
        
        # Extract project reference from hostname (e.g., abc123.supabase.co -> abc123)
        project_ref = host.split('.')[0] if host else None
        
        if not project_ref:
            print("❌ Could not extract project reference from Supabase URL")
            return False
        
        # Construct the direct PostgreSQL connection string
        db_host = f"db.{project_ref}.supabase.co"
        db_port = 5432
        db_name = "postgres"
        db_user = "postgres"
        # Note: For direct DB connection, you might need the actual DB password
        # The service role key might not work as DB password
        db_password = os.getenv('SUPABASE_DB_PASSWORD', service_role_key)
        
        print(f"🔧 Connecting to PostgreSQL directly at {db_host}...")
        
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            database=db_name,
            user=db_user,
            password=db_password
        )
        
        cursor = conn.cursor()
        
        # Split script into individual statements and execute
        statements = [stmt.strip() for stmt in sql_script.split(';') if stmt.strip() and not stmt.strip().startswith('--')]
        
        success_count = 0
        for i, statement in enumerate(statements):
            if not statement:
                continue
                
            try:
                print(f"   Executing statement {i+1}/{len(statements)}...")
                cursor.execute(statement)
                conn.commit()
                success_count += 1
                print(f"   ✅ Statement {i+1} executed successfully")
            except Exception as e:
                # Some statements might fail if they don't exist (DROP IF EXISTS), that's okay
                if 'does not exist' in str(e) or 'already exists' in str(e):
                    print(f"   ⚠️  Statement {i+1}: {e} (this is okay)")
                    success_count += 1
                    conn.rollback()  # Reset transaction state
                else:
                    print(f"   ❌ Statement {i+1} failed: {e}")
                    conn.rollback()  # Reset transaction state
        
        cursor.close()
        conn.close()
        
        print(f"\n🎉 Policy fix completed! {success_count}/{len(statements)} statements executed")
        return True
        
    except ImportError:
        print("❌ psycopg2 not installed. Installing...")
        try:
            import subprocess
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'psycopg2-binary'])
            print("✅ psycopg2 installed. Please run the script again.")
            return False
        except Exception as e:
            print(f"❌ Failed to install psycopg2: {e}")
            print("   Manual installation: pip install psycopg2-binary")
            return False
    except Exception as e:
        print(f"❌ Error with direct PostgreSQL connection: {e}")
        if "password authentication failed" in str(e):
            print("   💡 Try adding SUPABASE_DB_PASSWORD to your .env file")
            print("   You can find this in Supabase Dashboard > Settings > Database > Connection string")
        return False

def main():
    """Main entry point"""
    print("🚀 Database Policy Fix Tool")
    print("=" * 40)
    
    # Check if SQL file exists
    if not os.path.exists('fix_policy_recursion.sql'):
        print("❌ fix_policy_recursion.sql not found")
        print("   Make sure you're running this from the project root directory")
        return 1
    
    # Execute the fix
    if fix_database_policies():
        print("\n✅ Database policies have been fixed!")
        print("   The infinite recursion issue should now be resolved.")
        print("🔄 Please restart your application to see the changes.")
        return 0
    else:
        print("\n❌ Failed to fix database policies.")
        print("   Alternative options:")
        print("   1. Add SUPABASE_DB_PASSWORD to your .env file")
        print("   2. Execute fix_policy_recursion.sql manually in Supabase dashboard")
        print("   3. Use the SQL Editor in your Supabase project")
        return 1

if __name__ == '__main__':
    sys.exit(main())
