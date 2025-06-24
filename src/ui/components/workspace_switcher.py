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
        self.current_workspace = org_id
        self._update_display()


class CompactWorkspaceSwitcher(QWidget):
    """
    A more compact version for smaller spaces
    """
    workspace_changed = pyqtSignal(str, str)
    
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
        """Setup compact UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(6)
        
        # Just a combo box for workspace selection
        self.workspace_combo = QComboBox()
        self.workspace_combo.setObjectName("WorkspaceCombo")
        self.workspace_combo.currentTextChanged.connect(self._on_workspace_changed)
        layout.addWidget(self.workspace_combo)
        
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.setMaximumHeight(32)
    
    def _apply_styling(self):
        """Apply compact styling"""
        self.setStyleSheet(f"""
            QComboBox#WorkspaceCombo {{
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 16px;
                color: white;
                padding: 4px 12px;
                font-size: {ResponsiveHelper.scale_size(12, 11, 13)}px;
                min-width: 150px;
            }}
            
            QComboBox#WorkspaceCombo::drop-down {{
                border: none;
                background: transparent;
                width: 20px;
            }}
            
            QComboBox#WorkspaceCombo::down-arrow {{
                image: none;
                border: none;
                width: 0;
                height: 0;
            }}
            
            QComboBox#WorkspaceCombo:hover {{
                background: rgba(255, 255, 255, 0.15);
                border: 1px solid rgba(255, 255, 255, 0.3);
            }}
            
            QComboBox#WorkspaceCombo QAbstractItemView {{
                background: rgba(30, 30, 30, 0.95);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                color: white;
                selection-background-color: rgba(74, 144, 226, 0.8);
                outline: none;
            }}
        """)
    
    def _load_workspaces(self):
        """Load workspaces into combo box"""
        if not self.auth_manager:
            self.workspace_combo.addItem("🏠 Local Workspace")
            return
            
        try:
            user_orgs = self.auth_manager.get_user_organizations()
            self.workspace_combo.clear()
            self.workspaces = []
            
            if user_orgs:
                for org_member in user_orgs:
                    org = org_member.get('organizations', {})
                    if org:
                        workspace = {
                            'id': org.get('id'),
                            'name': org.get('name', 'Unknown'),
                            'role': org_member.get('role', 'accountant'),
                            'type': 'personal' if "'s Workspace" in org.get('name', '') else 'organization'
                        }
                        self.workspaces.append(workspace)
                        
                        # Add to combo box
                        if workspace['type'] == 'personal':
                            display_name = f"🏠 {workspace['name']}"
                        else:
                            role_text = workspace['role'].replace('_', ' ').title()
                            display_name = f"🏢 {workspace['name']} ({role_text})"
                        
                        self.workspace_combo.addItem(display_name)
                        
        except Exception as e:
            print(f"Error loading compact workspaces: {e}")
            self.workspace_combo.addItem("🏠 Local Workspace")
    
    def _on_workspace_changed(self, text):
        """Handle workspace selection change"""
        if not self.workspaces:
            return
            
        index = self.workspace_combo.currentIndex()
        if 0 <= index < len(self.workspaces):
            workspace = self.workspaces[index]
            self.current_workspace = workspace['id']
            
            if self.session_manager:
                self.session_manager.set_active_organization(workspace['id'])
            
            self.workspace_changed.emit(workspace['id'], workspace['name'])
    
    def refresh_workspaces(self):
        """Refresh workspaces"""
        self._load_workspaces()
