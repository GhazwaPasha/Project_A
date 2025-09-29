#!/usr/bin/env python3
"""
Fix the old classification constraint issue
"""
import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def fix_constraint():
    """Run the migration to fix the old classification constraint"""
    try:
        # Database connection parameters from environment
        conn_params = {
            'host': os.getenv('POSTGRES_HOST'),
            'port': int(os.getenv('POSTGRES_PORT', 5432)),
            'database': os.getenv('POSTGRES_DB'),
            'user': os.getenv('POSTGRES_USER'),
            'password': os.getenv('POSTGRES_PASSWORD')
        }
        
        # Validate required parameters
        if not all([conn_params['host'], conn_params['database'], 
                   conn_params['user'], conn_params['password']]):
            print("❌ Missing required database connection parameters in .env file")
            print("Required: POSTGRES_HOST, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD")
            return False
        
        print("Connecting to Supabase database...")
        conn = psycopg2.connect(**conn_params)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Drop the old constraint directly
        drop_sql = """
        DO $$
        BEGIN
            -- Check if the old classification_check constraint exists
            IF EXISTS (
                SELECT 1 FROM information_schema.table_constraints 
                WHERE table_name = 'accounts' 
                AND table_schema = 'public' 
                AND constraint_name = 'accounts_classification_check'
            ) THEN
                -- Drop the old constraint
                ALTER TABLE public.accounts DROP CONSTRAINT accounts_classification_check;
                RAISE NOTICE 'Dropped old accounts_classification_check constraint';
            ELSE
                RAISE NOTICE 'Old accounts_classification_check constraint does not exist';
            END IF;
        END $$;
        """
        
        print("Running constraint fix...")
        cursor.execute(drop_sql)
        conn.commit()
        
        print("✅ Old constraint dropped successfully!")
        print("You can now update accounts with new group values like 'sales_revenue', 'cogs', etc.")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Constraint fix failed: {e}")
        print("\nManual fix required:")
        print("1. Connect to your Supabase database")
        print("2. Run: ALTER TABLE public.accounts DROP CONSTRAINT IF EXISTS accounts_classification_check;")
        print("3. Restart the application")
        return False

if __name__ == "__main__":
    fix_constraint() 