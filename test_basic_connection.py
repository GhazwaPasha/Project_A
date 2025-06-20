#!/usr/bin/env python3
"""Test basic database connectivity."""

import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv()

def test_basic_connection():
    """Test basic database connection."""
    print("Testing basic database connection...")
    
    # Get connection parameters
    host = os.getenv('POSTGRES_HOST')
    port = int(os.getenv('POSTGRES_PORT', 5432))
    database = os.getenv('POSTGRES_DB')
    user = os.getenv('POSTGRES_USER')
    password = os.getenv('POSTGRES_PASSWORD')
    
    print(f"Connecting to: {user}@{host}:{port}/{database}")
    
    try:
        # Create connection with a timeout
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
            connect_timeout=10,
            cursor_factory=RealDictCursor
        )
        
        print("✓ Connected to database")
        
        # Test query
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as count FROM accounts")
            result = cursor.fetchone()
            print(f"✓ Found {result['count']} accounts")
            
        conn.close()
        print("✓ Connection closed successfully")
        
    except Exception as e:
        print(f"✗ Connection failed: {e}")

if __name__ == "__main__":
    test_basic_connection()
