"""
Modern login window with your existing styling
"""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QLineEdit, QCheckBox, QFrame, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QIcon, QPixmap

from ..common import ResponsiveHelper
from ..components.styles import ModernStyles, GlassmorphismHelper
from ..components.mica_effect import MicaEffect
import os

class LoginWindow(QDialog):
    """Modern login window with glassmorphism styling"""
    
    login_successful = pyqtSignal(dict, list)  # user_data, organizations
    signup_requested = pyqtSignal()
    
    def __init__(self, auth_manager):
        super().__init__()
        self.auth_manager = auth_manager
        self.setWindowTitle("AI Accountant - Sign In")
        self.setModal(True)
        self._setup_ui()
        self._apply_styling()
        
    def _setup_ui(self):
        """Setup the login UI"""
        # Responsive dialog sizing
        dialog_width = ResponsiveHelper.scale_size(450, 400, 500)
        dialog_height = ResponsiveHelper.scale_size(600, 550, 650)
        self.setFixedSize(dialog_width, dialog_height)
        
        # Main layout
        layout = QVBoxLayout(self)
        margins = ResponsiveHelper.scale_size(40, 32, 48)
        layout.setContentsMargins(margins, margins, margins, margins)
        layout.setSpacing(ResponsiveHelper.scale_size(24, 20, 28))
        
        # Header section
        self._create_header(layout)
        
        # Login form
        self._create_login_form(layout)
        
        # Footer
        self._create_footer(layout)
        
        layout.addStretch()
    
    def _create_header(self, layout):
        """Create header with logo and title"""
        header_layout = QVBoxLayout()
        header_layout.setSpacing(ResponsiveHelper.scale_size(16, 12, 20))
        
        # Logo
        logo_label = QLabel()
        logo_path = os.path.join("assets", "icons", "dashboard_modern.svg")
        if os.path.exists(logo_path):
            logo_label.setPixmap(QIcon(logo_path).pixmap(64, 64))
        else:
            logo_label.setText("🧮")
            logo_label.setStyleSheet(f"font-size: {ResponsiveHelper.scale_size(48, 40, 56)}px;")
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(logo_label)
        
        # Title
        title = QLabel("AI Accountant")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"""
            QLabel {{
                color: white;
                font-size: {ResponsiveHelper.scale_size(28, 24, 32)}px;
                font-weight: 600;
                background: transparent;
                margin-bottom: {ResponsiveHelper.scale_size(8, 6, 10)}px;
            }}
        """)
        header_layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel("Sign in to your account")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet(f"""
            QLabel {{
                color: rgba(255, 255, 255, 0.7);
                font-size: {ResponsiveHelper.scale_size(16, 14, 18)}px;
                background: transparent;
            }}
        """)
        header_layout.addWidget(subtitle)
        
        layout.addLayout(header_layout)
    
    def _create_login_form(self, layout):
        """Create login form fields"""
        form_layout = QVBoxLayout()
        form_layout.setSpacing(ResponsiveHelper.scale_size(20, 16, 24))
        
        # Email field
        email_label = QLabel("Email Address")
        email_label.setStyleSheet(self._get_label_style())
        form_layout.addWidget(email_label)
        
        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("Enter your email address")
        self.email_edit.setStyleSheet(self._get_input_style())
        form_layout.addWidget(self.email_edit)
        
        # Password field
        password_label = QLabel("Password")
        password_label.setStyleSheet(self._get_label_style())
        form_layout.addWidget(password_label)
        
        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("Enter your password")
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setStyleSheet(self._get_input_style())
        form_layout.addWidget(self.password_edit)
        
        # Options row
        options_layout = QHBoxLayout()
        
        # Remember me checkbox
        self.remember_check = QCheckBox("Remember me")
        self.remember_check.setStyleSheet(self._get_checkbox_style())
        options_layout.addWidget(self.remember_check)
        
        options_layout.addStretch()
        
        # Forgot password link
        forgot_btn = QPushButton("Forgot password?")
        forgot_btn.setStyleSheet(self._get_link_style())
        forgot_btn.clicked.connect(self._forgot_password)
        options_layout.addWidget(forgot_btn)
        
        form_layout.addLayout(options_layout)
        
        # Sign in button
        self.signin_btn = QPushButton("Sign In")
        self.signin_btn.setStyleSheet(self._get_primary_button_style())
        self.signin_btn.clicked.connect(self._handle_signin)
        form_layout.addWidget(self.signin_btn)
        
        # Connect enter key
        self.password_edit.returnPressed.connect(self._handle_signin)
        
        layout.addLayout(form_layout)
    
    def _create_footer(self, layout):
        """Create footer with signup link"""
        footer_layout = QHBoxLayout()
        footer_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        signup_label = QLabel("Don't have an account?")
        signup_label.setStyleSheet(f"""
            QLabel {{
                color: rgba(255, 255, 255, 0.7);
                font-size: {ResponsiveHelper.scale_size(14, 12, 16)}px;
                background: transparent;
            }}
        """)
        footer_layout.addWidget(signup_label)
        
        signup_btn = QPushButton("Sign up")
        signup_btn.setStyleSheet(self._get_link_style())
        signup_btn.clicked.connect(self._handle_signup)
        footer_layout.addWidget(signup_btn)
        
        layout.addLayout(footer_layout)
    
    def _handle_signin(self):
        """Handle sign in button click"""
        email = self.email_edit.text().strip()
        password = self.password_edit.text()
        
        if not email or not password:
            self._show_error("Please enter both email and password")
            return
          # Disable button and show loading
        self.signin_btn.setText("Signing in...")
        self.signin_btn.setEnabled(False)
        
        # Perform authentication
        QTimer.singleShot(100, lambda: self._perform_signin(email, password))
    
    def _perform_signin(self, email: str, password: str):
        """Perform actual sign in"""
        result = self.auth_manager.sign_in(email, password)
        
        if result["success"]:
            user_obj = result.get("user", {})
            organizations = result.get("organizations", [])
            
            # Convert User object to dictionary if needed
            if hasattr(user_obj, '__dict__'):
                # If it's a User object, convert to dict
                user_dict = {
                    'id': str(user_obj.id) if hasattr(user_obj, 'id') else '',
                    'email': user_obj.email if hasattr(user_obj, 'email') else '',
                    'created_at': str(user_obj.created_at) if hasattr(user_obj, 'created_at') else '',
                    'updated_at': str(user_obj.updated_at) if hasattr(user_obj, 'updated_at') else '',
                    'email_confirmed_at': str(user_obj.email_confirmed_at) if hasattr(user_obj, 'email_confirmed_at') else None,
                    'phone': user_obj.phone if hasattr(user_obj, 'phone') else None,
                    'user_metadata': user_obj.user_metadata if hasattr(user_obj, 'user_metadata') else {},
                    'app_metadata': user_obj.app_metadata if hasattr(user_obj, 'app_metadata') else {}
                }
            else:
                # It's already a dict
                user_dict = user_obj if isinstance(user_obj, dict) else {}
            
            self.login_successful.emit(user_dict, organizations)
            self.accept()
        else:
            self._show_error(result.get("error", "Sign in failed"))
            self.signin_btn.setText("Sign In")
            self.signin_btn.setEnabled(True)
    
    def _handle_signup(self):
        """Handle signup button click"""
        self.signup_requested.emit()
        self.close()
    
    def _forgot_password(self):
        """Handle forgot password"""
        # TODO: Implement password reset
        self._show_info("Password reset feature coming soon!")
    
    def _show_error(self, message: str):
        """Show error message"""
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle("Sign In Error")
        msg.setText(message)
        msg.setStyleSheet(ModernStyles.get_complete_stylesheet())
        msg.exec()
    
    def _show_info(self, message: str):
        """Show info message"""
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowTitle("Information")
        msg.setText(message)
        msg.setStyleSheet(ModernStyles.get_complete_stylesheet())
        msg.exec()
    
    def _apply_styling(self):
        """Apply glassmorphism styling"""
        # Apply Mica effect
        MicaEffect.apply_mica(self, dark_mode=True)
        GlassmorphismHelper.apply_main_container_effect(self)
        
        # Main dialog styling
        self.setStyleSheet(f"""
            QDialog {{
                background: rgba(0, 0, 0, 0.3);
                border-radius: {ResponsiveHelper.scale_size(16, 12, 20)}px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }}
        """)
    
    def _get_label_style(self):
        """Get label styling"""
        return f"""
            QLabel {{
                color: rgba(255, 255, 255, 0.9);
                font-size: {ResponsiveHelper.scale_size(14, 12, 16)}px;
                font-weight: 500;
                background: transparent;
                margin-bottom: {ResponsiveHelper.scale_size(6, 4, 8)}px;
            }}
        """
    
    def _get_input_style(self):
        """Get input field styling"""
        padding = ResponsiveHelper.scale_size(16, 12, 20)
        font_size = ResponsiveHelper.scale_size(16, 14, 18)
        return f"""
            QLineEdit {{
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: {ResponsiveHelper.scale_size(8, 6, 10)}px;
                padding: {padding}px;
                color: white;
                font-size: {font_size}px;
                outline: none;
            }}
            QLineEdit:focus {{
                background: rgba(255, 255, 255, 0.15);
                border-color: rgba(0, 120, 215, 0.8);
                outline: none;
            }}
            QLineEdit::placeholder {{
                color: rgba(255, 255, 255, 0.5);
            }}
        """
    
    def _get_checkbox_style(self):
        """Get checkbox styling"""
        return f"""
            QCheckBox {{
                color: rgba(255, 255, 255, 0.8);
                font-size: {ResponsiveHelper.scale_size(14, 12, 16)}px;
                spacing: {ResponsiveHelper.scale_size(8, 6, 10)}px;
            }}
            QCheckBox::indicator {{
                width: {ResponsiveHelper.scale_size(18, 16, 20)}px;
                height: {ResponsiveHelper.scale_size(18, 16, 20)}px;
                border: 1px solid rgba(255, 255, 255, 0.4);
                border-radius: {ResponsiveHelper.scale_size(3, 2, 4)}px;
                background: rgba(255, 255, 255, 0.1);
            }}
            QCheckBox::indicator:checked {{
                background: rgba(0, 120, 215, 0.8);
                border-color: rgba(0, 120, 215, 1.0);
            }}
        """
    
    def _get_primary_button_style(self):
        """Get primary button styling"""
        padding_v = ResponsiveHelper.scale_size(16, 12, 20)
        font_size = ResponsiveHelper.scale_size(16, 14, 18)
        return f"""
            QPushButton {{
                background: rgba(0, 120, 215, 0.8);
                border: 1px solid rgba(0, 120, 215, 1.0);
                border-radius: {ResponsiveHelper.scale_size(8, 6, 10)}px;
                padding: {padding_v}px;
                color: white;
                font-size: {font_size}px;
                font-weight: 600;
                outline: none;
            }}
            QPushButton:hover {{
                background: rgba(0, 120, 215, 0.9);
                outline: none;
            }}
            QPushButton:pressed {{
                background: rgba(0, 120, 215, 0.7);
                outline: none;
            }}
            QPushButton:disabled {{
                background: rgba(255, 255, 255, 0.1);
                border-color: rgba(255, 255, 255, 0.2);
                color: rgba(255, 255, 255, 0.5);
            }}
        """
    
    def _get_link_style(self):
        """Get link button styling"""
        return f"""
            QPushButton {{
                background: transparent;
                border: none;
                color: rgba(0, 120, 215, 1.0);
                font-size: {ResponsiveHelper.scale_size(14, 12, 16)}px;
                text-decoration: underline;
                outline: none;
            }}
            QPushButton:hover {{
                color: rgba(0, 120, 215, 0.8);
                outline: none;
            }}
            QPushButton:pressed {{
                color: rgba(0, 120, 215, 0.6);
                outline: none;
            }}
        """
