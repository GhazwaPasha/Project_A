"""
Simple Windows 11 Login Dialog
"""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QLineEdit, QCheckBox, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal

class LoginWindow(QDialog):
    """Simple Windows 11 login dialog"""
    
    login_successful = pyqtSignal(dict, list)
    signup_requested = pyqtSignal()
    
    def __init__(self, auth_manager):
        super().__init__()
        self.auth_manager = auth_manager
        self.setWindowTitle("AI Accountant - Sign In")
        self.setModal(True)
        self.setFixedSize(450, 350)
        
        self._setup_ui()
        self._apply_style()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(20)
        
        # Title
        title = QLabel("Sign In")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setObjectName("title")
        layout.addWidget(title)
        
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
        
        # Remember me
        self.remember_check = QCheckBox("Remember me")
        layout.addWidget(self.remember_check)
        
        # Sign in button
        self.signin_btn = QPushButton("Sign In")
        self.signin_btn.setObjectName("primary")
        self.signin_btn.clicked.connect(self._signin)
        layout.addWidget(self.signin_btn)
        
        # Footer
        footer = QHBoxLayout()
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        footer_text = QLabel("Don't have an account?")
        footer_text.setObjectName("subtitle")
        footer.addWidget(footer_text)
        
        signup_btn = QPushButton("Sign up")
        signup_btn.setObjectName("link")
        signup_btn.clicked.connect(self.signup_requested.emit)
        footer.addWidget(signup_btn)
        
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
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iOSIgdmlld0JveD0iMCAwIDEyIDkiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxwYXRoIGQ9Ik0xIDQuNUw0LjUgOEwxMSAxIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIvPgo8L3N2Zz4K);
            }
            
            QCheckBox::indicator:hover {
                border-color: #808080;
            }        """)
        
    def _signin(self):
        email = self.email_edit.text().strip()
        password = self.password_edit.text()
        
        if not email or not password:
            QMessageBox.warning(self, "Error", "Please enter both email and password.")
            return
            
        try:
            result = self.auth_manager.sign_in(email, password)
            if result.get("success"):
                user_data = result.get("user")
                organizations = result.get("organizations", [])
                self.login_successful.emit(user_data, organizations)
                self.accept()
            else:
                error_msg = result.get("error", "Invalid email or password.")
                QMessageBox.warning(self, "Login Failed", error_msg)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Login failed: {str(e)}")
