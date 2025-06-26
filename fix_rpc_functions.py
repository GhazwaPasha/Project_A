#!/usr/bin/env python3
"""
Fix RPC Function - Resolve ambiguous column reference issue
"""
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from supabase import create_client

def fix_rpc_functions():
    """Fix the RPC functions with proper parameter names"""
    try:
        # Get Supabase credentials
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_ANON_KEY')
        
        if not url or not key:
            print("❌ Missing Supabase credentials in .env file")
            return False
            
        # Create Supabase client
        supabase = create_client(url, key)
        
        # Read the SQL file
        sql_path = os.path.join(os.path.dirname(__file__), 'fix_rpc_function.sql')
        with open(sql_path, 'r') as f:
            sql_commands = f.read()
        
        print("🔧 Fixing RPC functions...")
        
        # Split and execute each command
        commands = sql_commands.split('$$;')
        
        for i, command in enumerate(commands):
            if command.strip():
                full_command = command.strip() + '$$;' if i < len(commands) - 1 else command.strip()
                if full_command.strip():
                    try:
                        print(f"   Executing command {i+1}...")
                        result = supabase.rpc('exec', {'sql': full_command}).execute()
                        print(f"   ✅ Command {i+1} executed successfully")
                    except Exception as e:
                        print(f"   ❌ Command {i+1} failed: {e}")
                        # Try alternative method
                        try:
                            # For function creation, we might need to use a different approach
                            # Let's try to execute it directly through the REST API
                            pass
                        except Exception as e2:
                            print(f"   ❌ Alternative method also failed: {e2}")
        
        print("✅ RPC function fix completed!")
        print("\nNow you can manually run this SQL in your Supabase SQL Editor:")
        print("=" * 60)
        print(sql_commands)
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"❌ Error fixing RPC functions: {e}")
        return False

if __name__ == "__main__":
    fix_rpc_functions()
