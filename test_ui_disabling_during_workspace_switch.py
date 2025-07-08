#!/usr/bin/env python3
"""
Test script to verify UI disabling during workspace switching
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_ui_disabling_functionality():
    """Test that UI disabling works correctly during workspace switching"""
    try:
        from src.core.auth_manager import AuthManager
        from src.core.session_manager import SessionManager
        from src.ui.mainwindow import MainWindow
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import QTimer
        
        print("🔍 Testing UI disabling during workspace switching...")
        
        # Initialize QApplication
        app = QApplication(sys.argv)
        
        # Initialize auth manager
        auth_manager = AuthManager()
        
        # Test login (you'll need to provide credentials)
        email = input("Enter your email: ")
        password = input("Enter your password: ")
        
        result = auth_manager.sign_in(email, password)
        if not result.get('success'):
            print(f"❌ Login failed: {result.get('message', 'Unknown error')}")
            return False
        
        print(f"✅ Login successful for {email}")
        
        # Initialize session manager
        session_manager = SessionManager(auth_manager)
        session_manager.initialize_session(result['user'])
        
        # Get available organizations
        organizations = session_manager.get_available_organizations()
        print(f"📋 Found {len(organizations)} organizations:")
        for i, org in enumerate(organizations):
            print(f"   {i+1}. {org.get('name', 'Unknown')} (ID: {org.get('id', 'Unknown')}) Type: {org.get('organization_type', 'Unknown')}")
        
        if len(organizations) < 2:
            print("⚠️ Need at least 2 organizations to test switching")
            return False
        
        # Create main window
        main_window = MainWindow(auth_manager, session_manager)
        main_window.show()
        
        print("\n🧪 Testing UI disabling functionality:")
        print("1. The main window should be visible")
        print("2. Click on the workspace switcher in the bottom bar")
        print("3. Select a different organization")
        print("4. Observe that the UI becomes disabled during the switch")
        print("5. A progress popup should appear showing the switch progress")
        print("6. The UI should be re-enabled after the switch completes")
        
        # Set up a timer to close the app after 30 seconds for testing
        def close_app():
            print("\n⏰ Test timeout - closing application")
            app.quit()
        
        QTimer.singleShot(30000, close_app)
        
        print("\n⏱️  You have 30 seconds to test the workspace switching...")
        
        # Run the application
        return app.exec()
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_freeze_unfreeze_methods():
    """Test the freeze/unfreeze methods directly"""
    try:
        from src.ui.mainwindow import MainWindow
        from PyQt6.QtWidgets import QApplication
        
        print("🔍 Testing freeze/unfreeze methods directly...")
        
        # Initialize QApplication
        app = QApplication(sys.argv)
        
        # Create main window without auth (for testing methods only)
        main_window = MainWindow()
        
        print("✅ Testing _freeze_ui_during_switch()...")
        main_window._freeze_ui_during_switch()
        
        # Check if UI elements are disabled
        if hasattr(main_window, 'sidebar'):
            print(f"   Sidebar enabled: {main_window.sidebar.isEnabled()}")
        if hasattr(main_window, 'stack'):
            print(f"   Content area enabled: {main_window.stack.isEnabled()}")
        if hasattr(main_window, 'bottom_bar'):
            print(f"   Bottom bar enabled: {main_window.bottom_bar.isEnabled()}")
        
        print("✅ Testing _unfreeze_ui_after_switch()...")
        main_window._unfreeze_ui_after_switch()
        
        # Check if UI elements are re-enabled
        if hasattr(main_window, 'sidebar'):
            print(f"   Sidebar enabled: {main_window.sidebar.isEnabled()}")
        if hasattr(main_window, 'stack'):
            print(f"   Content area enabled: {main_window.stack.isEnabled()}")
        if hasattr(main_window, 'bottom_bar'):
            print(f"   Bottom bar enabled: {main_window.bottom_bar.isEnabled()}")
        
        print("✅ Freeze/unfreeze methods test completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Freeze/unfreeze test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("UI Disabling During Workspace Switch Test")
    print("=" * 50)
    
    # Test 1: Direct method testing
    print("\n🧪 Test 1: Direct method testing")
    test_freeze_unfreeze_methods()
    
    # Test 2: Full integration testing (requires user interaction)
    print("\n🧪 Test 2: Full integration testing")
    print("This test requires user interaction to verify workspace switching.")
    response = input("Do you want to run the full integration test? (y/n): ")
    
    if response.lower() == 'y':
        test_ui_disabling_functionality()
    else:
        print("Skipping full integration test.")
    
    print("\n✅ Test completed!") 