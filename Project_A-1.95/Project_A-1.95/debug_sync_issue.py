#!/usr/bin/env python3
"""
Debug script to check offline sync issue
"""

import sqlite3
import json
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def debug_offline_cache():
    """Debug the offline cache database"""
    cache_db_path = "offline_cache.db"
    
    print("🔍 Debugging Offline Cache Database")
    print("=" * 50)
    
    try:
        conn = sqlite3.connect(cache_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check if tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"📋 Tables in cache database: {[table['name'] for table in tables]}")
        
        # Check pending operations
        cursor.execute("SELECT COUNT(*) as count FROM pending_operations")
        pending_count = cursor.fetchone()['count']
        print(f"📊 Total pending operations: {pending_count}")
        
        if pending_count > 0:
            cursor.execute("SELECT * FROM pending_operations ORDER BY created_at DESC LIMIT 5")
            operations = cursor.fetchall()
            
            print("\n🔄 Recent pending operations:")
            for i, op in enumerate(operations, 1):
                print(f"  {i}. ID: {op['id']}")
                print(f"     Type: {op['operation_type']}")
                print(f"     Table: {op['table_name']}")
                print(f"     Org ID: {op['organization_id']}")
                print(f"     User ID: {op['user_id']}")
                print(f"     Created: {op['created_at']}")
                print(f"     Retry Count: {op['retry_count']}")
                
                # Parse and show data structure
                try:
                    data = json.loads(op['data'])
                    print(f"     Data Keys: {list(data.keys())}")
                    if 'header' in data and 'lines' in data:
                        print(f"     ✅ Has header/lines structure")
                        print(f"     Header Keys: {list(data['header'].keys())}")
                        print(f"     Lines Count: {len(data['lines'])}")
                    else:
                        print(f"     ❌ Missing header/lines structure")
                except Exception as e:
                    print(f"     ❌ Failed to parse data: {e}")
                print()
        
        # Check cached journal entries
        cursor.execute("SELECT COUNT(*) as count FROM cached_journal_entries")
        cached_count = cursor.fetchone()['count']
        print(f"📊 Cached journal entries: {cached_count}")
        
        # Check cached accounts
        cursor.execute("SELECT COUNT(*) as count FROM cached_accounts")
        accounts_count = cursor.fetchone()['count']
        print(f"📊 Cached accounts: {accounts_count}")
        
        conn.close()
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_sync_manually():
    """Test the sync process manually"""
    print("\n🧪 Testing Sync Process")
    print("=" * 30)
    
    try:
        from src.core.unified_accounting_system import UnifiedAccountingSystem
        from src.core.auth_manager import AuthManager
        
        # Initialize the system
        auth_manager = AuthManager()
        current_user = auth_manager.get_current_user()
        if not current_user:
            print("❌ Not authenticated - please login first")
            return
        
        accounting_system = UnifiedAccountingSystem(auth_manager)
        
        # Check if we're online
        print(f"🌐 Online status: {accounting_system.is_online}")
        
        # Get sync status
        sync_status = accounting_system.get_sync_status()
        print(f"📊 Sync Status: {sync_status}")
        
        if sync_status.get('pending_operations', 0) > 0:
            print(f"\n🔄 Attempting to sync {sync_status['pending_operations']} pending operations...")
            
            # Force sync
            sync_result = accounting_system.force_sync()
            print(f"🔄 Sync Result: {sync_result}")
            
            if sync_result.get('success'):
                print(f"✅ Successfully synced {sync_result.get('synced_operations', 0)} operations")
            else:
                print(f"❌ Sync failed: {sync_result.get('error', 'Unknown error')}")
        else:
            print("ℹ️ No pending operations to sync")
            
    except Exception as e:
        print(f"❌ Manual sync test failed: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")

def main():
    """Main debug function"""
    debug_offline_cache()
    test_sync_manually()

if __name__ == "__main__":
    main() 