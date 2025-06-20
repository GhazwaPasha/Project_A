"""
Multi-tenant Accounting Application with Authentication
Entry point with Supabase Auth and role-based access control
"""
import sys
import os
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt
from src.ui.mainwindow import MainWindow
from src.ui.auth.login_window import LoginWindow
from src.ui.auth.organization_selector import OrganizationSelectorDialog
from src.ui.auth.signup_dialog import SignupDialog
from src.core.auth_manager import AuthManager
from src.core.session_manager import SessionManager

# Set environment variables (for development - use proper config in production)
os.environ['SUPABASE_URL'] = 'https://your-project.supabase.co'
os.environ['SUPABASE_ANON_KEY'] = 'your-anon-key'
os.environ['MISTRAL_API_KEY'] = '***REMOVED***'

class AuthenticatedApp:
    """Main application with authentication flow"""
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.auth_manager = None
        self.session_manager = None
        self.main_window = None
        
        # Apply application-wide styles
        self.app.setStyle('Fusion')
        
    def start(self):
        """Start the application with authentication flow"""
        try:
            # Initialize auth manager
            self.auth_manager = AuthManager()
            
            # Show login window
            login_window = LoginWindow(self.auth_manager)
            
            # Connect login success to main app
            login_window.login_successful.connect(self.on_login_success)
            login_window.signup_requested.connect(self.show_signup)
            
            if login_window.exec() == login_window.DialogCode.Accepted:
                # Login successful, start main application
                return self.app.exec()
            else:
                # Login cancelled or failed
                return 0
                
        except Exception as e:
            self.show_startup_error(str(e))
            return 1
    
    def show_signup(self):
        """Show signup dialog"""
        signup_dialog = SignupDialog(self.auth_manager)
        signup_dialog.signup_successful.connect(self.on_signup_success)
        signup_dialog.exec()
    
    def on_signup_success(self, signup_data):
        """Handle successful signup"""
        # After successful signup, show login window again
        QMessageBox.information(None, "Account Created", 
                              "Your account has been created successfully. Please check your email for verification.")
        # TODO: Auto-login or return to login window
    
    def on_login_success(self, user_data: dict, organizations: list):
        """Handle successful login"""
        try:
            # Initialize session manager
            self.session_manager = SessionManager(self.auth_manager)
            
            # If user has multiple organizations, show selector
            if len(organizations) > 1:
                org_selector = OrganizationSelectorDialog(organizations)
                org_selector.organization_selected.connect(self._set_organization_and_continue)
                
                if org_selector.exec() == org_selector.DialogCode.Accepted:
                    selected_org = org_selector.selected_org
                else:
                    return  # User cancelled organization selection
            else:
                selected_org = organizations[0] if organizations else None
            
            if not selected_org:
                QMessageBox.warning(None, "No Organization", 
                                  "You don't belong to any organization. Contact your administrator.")
                return
            
            self._set_organization_and_continue(selected_org)
            
        except Exception as e:
            self.show_startup_error(f"Failed to initialize application: {str(e)}")
    
    def _set_organization_and_continue(self, selected_org):
        """Set active organization and continue to main app"""
        try:
            # Set active organization
            self.session_manager.set_active_organization(selected_org['id'])
            
            # Create and show main window with auth context
            self.main_window = MainWindow(
                db_mode='hybrid', 
                prefer_local=True, 
                auto_sync=True,
                auth_manager=self.auth_manager,
                session_manager=self.session_manager
            )
            self.main_window.show()
            
        except Exception as e:
            self.show_startup_error(f"Failed to initialize main application: {str(e)}")
    
    def show_startup_error(self, error_message: str):
        """Show startup error dialog"""
        QMessageBox.critical(None, "Startup Error", 
                           f"Failed to start application: {error_message}\n\n"
                           f"Please check your configuration and try again.")

if __name__ == "__main__":
    app = AuthenticatedApp()
    sys.exit(app.start())
