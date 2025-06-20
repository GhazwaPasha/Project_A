"""
Organization Selector Dialog for Multi-Tenant SaaS
"""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QListWidget, QListWidgetItem, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPalette, QColor
from .login_window import GlassmorphismHelper

class OrganizationSelectorDialog(QDialog):
    """Dialog for selecting organization when user belongs to multiple orgs"""
    
    organization_selected = pyqtSignal(dict)
    
    def __init__(self, organizations, parent=None):
        super().__init__(parent)
        self.organizations = organizations
        self.selected_org = None
        
        self.setWindowTitle("Select Organization")
        self.setModal(True)
        self.resize(400, 300)
        
        self._setup_ui()
        self._apply_styling()
    
    def _setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Title
        title = QLabel("Select Organization")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setObjectName("title")
        layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel("You belong to multiple organizations. Please select one to continue.")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setWordWrap(True)
        subtitle.setObjectName("subtitle")
        layout.addWidget(subtitle)
        
        # Organization list
        self.org_list = QListWidget()
        self.org_list.setObjectName("orgList")
        
        for org in self.organizations:
            item = QListWidgetItem(org['name'])
            item.setData(Qt.ItemDataRole.UserRole, org)
            self.org_list.addItem(item)
        
        # Select first item by default
        if self.organizations:
            self.org_list.setCurrentRow(0)
            
        self.org_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.org_list)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setObjectName("cancelButton")
        self.cancel_btn.clicked.connect(self.reject)
        
        self.select_btn = QPushButton("Select Organization")
        self.select_btn.setObjectName("selectButton")
        self.select_btn.clicked.connect(self._select_organization)
        self.select_btn.setDefault(True)
        
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.select_btn)
        layout.addLayout(button_layout)
    
    def _on_item_double_clicked(self, item):
        """Handle double-click on organization item"""
        self._select_organization()
    
    def _select_organization(self):
        """Select the current organization"""
        current_item = self.org_list.currentItem()
        if current_item:
            self.selected_org = current_item.data(Qt.ItemDataRole.UserRole)
            self.organization_selected.emit(self.selected_org)
            self.accept()
    
    def _apply_styling(self):
        """Apply glassmorphism styling"""
        self.setStyleSheet(f"""
            QDialog {{
                background: rgba(30, 30, 30, 0.85);
                border-radius: 15px;
                border: 1px solid rgba(255, 255, 255, 0.2);
            }}
            
            QLabel#title {{
                font-size: 24px;
                font-weight: bold;
                color: #FFFFFF;
                margin-bottom: 10px;
            }}
            
            QLabel#subtitle {{
                font-size: 14px;
                color: rgba(255, 255, 255, 0.8);
                margin-bottom: 20px;
            }}
            
            QListWidget#orgList {{
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 10px;
                padding: 10px;
                font-size: 14px;
                color: #FFFFFF;
                selection-background-color: rgba(0, 123, 255, 0.3);
            }}
            
            QListWidget#orgList::item {{
                padding: 12px;
                border-radius: 8px;
                margin: 2px 0;
            }}
            
            QListWidget#orgList::item:hover {{
                background: rgba(255, 255, 255, 0.1);
            }}
            
            QListWidget#orgList::item:selected {{
                background: rgba(0, 123, 255, 0.4);
                border: 1px solid rgba(0, 123, 255, 0.6);
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
            
            QPushButton#selectButton {{
                background: rgba(0, 123, 255, 0.4);
                border: 1px solid rgba(0, 123, 255, 0.6);
            }}
            
            QPushButton#selectButton:hover {{
                background: rgba(0, 123, 255, 0.5);
                border: 1px solid rgba(0, 123, 255, 0.7);
            }}
            
            QPushButton#selectButton:pressed {{
                background: rgba(0, 123, 255, 0.6);
            }}
        """)
