"""
Bottom Bar Component for Main Window
Contains workspace switcher, status information, and other useful widgets
"""
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, 
                            QFrame, QSizePolicy, QSpacerItem)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QIcon, QFont
from .styles import GlassmorphismHelper, ModernStyles
from .mica_effect import MicaEffect
from ..common import ResponsiveHelper
import os
from datetime import datetime

class BottomBar(QWidget):
    """
    Modern bottom bar for the main window containing workspace switcher and status info
    """
    
    def __init__(self, auth_manager=None, session_manager=None, parent=None):
        super().__init__(parent)
        self.auth_manager = auth_manager
        self.session_manager = session_manager
        
        # Debug output to check if authentication context is available
        print(f"🔍 BottomBar Debug:")
        print(f"   auth_manager: {auth_manager is not None}")
        print(f"   session_manager: {session_manager is not None}")
        if auth_manager:
            print(f"   auth_manager type: {type(auth_manager)}")
        if session_manager:
            print(f"   session_manager type: {type(session_manager)}")
        
        self._setup_ui()
        self._apply_styling()
        self._setup_timer()
        
    def _setup_ui(self):
        """Setup the bottom bar UI"""
        # Main horizontal layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(16)
        
        # Left section - Status info
        self._create_left_section(layout)
        
        # Center section - Workspace switcher (if available)
        self._create_center_section(layout)
        
        # Right section - Additional info
        self._create_right_section(layout)
        
    def _create_left_section(self, layout):
        """Create left section with status info"""
        left_widget = QWidget()
        left_layout = QHBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(12)
        
        # Connection status indicator
        self.connection_status = QLabel()
        self.connection_status.setObjectName("StatusLabel")
        self._update_connection_status()
        left_layout.addWidget(self.connection_status)
        
        # Database status
        self.db_status = QLabel("💾 Local DB")
        self.db_status.setObjectName("StatusLabel")
        self.db_status.setToolTip("Database connection status")
        left_layout.addWidget(self.db_status)
        
        layout.addWidget(left_widget)
        
    def _create_center_section(self, layout):
        """Create center section with workspace switcher"""
        # Add stretch to push center content to the middle
        layout.addStretch()
        
        center_widget = QWidget()
        center_layout = QHBoxLayout(center_widget)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(8)
        
        print(f"🔍 BottomBar Center Section Debug:")
        print(f"   auth_manager exists: {self.auth_manager is not None}")
        print(f"   session_manager exists: {self.session_manager is not None}")
        
        if self.auth_manager and self.session_manager:
            print("   Creating WorkspaceSwitcher...")
            # Import and create workspace switcher if in multi-tenant mode
            try:
                from .workspace_switcher import WorkspaceSwitcher
                self.workspace_switcher = WorkspaceSwitcher(
                    auth_manager=self.auth_manager,
                    session_manager=self.session_manager,
                    parent=self
                )
                center_layout.addWidget(self.workspace_switcher)
                print("   ✅ WorkspaceSwitcher created successfully!")
            except ImportError as e:
                print(f"   ❌ ImportError: {e}")
                # Fallback if workspace switcher not available
                workspace_label = QLabel("🏢 Single Tenant Mode")
                workspace_label.setObjectName("WorkspaceLabel")
                center_layout.addWidget(workspace_label)
            except Exception as e:
                print(f"   ❌ Exception creating WorkspaceSwitcher: {e}")
                # Fallback on any error
                workspace_label = QLabel("🏢 Error Loading Switcher")
                workspace_label.setObjectName("WorkspaceLabel")
                center_layout.addWidget(workspace_label)
        else:
            print("   Using single tenant mode indicator...")
            # Single tenant mode indicator
            workspace_label = QLabel("📊 AI Accountant")
            workspace_label.setObjectName("WorkspaceLabel")
            workspace_label.setToolTip("Running in single-tenant mode")
            center_layout.addWidget(workspace_label)
        
        layout.addWidget(center_widget)
        layout.addStretch()
        
    def _create_right_section(self, layout):
        """Create right section with additional info"""
        right_widget = QWidget()
        right_layout = QHBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(12)
        
        # Current time
        self.time_label = QLabel()
        self.time_label.setObjectName("TimeLabel")
        self._update_time()
        right_layout.addWidget(self.time_label)
        
        # User info (if available)
        if self.auth_manager and hasattr(self.auth_manager, 'current_user') and self.auth_manager.current_user:
            user_email = getattr(self.auth_manager.current_user, 'email', 'User')
            user_label = QLabel(f"👤 {user_email}")
            user_label.setObjectName("UserLabel")
            user_label.setToolTip(f"Signed in as {user_email}")
            right_layout.addWidget(user_label)
        
        layout.addWidget(right_widget)
        
    def _apply_styling(self):
        """Apply modern styling to the bottom bar"""
        MicaEffect.apply_mica(self, dark_mode=True)
        GlassmorphismHelper.apply_main_container_effect(self)
        
        self.setStyleSheet(f"""
            BottomBar {{
                background: rgba(30, 30, 30, 0.95);
                border-top: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 0px;
                min-height: 40px;
                max-height: 40px;
            }}
            
            QLabel#StatusLabel {{
                color: #4CAF50;
                font-size: {ResponsiveHelper.scale_size(11, 10, 12)}px;
                font-weight: 500;
                padding: 2px 6px;
                background: rgba(76, 175, 80, 0.1);
                border: 1px solid rgba(76, 175, 80, 0.3);
                border-radius: 4px;
            }}
            
            QLabel#WorkspaceLabel {{
                color: #FFFFFF;
                font-size: {ResponsiveHelper.scale_size(12, 11, 13)}px;
                font-weight: 600;
                padding: 4px 12px;
                background: rgba(74, 144, 226, 0.2);
                border: 1px solid rgba(74, 144, 226, 0.4);
                border-radius: 6px;
            }}
            
            QLabel#TimeLabel {{
                color: #CCCCCC;
                font-size: {ResponsiveHelper.scale_size(11, 10, 12)}px;
                font-weight: 400;
                padding: 2px 6px;
            }}
            
            QLabel#UserLabel {{
                color: #FFFFFF;
                font-size: {ResponsiveHelper.scale_size(11, 10, 12)}px;
                font-weight: 500;
                padding: 2px 8px;
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 4px;
            }}
        """)
        
    def _setup_timer(self):
        """Setup timer for updating dynamic content"""
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_dynamic_content)
        self.timer.start(30000)  # Update every 30 seconds
        
    def _update_dynamic_content(self):
        """Update time and other dynamic content"""
        self._update_time()
        self._update_connection_status()
        
    def _update_time(self):
        """Update the time display"""
        current_time = datetime.now().strftime("%H:%M")
        self.time_label.setText(f"🕐 {current_time}")
        
    def _update_connection_status(self):
        """Update connection status indicator"""
        if self.auth_manager and hasattr(self.auth_manager, 'current_user') and self.auth_manager.current_user:
            self.connection_status.setText("🟢 Connected")
            self.connection_status.setToolTip("Connected to Supabase")
        else:
            self.connection_status.setText("🔵 Local")
            self.connection_status.setToolTip("Running in local mode")
            
    def refresh_workspace_info(self):
        """Refresh workspace switcher if available"""
        if hasattr(self, 'workspace_switcher'):
            self.workspace_switcher.refresh_workspaces()
            
    def update_user_info(self, user_email=None):
        """Update user information display"""
        # This can be called when user signs in/out
        # For now, we'll refresh the entire right section
        self._setup_ui()
