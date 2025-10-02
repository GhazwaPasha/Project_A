#!/usr/bin/env python3
"""
Script to set up the calculate_all_ratios function in the database
"""

import psycopg2
import os
from dotenv import load_dotenv

def setup_ratios_function():
    """Set up the calculate_all_ratios function in the database"""
    
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
    
    try:
        # Connect to database
        print("Connecting to database...")
        conn = psycopg2.connect(**db_config)
        cur = conn.cursor()
        
        # Read the SQL file
        sql_file_path = os.path.join(os.path.dirname(__file__), '..', 'database', 'calculate_all_ratios.sql')
        with open(sql_file_path, 'r') as f:
            sql_content = f.read()
        
        # Execute the SQL
        print("Creating calculate_all_ratios function...")
        cur.execute(sql_content)
        
        # Commit the changes
        conn.commit()
        print("✅ Successfully created calculate_all_ratios function")
        
        # Test the function
        print("Testing the function...")
        cur.execute("""
            SELECT calculate_all_ratios(
                '00000000-0000-0000-0000-000000000000'::uuid,
                CURRENT_DATE - INTERVAL '30 days',
                CURRENT_DATE,
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
        print(f"❌ Error setting up ratios function: {e}")
        if conn:
            conn.rollback()
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    setup_ratios_function()
