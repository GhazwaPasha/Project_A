"""
Bottom Bar Component for Main Window
Contains workspace switcher, status information, and other useful widgets
"""
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, 
    QPushButton, QFrame, QSizePolicy, QSpacerItem
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QFont
from .styles import GlassmorphismHelper, ModernStyles
from .mica_effect import MicaEffect
from ..common import ResponsiveHelper
import os

class BottomBar(QWidget):
    """
    Modern bottom bar for the main window containing workspace switcher and status info
    """
    
    def __init__(self, auth_manager=None, session_manager=None, parent=None):
        super().__init__(parent)
        self.auth_manager = auth_manager
        self.session_manager = session_manager
        
        self._setup_ui()
        self._apply_styling()
    
    def _setup_ui(self):
        """Setup the bottom bar UI"""
        # Main horizontal layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)  # Reduced margins
        layout.setSpacing(8)  # Reduced spacing
        
        # Add stretch to push workspace switcher to the right
        layout.addStretch()
        
        # Right section - Workspace switcher
        self._create_right_section(layout)
        
    def _create_right_section(self, layout):
        """Create right section with workspace switcher"""
        right_widget = QWidget()
        right_layout = QHBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)
        
        if self.auth_manager and self.session_manager:
            # Import and create workspace switcher if in multi-tenant mode
            try:
                from .workspace_switcher import WorkspaceSwitcher
                self.workspace_switcher = WorkspaceSwitcher(
                    auth_manager=self.auth_manager,
                    session_manager=self.session_manager,
                    parent=self
                )
                right_layout.addWidget(self.workspace_switcher)
            except ImportError:
                # Fallback if workspace switcher not available
                workspace_label = QLabel("🏢 Single Tenant Mode")
                workspace_label.setObjectName("WorkspaceLabel")
                workspace_label.setStyleSheet("""
                    background: rgba(255, 255, 255, 0.08);
                    border: 1px solid rgba(0, 0, 0, 0.3);
                    border-radius: 8px;
                    padding: 4px 8px;
                """)
                right_layout.addWidget(workspace_label)
            except Exception:
                # Fallback on any error
                workspace_label = QLabel("🏢 Error Loading Switcher")
                workspace_label.setObjectName("WorkspaceLabel")
                workspace_label.setStyleSheet("""
                    background: rgba(255, 255, 255, 0.08);
                    border: 1px solid rgba(0, 0, 0, 0.3);
                    border-radius: 8px;
                    padding: 4px 8px;
                """)
                right_layout.addWidget(workspace_label)
        else:
            # Single tenant mode indicator
            workspace_label = QLabel("🏢 Workspace")
            workspace_label.setObjectName("WorkspaceLabel")
            workspace_label.setToolTip("Single tenant workspace")
            workspace_label.setStyleSheet("""
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(0, 0, 0, 0.3);
                border-radius: 8px;
                padding: 4px 8px;
            """)
            right_layout.addWidget(workspace_label)
        
        layout.addWidget(right_widget)
    
    def _apply_styling(self):
        """Apply modern styling to the bottom bar"""
        try:
            MicaEffect.apply_mica(self, dark_mode=True)
            GlassmorphismHelper.apply_main_container_effect(self)
        except Exception:
            # Fallback if styling fails
            pass
        
        # Set fixed height for the bottom bar
        self.setFixedHeight(36)
        
        # Make sure the widget is visible
        self.setVisible(True)
        self.show()
        
        self.setStyleSheet(f"""
            BottomBar {{
                background: rgba(30, 30, 30, 0.98);
                border-top: 1px solid rgba(255, 255, 255, 0.1);
                padding: 0px;
                min-height: 36px;
                max-height: 36px;
            }}
            
            QLabel#WorkspaceLabel {{
                color: #FFFFFF;
                font-size: {ResponsiveHelper.scale_size(12, 11, 13)}px;
                font-weight: 600;
                padding: 4px 12px;
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(0, 0, 0, 0.3);
                border-radius: 8px;
            }}
        """)
        
    def refresh_workspace_info(self):
        """Refresh workspace switcher if available"""
        if hasattr(self, 'workspace_switcher'):
            self.workspace_switcher.refresh_workspaces()
