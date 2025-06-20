"""
Multi-tenant Accounting Application with Authentication
Entry point with Supabase Auth and role-based access control
"""
import sys
import os
from dotenv import load_dotenv
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt
from src.ui.mainwindow import MainWindow
from src.ui.auth.login_window import LoginWindow
from src.ui.auth.organization_selector import OrganizationSelectorDialog
from src.ui.auth.signup_dialog import SignupDialog
from src.core.auth_manager_temp import AuthManager  # Using temporary working version
from src.core.session_manager import SessionManager

# Load environment variables from .env file
load_dotenv()

# Validate required environment variables
REQUIRED_ENV_VARS = ['SUPABASE_URL', 'SUPABASE_ANON_KEY']
missing_vars = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]

if missing_vars:
    raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

class AuthenticatedApp:
    """Main application with authentication flow"""
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.auth_manager = None
        self.session_manager = None
        self.main_window = None
        self.login_window = None
        
        # Apply application-wide styles
        self.app.setStyle('Fusion')
        
    def _validate_environment(self):
        """Validate that required environment variables are available"""
        missing_vars = []
        required_vars = ['SUPABASE_URL', 'SUPABASE_ANON_KEY']
        
        for var in required_vars:
            value = os.getenv(var)
            if not value or value.strip() == '':
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing or empty required environment variables: {', '.join(missing_vars)}")
        
        # Log successful validation (optional)
        print(f"✓ Environment validation successful")
        print(f"✓ SUPABASE_URL: {os.getenv('SUPABASE_URL')}")
        print(f"✓ SUPABASE_ANON_KEY: {'*' * 20}...{os.getenv('SUPABASE_ANON_KEY')[-10:]}")

    def start(self):
        """Start the application with authentication flow"""
        try:
            # Validate environment variables again at runtime
            self._validate_environment()
            
            # Initialize auth manager
            self.auth_manager = AuthManager()
            
            # Show login window
            self.login_window = LoginWindow(self.auth_manager)
            
            # Connect login success to main app
            self.login_window.login_successful.connect(self.on_login_success)
            self.login_window.signup_requested.connect(self.show_signup)
            
            # Show login dialog and start the app
            self.login_window.show()
            return self.app.exec()
                
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
            # Close the login window properly
            if hasattr(self, 'login_window') and self.login_window:
                self.login_window.close()
                self.login_window = None
            
            # Initialize session manager (skip for now due to import issues)
            # self.session_manager = SessionManager(self.auth_manager)
            self.session_manager = None
            
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
                # Show more helpful message and offer to create organization
                reply = QMessageBox.question(None, "No Organization", 
                                           "You don't belong to any organization yet.\n\n"
                                           "Would you like to create a new organization?",
                                           QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                
                if reply == QMessageBox.StandardButton.Yes:
                    try:
                        self._create_first_organization()
                    except Exception as e:
                        QMessageBox.critical(None, "Error", 
                                           f"Failed to create organization due to system issues.\n\n"
                                           f"Please contact your administrator or try creating an organization manually.\n\n"
                                           f"Error: {str(e)}")
                else:
                    QMessageBox.information(None, "Contact Administrator", 
                                          "Please contact your system administrator to be added to an organization.")
                return
            
            self._set_organization_and_continue(selected_org)
            
        except Exception as e:
            self.show_startup_error(f"Failed to initialize application: {str(e)}")
    
    def _create_first_organization(self):
        """Create the first organization for a new user"""
        try:
            from PyQt6.QtWidgets import QInputDialog
            
            # Get organization name from user
            org_name, ok = QInputDialog.getText(None, "Create Organization", 
                                               "Enter your organization name:")
            
            if not ok or not org_name.strip():
                return
            
            # Create organization using auth manager
            result = self.auth_manager.create_organization(org_name.strip())
            
            if result.get("success"):
                QMessageBox.information(None, "Organization Created", 
                                      f"Organization '{org_name}' has been created successfully!\n"
                                      f"You are now the owner of this organization.")
                
                # Reload organizations and continue
                self.auth_manager._load_user_organizations()
                organizations = self.auth_manager.user_organizations
                
                if organizations:
                    selected_org = organizations[0]
                    self._set_organization_and_continue(selected_org)
                else:
                    QMessageBox.warning(None, "Error", "Failed to load the created organization.")
            else:
                QMessageBox.warning(None, "Creation Failed", 
                                  f"Failed to create organization: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            QMessageBox.critical(None, "Error", f"Failed to create organization: {str(e)}")

    def _set_organization_and_continue(self, selected_org):
        """Set active organization and continue to main app"""
        try:
            # Set active organization (skip session manager for now)
            # self.session_manager.set_active_organization(selected_org['id'])
            
            # Make sure we don't have a main window already
            if self.main_window:
                self.main_window.close()
                self.main_window = None
            
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
