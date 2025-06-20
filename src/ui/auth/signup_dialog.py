"""
Signup Dialog for Multi-Tenant SaaS
"""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QLineEdit, QComboBox, QCheckBox, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPalette, QColor
from .login_window import GlassmorphismHelper

class SignupDialog(QDialog):
    """Dialog for user registration"""
    
    signup_successful = pyqtSignal(dict)
    
    def __init__(self, auth_manager, parent=None):
        super().__init__(parent)
        self.auth_manager = auth_manager
        
        self.setWindowTitle("Create Account")
        self.setModal(True)
        self.resize(450, 600)
        
        self._setup_ui()
        self._apply_styling()
    
    def _setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)
        
        # Title
        title = QLabel("Create Your Account")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setObjectName("title")
        layout.addWidget(title)
        
        # Form fields
        self._create_form_field(layout, "First Name", "firstName")
        self._create_form_field(layout, "Last Name", "lastName")
        self._create_form_field(layout, "Email", "email")
        self._create_form_field(layout, "Password", "password", password=True)
        self._create_form_field(layout, "Confirm Password", "confirmPassword", password=True)
        
        # Organization section
        org_frame = QFrame()
        org_layout = QVBoxLayout(org_frame)
        
        org_label = QLabel("Organization")
        org_label.setObjectName("fieldLabel")
        org_layout.addWidget(org_label)
        
        self.org_combo = QComboBox()
        self.org_combo.setObjectName("comboBox")
        self.org_combo.addItem("Create New Organization", "new")
        self.org_combo.addItem("Join Existing Organization", "existing")
        self.org_combo.currentTextChanged.connect(self._on_org_type_changed)
        org_layout.addWidget(self.org_combo)
        
        # Organization name field (shown when creating new)
        self.org_name_frame = QFrame()
        org_name_layout = QVBoxLayout(self.org_name_frame)
        org_name_layout.setContentsMargins(0, 10, 0, 0)
        
        org_name_label = QLabel("Organization Name")
        org_name_label.setObjectName("fieldLabel")
        org_name_layout.addWidget(org_name_label)
        
        self.org_name_input = QLineEdit()
        self.org_name_input.setObjectName("inputField")
        self.org_name_input.setPlaceholderText("Enter your organization name")
        org_name_layout.addWidget(self.org_name_input)
        
        org_layout.addWidget(self.org_name_frame)
        
        # Invitation code field (shown when joining existing)
        self.invite_frame = QFrame()
        invite_layout = QVBoxLayout(self.invite_frame)
        invite_layout.setContentsMargins(0, 10, 0, 0)
        
        invite_label = QLabel("Invitation Code")
        invite_label.setObjectName("fieldLabel")
        invite_layout.addWidget(invite_label)
        
        self.invite_input = QLineEdit()
        self.invite_input.setObjectName("inputField")
        self.invite_input.setPlaceholderText("Enter invitation code")
        invite_layout.addWidget(self.invite_input)
        
        self.invite_frame.hide()  # Hidden by default
        org_layout.addWidget(self.invite_frame)
        
        layout.addWidget(org_frame)
        
        # Terms checkbox
        self.terms_checkbox = QCheckBox("I agree to the Terms of Service and Privacy Policy")
        self.terms_checkbox.setObjectName("checkbox")
        layout.addWidget(self.terms_checkbox)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setObjectName("cancelButton")
        self.cancel_btn.clicked.connect(self.reject)
        
        self.signup_btn = QPushButton("Create Account")
        self.signup_btn.setObjectName("signupButton")
        self.signup_btn.clicked.connect(self._signup)
        self.signup_btn.setDefault(True)
        
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.signup_btn)
        layout.addLayout(button_layout)
        
        # Already have account link
        login_layout = QHBoxLayout()
        login_layout.addStretch()
        
        login_label = QLabel("Already have an account?")
        login_label.setObjectName("linkLabel")
        login_layout.addWidget(login_label)
        
        login_link = QPushButton("Sign In")
        login_link.setObjectName("linkButton")
        login_link.clicked.connect(self.reject)
        login_layout.addWidget(login_link)
        
        login_layout.addStretch()
        layout.addLayout(login_layout)
    
    def _create_form_field(self, layout, label_text, field_name, password=False):
        """Create a form field with label and input"""
        frame = QFrame()
        field_layout = QVBoxLayout(frame)
        field_layout.setContentsMargins(0, 0, 0, 0)
        
        label = QLabel(label_text)
        label.setObjectName("fieldLabel")
        field_layout.addWidget(label)
        
        input_field = QLineEdit()
        input_field.setObjectName("inputField")
        if password:
            input_field.setEchoMode(QLineEdit.EchoMode.Password)
        
        setattr(self, f"{field_name}_input", input_field)
        field_layout.addWidget(input_field)
        
        layout.addWidget(frame)
    
    def _on_org_type_changed(self, text):
        """Handle organization type change"""
        if "Create New" in text:
            self.org_name_frame.show()
            self.invite_frame.hide()
        else:
            self.org_name_frame.hide()
            self.invite_frame.show()
    
    def _signup(self):
        """Handle signup"""
        # Validate form
        if not self._validate_form():
            return
        
        try:
            # Prepare signup data
            signup_data = {
                'first_name': self.firstName_input.text().strip(),
                'last_name': self.lastName_input.text().strip(),
                'email': self.email_input.text().strip(),
                'password': self.password_input.text(),
                'organization_type': self.org_combo.currentData(),
                'organization_name': self.org_name_input.text().strip() if self.org_name_frame.isVisible() else None,
                'invitation_code': self.invite_input.text().strip() if self.invite_frame.isVisible() else None
            }
            
            # Call auth manager signup
            result = self.auth_manager.sign_up(**signup_data)
            
            if result.get('success'):
                self.signup_successful.emit(result)
                self.accept()
            else:
                self._show_error(result.get('error', 'Signup failed'))
        
        except Exception as e:
            self._show_error(str(e))
    
    def _validate_form(self):
        """Validate form data"""
        if not self.firstName_input.text().strip():
            self._show_error("First name is required")
            return False
        
        if not self.lastName_input.text().strip():
            self._show_error("Last name is required")
            return False
        
        if not self.email_input.text().strip():
            self._show_error("Email is required")
            return False
        
        if not self.password_input.text():
            self._show_error("Password is required")
            return False
        
        if self.password_input.text() != self.confirmPassword_input.text():
            self._show_error("Passwords do not match")
            return False
        
        if self.org_name_frame.isVisible() and not self.org_name_input.text().strip():
            self._show_error("Organization name is required")
            return False
        
        if self.invite_frame.isVisible() and not self.invite_input.text().strip():
            self._show_error("Invitation code is required")
            return False
        
        if not self.terms_checkbox.isChecked():
            self._show_error("You must agree to the Terms of Service")
            return False
        
        return True
    
    def _show_error(self, message):
        """Show error message (placeholder for now)"""
        # TODO: Implement proper error display
        print(f"Signup Error: {message}")
    
    def _apply_styling(self):
        """Apply glassmorphism styling"""
        self.setStyleSheet(f"""
            QDialog {{
                background: {GlassmorphismHelper.get_background_color()};
                border-radius: 15px;
                border: 1px solid rgba(255, 255, 255, 0.2);
            }}
            
            QLabel#title {{
                font-size: 24px;
                font-weight: bold;
                color: #FFFFFF;
                margin-bottom: 10px;
            }}
            
            QLabel#fieldLabel {{
                font-size: 14px;
                color: #FFFFFF;
                margin-bottom: 5px;
                font-weight: 500;
            }}
            
            QLabel#linkLabel {{
                font-size: 14px;
                color: rgba(255, 255, 255, 0.8);
            }}
            
            QLineEdit#inputField {{
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
                color: #FFFFFF;
                min-height: 20px;
            }}
            
            QLineEdit#inputField:focus {{
                border: 2px solid rgba(0, 123, 255, 0.8);
                background: rgba(255, 255, 255, 0.15);
            }}
            
            QComboBox#comboBox {{
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
                color: #FFFFFF;
                min-height: 20px;
            }}
            
            QComboBox#comboBox:focus {{
                border: 2px solid rgba(0, 123, 255, 0.8);
            }}
            
            QComboBox#comboBox::drop-down {{
                border: none;
                background: transparent;
            }}
            
            QComboBox#comboBox::down-arrow {{
                border: none;
                background: transparent;
            }}
            
            QCheckBox#checkbox {{
                color: #FFFFFF;
                font-size: 14px;
            }}
            
            QCheckBox#checkbox::indicator {{
                width: 18px;
                height: 18px;
                border-radius: 3px;
                border: 1px solid rgba(255, 255, 255, 0.3);
                background: rgba(255, 255, 255, 0.1);
            }}
            
            QCheckBox#checkbox::indicator:checked {{
                background: rgba(0, 123, 255, 0.6);
                border: 1px solid rgba(0, 123, 255, 0.8);
            }}
            
            QPushButton {{
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: 500;
                color: #FFFFFF;
                min-width: 120px;
            }}
            
            QPushButton:hover {{
                background: rgba(255, 255, 255, 0.2);
                border: 1px solid rgba(255, 255, 255, 0.4);
            }}
            
            QPushButton:pressed {{
                background: rgba(255, 255, 255, 0.3);
            }}
            
            QPushButton#signupButton {{
                background: rgba(0, 123, 255, 0.4);
                border: 1px solid rgba(0, 123, 255, 0.6);
            }}
            
            QPushButton#signupButton:hover {{
                background: rgba(0, 123, 255, 0.5);
                border: 1px solid rgba(0, 123, 255, 0.7);
            }}
            
            QPushButton#signupButton:pressed {{
                background: rgba(0, 123, 255, 0.6);
            }}
            
            QPushButton#linkButton {{
                background: transparent;
                border: none;
                color: rgba(0, 123, 255, 0.9);
                font-weight: 600;
                text-decoration: underline;
                padding: 5px;
                min-width: auto;
            }}
            
            QPushButton#linkButton:hover {{
                color: rgba(0, 123, 255, 1.0);
            }}
        """)
