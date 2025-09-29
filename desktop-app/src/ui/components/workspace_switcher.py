"""
Workspace Switcher Component
Allows users to switch between personal workspace and organizations
"""
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, 
                            QComboBox, QFrame, QSizePolicy, QMenu, QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QFont, QPalette, QColor
from .styles import GlassmorphismHelper
from .mica_effect import MicaEffect
from ..common import ResponsiveHelper
from ..common import ResponsiveHelper
import os

class WorkspaceSwitcher(QWidget):
    """
    A compact workspace switcher component for the bottom center of main window
    """
    workspace_changed = pyqtSignal(str, str)  # organization_id, organization_name
    
    def __init__(self, auth_manager=None, session_manager=None, parent=None):
        super().__init__(parent)
        self.auth_manager = auth_manager
        self.session_manager = session_manager
        self.workspaces = []
        self.current_workspace = None
        
        self._setup_ui()
        self._apply_styling()
        self._load_workspaces()
        
    def mousePressEvent(self, event):
        """Handle mouse press to show workspace menu"""
        if event.button() == Qt.MouseButton.LeftButton:
            self._show_workspace_menu()
        super().mousePressEvent(event)
        
    def _setup_ui(self):
        """Setup the workspace switcher UI as a single clickable component"""
        # Main horizontal layout
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(8, 4, 8, 4)
        self.layout.setSpacing(0)  # No spacing needed for single component
        
        # Set fixed size for consistency - increased size
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(32)  # Increased from 28 to 32px
        self.setMinimumWidth(140)  # Increased from 120 to 140px  
        self.setMaximumWidth(240)  # Increased from 200 to 240px
        
        # Make the entire widget clickable
        self.setToolTip("Click to switch workspace")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Current workspace label - this will be the only visible component
        self.workspace_label = QLabel("LOADING...")
        self.workspace_label.setObjectName("WorkspaceLabel")
        self.workspace_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.workspace_label)
        
    def _apply_styling(self):
        """Apply styling to match user profile button exactly"""
        # Use 6px border-radius to match dashboard cards and other UI components
        self.setStyleSheet(f"""
            QLabel#WorkspaceLabel {{
                color: white;
                font-size: 12px;
                font-family: 'Segoe UI', system-ui, sans-serif;
                font-weight: bold;
                text-align: center;
                text-transform: uppercase;
                padding: 6px 16px;
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(0, 0, 0, 0.3);
                border-radius: 6px;
                margin: 0px;
            }}
            
            QLabel#WorkspaceLabel:hover {{
                background: rgba(255, 255, 255, 0.12);
                border: 1px solid rgba(100, 181, 246, 0.3);
            }}
            
            QLabel#WorkspaceLabel:disabled {{
                color: rgba(255, 255, 255, 0.4);
                background: rgba(255, 255, 255, 0.04);
                border: 1px solid rgba(0, 0, 0, 0.2);
            }}
        """)

    def _load_workspaces(self):
        """Load available workspaces from session manager"""
        try:
            if not self.session_manager:
                self.workspace_label.setText("PERSONAL WORKSPACE")
                return
                
            if not self.auth_manager or not self.auth_manager.current_user:
                self.workspace_label.setText("NOT LOGGED IN")
                return
                
            # Get workspaces from session manager
            self.workspaces = self.session_manager.get_available_organizations()
            
            if not self.workspaces:
                self.workspace_label.setText("PERSONAL WORKSPACE")
                return
                
            # Get current workspace
            current_org = self.session_manager.get_current_organization()
            if current_org:
                self.current_workspace = current_org
                self.workspace_label.setText(current_org.get('name', 'Unknown').upper())
            else:
                # Set first organization as active if none is selected
                first_org = self.workspaces[0]
                if self.session_manager.set_active_organization(first_org['id']):
                    self.current_workspace = first_org
                    self.workspace_label.setText(first_org['name'].upper())
                else:
                    self.workspace_label.setText("SELECT ORGANIZATION")
                
        except Exception as e:
            print(f"Error loading workspaces: {e}")
            import traceback
            traceback.print_exc()
            self.workspace_label.setText("PERSONAL WORKSPACE")
    
    def _show_workspace_menu(self):
        """Show the workspace selection menu"""
        try:
            menu = QMenu(self)
            menu.setWindowFlags(menu.windowFlags() | Qt.WindowType.FramelessWindowHint | Qt.WindowType.NoDropShadowWindowHint)
            menu.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
            
            # Style the menu to match our design system with consistent sizing
            menu.setStyleSheet(f"""
                QMenu {{
                    background: rgba(30, 30, 30, 0.98);
                    border: 1px solid rgba(0, 0, 0, 0.3);
                    border-radius: 6px;
                    padding: 4px;
                    color: white;
                    font-family: 'Segoe UI', system-ui, sans-serif;
                    font-size: 12px;
                    font-weight: bold;
                }}
                QMenu::item {{
                    color: white;
                    background: transparent;
                    padding: 6px 16px;
                    border-radius: 4px;
                    margin: 2px;
                    font-weight: bold;
                    text-transform: uppercase;
                }}
                QMenu::item:selected {{
                    background: rgba(255, 255, 255, 0.12);
                    border: 1px solid rgba(100, 181, 246, 0.3);
                }}
                QMenu::item:pressed {{
                    background: rgba(255, 255, 255, 0.15);
                }}
            """)
            
            # Add all workspaces to menu
            for workspace in self.workspaces:
                action = menu.addAction(workspace.get('name', 'Unknown'))
                action.setData(workspace.get('id'))
            
            # Show menu aligned with the widget (bottom left)
            action = menu.exec(self.mapToGlobal(
                self.rect().bottomLeft()
            ))
            
            if action:
                workspace_id = action.data()
                workspace_name = action.text()
                self._switch_workspace(workspace_id, workspace_name)
                
        except Exception as e:
            print(f"Error showing workspace menu: {e}")
    
    def _switch_workspace(self, workspace_id, workspace_name):
        """Switch to the selected workspace"""
        try:
            if self.session_manager.set_active_organization(workspace_id):
                self.current_workspace = {'id': workspace_id, 'name': workspace_name}
                self.workspace_label.setText(workspace_name.upper())
                
                # Save the last active workspace to user preferences
                if self.session_manager:
                    self.session_manager.save_last_active_workspace(workspace_id)
                
                self.workspace_changed.emit(workspace_id, workspace_name)
        except Exception as e:
            print(f"Error switching workspace: {e}")
    
    def refresh_workspaces(self):
        """Refresh the list of available workspaces"""
        self._load_workspaces()
    
    def set_current_workspace(self, org_id: str):
        """Set the current workspace programmatically"""
        try:
            # Find the organization by ID
            for workspace in self.workspaces:
                if workspace.get('id') == org_id:
                    # Update session manager first
                    if self.session_manager:
                        success = self.session_manager.set_active_organization(org_id)
                        if not success:
                            print(f"❌ Failed to update session manager for organization {org_id}")
                            return False
                    
                    # Update UI
                    self.current_workspace = workspace
                    self.workspace_label.setText(workspace.get('name', 'Unknown').upper())
                    
                    # Save the last active workspace to user preferences
                    if self.session_manager:
                        self.session_manager.save_last_active_workspace(org_id)
                    
                    print(f"✅ Workspace switcher updated to: {workspace.get('name', 'Unknown')}")
                    return True
            return False
        except Exception as e:
            print(f"Error setting current workspace: {e}")
            return False

    def get_current_workspace_id(self) -> str:
        """Get the current workspace ID"""
        if self.current_workspace:
            return self.current_workspace.get('id', '')
        return ''
    
    def get_current_workspace_name(self) -> str:
        """Get the current workspace name"""
        if self.current_workspace:
            return self.current_workspace.get('name', 'Unknown')
        return 'Unknown'
