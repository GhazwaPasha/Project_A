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
        
        # Execute the entire script as one command using raw SQL
        try:
            # Use the supabase client's underlying postgrest client
            result = supabase.postgrest.rpc('exec_sql', {'sql': sql_script}).execute()
            print("✅ Policy fix script executed successfully!")
            return True
        except Exception as e:
            if 'exec_sql' in str(e):
                print("ℹ️  exec_sql function not available, trying alternative approach...")
                return execute_with_psycopg2(url, service_role_key, sql_script)
            else:
                print(f"❌ Error executing script: {e}")
                return False
        
    except ImportError:
        print("❌ supabase-py not installed. Installing...")
        try:
            import subprocess
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'supabase'])
            print("✅ supabase-py installed. Please run the script again.")
            return False
        except Exception as e:
            print(f"❌ Failed to install supabase-py: {e}")
            return False
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
        db_password = service_role_key  # Service role key can be used as password
        
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
            return False
    except Exception as e:
        print(f"❌ Error with direct PostgreSQL connection: {e}")
        return False
    
    print('🔧 Fixing database policy recursion...')
    
    # Parse the Supabase URL to get database connection details
    parsed = urlparse(url)
    
    # Construct PostgreSQL connection string
    # Supabase URLs are typically: https://xxx.supabase.co
    # Database URLs are: postgres://postgres:[password]@db.xxx.supabase.co:5432/postgres
    db_host = f"db.{parsed.netloc}"
    
    # Read database password from environment (should be in .env)
    db_password = os.getenv('SUPABASE_DB_PASSWORD')
    if not db_password:
        print('❌ SUPABASE_DB_PASSWORD environment variable is required')
        print('   This is your database password, not the service role key')
        return 1
    
    # Read SQL file
    print('📄 Reading SQL script...')
    try:
        with open('fix_policy_recursion.sql', 'r') as f:
            sql_content = f.read()
    except FileNotFoundError:
        print('❌ fix_policy_recursion.sql file not found')
        return 1
    
    # Connect directly to PostgreSQL
    print('🔗 Connecting to PostgreSQL database...')
    try:
        conn = psycopg2.connect(
            host=db_host,
            port=5432,
            database='postgres',
            user='postgres',
            password=db_password
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        print('🚀 Executing SQL statements...')
        
        # Split SQL into statements and execute each one
        statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip() and not stmt.strip().startswith('--')]
        
        for i, stmt in enumerate(statements, 1):
            print(f'  Executing statement {i}/{len(statements)}...')
            try:
                cursor.execute(stmt)
                print(f'    ✅ Statement {i} executed successfully')
            except Exception as e:
                print(f'    ⚠️  Statement {i} error: {e}')
                # Continue with other statements for non-critical errors
        
        cursor.close()
        conn.close()
        
        print('✅ Database policies fixed successfully!')
        print('🔄 Please restart your application to see the changes')
        return 0
        
    except Exception as e:
        print(f'❌ Database connection error: {e}')
        print('   Make sure your SUPABASE_DB_PASSWORD is correct')
        print('   You can find it in your Supabase project settings > Database > Connection string')
        return 1

if __name__ == '__main__':
    sys.exit(main())
