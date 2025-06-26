#!/usr/bin/env python3
"""
Fix can_access_page function parameter ambiguity
"""
import os
from supabase import create_client

# Load environment
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def fix_functions():
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_ANON_KEY') 
    
    if not url or not key:
        print("❌ Missing Supabase credentials")
        return
    
    client = create_client(url, key)
    
    # Read and execute the SQL fix
    with open('fix_can_access_page_function.sql', 'r') as f:
        sql_content = f.read()
    
    try:
        # Split by semicolon and execute each statement
        statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
        
        for i, statement in enumerate(statements):
            print(f"Executing statement {i+1}...")
            result = client.rpc('exec_sql', {'sql': statement}).execute()
            print(f"✅ Statement {i+1} executed successfully")
            
        print("✅ All function fixes applied successfully!")
        
    except Exception as e:
        print(f"❌ Error executing SQL: {e}")

if __name__ == "__main__":
    fix_functions()
