#!/usr/bin/env python3
"""
Script to set up all report generation functions in the database
"""

import psycopg2
import os
from dotenv import load_dotenv

def setup_reports_functions():
    """Set up all report generation functions in the database"""
    
    # Load environment variables
    load_dotenv()
    
    # Database connection parameters
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'database': os.getenv('DB_NAME', 'accountuitive'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', ''),
        'port': os.getenv('DB_PORT', '5432')
    }
    
    # List of SQL files to execute
    sql_files = [
        'database/get_balance_sheet_data.sql',
        'database/get_income_statement_data.sql',
        'database/get_trial_balance_data.sql',
        'database/get_aged_receivables_data.sql',
        'database/get_aged_payables_data.sql'
    ]
    
    try:
        # Connect to database
        print("Connecting to database...")
        conn = psycopg2.connect(**db_config)
        cur = conn.cursor()
        
        # Execute each SQL file
        for sql_file in sql_files:
            print(f"Creating function from {sql_file}...")
            with open(sql_file, 'r') as f:
                sql_content = f.read()
            
            cur.execute(sql_content)
            print(f"✅ Successfully created function from {sql_file}")
        
        # Commit all changes
        conn.commit()
        print("✅ All report functions created successfully")
        
        # Test one of the functions
        print("Testing get_balance_sheet_data function...")
        cur.execute("""
            SELECT get_balance_sheet_data(
                '00000000-0000-0000-0000-000000000000'::uuid,
                CURRENT_DATE
            )
        """)
        
        result = cur.fetchone()
        if result:
            print("✅ Function test successful")
            print(f"Sample result: {result[0]}")
        else:
            print("⚠️  Function test returned no result")
        
    except Exception as e:
        print(f"❌ Error setting up report functions: {e}")
        if conn:
            conn.rollback()
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    setup_reports_functions()
