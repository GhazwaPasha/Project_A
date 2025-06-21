"""
Simple Windows 11 Signup Dialog
"""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QLineEdit, QComboBox, QCheckBox, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal

class SignupDialog(QDialog):
    """Simple Windows 11 signup dialog"""
    
    signup_successful = pyqtSignal(dict)
    
    def __init__(self, auth_manager, parent=None):
        super().__init__(parent)
        self.auth_manager = auth_manager
        
        self.setWindowTitle("AI Accountant - Create Account")
        self.setModal(True)
        self.setFixedSize(450, 550)
        
        self._setup_ui()
        self._apply_style()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(20)
        
        # Title
        title = QLabel("Create Account")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setObjectName("title")
        layout.addWidget(title)
        
        # Name fields in one row
        name_layout = QHBoxLayout()
        name_layout.setSpacing(12)
        
        self.first_name_input = QLineEdit()
        self.first_name_input.setPlaceholderText("First name")
        self.first_name_input.setObjectName("input")
        name_layout.addWidget(self.first_name_input)
        
        self.last_name_input = QLineEdit()
        self.last_name_input.setPlaceholderText("Last name")
        self.last_name_input.setObjectName("input")
        name_layout.addWidget(self.last_name_input)
        
        layout.addLayout(name_layout)
        
        # Email field
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email address")
        self.email_input.setObjectName("input")
        layout.addWidget(self.email_input)
        
        # Password fields in one row
        password_layout = QHBoxLayout()
        password_layout.setSpacing(12)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setObjectName("input")
        password_layout.addWidget(self.password_input)
        
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setPlaceholderText("Confirm password")
        self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password_input.setObjectName("input")
        password_layout.addWidget(self.confirm_password_input)
        
        layout.addLayout(password_layout)
        
        # Organization type
        self.org_combo = QComboBox()
        self.org_combo.setObjectName("combo")
        self.org_combo.addItem("Create New Organization", "new")
        self.org_combo.addItem("Join Existing Organization", "existing")
        self.org_combo.currentTextChanged.connect(self._on_org_type_changed)
        layout.addWidget(self.org_combo)
        
        # Organization name field
        self.org_name_input = QLineEdit()
        self.org_name_input.setPlaceholderText("Organization name")
        self.org_name_input.setObjectName("input")
        layout.addWidget(self.org_name_input)
        
        # Invitation code field (hidden by default)
        self.invite_input = QLineEdit()
        self.invite_input.setPlaceholderText("Invitation code")
        self.invite_input.setObjectName("input")
        self.invite_input.hide()
        layout.addWidget(self.invite_input)
        
        # Terms checkbox
        self.terms_checkbox = QCheckBox("I agree to the Terms of Service and Privacy Policy")
        layout.addWidget(self.terms_checkbox)
        
        # Create account button
        self.signup_btn = QPushButton("Create Account")
        self.signup_btn.setObjectName("primary")
        self.signup_btn.clicked.connect(self._handle_signup)
        layout.addWidget(self.signup_btn)
        
        # Footer
        footer = QHBoxLayout()
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        footer_text = QLabel("Already have an account?")
        footer_text.setObjectName("subtitle")
        footer.addWidget(footer_text)
        
        signin_btn = QPushButton("Sign in")
        signin_btn.setObjectName("link")
        signin_btn.clicked.connect(self.reject)
        footer.addWidget(signin_btn)
        
        layout.addLayout(footer)
        
        # Connect enter key
        self.confirm_password_input.returnPressed.connect(self._handle_signup)
        
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
            }
            
            QLabel#subtitle {
                font-size: 14px;
                color: #cccccc;
                margin-right: 8px;
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
            
            QComboBox#combo {
                padding: 14px 16px;
                border: 1px solid #404040;
                border-radius: 6px;
                font-size: 15px;
                background-color: #2d2d2d;
                color: #ffffff;
                min-height: 22px;
            }
            
            QComboBox#combo:focus {
                border-color: #0078d4;
                background-color: #333333;
            }
            
            QComboBox#combo:hover {
                border-color: #606060;
                background-color: #303030;
            }
            
            QComboBox#combo::drop-down {
                border: none;
                width: 20px;
            }
            
            QComboBox#combo::down-arrow {
                width: 12px;
                height: 12px;
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iOCIgdmlld0JveD0iMCAwIDEyIDgiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxwYXRoIGQ9Ik0xIDFMNiA2TDExIDEiIHN0cm9rZT0iIzk5OTk5OSIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiLz4KPC9zdmc+);
            }
            
            QComboBox#combo QAbstractItemView {
                background-color: #2d2d2d;
                border: 1px solid #404040;
                color: #ffffff;
                selection-background-color: #0078d4;
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
            }
            
            QPushButton#link {
                background: transparent;
                border: none;
                color: #0078d4;
                font-size: 14px;
                padding: 6px 12px;
                font-weight: 500;
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
        """)
    
    def _on_org_type_changed(self):
        """Handle organization type change"""
        if self.org_combo.currentData() == "existing":
            self.org_name_input.hide()
            self.invite_input.show()
        else:
            self.invite_input.hide()
            self.org_name_input.show()
    
    def _handle_signup(self):
        """Handle signup button click"""
        # Get form data
        first_name = self.first_name_input.text().strip()
        last_name = self.last_name_input.text().strip()
        email = self.email_input.text().strip()
        password = self.password_input.text()
        confirm_password = self.confirm_password_input.text()
        
        # Validate required fields
        if not all([first_name, last_name, email, password, confirm_password]):
            QMessageBox.warning(self, "Error", "Please fill in all required fields.")
            return
        
        # Validate password match
        if password != confirm_password:
            QMessageBox.warning(self, "Error", "Passwords do not match.")
            return
        
        # Validate terms acceptance
        if not self.terms_checkbox.isChecked():
            QMessageBox.warning(self, "Error", "Please accept the Terms of Service and Privacy Policy.")
            return
        
        # Get organization data
        org_type = self.org_combo.currentData()
        if org_type == "new":
            org_name = self.org_name_input.text().strip()
            if not org_name:
                QMessageBox.warning(self, "Error", "Please enter an organization name.")
                return
            org_data = {"type": "new", "name": org_name}
        else:
            invite_code = self.invite_input.text().strip()
            if not invite_code:
                QMessageBox.warning(self, "Error", "Please enter an invitation code.")
                return
            org_data = {"type": "existing", "invite_code": invite_code}
        
        # Prepare user data
        user_data = {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "password": password,
            "organization": org_data
        }
        
        try:
            # Attempt to create the user
            success = self.auth_manager.create_user(user_data)
            if success:
                self.signup_successful.emit(user_data)
                self.accept()
            else:
                QMessageBox.warning(self, "Signup Failed", "Failed to create account. Please try again.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Signup failed: {str(e)}")