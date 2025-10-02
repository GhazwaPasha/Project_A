#!/usr/bin/env python3
"""
Simple script to run the calculate_all_ratios function
"""

import psycopg2
import os
from dotenv import load_dotenv

def run_ratios_function():
    """Run the calculate_all_ratios function"""
    
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
        
        # Read and execute the SQL file
        with open('database/calculate_all_ratios.sql', 'r') as f:
            sql_content = f.read()
        
        print("Creating/updating calculate_all_ratios function...")
        cur.execute(sql_content)
        conn.commit()
        print("✅ Function created successfully")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        if conn:
            conn.rollback()
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    run_ratios_function()
