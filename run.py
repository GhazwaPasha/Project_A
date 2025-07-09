#!/usr/bin/env python3
"""
Clean Multi-Tenant Launcher for New Schema
Works with the new Supabase-only backend (NEW_SCHEMA.sql)
"""
import sys
import os
from PyQt6.QtWidgets import QApplication, QMessageBox

# Load environment variables if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.ui.mainwindow import MainWindow

def is_supabase_configured():
    """Check if Supabase is properly configured"""
    url = os.getenv('SUPABASE_URL', '')
    key = os.getenv('SUPABASE_ANON_KEY', '')
    
    # Check if values exist and are not placeholder values
    return (url and key and 
            'your-project' not in url and 
            'your-anon-key' not in key and
            url.startswith('https://') and
            len(key) > 20)

class CleanApp:
    """Clean application launcher for the new schema"""
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setStyle('Fusion')
        
    def start(self):
        """Start the application"""
        try:
            if is_supabase_configured():
                return self.start_with_auth()
            else:
                self.show_config_error()
                return 1
                
        except Exception as e:
            self.show_startup_error(str(e))
            return 1
    
    def start_with_auth(self):
        """Start with authentication system"""
        print("🔐 Starting with multi-tenant authentication...")
        
        try:
            from src.ui.auth.login_window import LoginWindow
            from src.ui.auth.signup_dialog import SignupDialog
            from src.core.auth_manager import AuthManager
            from src.core.accounting_system import AccountingSystem
            
            # Initialize auth manager
            auth_manager = AuthManager()
            
            # Show login window
            login_window = LoginWindow(auth_manager)
            
            # Store session manager reference
            session_manager = None
            
            # Handle successful login and set up session
            def handle_login_success(user_data, organizations):
                nonlocal session_manager
                from src.core.session_manager import SessionManager
                session_manager = SessionManager(auth_manager)
                
                print(f"🔍 Debug: Received {len(organizations)} organizations from auth manager")
                for i, org in enumerate(organizations):
                    print(f"   Org {i+1}: {org.get('name', 'Unknown')} (ID: {org.get('id', 'Unknown')}) Role: {org.get('user_role', 'Unknown')}")
                
                # Initialize session with user data
                success = session_manager.initialize_session(user_data)
                if success:
                    current_org = session_manager.get_current_organization()
                    if current_org:
                        print(f"✅ User logged in: {user_data.get('email', 'Unknown')} - Active org: {current_org.get('name', 'Unknown')}")
                        print(f"   Role in org: {session_manager.get_current_user_role()}")
                        print(f"   Is super admin: {session_manager.is_super_admin()}")
                        print(f"   Organization type: {session_manager.get_current_organization_type()}")
                    else:
                        print(f"✅ User logged in: {user_data.get('email', 'Unknown')} - No active organization")
                else:
                    print(f"❌ Failed to initialize session for {user_data.get('email', 'Unknown')}")
                    
                    # Check for existing personal workspace
                    if not organizations:
                        print("⚠️ No organizations in initial fetch, checking for existing personal workspace...")
                        try:
                            # Try to find the user's personal workspace directly
                            if auth_manager.db_manager and auth_manager.db_manager.supabase:
                                result = auth_manager.db_manager.supabase.table('organizations')\
                                    .select('*')\
                                    .eq('created_by', user_data.get('id'))\
                                    .eq('organization_type', 'personal')\
                                    .execute()

                                if result.data:
                                    print("✅ Found existing personal workspace, reinitializing session...")
                                    success = session_manager.initialize_session(user_data)
                                    if not success:
                                        print("❌ Failed to initialize session with existing workspace")
                                        print("Debug info:")
                                        print(f"  Found org: {result.data[0]}")
                                else:
                                    print("❌ No personal workspace found for user!")
                                    print("Debug info:")
                                    print(f"  User ID: {user_data.get('id')}")
                                    print(f"  Email: {user_data.get('email')}")
                                    
                                    # Also check organization_members table
                                    if auth_manager.db_manager and auth_manager.db_manager.supabase:
                                        members = auth_manager.db_manager.supabase.table('organization_members')\
                                            .select('organization_id')\
                                            .eq('user_id', user_data.get('id'))\
                                            .execute()
                                            
                                        print(f"  Organization memberships found: {len(members.data) if members.data else 0}")
                            else:
                                print("❌ Database manager or Supabase client not available")
                                
                        except Exception as e:
                            print(f"❌ Error checking for personal workspace: {e}")
                            # Log additional error information if available
                            error_str = str(e)
                            if 'code' in error_str.lower() or 'details' in error_str.lower():
                                print(f"  Full error: {error_str}")
            
            login_window.login_successful.connect(handle_login_success)
            
            # Connect signup signal to show signup dialog
            def show_signup():
                signup_dialog = SignupDialog(auth_manager, login_window)
                if signup_dialog.exec() == signup_dialog.DialogCode.Accepted:
                    # After successful signup, user can proceed to login
                    QMessageBox.information(login_window, "Account Created", 
                                          "Your account has been created successfully!\n"
                                          "Please sign in with your new credentials.")
            
            login_window.signup_requested.connect(show_signup)
            
            if login_window.exec() == login_window.DialogCode.Accepted:
                # Ensure session manager was created during login
                if session_manager is None:
                    print("⚠️  Session manager not created - creating fallback")
                    from src.core.session_manager import SessionManager
                    session_manager = SessionManager(auth_manager)
                    
                    # Try to get organizations again
                    organizations = auth_manager.get_user_organizations()
                    if organizations:
                        session_manager.set_current_organization(organizations[0])
                        print(f"🔧 Fallback: Set organization {organizations[0].get('name', 'Unknown')}")
                
                # Start main app with authentication context
                return self.start_main_app(auth_manager, session_manager)
            else:
                print("Login cancelled by user")
                return 0
                
        except ImportError as e:
            print(f"⚠️  Authentication components not available: {e}")
            self.show_startup_error(f"Missing authentication components: {e}")
            return 1

    def start_main_app(self, auth_manager=None, session_manager=None):
        """Start the main application window"""
        try:
            # Create main window with auth context
            main_window = MainWindow(
                auth_manager=auth_manager,
                session_manager=session_manager
            )
            
            # If session manager was created after MainWindow, update it
            if session_manager and hasattr(main_window, 'set_session_manager'):
                main_window.set_session_manager(session_manager)
            
            main_window.show()
            
            # Refresh workspace switcher after window is shown to ensure it has latest data
            if hasattr(main_window, 'refresh_workspace_switcher'):
                main_window.refresh_workspace_switcher()
            
            # Force refresh user profile button to show initials
            if hasattr(main_window, 'user_profile_button') and session_manager:
                main_window.user_profile_button.update_user_profile(session_manager)
            
            return self.app.exec()
            
        except Exception as e:
            print(f"⚠️  Error starting application: {e}")
            raise
    
    def show_config_error(self):
        """Show configuration error dialog"""
        QMessageBox.critical(None, "Configuration Required", 
                           "Supabase configuration is required to run this application.\n\n"
                           "Please:\n"
                           "1. ✅ Supabase project is set up\n"
                           "2. ✅ CLEAN_SUPABASE_RESET.sql has been run successfully\n"
                           "3. Configure your .env file with Supabase credentials\n"
                           "4. Test user signup to verify auto-user creation works")
    
    def show_startup_error(self, error_message: str):
        """Show startup error dialog"""
        QMessageBox.critical(None, "Startup Error", 
                           f"Failed to start application: {error_message}\n\n"
                           f"Please check your configuration and try again.")


def main():
    """Main entry point"""
    print("Accountuitive - Clean Multi-Tenant SaaS")
    print("=" * 40)
    
    if is_supabase_configured():
        print("Supabase configured - Starting application...")
    else:
        print("Supabase not configured!")
        print("   Required setup:")
        print("   1. Create Supabase project")
        print("   2. Run CLEAN_SUPABASE_RESET.sql in Supabase SQL Editor")
        print("   3. Configure .env with your Supabase credentials")
        print("   4. Test user signup to verify auto-user creation works")
    
    print("-" * 40)
    
    app = CleanApp()
    return app.start()

if __name__ == "__main__":
    sys.exit(main())
