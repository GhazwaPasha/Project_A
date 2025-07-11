"""
Simple Windows 11 Login Dialog
"""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QLineEdit, QCheckBox, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal, QSettings
from PyQt6.QtGui import QIcon
import base64
import hashlib
import platform

class LoginWindow(QDialog):
    """Simple Windows 11 login dialog"""
    
    login_successful = pyqtSignal(dict, list)
    signup_requested = pyqtSignal()
    
    def __init__(self, auth_manager):
        super().__init__()
        self.auth_manager = auth_manager
        self.settings = QSettings("AI_Accountant", "LoginCredentials")
        self.setWindowTitle("Accountuitive - Sign In")
        self.setModal(True)
        self.setFixedSize(450, 550)  # Match signup dialog size
        
        # Set application icon
        from ...core.resource_manager import ResourceManager
        app_icon_path = ResourceManager.get_icon_path("app-icon.png")
        if app_icon_path:
            self.setWindowIcon(QIcon(app_icon_path))
        
        self._setup_ui()
        self._apply_style()
        self._load_saved_credentials()  # Load saved credentials if any
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(20)  # Restored to match signup dialog spacing
          # Title
        title = QLabel("Sign In")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setObjectName("title")
        layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel("Welcome back! Please sign in to your account.")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setObjectName("subtitle")
        layout.addWidget(subtitle)
        
        # Email field
        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("Email address")
        self.email_edit.setObjectName("input")
        layout.addWidget(self.email_edit)
        
        # Password field
        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("Password")
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setObjectName("input")
        layout.addWidget(self.password_edit)
          # Add some spacing before remember checkbox
        layout.addSpacing(12)
          # Remember me and forgot password row
        remember_row = QHBoxLayout()
        
        self.remember_check = QCheckBox("Remember me")
        self.remember_check.toggled.connect(self._on_remember_toggled)  # Handle checkbox changes
        remember_row.addWidget(self.remember_check)
        
        remember_row.addStretch()  # Push forgot password to the right
        
        forgot_btn = QPushButton("Forgot password?")
        forgot_btn.setObjectName("link")
        forgot_btn.clicked.connect(self._forgot_password)
        remember_row.addWidget(forgot_btn)
        
        layout.addLayout(remember_row)
        
        # Add some spacing before sign in button
        layout.addSpacing(16)
        
        # Sign in button
        self.signin_btn = QPushButton("Sign In")
        self.signin_btn.setObjectName("primary")
        self.signin_btn.clicked.connect(self._signin)
        layout.addWidget(self.signin_btn)
        
        # Add a status label for auto-login feedback
        self.status_label = QLabel("")
        self.status_label.setObjectName("status")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.hide()  # Hidden by default
        layout.addWidget(self.status_label)

          # Add spacing before footer
        layout.addSpacing(20)        # Footer
        footer = QHBoxLayout()
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setSpacing(8)  # Increased spacing for better visual balance
        
        footer_text = QLabel("Don't have an account?")
        footer_text.setObjectName("subtitle")
        footer_text.setAlignment(Qt.AlignmentFlag.AlignVCenter)  # Vertical center alignment
        footer.addWidget(footer_text, 0, Qt.AlignmentFlag.AlignVCenter)
        
        signup_btn = QPushButton("Sign up")
        signup_btn.setObjectName("link")
        signup_btn.clicked.connect(self.signup_requested.emit)
        footer.addWidget(signup_btn, 0, Qt.AlignmentFlag.AlignVCenter)
        
        layout.addLayout(footer)
        
        # Connect enter key
        self.password_edit.returnPressed.connect(self._signin)
        
    def _apply_style(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #202020;
                font-family: 'Segoe UI';
                color: #ffffff;
            }
            
            QLabel#title {
                font-size: 28px;
                font-weight: 300;
                color: #ffffff;
                margin-bottom: 20px;
            }            QLabel#subtitle {
                font-size: 14px;
                color: #cccccc;
                margin: 0px;
                padding: 0px;
                line-height: 20px;
            }
            
            QLabel[objectName="subtitle"] {
                font-size: 14px;
                color: #cccccc;
                margin: 0px;
                padding: 0px;
                line-height: 20px;
            }
            
            QLineEdit#input {
                padding: 14px 16px;
                border: 1px solid #404040;
                border-radius: 6px;
                font-size: 15px;
                background-color: #2d2d2d;
                color: #ffffff;
                min-height: 22px;
            }
            
            QLineEdit#input:focus {
                border-color: #0078d4;
                background-color: #333333;
                outline: none;
            }
            
            QLineEdit#input:hover {
                border-color: #606060;
                background-color: #303030;
            }
            
            QLineEdit#input::placeholder {
                color: #999999;
                font-style: normal;
            }
            
            QPushButton#primary {
                background-color: #0078d4;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 14px 28px;
                font-size: 15px;
                font-weight: 500;
                min-height: 22px;
            }
            
            QPushButton#primary:hover {
                background-color: #106ebe;
            }
            
            QPushButton#primary:pressed {
                background-color: #005a9e;
            }            QPushButton#link {
                background: transparent;
                border: none;
                color: #0078d4;
                font-size: 14px;
                padding: 0px 4px;
                font-weight: 500;
                margin: 0px;
                text-align: left;
            }
            
            QPushButton#link:hover {
                color: #40a6ff;
                text-decoration: underline;
            }
            
            QCheckBox {
                font-size: 14px;
                color: #ffffff;
                spacing: 8px;
            }
            
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #606060;
                border-radius: 4px;
                background-color: #2d2d2d;
            }
            
            QCheckBox::indicator:checked {
                background-color: #0078d4;
                border-color: #0078d4;
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iOSIgdmlld0JveD0iMCAwIDEyIDkiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxwYXRoIGQ9Ike0xIDQuNUw0LjUgOEwxMSAxIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIvPgo8L3N2Zz4K);
            }
              QCheckBox::indicator:hover {
                border-color: #808080;
            }
            
            QLabel#status {
                font-size: 12px;
                color: #0078d4;
                margin: 8px 0px;
                padding: 4px;
            }
        """)
        
    def _signin(self):
        email = self.email_edit.text().strip()
        password = self.password_edit.text()
        
        if not email or not password:
            QMessageBox.warning(self, "Error", "Please enter both email and password.")
            return
            
        try:
            result = self.auth_manager.sign_in(email, password)
            if result.get("success"):
                # Handle remember me functionality
                if self.remember_check.isChecked():
                    self._save_credentials(email, password)
                else:
                    self._clear_saved_credentials()
                
                user_data = result.get("user")
                organizations = result.get("organizations", [])
                self.login_successful.emit(user_data, organizations)
                self.accept()
            else:
                error_msg = result.get("error", "Invalid email or password.")
                QMessageBox.warning(self, "Login Failed", error_msg)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Login failed: {str(e)}")
    
    def _forgot_password(self):
        """Handle forgot password click"""
        QMessageBox.information(self, "Forgot Password", 
                              "Password reset functionality will be implemented soon.\n\n"
                              "For now, please contact your administrator for assistance.")
        
    def _load_saved_credentials(self):
        """Load saved credentials if remember me was checked previously"""
        try:
            if self.settings.value("remember_me", False, type=bool):
                saved_email = self.settings.value("email", "", type=str)
                saved_password = self.settings.value("password", "", type=str)
                
                if saved_email and saved_password:
                    self.email_edit.setText(saved_email)
                    # Decode the password (simple base64 encoding for basic security)
                    try:
                        decoded_password = self._decode_password(saved_password)
                        self.password_edit.setText(decoded_password)
                        self.remember_check.setChecked(True)
                    except:
                        # If decoding fails, clear saved credentials
                        self._clear_saved_credentials()
        except Exception as e:
            print(f"Error loading saved credentials: {e}")

    def _save_credentials(self, email, password):
        """Save credentials when remember me is checked"""
        try:
            self.settings.setValue("remember_me", True)
            self.settings.setValue("email", email)
            # Encode password with simple base64 (basic security)
            encoded_password = self._encode_password(password)
            self.settings.setValue("password", encoded_password)
            self.settings.sync()
        except Exception as e:
            print(f"Error saving credentials: {e}")

    def _clear_saved_credentials(self):
        """Clear saved credentials"""
        try:
            self.settings.setValue("remember_me", False)
            self.settings.remove("email")
            self.settings.remove("password")
            self.settings.sync()
        except Exception as e:
            print(f"Error clearing credentials: {e}")

    def _on_remember_toggled(self, checked):
        """Handle when remember me checkbox is toggled"""
        if not checked:
            # If unchecked, clear saved credentials immediately
            self._clear_saved_credentials()

    def has_saved_credentials(self):
        """Check if there are saved credentials available"""
        try:
            return (self.settings.value("remember_me", False, type=bool) and 
                   self.settings.value("email", "", type=str) and 
                   self.settings.value("password", "", type=str))
        except:
            return False

    def try_auto_login(self):
        """Attempt automatic login if credentials are saved"""
        if self.has_saved_credentials():
            self.status_label.setText("🔄 Signing in automatically...")
            self.status_label.show()
            
            try:
                email = self.settings.value("email", "", type=str)
                password_encoded = self.settings.value("password", "", type=str)
                password = self._decode_password(password_encoded)
                
                if password:
                    result = self.auth_manager.sign_in(email, password)
                    if result.get("success"):
                        self.status_label.setText("✅ Auto-login successful!")
                        user_data = result.get("user")
                        organizations = result.get("organizations", [])
                        self.login_successful.emit(user_data, organizations)
                        return True
                    else:
                        # If auto-login fails, clear saved credentials
                        self.status_label.setText("❌ Auto-login failed. Please sign in manually.")
                        self._clear_saved_credentials()
                        return False
                else:
                    # If password decoding fails, clear saved credentials
                    self.status_label.setText("❌ Saved credentials invalid. Please sign in manually.")
                    self._clear_saved_credentials()
                    return False
            except Exception as e:
                print(f"Auto-login failed: {e}")
                self.status_label.setText("❌ Auto-login error. Please sign in manually.")
                self._clear_saved_credentials()
                return False
        return False

    def _get_machine_key(self):
        """Generate a simple machine-specific key for password encoding"""
        machine_info = f"{platform.node()}{platform.machine()}"
        return hashlib.md5(machine_info.encode()).hexdigest()[:16]

    def _encode_password(self, password):
        """Encode password with simple XOR + base64"""
        key = self._get_machine_key()
        encoded = ""
        for i, char in enumerate(password):
            encoded += chr(ord(char) ^ ord(key[i % len(key)]))
        return base64.b64encode(encoded.encode()).decode()

    def _decode_password(self, encoded_password):
        """Decode password from XOR + base64"""
        try:
            key = self._get_machine_key()
            decoded_bytes = base64.b64decode(encoded_password.encode()).decode()
            password = ""
            for i, char in enumerate(decoded_bytes):
                password += chr(ord(char) ^ ord(key[i % len(key)]))
            return password
        except:
            return None
