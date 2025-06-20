#!/usr/bin/env python3
"""Simple test to check account access."""

import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_simple_account_access():
    """Test direct database access for accounts."""
    print("Testing simple account access...")
    
    try:
        from core.config import DatabaseConfig
        from core.database_manager import DatabaseManager
        
        # Just test direct database access
        config = DatabaseConfig()
        db_manager = DatabaseManager(config)
        
        print("✓ Database manager created")
        
        # Test direct query
        with db_manager.get_db_cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM accounts")
            count = cursor.fetchone()
            print(f"✓ Direct query: {count['count']} accounts in database")
            
            cursor.execute("SELECT name, type, code, is_postable FROM accounts LIMIT 5")
            accounts = cursor.fetchall()
            print(f"✓ Sample accounts:")
            for acc in accounts:
                print(f"  - {acc['code']} - {acc['name']} ({acc['type']}) [Postable: {acc['is_postable']}]")
                
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_simple_account_access()
