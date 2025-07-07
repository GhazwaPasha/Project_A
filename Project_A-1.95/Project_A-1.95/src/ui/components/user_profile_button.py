"""
User Profile Button - Round Profile Picture with Dropdown
Shows user's profile picture (if available) or placeholder with sign out option
"""
from PyQt6.QtWidgets import QWidget, QPushButton, QMenu, QHBoxLayout
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QPixmap, QIcon, QPainterPath
from ..common import ResponsiveHelper
import logging
import os

class UserProfileButton(QWidget):
    """Round user profile button with dropdown menu"""
    
    # Signal emitted when user wants to sign out
    sign_out_requested = pyqtSignal()
    
    def __init__(self, session_manager=None, parent=None):
        super().__init__(parent)
        self.setObjectName("UserProfileButton")
        self.setFixedSize(40, 32)  # Match window control button size exactly
        self.setToolTip("User Profile")
        
        self.session_manager = session_manager
        self.logger = logging.getLogger(__name__)
        
        # Setup the main button
        self._setup_button()
        
        # Load user profile data
        self._load_user_profile()
        
    def _setup_button(self):
        """Setup the main profile button"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.profile_btn = QPushButton()
        self.profile_btn.setObjectName("ProfileButton")
        self.profile_btn.setFixedSize(40, 32)
        self.profile_btn.clicked.connect(self._show_profile_menu)
        
        # Apply styling to match dashboard cards with 6px border-radius
        self.profile_btn.setStyleSheet(f"""
            QPushButton#ProfileButton {{
                background: transparent;
                border: none;
                border-radius: 6px;
                padding: 0px;
                margin: 0px;
            }}
            QPushButton#ProfileButton:hover {{
                background: rgba(255, 255, 255, 0.12);
                border: 1px solid rgba(100, 181, 246, 0.3);
                border-radius: 6px;
            }}
            QPushButton#ProfileButton:pressed {{
                background: rgba(255, 255, 255, 0.15);
                border: 1px solid rgba(100, 181, 246, 0.5);
                border-radius: 6px;
            }}
        """)
        
        layout.addWidget(self.profile_btn)
        
    def _load_user_profile(self):
        """Load user profile data and set profile picture"""
        if not self.session_manager:
            self._set_placeholder_icon()
            return
            
        try:
            # Get user profile from auth_manager
            user_data = self.session_manager.auth_manager.get_user_profile()
            if user_data:
                user_email = user_data.get('email', 'User')
                full_name = user_data.get('full_name', '').strip()
                
                if full_name:
                    self.setToolTip(f"Profile: {full_name}")
                else:
                    self.setToolTip(f"Profile: {user_email}")
                
                # Check if user has a profile picture
                profile_picture_url = user_data.get('avatar_url') or user_data.get('profile_picture')
                
                if profile_picture_url:
                    self._load_profile_picture(profile_picture_url)
                else:
                    self._set_placeholder_icon()
            else:
                self._set_placeholder_icon()
                
        except Exception as e:
            self.logger.warning(f"Failed to load user profile: {e}")
            self._set_placeholder_icon()
    
    def _load_profile_picture(self, url):
        """Load profile picture from URL (for future implementation)"""
        # For now, just use initials placeholder - in the future this could load from URL
        self.logger.info(f"Profile picture URL found: {url}")
        # TODO: Implement actual profile picture loading from URL
        # For now, fall back to initials
        self._set_placeholder_icon()
    
    def _set_placeholder_icon(self):
        """Set a placeholder user icon with user initial matching AI status bar styling"""
        # Get user initial (single character)
        initial = self._get_user_initial()
        self.logger.debug(f"Setting placeholder icon with initial: '{initial}'")
        
        # Create a round placeholder icon
        pixmap = QPixmap(24, 24)  # 24x24 for good centering in 40x32 button
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        
        # Draw rounded rectangle background - match AI status bar styling
        # Convert rgba to QColor - 0.08 alpha on white = approximately RGB(20, 20, 20) on dark background
        background_color = QColor(255, 255, 255, int(255 * 0.08))  # Semi-transparent white
        border_color = QColor(0, 0, 0, int(255 * 0.3))  # Semi-transparent black border
        
        painter.setBrush(QBrush(background_color))
        painter.setPen(QPen(border_color, 1))
        
        # Draw rounded rectangle instead of circle to match AI status bar
        painter.drawRoundedRect(2, 2, 20, 20, 6, 6)  # 6px border radius to match the visual style
        
        # Draw initial in the center (always show initial if available)
        if initial:
            painter.setPen(QPen(QColor(255, 255, 255)))  # White text
            font = painter.font()
            font.setPointSize(10)  # Good size for single character
            font.setBold(True)     # Bold as specified
            font.setFamily('Segoe UI')  # Match AI status bar font
            painter.setFont(font)
            
            # Use Qt's built-in text alignment for perfect centering
            # The drawable area is the rounded rectangle from (2,2) to (22,22)
            text_rect = painter.fontMetrics().boundingRect(2, 2, 20, 20, Qt.AlignmentFlag.AlignCenter, initial)
            
            # Draw text centered in the rectangle
            painter.drawText(2, 2, 20, 20, Qt.AlignmentFlag.AlignCenter, initial)
        
        painter.end()
        
        # Set the icon to the button
        icon = QIcon(pixmap)
        self.profile_btn.setIcon(icon)
        self.profile_btn.setIconSize(pixmap.size())
    
    def _get_user_initial(self):
        """Extract the first initial from user's name"""
        if not self.session_manager:
            self.logger.debug("No session manager available for initial")
            return ""
        
        try:
            # Get user profile from auth_manager
            user_data = self.session_manager.auth_manager.get_user_profile()
            if not user_data:
                self.logger.debug("No user data available for initial")
                return ""
            
            self.logger.debug(f"User data for initial: {user_data.keys()}")
            
            # Try to get first initial from first_name
            first_name = user_data.get('first_name', '').strip()
            if first_name and first_name[0].isalpha():
                initial = first_name[0].upper()
                return initial
            
            # Fallback to full_name
            full_name = user_data.get('full_name', '').strip()
            if full_name:
                # Extract first part of full name
                name_parts = full_name.split()
                if name_parts and name_parts[0] and name_parts[0][0].isalpha():
                    initial = name_parts[0][0].upper()
                    return initial
            
            # Last fallback to email
            email = user_data.get('email', '').strip()
            if email and email[0].isalpha():
                initial = email[0].upper()
                return initial
            
            return ""
            
        except Exception as e:
            self.logger.warning(f"Failed to get user initial: {e}")
            return ""
    
    def _show_profile_menu(self):
        """Show the profile dropdown menu"""
        menu = QMenu(self)
        menu.setObjectName("ProfileMenu")
        
        # Style the menu to match the app theme with responsive border-radius
        border_radius = ResponsiveHelper.scale_size(10, 8, 12)
        item_radius = ResponsiveHelper.scale_size(5, 4, 6)
        menu.setStyleSheet(f"""
            QMenu#ProfileMenu {{
                background: rgba(30, 30, 30, 0.98);
                border: 1px solid rgba(0, 0, 0, 0.3);
                border-radius: {border_radius}px;
                padding: 4px;
                color: white;
                font-family: 'Segoe UI', system-ui, sans-serif;
                font-size: 12px;
            }}
            QMenu#ProfileMenu::item {{
                color: white;
                background: transparent;
                padding: 8px 16px;
                border-radius: {item_radius}px;
                margin: 2px;
                font-weight: 500;
            }}
            QMenu#ProfileMenu::item:selected {{
                background: rgba(255, 255, 255, 0.12);
                border: 1px solid rgba(100, 181, 246, 0.3);
            }}
            QMenu#ProfileMenu::item:pressed {{
                background: rgba(255, 255, 255, 0.15);
            }}
        """)
        
        # Add user info (if available)
        if self.session_manager:
            try:
                user_data = self.session_manager.auth_manager.get_user_profile()
                if user_data:
                    full_name = user_data.get('full_name', '').strip()
                    user_email = user_data.get('email', 'Unknown User')
                    
                    # Show name if available, otherwise email
                    if full_name:
                        user_info_action = menu.addAction(f"👤 {full_name}")
                    else:
                        user_info_action = menu.addAction(f"📧 {user_email}")
                    
                    user_info_action.setEnabled(False)
                    menu.addSeparator()
            except Exception as e:
                self.logger.warning(f"Failed to get user info for menu: {e}")
        
        # Add sign out action
        sign_out_action = menu.addAction("🚪 Sign Out")
        sign_out_action.triggered.connect(self._handle_sign_out)
        
        # Show menu below the button
        button_rect = self.profile_btn.geometry()
        menu_pos = self.mapToGlobal(button_rect.bottomLeft())
        menu.exec(menu_pos)
    
    def _handle_sign_out(self):
        """Handle sign out request"""
        self.logger.info("Sign out requested by user")
        self.sign_out_requested.emit()
    
    def update_user_profile(self, session_manager):
        """Update the profile button when session changes"""
        print(f"🔍 Profile Update: Session manager provided: {session_manager is not None}")
        self.session_manager = session_manager
        if session_manager:
            try:
                user_data = session_manager.auth_manager.get_user_profile()
                print(f"🔍 Profile Update: User data available: {user_data is not None}")
                if user_data:
                    print(f"🔍 Profile Update: User email: {user_data.get('email', 'No email')}")
                    print(f"🔍 Profile Update: Available keys: {list(user_data.keys())}")
            except Exception as e:
                print(f"🔍 Profile Update: Error getting user data: {e}")
        self.logger.info("Updating user profile with new session manager")
        self._load_user_profile()
