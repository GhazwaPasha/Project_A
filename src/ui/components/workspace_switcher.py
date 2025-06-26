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
        
    def _setup_ui(self):
        """Setup the workspace switcher UI"""
        # Main horizontal layout
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(8, 4, 8, 4)
        self.layout.setSpacing(6)
        
        # Set fixed size for consistency
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(32)
        self.setFixedWidth(200)
        
        # Workspace icon
        self.workspace_icon = QLabel()
        icon_path = os.path.join("assets", "icons", "global_orgs_new.svg")
        if os.path.exists(icon_path):
            icon = QIcon(icon_path)
            self.workspace_icon.setPixmap(icon.pixmap(16, 16))
        else:
            self.workspace_icon.setText("🏢")
        self.workspace_icon.setFixedSize(20, 20)
        self.layout.addWidget(self.workspace_icon)
        
        # Current workspace label
        self.workspace_label = QLabel("Loading...")
        self.workspace_label.setObjectName("WorkspaceLabel")
        self.workspace_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.workspace_label, 1)  # Give label stretch priority
        
        # Workspace dropdown button
        self.workspace_button = QPushButton("▼")
        self.workspace_button.setObjectName("WorkspaceButton")
        self.workspace_button.setFixedSize(20, 20)
        self.workspace_button.clicked.connect(self._show_workspace_menu)
        self.layout.addWidget(self.workspace_button)
        
    def _apply_styling(self):
        """Apply styling to the workspace switcher"""
        # Add subtle background and border
        self.setStyleSheet("""
            WorkspaceSwitcher {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 16px;
            }
            
            QLabel {
                color: white;
                font-size: 12px;
                padding: 0px;
            }
            
            QLabel#WorkspaceLabel {
                color: white;
                font-weight: 500;
            }
            
            QPushButton#WorkspaceButton {
                background: transparent;
                border: none;
                color: rgba(255, 255, 255, 0.7);
                font-size: 10px;
                padding: 0px;
            }
            
            QPushButton#WorkspaceButton:hover {
                color: white;
            }
        """)

    def _load_workspaces(self):
        """Load available workspaces from session manager"""
        try:
            if not self.session_manager:
                self.workspace_label.setText("Personal Workspace")
                self.workspace_button.setEnabled(False)
                return
                
            if not self.auth_manager or not self.auth_manager.current_user:
                self.workspace_label.setText("Not Logged In")
                self.workspace_button.setEnabled(False)
                return
                
            # Get workspaces from session manager
            self.workspaces = self.session_manager.get_available_organizations()
            
            if not self.workspaces:
                self.workspace_label.setText("Personal Workspace")
                self.workspace_button.setEnabled(True)
                return
                
            # Get current workspace
            current_org = self.session_manager.get_current_organization()
            if current_org:
                self.current_workspace = current_org
                self.workspace_label.setText(current_org.get('name', 'Unknown'))
            else:
                # Set first organization as active if none is selected
                first_org = self.workspaces[0]
                if self.session_manager.set_active_organization(first_org['id']):
                    self.current_workspace = first_org
                    self.workspace_label.setText(first_org['name'])
                else:
                    self.workspace_label.setText("Select Organization")
            
            self.workspace_button.setEnabled(True)
                
        except Exception as e:
            print(f"Error loading workspaces: {e}")
            import traceback
            traceback.print_exc()
            self.workspace_label.setText("Personal Workspace")
            self.workspace_button.setEnabled(False)
    
    def _show_workspace_menu(self):
        """Show the workspace selection menu"""
        try:
            menu = QMenu(self)
            menu.setWindowFlags(menu.windowFlags() | Qt.WindowType.FramelessWindowHint | Qt.WindowType.NoDropShadowWindowHint)
            menu.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
            
            # Style the menu
            menu.setStyleSheet("""
                QMenu {
                    background: rgba(45, 45, 48, 0.98);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 8px;
                    padding: 4px;
                }
                QMenu::item {
                    color: white;
                    background: transparent;
                    padding: 8px 16px;
                    border-radius: 4px;
                    margin: 2px;
                }
                QMenu::item:selected {
                    background: rgba(255, 255, 255, 0.1);
                }
            """)
            
            # Add all workspaces to menu
            for workspace in self.workspaces:
                action = menu.addAction(workspace.get('name', 'Unknown'))
                action.setData(workspace.get('id'))
            
            # Show menu aligned with button
            action = menu.exec(self.workspace_button.mapToGlobal(
                self.workspace_button.rect().bottomLeft()
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
                self.workspace_label.setText(workspace_name)
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
                    self.current_workspace = workspace
                    self.workspace_label.setText(workspace.get('name', 'Unknown'))
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
