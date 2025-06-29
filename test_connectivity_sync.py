#!/usr/bin/env python3
"""
Test connectivity and immediate sync functionality.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.enhanced_accounting_system import EnhancedAccountingSystem
from src.core.session_manager import SessionManager

def test_connectivity_and_sync():
    """Test connectivity and sync functionality."""
    
    print("🧪 Testing Connectivity and Sync")
    print("=" * 50)
    
    # Initialize the session manager
    session_manager = SessionManager()
    
    # Set organization context (same as UI does)
    org_id = "0946405f-3b8a-4fe5-8c29-125b39d9ca8e"
    session_manager.set_current_organization(org_id)
    
    print(f"✅ Organization set: {org_id}")
    
    # Initialize enhanced accounting system (same as UI)
    system = EnhancedAccountingSystem(session_manager=session_manager)
    
    print(f"✅ System initialized")
    print(f"   Type: {type(system)}")
    print(f"   Has base_system: {hasattr(system, 'base_system')}")
    
    if hasattr(system, 'base_system'):
        print(f"   Base system type: {type(system.base_system)}")
        print(f"   Base system online: {getattr(system.base_system, 'is_online', 'Unknown')}")
        
        # Test connectivity directly
        print(f"\n🌐 Testing connectivity...")
        try:
            connectivity_result = system.base_system._test_connectivity()
            print(f"   Connectivity test result: {connectivity_result}")
        except Exception as e:
            print(f"   Connectivity test error: {e}")
        
        # Check sync status
        print(f"\n📊 Checking sync status...")
        try:
            sync_status = system.base_system.get_sync_status()
            print(f"   Sync status: {sync_status}")
        except Exception as e:
            print(f"   Sync status error: {e}")
        
        # Try to force sync
        print(f"\n🔄 Testing force sync...")
        try:
            force_sync_result = system.base_system.force_sync()
            print(f"   Force sync result: {force_sync_result}")
        except Exception as e:
            print(f"   Force sync error: {e}")
    
    # Test account data (same structure as UI creates)
    test_account_data = {
        'name': 'Test Sync Account',
        'account_type': 'Asset',
        'code': 'SYNC001',
        'parent_id': None,  # Top-level account
        'is_postable': True,
        'description': 'Test account to verify sync functionality'
    }
    
    print(f"\n📝 Creating test account:")
    print(f"   Data: {test_account_data}")
    
    try:
        # Use the same method path as the UI
        if hasattr(system, 'base_system'):
            print("   Using base_system.create_account")
            result = system.base_system.create_account(test_account_data)
        else:
            print("   Using system.create_account")
            result = system.create_account(test_account_data)
        
        print(f"\n✅ Account creation result: {result}")
        
        if result:
            print(f"   Created account ID: {result.get('id', 'No ID returned')}")
            queued = result.get('queued', False)
            print(f"   Queued: {queued}")
            
            if queued:
                print("   🔄 Account was queued, trying immediate sync...")
                try:
                    if hasattr(system, 'base_system'):
                        sync_result = system.base_system.force_sync()
                    else:
                        sync_result = system.force_sync()
                    
                    print(f"   Sync result: {sync_result}")
                    
                    if sync_result.get('success'):
                        print(f"   ✅ Synced {sync_result.get('synced_operations', 0)} operations")
                    else:
                        print(f"   ❌ Sync failed: {sync_result.get('error', 'Unknown error')}")
                except Exception as sync_error:
                    print(f"   ❌ Sync error: {sync_error}")
            else:
                print("   ✅ Account was created directly (not queued)")
        else:
            print("   ❌ FAILED: No result returned")
            
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_connectivity_and_sync()
