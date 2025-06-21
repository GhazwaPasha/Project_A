"""
Organization switcher component for multi-tenant support
"""
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QComboBox, QFrame, QDialog, QListWidget, QListWidgetItem
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QFont
from .styles import ModernStyles, GlassmorphismHelper
from .mica_effect import MicaEffect
from ..common import ResponsiveHelper


class OrganizationSwitcher(QWidget):
    """Organization switcher widget for the main window header"""
    
    organization_changed = pyqtSignal(str)  # Emits organization ID when organization changes
    
    def __init__(self, auth_manager, parent=None):
        super().__init__(parent)
        self.auth_manager = auth_manager
        self.current_organization = None
        self.organizations = []
        self._setup_ui()
        self._apply_styling()
        self._load_organizations()
        
    def _setup_ui(self):
        """Setup the organization switcher UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)
        
        # Organization icon
        self.org_icon = QLabel()
        self.org_icon.setFixedSize(24, 24)
        self.org_icon.setStyleSheet("QLabel { background: rgba(74, 144, 226, 0.8); border-radius: 12px; }")
        layout.addWidget(self.org_icon)
        
        # Organization name and dropdown
        self.org_selector = QPushButton("Select Organization")
        self.org_selector.setObjectName("OrgSelector")
        self.org_selector.clicked.connect(self._show_organization_dialog)
        layout.addWidget(self.org_selector)
        
    def _apply_styling(self):
        """Apply modern styling to the switcher"""
        self.setStyleSheet(f"""
            QWidget {{
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                padding: 4px;
            }}
            
            QPushButton#OrgSelector {{
                background: transparent;
                border: none;
                color: white;
                font-size: {ResponsiveHelper.scale_size(14, 12, 16)}px;
                font-weight: 500;
                padding: 8px 12px;
                text-align: left;
                min-width: 150px;
            }}
            
            QPushButton#OrgSelector:hover {{
                background: rgba(255, 255, 255, 0.1);
                border-radius: 6px;            }}
        """)
        
    def _load_organizations(self):
        """Load user's organizations"""
        if self.auth_manager and hasattr(self.auth_manager, 'user_organizations'):
            self.organizations = self.auth_manager.user_organizations
            if self.organizations:
                self.set_current_organization(self.organizations[0])
                
    def set_current_organization(self, organization):
        """Set the current organization"""
        self.current_organization = organization
        if organization:
            self.org_selector.setText(organization.get('name', 'Unknown Organization'))
            # Emit organization ID instead of full organization dict
            org_id = organization.get('organizations', {}).get('id') or organization.get('id')
            if org_id:
                self.organization_changed.emit(org_id)
            
    def _show_organization_dialog(self):
        """Show organization selection dialog"""
        dialog = OrganizationSelectionDialog(self.organizations, self.current_organization, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected_org = dialog.get_selected_organization()
            if selected_org:
                self.set_current_organization(selected_org)

    def set_expanded(self, expanded):
        """Set the expanded state of the organization switcher"""
        if expanded:
            self.org_selector.setText(self.current_organization.get('name', 'Select Organization') if self.current_organization else 'Select Organization')
            self.show()
        else:
            self.org_selector.setText("")
            # In collapsed mode, just show the icon or hide completely
            # For now, we'll hide it as it takes up space
            
    def refresh_organizations(self):
        """Refresh the list of organizations"""
        self._load_organizations()


class OrganizationSelectionDialog(QDialog):
    """Dialog for selecting an organization"""
    
    def __init__(self, organizations, current_org=None, parent=None):
        super().__init__(parent)
        self.organizations = organizations
        self.current_org = current_org
        self.selected_organization = None
        self._setup_ui()
        self._apply_styling()
        
    def _setup_ui(self):
        """Setup the dialog UI"""
        self.setWindowTitle("Select Organization")
        self.setModal(True)
        self.setFixedSize(400, 300)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("Switch Organization")
        title.setStyleSheet(f"""
            QLabel {{
                color: white;
                font-size: {ResponsiveHelper.scale_size(18, 16, 20)}px;
                font-weight: 600;
                margin-bottom: 8px;
            }}
        """)
        layout.addWidget(title)
        
        # Organization list
        self.org_list = QListWidget()
        self.org_list.setObjectName("OrgList")
        layout.addWidget(self.org_list)
        
        # Populate organizations
        for org in self.organizations:
            item = QListWidgetItem(org.get('name', 'Unknown'))
            item.setData(Qt.ItemDataRole.UserRole, org)
            self.org_list.addItem(item)
            
            if self.current_org and org.get('id') == self.current_org.get('id'):
                item.setSelected(True)
                
        # Buttons
        button_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        select_btn = QPushButton("Select")
        select_btn.setObjectName("PrimaryButton")
        select_btn.clicked.connect(self._select_organization)
        button_layout.addWidget(select_btn)
        
        layout.addLayout(button_layout)
        
    def _apply_styling(self):
        """Apply dialog styling"""
        MicaEffect.apply_mica(self, dark_mode=True)
        self.setStyleSheet(f"""
            QDialog {{
                background: rgba(30, 30, 30, 0.95);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
            }}
            
            QListWidget#OrgList {{
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                color: white;
                font-size: {ResponsiveHelper.scale_size(14, 12, 16)}px;
                padding: 8px;
            }}
            
            QListWidget#OrgList::item {{
                padding: 12px;
                border-radius: 6px;
                margin: 2px;
            }}
            
            QListWidget#OrgList::item:hover {{
                background: rgba(255, 255, 255, 0.1);
            }}
            
            QListWidget#OrgList::item:selected {{
                background: rgba(74, 144, 226, 0.6);
            }}
            
            QPushButton {{
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 6px;
                color: white;
                font-size: {ResponsiveHelper.scale_size(14, 12, 16)}px;
                padding: 8px 16px;
                min-width: 80px;
            }}
            
            QPushButton:hover {{
                background: rgba(255, 255, 255, 0.2);
            }}
            
            QPushButton#PrimaryButton {{
                background: rgba(74, 144, 226, 0.8);
                border: 1px solid rgba(74, 144, 226, 1.0);
            }}
            
            QPushButton#PrimaryButton:hover {{
                background: rgba(74, 144, 226, 1.0);
            }}
        """)
        
    def _select_organization(self):
        """Select the chosen organization"""
        current_item = self.org_list.currentItem()
        if current_item:
            self.selected_organization = current_item.data(Qt.ItemDataRole.UserRole)
            self.accept()
            
    def get_selected_organization(self):
        """Get the selected organization"""
        return self.selected_organization
