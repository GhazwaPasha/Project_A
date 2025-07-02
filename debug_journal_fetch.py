#!/usr/bin/env python3
"""
Debug script to check journal entry fetching and transformation
"""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def debug_journal_fetch():
    """Debug the journal entry fetching process"""
    print("🔍 DEBUGGING JOURNAL ENTRY FETCH")
    print("=" * 50)
    
    try:
        from src.core.auth_manager import AuthManager
        from src.core.unified_accounting_system import UnifiedAccountingSystem
        
        # Initialize system
        print("🔐 Initializing system...")
        auth_manager = AuthManager()
        current_user = auth_manager.get_current_user()
        
        if not current_user:
            print("❌ No authenticated user found. Please login first.")
            return
            
        print(f"✅ Authenticated as: {current_user.get('email', 'Unknown')}")
        
        # Get organizations
        organizations = auth_manager.get_user_organizations()
        if not organizations:
            print("❌ No organizations found")
            return
            
        # Initialize accounting system
        system = UnifiedAccountingSystem(auth_manager)
        org = organizations[0]
        org_id = org.get('id')
        system.set_organization(org_id)
        print(f"✅ Using organization: {org.get('name', 'Unknown')} (ID: {org_id})")
        
        # Check online status
        print(f"\n🌐 Online status: {'✅ Online' if system.is_online else '📱 Offline'}")
        
        # Test direct database query
        print("\n🔍 STEP 1: Testing direct database query")
        print("-" * 40)
        
        if system.is_online and hasattr(system, 'db_manager'):
            try:
                system._set_database_context()
                raw_entries = system.db_manager.get_journal_entries(org_id)
                print(f"📊 Raw database query returned: {len(raw_entries)} entries")
                
                if raw_entries:
                    print("\n🔍 First raw entry structure:")
                    entry = raw_entries[0]
                    print(f"  Entry keys: {list(entry.keys())}")
                    print(f"  ID: {entry.get('id', 'N/A')}")
                    print(f"  Entry Number: {entry.get('entry_number', 'N/A')}")
                    print(f"  Entry Date: {entry.get('entry_date', 'N/A')}")
                    print(f"  Description: {entry.get('description', 'N/A')}")
                    print(f"  Total Amount: {entry.get('total_amount', 'N/A')}")
                    
                    # Check journal entry lines
                    lines = entry.get('journal_entry_lines', [])
                    print(f"  Journal Entry Lines: {len(lines)} lines")
                    
                    if lines:
                        for i, line in enumerate(lines):
                            print(f"    Line {i+1}:")
                            print(f"      Keys: {list(line.keys())}")
                            print(f"      Debit Amount: {line.get('debit_amount', 'N/A')}")
                            print(f"      Credit Amount: {line.get('credit_amount', 'N/A')}")
                            
                            # Check account info
                            accounts = line.get('accounts', {})
                            if accounts:
                                print(f"      Account: {accounts.get('code', 'N/A')} - {accounts.get('name', 'N/A')}")
                            else:
                                print(f"      Account: No account data")
                else:
                    print("  ⚠️ No entries found in raw database query")
                    
            except Exception as e:
                print(f"  ❌ Direct database query failed: {e}")
                raw_entries = []
        else:
            print("  ⚠️ System offline or no db_manager available")
            raw_entries = []
        
        # Test system.get_journal_entries()
        print("\n🔍 STEP 2: Testing system.get_journal_entries()")
        print("-" * 40)
        
        try:
            system_entries = system.get_journal_entries()
            print(f"📊 system.get_journal_entries() returned: {len(system_entries)} entries")
            
            if system_entries:
                entry = system_entries[0]
                print(f"\n🔍 First system entry structure:")
                print(f"  Entry keys: {list(entry.keys())}")
                print(f"  Date: {entry.get('date', entry.get('entry_date', 'N/A'))}")
                print(f"  Description: {entry.get('description', 'N/A')}")
                print(f"  Debit Account: {entry.get('debit_account', 'N/A')}")
                print(f"  Credit Account: {entry.get('credit_account', 'N/A')}")
                print(f"  Amount: {entry.get('amount', 'N/A')}")
            else:
                print("  ⚠️ No entries found from system.get_journal_entries()")
                
        except Exception as e:
            print(f"  ❌ system.get_journal_entries() failed: {e}")
            system_entries = []
        
        # Test system.get_recent_journal_entries()
        print("\n🔍 STEP 3: Testing system.get_recent_journal_entries()")
        print("-" * 40)
        
        try:
            recent_entries = system.get_recent_journal_entries(limit=5)
            print(f"📊 system.get_recent_journal_entries() returned: {len(recent_entries)} entries")
            
            if recent_entries:
                entry = recent_entries[0]
                print(f"\n🔍 First recent entry structure:")
                print(f"  Entry keys: {list(entry.keys())}")
                print(f"  Date: {entry.get('date', 'N/A')}")
                print(f"  Description: {entry.get('description', 'N/A')}")
                print(f"  Debit Account: {entry.get('debit_account', 'N/A')}")
                print(f"  Credit Account: {entry.get('credit_account', 'N/A')}")
                print(f"  Amount: {entry.get('amount', 'N/A')}")
                print(f"  Entry Number: {entry.get('entry_number', 'N/A')}")
            else:
                print("  ⚠️ No entries found from system.get_recent_journal_entries()")
                
        except Exception as e:
            print(f"  ❌ system.get_recent_journal_entries() failed: {e}")
        
        # Test data transformation manually
        print("\n🔍 STEP 4: Testing manual data transformation")
        print("-" * 40)
        
        if raw_entries:
            try:
                from src.core.data_transformer import data_transformer
                
                print("🔄 Manually transforming first raw entry...")
                transformed = data_transformer.db_to_app_journal_entry(raw_entries[0])
                
                if transformed:
                    print("✅ Manual transformation successful!")
                    print(f"  Date: {transformed.get('date', 'N/A')}")
                    print(f"  Description: {transformed.get('description', 'N/A')}")
                    print(f"  Debit Account: {transformed.get('debit_account', 'N/A')}")
                    print(f"  Credit Account: {transformed.get('credit_account', 'N/A')}")
                    print(f"  Amount: {transformed.get('amount', 'N/A')}")
                else:
                    print("❌ Manual transformation failed!")
                    
            except Exception as e:
                print(f"❌ Manual transformation error: {e}")
        
        # Check cache
        print("\n🔍 STEP 5: Testing cached data")
        print("-" * 40)
        
        try:
            cached_entries = system.offline_cache.get_cached_data('journal_entries', org_id)
            print(f"📊 Cached entries: {len(cached_entries)} entries")
            
            if cached_entries:
                entry = cached_entries[0]
                print(f"\n🔍 First cached entry structure:")
                print(f"  Entry keys: {list(entry.keys())}")
                print(f"  Date: {entry.get('date', entry.get('entry_date', 'N/A'))}")
                print(f"  Description: {entry.get('description', 'N/A')}")
                print(f"  Debit Account: {entry.get('debit_account', 'N/A')}")
                print(f"  Credit Account: {entry.get('credit_account', 'N/A')}")
                print(f"  Amount: {entry.get('amount', entry.get('total_amount', 'N/A'))}")
            else:
                print("  ⚠️ No cached entries found")
                
        except Exception as e:
            print(f"  ❌ Cache check failed: {e}")
        
        print("\n" + "=" * 50)
        print("🎯 DIAGNOSIS COMPLETE")
        print("Please share this output to identify the issue!")
        
    except Exception as e:
        print(f"❌ Fatal error during debugging: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_journal_fetch() 