#!/usr/bin/env python3
"""
Smart Multi-Tenant Launcher
Automatically detects if Supabase is configured and enables authentication accordingly
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

# Set default Mistral API key
os.environ.setdefault('MISTRAL_API_KEY', '***REMOVED***')

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

class SmartApp:
    """Smart application launcher that adapts based on configuration"""
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setStyle('Fusion')
        
    def start(self):
        """Start the application with appropriate mode"""
        try:
            if is_supabase_configured():
                return self.start_with_auth()
            else:
                return self.start_without_auth()
                
        except Exception as e:
            self.show_startup_error(str(e))
            return 1
    
    def start_with_auth(self):
        """Start with full authentication system"""
        print("🔐 Starting with multi-tenant authentication...")
        
        try:
            from src.ui.auth.login_window import LoginWindow
            from src.ui.auth.signup_dialog import SignupDialog
            from src.core.auth_manager import AuthManager
            from src.core.session_manager import SessionManager
            
            # Initialize auth manager
            auth_manager = AuthManager()
              # Show login window
            login_window = LoginWindow(auth_manager)
            
            # Try auto-login first if credentials are saved
            if login_window.try_auto_login():
                # Auto-login successful, create session manager
                session_manager = SessionManager(auth_manager)
                return self.start_main_app(auth_manager, session_manager)
            
            # Connect signup signal to show signup dialog
            login_window.signup_requested.connect(lambda: self._show_signup_dialog(auth_manager, login_window))
            
            if login_window.exec() == login_window.DialogCode.Accepted:
                # Create session manager after successful login
                session_manager = SessionManager(auth_manager)
                
                # Start main app with authentication context
                return self.start_main_app(auth_manager, session_manager)
            else:
                print("Login cancelled by user")
                return 0
                
        except ImportError as e:
            print(f"⚠️  Authentication components not available: {e}")
            print("Falling back to single-tenant mode...")
            return self.start_without_auth()
    
    def _show_signup_dialog(self, auth_manager, parent_window):
        """Show signup dialog when requested from login window"""
        try:
            from src.ui.auth.signup_dialog import SignupDialog
            
            signup_dialog = SignupDialog(auth_manager, parent_window)
            
            # Handle successful signup
            def handle_signup_success(user_data):
                QMessageBox.information(parent_window, "Success", 
                                      "Account created successfully! Please sign in with your new credentials.")
                # Close signup dialog and return to login
                signup_dialog.accept()
            
            signup_dialog.signup_successful.connect(handle_signup_success)
            signup_dialog.exec()
            
        except Exception as e:
            QMessageBox.warning(parent_window, "Error", f"Could not open signup dialog: {str(e)}")

    def start_without_auth(self):
        """Start without authentication (single-tenant mode)"""
        print("🚀 Starting in single-tenant mode...")
        return self.start_main_app()

    def start_main_app(self, auth_manager=None, session_manager=None):
        """Start the main application window"""
        try:
            # Create main window with optional auth context
            main_window = MainWindow(
                auth_manager=auth_manager,
                session_manager=session_manager
            )
            
            main_window.show()
            return self.app.exec()
            
        except Exception as e:
            print(f"⚠️  Error starting application: {e}")
            raise
    
    def show_startup_error(self, error_message: str):
        """Show startup error dialog"""
        QMessageBox.critical(None, "Startup Error", 
                           f"Failed to start application: {error_message}\n\n"
                           f"Please check your configuration and try again.")

def main():
    """Main entry point"""
    print("🚀 AI Accountant - Multi-Tenant SaaS")
    print("=" * 40)
    
    if is_supabase_configured():
        print("✅ Supabase configured - Multi-tenant mode available")
    else:
        print("ℹ️  Supabase not configured - Running in single-tenant mode")
        print("   To enable multi-tenant features:")
        print("   1. Copy .env.example to .env")
        print("   2. Add your Supabase credentials")
        print("   3. Run: python tools/setup_multitenant.py")
    
    print("-" * 40)
    
    app = SmartApp()
    return app.start()

if __name__ == "__main__":
    sys.exit(main())
