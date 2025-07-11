#!/usr/bin/env python3
"""
Test script to verify resource manager functionality
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core.resource_manager import ResourceManager

def test_resource_manager():
    """Test the resource manager functionality"""
    print("🔍 Testing Resource Manager...")
    
    # Test icon path resolution
    test_icons = [
        "dashboard_new.svg",
        "journal_new.svg",
        "ledger_new.svg",
        "trial_balance_new.svg",
        "reports_new.svg",
        "accounts_new.svg",
        "ledger_note.svg",
        "period_closing_modern.svg",
        "team_new.svg",
        "org_settings_new.svg",
        "user_mgmt_new.svg",
        "platform_new.svg",
        "global_orgs_new.svg",
        "settings_new.svg",
        "menu_modern.svg",
        "minimize.svg",
        "maximize.svg",
        "close.svg",
        "notification_modern.svg",
        "wifi.png",
        "app-icon.png"
    ]
    
    print("\n📋 Testing icon path resolution:")
    found_icons = []
    missing_icons = []
    
    for icon in test_icons:
        path = ResourceManager.get_icon_path(icon)
        if path and os.path.exists(path):
            print(f"✅ {icon} -> {path}")
            found_icons.append(icon)
        else:
            print(f"❌ {icon} -> Not found")
            missing_icons.append(icon)
    
    print(f"\n📊 Results:")
    print(f"✅ Found: {len(found_icons)} icons")
    print(f"❌ Missing: {len(missing_icons)} icons")
    
    if missing_icons:
        print(f"\n❌ Missing icons: {missing_icons}")
        return False
    else:
        print("\n🎉 All icons found successfully!")
        return True

def test_executable_resources():
    """Test if we can access resources in executable mode"""
    print("\n🔍 Testing executable resource access...")
    
    # Simulate executable environment
    import tempfile
    import shutil
    
    # Create a temporary directory to simulate _MEIPASS
    with tempfile.TemporaryDirectory() as temp_dir:
        # Copy assets to temp directory
        assets_src = os.path.join(os.path.dirname(__file__), 'assets')
        assets_dst = os.path.join(temp_dir, 'assets')
        if os.path.exists(assets_src):
            shutil.copytree(assets_src, assets_dst)
            
            # Temporarily set sys._MEIPASS
            original_frozen = getattr(sys, 'frozen', False)
            original_meipass = getattr(sys, '_MEIPASS', None)
            
            try:
                sys.frozen = True
                sys._MEIPASS = temp_dir
                
                # Test resource access
                test_path = ResourceManager.get_icon_path("dashboard_new.svg")
                if test_path and os.path.exists(test_path):
                    print("✅ Executable resource access working!")
                    return True
                else:
                    print("❌ Executable resource access failed!")
                    return False
                    
            finally:
                # Restore original values
                sys.frozen = original_frozen
                if original_meipass is None:
                    delattr(sys, '_MEIPASS')
                else:
                    sys._MEIPASS = original_meipass

if __name__ == '__main__':
    print("🚀 Resource Manager Test")
    print("=" * 50)
    
    # Test development mode
    dev_success = test_resource_manager()
    
    # Test executable mode
    exe_success = test_executable_resources()
    
    print("\n" + "=" * 50)
    if dev_success and exe_success:
        print("🎉 All tests passed! Resource manager is working correctly.")
    else:
        print("❌ Some tests failed. Check the output above.") 