#!/usr/bin/env python3
"""
Simple script to check data in Supabase database
"""

def check_database_content():
    try:
        from src.core.database_manager import DatabaseManager
        
        print("🔍 Checking Supabase database content...")
        db_manager = DatabaseManager()
        
        # Test connection
        if not db_manager.test_connection():
            print("❌ Database connection failed")
            return
            
        print("✅ Database connection successful")
        
        # Check tables and data
        with db_manager.get_db_cursor() as cursor:
            print("\n📊 Database Tables and Content:")
            print("=" * 50)
            
            # Check accounts table
            cursor.execute("SELECT COUNT(*) as count FROM accounts")
            account_count = cursor.fetchone()['count']
            print(f"📁 Accounts table: {account_count} records")
            
            if account_count > 0:
                cursor.execute("SELECT name, type, code FROM accounts LIMIT 10")
                accounts = cursor.fetchall()
                print("   Sample accounts:")
                for acc in accounts:
                    print(f"     - {acc['name']} ({acc['type']}) [Code: {acc['code']}]")
            
            # Check journal entries table
            cursor.execute("SELECT COUNT(*) as count FROM journal_entries")
            entry_count = cursor.fetchone()['count']
            print(f"\n📝 Journal entries table: {entry_count} records")
            
            if entry_count > 0:
                cursor.execute("SELECT debit_account_name, credit_account_name, amount, description, entry_date FROM journal_entries ORDER BY entry_date DESC LIMIT 5")
                entries = cursor.fetchall()
                print("   Recent journal entries:")
                for entry in entries:
                    print(f"     - {entry['entry_date']}: {entry['debit_account_name']} -> {entry['credit_account_name']} ${entry['amount']} ({entry['description']})")
        
        print(f"\n✅ Database check completed!")
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_database_content()
