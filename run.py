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
                # Start main app with authentication context
                # Note: MainWindow will initialize its own accounting system
                return self.start_main_app(auth_manager, None)
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
            
            main_window.show()
            return self.app.exec()
            
        except Exception as e:
            print(f"⚠️  Error starting application: {e}")
            raise
    
    def show_config_error(self):
        """Show configuration error dialog"""
        QMessageBox.critical(None, "Configuration Required", 
                           "Supabase configuration is required to run this application.\n\n"
                           "Please:\n"
                           "1. Set up your Supabase project\n"
                           "2. Run the NEW_SCHEMA.sql script in Supabase SQL Editor\n"
                           "3. Configure your .env file with Supabase credentials\n"
                           "4. Run: python setup_initial_data.py")
    
    def show_startup_error(self, error_message: str):
        """Show startup error dialog"""
        QMessageBox.critical(None, "Startup Error", 
                           f"Failed to start application: {error_message}\n\n"
                           f"Please check your configuration and try again.")

def main():
    """Main entry point"""
    print("🚀 AI Accountant - Clean Multi-Tenant SaaS")
    print("=" * 40)
    
    if is_supabase_configured():
        print("✅ Supabase configured - Starting application...")
    else:
        print("❌ Supabase not configured!")
        print("   Required setup:")
        print("   1. Create Supabase project")
        print("   2. Run NEW_SCHEMA.sql in Supabase SQL Editor")
        print("   3. Configure .env with your Supabase credentials")
        print("   4. Run: python setup_initial_data.py")
    
    print("-" * 40)
    
    app = CleanApp()
    return app.start()

if __name__ == "__main__":
    sys.exit(main())
