#!/usr/bin/env python3
"""
Clear all pending operations from offline cache
"""

import sqlite3
import sys
from pathlib import Path

def clear_pending_operations():
    """Clear all pending operations from the offline cache"""
    cache_db_path = "offline_cache.db"
    
    print("🧹 Clearing Pending Operations from Offline Cache")
    print("=" * 50)
    
    try:
        conn = sqlite3.connect(cache_db_path)
        cursor = conn.cursor()
        
        # Count pending operations before deletion
        cursor.execute("SELECT COUNT(*) as count FROM pending_operations")
        before_count = cursor.fetchone()[0]
        print(f"📊 Pending operations before deletion: {before_count}")
        
        if before_count == 0:
            print("ℹ️  No pending operations to delete")
            conn.close()
            return
        
        # Show some details about what we're deleting
        cursor.execute("""
            SELECT 
                operation_type, 
                table_name, 
                COUNT(*) as count,
                AVG(retry_count) as avg_retry_count
            FROM pending_operations 
            GROUP BY operation_type, table_name
            ORDER BY count DESC
        """)
        
        operations_summary = cursor.fetchall()
        print("\n📋 Operations to be deleted:")
        for op in operations_summary:
            print(f"  - {op[1]} ({op[0]}): {op[2]} operations, avg retry count: {op[3]:.1f}")
        
        # Ask for confirmation
        print(f"\n⚠️  This will permanently delete {before_count} pending operations.")
        confirm = input("Are you sure you want to continue? (y/N): ")
        
        if confirm.lower() != 'y':
            print("❌ Operation cancelled")
            conn.close()
            return
        
        # Delete all pending operations
        cursor.execute("DELETE FROM pending_operations")
        deleted_count = cursor.rowcount
        
        # Commit the changes
        conn.commit()
        
        # Verify deletion
        cursor.execute("SELECT COUNT(*) as count FROM pending_operations")
        after_count = cursor.fetchone()[0]
        
        print(f"\n✅ Successfully deleted {deleted_count} pending operations")
        print(f"📊 Pending operations after deletion: {after_count}")
        
        if after_count == 0:
            print("🎉 Offline cache is now clean!")
        else:
            print("⚠️  Some operations may not have been deleted")
        
        conn.close()
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

def clear_all_cache():
    """Clear all cached data (optional - more aggressive cleanup)"""
    cache_db_path = "offline_cache.db"
    
    print("\n🧹 Optional: Clear ALL Cache Data")
    print("=" * 40)
    
    try:
        conn = sqlite3.connect(cache_db_path)
        cursor = conn.cursor()
        
        # Count all cached data
        cursor.execute("SELECT COUNT(*) as count FROM cached_journal_entries")
        entries_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) as count FROM cached_accounts")
        accounts_count = cursor.fetchone()[0]
        
        print(f"📊 Cached journal entries: {entries_count}")
        print(f"📊 Cached accounts: {accounts_count}")
        
        if entries_count == 0 and accounts_count == 0:
            print("ℹ️  No cached data to delete")
            conn.close()
            return
        
        print(f"\n⚠️  This will also delete all cached data (entries and accounts).")
        print("💡 This forces a fresh sync from the database on next use.")
        confirm = input("Clear all cached data too? (y/N): ")
        
        if confirm.lower() == 'y':
            cursor.execute("DELETE FROM cached_journal_entries")
            entries_deleted = cursor.rowcount
            
            cursor.execute("DELETE FROM cached_accounts")
            accounts_deleted = cursor.rowcount
            
            conn.commit()
            
            print(f"✅ Deleted {entries_deleted} cached journal entries")
            print(f"✅ Deleted {accounts_deleted} cached accounts")
            print("🎉 All cache data cleared!")
        else:
            print("ℹ️  Cached data kept")
        
        conn.close()
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Main function"""
    print("🗑️  Offline Cache Cleanup Utility")
    print("=" * 60)
    
    # Clear pending operations (the main request)
    clear_pending_operations()
    
    # Optionally clear all cached data
    clear_all_cache()
    
    print("\n✨ Cleanup complete!")
    print("💡 You can now test creating new journal entries.")

if __name__ == "__main__":
    main() 