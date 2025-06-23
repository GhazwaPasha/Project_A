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
        
        print("🔍 WorkspaceSwitcher: Starting initialization...")
        try:
            print("🔍 WorkspaceSwitcher: Setting up UI...")
            self._setup_ui()
            print("🔍 WorkspaceSwitcher: Applying styling...")
            self._apply_styling()
            print("🔍 WorkspaceSwitcher: Loading workspaces...")
            self._load_workspaces()
            print("🔍 WorkspaceSwitcher: Initialization complete!")
        except Exception as e:
            print(f"❌ WorkspaceSwitcher initialization error: {e}")
            import traceback
            traceback.print_exc()
            raise
        
    def _setup_ui(self):
        """Setup the workspace switcher UI"""
        # Main horizontal layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(12)
        
        # Workspace icon
        self.workspace_icon = QLabel()
        icon_path = os.path.join("assets", "icons", "global_orgs_new.svg")
        if os.path.exists(icon_path):
            icon = QIcon(icon_path)
            self.workspace_icon.setPixmap(icon.pixmap(20, 20))
        else:
            self.workspace_icon.setText("🏢")
        layout.addWidget(self.workspace_icon)
        
        # Current workspace label
        self.workspace_label = QLabel("Personal Workspace")
        self.workspace_label.setObjectName("WorkspaceLabel")
        layout.addWidget(self.workspace_label)
        
        # Workspace dropdown button
        self.workspace_button = QPushButton()
        self.workspace_button.setObjectName("WorkspaceButton")
        self.workspace_button.setText("▼")
        self.workspace_button.setMaximumSize(24, 24)
        self.workspace_button.clicked.connect(self._show_workspace_menu)
        layout.addWidget(self.workspace_button)
        
        # Add some stretch to center the component
        layout.addStretch()
        
        # Set size policy to prefer minimum size
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.setMaximumHeight(40)
        
    def _apply_styling(self):
        """Apply glassmorphism styling to the workspace switcher"""
        # Apply glassmorphism effect
        GlassmorphismHelper.apply_glass_effect(self, blur_radius=20, opacity=0.15)
        
        # Add subtle shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setOffset(0, 2)
        shadow.setColor(QColor(0, 0, 0, 50))
        self.setGraphicsEffect(shadow)
        
        self.setStyleSheet(f"""
            WorkspaceSwitcher {{
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 20px;
                backdrop-filter: blur(10px);
            }}
            
            QLabel#WorkspaceLabel {{
                color: white;
                font-size: {ResponsiveHelper.scale_size(13, 12, 14)}px;
                font-weight: 500;
                background: transparent;
                border: none;
                padding: 4px 8px;
            }}
            
            QPushButton#WorkspaceButton {{
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 12px;
                color: white;
                font-size: 10px;
                font-weight: bold;
                padding: 2px;
            }}
            
            QPushButton#WorkspaceButton:hover {{
                background: rgba(255, 255, 255, 0.2);
                border: 1px solid rgba(255, 255, 255, 0.3);
            }}
            
            QPushButton#WorkspaceButton:pressed {{
                background: rgba(255, 255, 255, 0.3);
            }}
        """)
        
    def _load_workspaces(self):
        """Load user's workspaces from auth manager"""
        if not self.auth_manager or not self.session_manager:
            return
            
        try:
            # Get user organizations
            user_orgs = self.auth_manager.get_user_organizations()
            self.workspaces = []
            
            if user_orgs:
                for org_member in user_orgs:
                    org = org_member.get('organizations', {})
                    if org:
                        workspace = {
                            'id': org.get('id'),
                            'name': org.get('name', 'Unknown Organization'),
                            'role': org_member.get('role', 'accountant'),
                            'type': 'personal' if "'s Workspace" in org.get('name', '') else 'organization'
                        }
                        self.workspaces.append(workspace)
            
            # Set current workspace
            current_org = self.session_manager.get_current_organization()
            if current_org:
                self.current_workspace = current_org.get('id')
                self._update_display()
            elif self.workspaces:
                # Default to first workspace
                self.current_workspace = self.workspaces[0]['id']
                self._update_display()
                
        except Exception as e:
            print(f"Error loading workspaces: {e}")
            # Fallback for when auth is not available
            self.workspace_label.setText("Local Workspace")
            self.workspace_button.hide()
    
    def _update_display(self):
        """Update the displayed workspace name"""
        if not self.current_workspace:
            return
            
        for workspace in self.workspaces:
            if workspace['id'] == self.current_workspace:
                # Show workspace name and type
                name = workspace['name']
                if workspace['type'] == 'personal':
                    self.workspace_label.setText(f"🏠 {name}")
                else:
                    self.workspace_label.setText(f"🏢 {name}")
                break
    
    def _show_workspace_menu(self):
        """Show workspace selection menu"""
        if not self.workspaces:
            return
            
        menu = QMenu(self)
        menu.setObjectName("WorkspaceMenu")
        
        # Style the menu
        menu.setStyleSheet(f"""
            QMenu#WorkspaceMenu {{
                background: rgba(30, 30, 30, 0.95);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                padding: 4px;
                backdrop-filter: blur(10px);
            }}
            
            QMenu#WorkspaceMenu::item {{
                background: transparent;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: {ResponsiveHelper.scale_size(13, 12, 14)}px;
            }}
            
            QMenu#WorkspaceMenu::item:selected {{
                background: rgba(74, 144, 226, 0.8);
            }}
            
            QMenu#WorkspaceMenu::item:disabled {{
                color: rgba(255, 255, 255, 0.5);
            }}
            
            QMenu#WorkspaceMenu::separator {{
                height: 1px;
                background: rgba(255, 255, 255, 0.2);
                margin: 4px 8px;
            }}
        """)
        
        # Add workspace options
        personal_workspaces = [w for w in self.workspaces if w['type'] == 'personal']
        org_workspaces = [w for w in self.workspaces if w['type'] == 'organization']
        
        # Personal workspaces section
        if personal_workspaces:
            personal_header = menu.addAction("Personal Workspaces")
            personal_header.setEnabled(False)
            
            for workspace in personal_workspaces:
                action = menu.addAction(f"🏠 {workspace['name']}")
                action.setData(workspace)
                if workspace['id'] == self.current_workspace:
                    action.setText(f"🏠 {workspace['name']} ✓")
                action.triggered.connect(lambda checked, w=workspace: self._switch_workspace(w))
        
        # Separator if both types exist
        if personal_workspaces and org_workspaces:
            menu.addSeparator()
        
        # Organization workspaces section
        if org_workspaces:
            if personal_workspaces:  # Only add header if there are personal workspaces too
                org_header = menu.addAction("Organizations")
                org_header.setEnabled(False)
            
            for workspace in org_workspaces:
                role_text = workspace['role'].replace('_', ' ').title()
                action = menu.addAction(f"🏢 {workspace['name']} ({role_text})")
                action.setData(workspace)
                if workspace['id'] == self.current_workspace:
                    action.setText(f"🏢 {workspace['name']} ({role_text}) ✓")
                action.triggered.connect(lambda checked, w=workspace: self._switch_workspace(w))
        
        # Show menu
        button_rect = self.workspace_button.geometry()
        menu_pos = self.mapToGlobal(button_rect.bottomLeft())
        menu.exec(menu_pos)
    
    def _switch_workspace(self, workspace):
        """Switch to selected workspace"""
        if workspace['id'] != self.current_workspace:
            self.current_workspace = workspace['id']
            self._update_display()
            
            # Update session manager
            if self.session_manager:
                self.session_manager.set_active_organization(workspace['id'])
            
            # Emit signal for main window to handle
            self.workspace_changed.emit(workspace['id'], workspace['name'])
    
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
