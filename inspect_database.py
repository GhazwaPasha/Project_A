"""
Database Inspection Script
Check what tables exist and what data is available
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.supabase_manager import SupabaseManager

def inspect_database():
    """Inspect the database to see what tables and data exist."""
    print("🔍 Inspecting database structure and data...")
    
    try:
        db_manager = SupabaseManager()
        
        # List of tables to check
        tables_to_check = [
            'user_profiles',
            'organizations', 
            'organization_members',
            'chart_of_accounts'
        ]
        
        for table_name in tables_to_check:
            try:
                print(f"\n📋 Table: {table_name}")
                print("-" * 40)
                
                # Get count and sample data
                result = db_manager.supabase.table(table_name)\
                    .select('*')\
                    .limit(5)\
                    .execute()
                
                if result.data:
                    print(f"   📊 Found {len(result.data)} records (showing first 5)")
                    for i, record in enumerate(result.data):
                        print(f"   {i+1}. {record}")
                else:
                    print("   📭 No records found")
                    
            except Exception as e:
                print(f"   ❌ Error accessing table {table_name}: {e}")
        
        print(f"\n" + "=" * 50)
        print("🎯 Summary complete!")
        
    except Exception as e:
        print(f"❌ Error inspecting database: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    inspect_database()
