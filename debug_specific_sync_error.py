#!/usr/bin/env python3
"""
Debug specific sync errors for journal entries
"""

import sqlite3
import json
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_specific_sync():
    """Test syncing a specific operation to see the exact error"""
    print("🔍 Testing Specific Sync Error")
    print("=" * 40)
    
    try:
        # Get a specific failed operation
        cache_db_path = "offline_cache.db"
        conn = sqlite3.connect(cache_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get the most recent failed operation
        cursor.execute("SELECT * FROM pending_operations ORDER BY created_at DESC LIMIT 1")
        op = cursor.fetchone()
        
        if not op:
            print("❌ No pending operations found")
            return
        
        print(f"📋 Testing operation: {op['id']}")
        print(f"   Type: {op['operation_type']}")
        print(f"   Table: {op['table_name']}")
        print(f"   Retry Count: {op['retry_count']}")
        
        # Parse the data
        data = json.loads(op['data'])
        print(f"   Data structure: {list(data.keys())}")
        
        if 'header' in data and 'lines' in data:
            print(f"   Header: {data['header']}")
            print(f"   Lines: {data['lines']}")
            
            # Now try to manually sync this operation
            from src.core.supabase_manager import SupabaseManager
            
            print(f"\n🔄 Attempting manual sync...")
            
            # Initialize Supabase manager
            db_manager = SupabaseManager()
            
            # Test the exact sync logic
            print(f"📝 Step 1: Insert journal entry header...")
            try:
                entry_result = db_manager.supabase.table('journal_entries').insert(data['header']).execute()
                print(f"✅ Header insert result: {entry_result.data is not None}")
                
                if entry_result.data:
                    entry_id = entry_result.data[0]['id']
                    print(f"✅ Created journal entry with ID: {entry_id}")
                    
                    print(f"📝 Step 2: Insert journal entry lines...")
                    
                    # Add entry_id to each line
                    for line in data['lines']:
                        line['journal_entry_id'] = entry_id
                    
                    print(f"📝 Lines to insert: {data['lines']}")
                    
                    lines_result = db_manager.supabase.table('journal_entry_lines').insert(data['lines']).execute()
                    print(f"✅ Lines insert result: {lines_result.data is not None}")
                    
                    if lines_result.data:
                        print(f"✅ Successfully created journal entry with {len(lines_result.data)} lines!")
                        print(f"🎉 Manual sync was successful!")
                        
                        # Clean up - delete the test entry
                        print(f"🧹 Cleaning up test entry...")
                        db_manager.supabase.table('journal_entries').delete().eq('id', entry_id).execute()
                        
                    else:
                        print(f"❌ Lines insert failed")
                        # Rollback the header
                        db_manager.supabase.table('journal_entries').delete().eq('id', entry_id).execute()
                        
                else:
                    print(f"❌ Header insert failed - no data returned")
                
            except Exception as e:
                print(f"❌ Manual sync failed: {e}")
                print(f"Exception type: {type(e).__name__}")
                import traceback
                print(f"Traceback: {traceback.format_exc()}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    test_specific_sync() 