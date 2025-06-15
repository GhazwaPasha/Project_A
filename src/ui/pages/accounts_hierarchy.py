"""
Enhanced Chart of Accounts page with 3-level hierarchy system.
This module provides an intuitive hierarchical UI for managing account structure.
"""

from ..common import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QTreeWidget, QTreeWidgetItem, QHeaderView, QDialog, QLineEdit, 
    QComboBox, QCheckBox, QTextEdit, QSplitter, QGroupBox,
    Qt, QColor, QIcon, QFont, QSize, QSizePolicy,
    ResponsiveHelper, MODERN_BUTTON_STYLE
)
from PyQt6.QtWidgets import QAbstractItemView, QGraphicsDropShadowEffect, QSpacerItem
from ..components.styles import ModernStyles, GlassmorphismHelper
from ..components.widgets import PageHeader


class HierarchyAccountDialog(QDialog):
    """Modern dialog for adding/editing accounts in the 3-level hierarchy."""
    
    def __init__(self, parent=None, system=None, edit_mode=False, account_data=None):
        super().__init__(parent)
        self.system = system
        self.edit_mode = edit_mode
        self.account_data = account_data
        
        if edit_mode and account_data:
            self.setWindowTitle("Edit Account")
        else:
            self.setWindowTitle("Add New Account")
            
        self._setup_ui()
        self._apply_styling()
        
    def _setup_ui(self):
        """Setup the enhanced dialog UI."""
        # Responsive dialog sizing - larger for more fields
        dialog_width = ResponsiveHelper.scale_size(500, 400, 600)
        dialog_height = ResponsiveHelper.scale_size(600, 500, 700)
        self.setFixedSize(dialog_width, dialog_height)
        self.setModal(True)
        
        # Main layout
        layout = QVBoxLayout(self)
        margins = ResponsiveHelper.scale_size(32, 24, 40)
        layout.setContentsMargins(margins, 
                                 ResponsiveHelper.scale_size(24, 18, 30), 
                                 margins, 
                                 ResponsiveHelper.scale_size(24, 18, 30))
        layout.setSpacing(ResponsiveHelper.scale_size(20, 15, 25))
        
        self._create_title(layout)
        self._create_form_fields(layout)
        self._create_buttons(layout)
        
        # Pre-fill data if editing
        if self.edit_mode and self.account_data:
            self._populate_edit_data()
        
    def _create_title(self, layout):
        """Create dialog title."""
        title_text = "Edit Account" if self.edit_mode else "Add New Account"
        title = QLabel(title_text)
        title.setStyleSheet(f"""
            QLabel {{
                color: white;
                font-size: {ResponsiveHelper.scale_size(22, 18, 26)}px;
                font-weight: 700;
                background: transparent;
                margin-bottom: {ResponsiveHelper.scale_size(8, 6, 10)}px;
            }}
        """)
        layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel("Configure account details and hierarchy settings")
        subtitle.setStyleSheet(f"""
            QLabel {{
                color: rgba(255, 255, 255, 0.7);
                font-size: {ResponsiveHelper.scale_size(13, 11, 15)}px;
                font-weight: 400;
                background: transparent;
                margin-bottom: {ResponsiveHelper.scale_size(16, 12, 20)}px;
            }}
        """)
        layout.addWidget(subtitle)
        
    def _create_form_fields(self, layout):
        """Create comprehensive form fields."""
        # Basic Information Group
        basic_group = self._create_group("Basic Information", layout)
        self._create_basic_fields(basic_group)
        
        # Hierarchy Settings Group
        hierarchy_group = self._create_group("Hierarchy Settings", layout)
        self._create_hierarchy_fields(hierarchy_group)
        
        # Account Properties Group
        properties_group = self._create_group("Account Properties", layout)
        self._create_properties_fields(properties_group)
        
    def _create_group(self, title, parent_layout):
        """Create a grouped section."""
        group = QGroupBox(title)
        group.setStyleSheet(f"""
            QGroupBox {{
                color: rgba(255, 255, 255, 0.9);
                font-size: {ResponsiveHelper.scale_size(14, 12, 16)}px;
                font-weight: 600;
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                margin-top: 8px;
                padding-top: 8px;
                background: rgba(255, 255, 255, 0.05);
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                background: rgba(32, 32, 32, 0.9);
            }}
        """)
        
        group_layout = QVBoxLayout(group)
        group_layout.setSpacing(ResponsiveHelper.scale_size(12, 8, 16))
        
        parent_layout.addWidget(group)
        return group_layout
        
    def _create_basic_fields(self, layout):
        """Create basic account information fields."""
        # Account Name
        name_label = QLabel("Account Name:")
        name_label.setStyleSheet(self._get_label_style())
        layout.addWidget(name_label)
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter descriptive account name...")
        self.name_edit.setStyleSheet(self._get_input_style())
        layout.addWidget(self.name_edit)
        
        # Account Code
        code_label = QLabel("Account Code:")
        code_label.setStyleSheet(self._get_label_style())
        layout.addWidget(code_label)
        
        self.code_edit = QLineEdit()
        self.code_edit.setPlaceholderText("4-digit code (auto-generated if empty)")
        self.code_edit.setMaxLength(4)
        self.code_edit.setStyleSheet(self._get_input_style())
        layout.addWidget(self.code_edit)
        
        # Account Type
        type_label = QLabel("Account Type:")
        type_label.setStyleSheet(self._get_label_style())
        layout.addWidget(type_label)
        
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Asset", "Liability", "Equity", "Revenue", "Expense"])
        self.type_combo.setStyleSheet(self._get_combo_style())
        self.type_combo.currentIndexChanged.connect(self._on_type_changed)
        layout.addWidget(self.type_combo)
        
    def _create_hierarchy_fields(self, layout):
        """Create hierarchy-related fields."""
        # Level Selection
        level_label = QLabel("Hierarchy Level:")
        level_label.setStyleSheet(self._get_label_style())
        layout.addWidget(level_label)
        
        self.level_combo = QComboBox()
        self.level_combo.addItems([
            "Level 1 - Major Account Type (Non-postable)",
            "Level 2 - Primary Account Category", 
            "Level 3 - Detailed Sub-account"
        ])
        self.level_combo.setStyleSheet(self._get_combo_style())
        self.level_combo.currentIndexChanged.connect(self._on_level_changed)
        layout.addWidget(self.level_combo)
        
        # Parent Account
        parent_label = QLabel("Parent Account:")
        parent_label.setStyleSheet(self._get_label_style())
        layout.addWidget(parent_label)
        
        self.parent_combo = QComboBox()
        self.parent_combo.setStyleSheet(self._get_combo_style())
        layout.addWidget(self.parent_combo)
        
        # Update parent options when level changes
        self._update_parent_options()
        
    def _create_properties_fields(self, layout):
        """Create account properties fields."""
        # Postable Checkbox
        self.postable_checkbox = QCheckBox("Allow transactions to be posted to this account")
        self.postable_checkbox.setChecked(True)  # Default to postable
        self.postable_checkbox.setStyleSheet(f"""
            QCheckBox {{
                color: rgba(255, 255, 255, 0.9);
                font-size: {ResponsiveHelper.scale_size(13, 11, 15)}px;
                font-weight: 500;
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 3px;
                background: rgba(255, 255, 255, 0.1);
            }}
            QCheckBox::indicator:checked {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                            stop:0 rgba(46, 125, 50, 0.8), 
                            stop:1 rgba(67, 160, 71, 0.8));
                border-color: rgba(67, 160, 71, 0.8);
            }}
        """)
        layout.addWidget(self.postable_checkbox)
        
        # Description
        desc_label = QLabel("Description (Optional):")
        desc_label.setStyleSheet(self._get_label_style())
        layout.addWidget(desc_label)
        
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Enter account description or notes...")
        self.description_edit.setMaximumHeight(80)
        self.description_edit.setStyleSheet(f"""
            QTextEdit {{
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                padding: 8px 12px;
                color: white;
                font-size: {ResponsiveHelper.scale_size(13, 11, 15)}px;
            }}
            QTextEdit:focus {{
                background: rgba(255, 255, 255, 0.15);
                border-color: rgba(0, 120, 215, 0.6);
            }}
        """)
        layout.addWidget(self.description_edit)
        
    def _create_buttons(self, layout):
        """Create dialog action buttons."""
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(self._get_cancel_button_style())
        cancel_btn.clicked.connect(self.reject)
        
        button_text = "Update Account" if self.edit_mode else "Add Account"
        self.save_btn = QPushButton(button_text)
        self.save_btn.setStyleSheet(self._get_save_button_style())
        self.save_btn.clicked.connect(self.accept)
        
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(self.save_btn)
        
        layout.addLayout(button_layout)
        
    def _on_type_changed(self):
        """Handle account type change."""
        if not self.code_edit.text() and self.system:
            acc_type = self.type_combo.currentText()
            prefix_map = {
                'Asset': '1',
                'Liability': '2',
                'Equity': '3', 
                'Revenue': '4',
                'Expense': '5'
            }
            prefix = prefix_map.get(acc_type, '')
            if prefix:
                self.code_edit.setPlaceholderText(f"{prefix}XXX - Auto-generated")
                
    def _on_level_changed(self):
        """Handle hierarchy level change."""
        level = self.level_combo.currentIndex() + 1
        
        # Level 1 accounts cannot be postable (they are category headers)
        if level == 1:
            self.postable_checkbox.setChecked(False)
            self.postable_checkbox.setEnabled(False)
        else:
            self.postable_checkbox.setEnabled(True)
            
        self._update_parent_options()
        
    def _update_parent_options(self):
        """Update parent account options based on selected level."""
        if not self.system:
            return
            
        self.parent_combo.clear()
        level = self.level_combo.currentIndex() + 1
        
        if level == 1:
            # Level 1 accounts have no parent
            self.parent_combo.addItem("None (Top Level)", "")
            self.parent_combo.setEnabled(False)
        else:
            self.parent_combo.setEnabled(True)
            self.parent_combo.addItem("Select Parent Account...", "")
            
            # Get potential parents (accounts from previous levels)
            max_parent_level = level - 1
            potential_parents = self.system.get_parent_accounts(max_parent_level)
            
            for name, acc_type, code, parent_code, acc_level, is_postable, description in potential_parents:
                # Only show accounts of the same type and appropriate level
                if acc_type == self.type_combo.currentText() and acc_level < level:
                    indent = "  " * (acc_level - 1)
                    display_text = f"{indent}{code} - {name}"
                    self.parent_combo.addItem(display_text, code)
    
    def _populate_edit_data(self):
        """Populate form with existing account data for editing."""
        if not self.account_data:
            return
            
        name, acc_type, code, parent_code, level, is_postable, description = self.account_data
        
        self.name_edit.setText(name)
        self.code_edit.setText(code or "")
        
        # Set account type
        type_index = self.type_combo.findText(acc_type)
        if type_index >= 0:
            self.type_combo.setCurrentIndex(type_index)
            
        # Set level
        if level and 1 <= level <= 3:
            self.level_combo.setCurrentIndex(level - 1)
            
        # Set postable status
        self.postable_checkbox.setChecked(bool(is_postable))
        
        # Set description
        if description:
            self.description_edit.setPlainText(description)
            
        # Update parent options and set parent
        self._update_parent_options()
        if parent_code:
            for i in range(self.parent_combo.count()):
                if self.parent_combo.itemData(i) == parent_code:
                    self.parent_combo.setCurrentIndex(i)
                    break
    
    def get_account_data(self):
        """Get the form data."""
        level = self.level_combo.currentIndex() + 1
        return {
            'name': self.name_edit.text().strip(),
            'type': self.type_combo.currentText(),
            'code': self.code_edit.text().strip(),
            'parent_code': self.parent_combo.currentData() or None,
            'level': level,
            'is_postable': self.postable_checkbox.isChecked(),
            'description': self.description_edit.toPlainText().strip()
        }
    
    def _get_label_style(self):
        """Get label styling."""
        return f"""
            QLabel {{
                color: rgba(255, 255, 255, 0.9);
                font-size: {ResponsiveHelper.scale_size(13, 11, 15)}px;
                font-weight: 500;
                background: transparent;
                margin-bottom: 4px;
            }}
        """
        
    def _get_input_style(self):
        """Get input field styling."""
        return f"""
            QLineEdit {{
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                padding: 10px 12px;
                color: white;
                font-size: {ResponsiveHelper.scale_size(13, 11, 15)}px;
            }}
            QLineEdit:focus {{
                background: rgba(255, 255, 255, 0.15);
                border-color: rgba(0, 120, 215, 0.6);
            }}
            QLineEdit::placeholder {{
                color: rgba(255, 255, 255, 0.5);
            }}
        """
        
    def _get_combo_style(self):
        """Get combo box styling."""
        return f"""
            QComboBox {{
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                padding: 10px 12px;
                color: white;
                font-size: {ResponsiveHelper.scale_size(13, 11, 15)}px;
            }}
            QComboBox:hover {{
                background: rgba(255, 255, 255, 0.15);
                border-color: rgba(255, 255, 255, 0.3);
            }}
            QComboBox::drop-down {{
                border: none;
                width: 24px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border: none;
            }}
            QComboBox QAbstractItemView {{
                background: rgba(32, 32, 32, 0.95);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                color: white;
                selection-background-color: rgba(0, 120, 215, 0.3);
            }}
        """
        
    def _get_cancel_button_style(self):
        """Get cancel button styling."""
        return """
            QPushButton {
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                padding: 12px 24px;
                color: white;
                font-size: 13px;
                font-weight: 500;
                min-width: 100px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.15);
                border-color: rgba(255, 255, 255, 0.3);
            }
            QPushButton:pressed {
                background: rgba(255, 255, 255, 0.2);
            }
        """
        
    def _get_save_button_style(self):
        """Get save button styling."""
        return """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                            stop:0 rgba(46, 125, 50, 0.8), 
                            stop:1 rgba(67, 160, 71, 0.8));
                border: 1px solid rgba(46, 125, 50, 0.6);
                border-radius: 8px;
                padding: 12px 24px;
                color: white;
                font-size: 13px;
                font-weight: 600;
                min-width: 120px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                            stop:0 rgba(46, 125, 50, 1.0), 
                            stop:1 rgba(67, 160, 71, 1.0));
                border-color: rgba(67, 160, 71, 0.8);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                            stop:0 rgba(26, 105, 30, 1.0), 
                            stop:1 rgba(47, 140, 51, 1.0));
            }
        """
        
    def _apply_styling(self):
        """Apply dialog styling."""
        self.setStyleSheet("""
            QDialog {
                background: rgba(32, 32, 32, 0.95);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 16px;
            }
        """)


class HierarchicalAccountsPage(QWidget):
    """Enhanced Chart of Accounts page with intuitive 3-level hierarchy."""
    
    def __init__(self, system, parent=None):
        super().__init__(parent)
        self.system = system
        self._setup_ui()
        self._apply_styling()
        self._load_data()
        
    def _setup_ui(self):
        """Setup the enhanced accounts page UI."""
        layout = QVBoxLayout(self)
        responsive_margin = ResponsiveHelper.scale_size(32, 24, 48)
        layout.setContentsMargins(responsive_margin, responsive_margin, 
                                 responsive_margin, responsive_margin)
        layout.setSpacing(ResponsiveHelper.scale_size(24, 18, 32))
        
        # Page header with enhanced description
        header = PageHeader(
            "Chart of Accounts", 
            "Manage your 3-level account hierarchy: Major Types → Primary Categories → Detailed Sub-accounts"
        )
        layout.addWidget(header)
        
        # Create main content area
        self._create_content_area(layout)
        
        # Create toolbar
        self._create_toolbar(layout)
        
    def _create_content_area(self, layout):
        """Create the main content area with splitter."""
        # Use splitter for resizable panels
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        
        # Left panel - Hierarchy tree
        self._create_hierarchy_panel(splitter)
        
        # Right panel - Account details
        self._create_details_panel(splitter)
        
        # Set splitter proportions (70% tree, 30% details)
        splitter.setSizes([700, 300])
        
        layout.addWidget(splitter, stretch=1)
        
    def _create_hierarchy_panel(self, parent):
        """Create the left panel with hierarchical tree view."""
        tree_frame = QFrame()
        tree_frame.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                margin: 4px;
            }
        """)
        
        tree_layout = QVBoxLayout(tree_frame)
        tree_layout.setContentsMargins(16, 16, 16, 16)
        tree_layout.setSpacing(12)
        
        # Tree header
        tree_header = QLabel("Account Hierarchy")
        tree_header.setStyleSheet(f"""
            QLabel {{
                color: white;
                font-size: {ResponsiveHelper.scale_size(16, 14, 18)}px;
                font-weight: 600;
                background: transparent;
                margin-bottom: 8px;
            }}
        """)
        tree_layout.addWidget(tree_header)
        
        # Create tree widget
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Code", "Account Name", "Type", "Level", "Postable"])
        self.tree.setRootIsDecorated(True)
        self.tree.setAnimated(True)
        self.tree.setIndentation(20)
        
        # Configure tree appearance
        self._style_tree()
        
        # Connect tree selection
        self.tree.itemSelectionChanged.connect(self._on_tree_selection_changed)
        self.tree.itemDoubleClicked.connect(self._edit_selected_account)
        
        tree_layout.addWidget(self.tree)
        parent.addWidget(tree_frame)
        
    def _create_details_panel(self, parent):
        """Create the right panel with account details."""
        details_frame = QFrame()
        details_frame.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                margin: 4px;
            }
        """)
        
        details_layout = QVBoxLayout(details_frame)
        details_layout.setContentsMargins(16, 16, 16, 16)
        details_layout.setSpacing(16)
        
        # Details header
        details_header = QLabel("Account Details")
        details_header.setStyleSheet(f"""
            QLabel {{
                color: white;
                font-size: {ResponsiveHelper.scale_size(16, 14, 18)}px;
                font-weight: 600;
                background: transparent;
                margin-bottom: 8px;
            }}
        """)
        details_layout.addWidget(details_header)
        
        # Account info display
        self.info_widget = self._create_info_widget()
        details_layout.addWidget(self.info_widget)
        
        # Add stretch
        details_layout.addStretch()
        
        parent.addWidget(details_frame)
        
    def _create_info_widget(self):
        """Create widget to display selected account information."""
        info_frame = QFrame()
        info_frame.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.03);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                padding: 12px;
            }
        """)
        
        layout = QVBoxLayout(info_frame)
        layout.setSpacing(12)
        
        # Default message
        self.info_label = QLabel("Select an account to view details")
        self.info_label.setStyleSheet(f"""
            QLabel {{
                color: rgba(255, 255, 255, 0.7);
                font-size: {ResponsiveHelper.scale_size(13, 11, 15)}px;
                font-style: italic;
                background: transparent;
                padding: 20px;
                text-align: center;
            }}
        """)
        self.info_label.setWordWrap(True)
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.info_label)
        
        return info_frame
        
    def _create_toolbar(self, layout):
        """Create enhanced toolbar with hierarchy-specific actions."""
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setSpacing(12)
        
        # Level filter buttons
        self._create_level_filters(toolbar_layout)
        
        toolbar_layout.addStretch()
        
        # Action buttons
        self._create_action_buttons(toolbar_layout)
        
        layout.addLayout(toolbar_layout)
        
    def _create_level_filters(self, layout):
        """Create level filter buttons."""
        filter_label = QLabel("Show:")
        filter_label.setStyleSheet(f"""
            QLabel {{
                color: rgba(255, 255, 255, 0.8);
                font-size: {ResponsiveHelper.scale_size(13, 11, 15)}px;
                font-weight: 500;
                background: transparent;
                margin-right: 8px;
            }}
        """)
        layout.addWidget(filter_label)
        
        # Level filter buttons
        self.level_filters = {}
        levels = [
            ("All Levels", "all"),
            ("Level 1 Only", "1"), 
            ("Level 2 Only", "2"),
            ("Level 3 Only", "3"),
            ("Postable Only", "postable")
        ]
        
        for label, level in levels:
            btn = QPushButton(label)
            btn.setCheckable(True)
            if level == "all":
                btn.setChecked(True)  # Default to show all
            btn.setStyleSheet(self._get_filter_button_style())
            btn.clicked.connect(lambda checked, l=level: self._filter_by_level(l))
            self.level_filters[level] = btn
            layout.addWidget(btn)
            
    def _create_action_buttons(self, layout):
        """Create action buttons."""
        # Add Account button
        add_btn = QPushButton()
        add_btn.setText("  Add Account")
        
        try:
            add_icon = QIcon("assets/icons/accounts_modern.svg")
            if not add_icon.isNull():
                add_btn.setIcon(add_icon)
            else:
                add_btn.setText("➕ Add Account")
        except:
            add_btn.setText("➕ Add Account")
            
        add_btn.setStyleSheet(self._get_add_button_style())
        add_btn.clicked.connect(self._add_account)
        layout.addWidget(add_btn)
        
        # Edit Account button
        self.edit_btn = QPushButton()
        self.edit_btn.setText("  Edit Account")
        self.edit_btn.setEnabled(False)  # Disabled until selection
        
        try:
            edit_icon = QIcon("assets/icons/pen.svg")
            if not edit_icon.isNull():
                self.edit_btn.setIcon(edit_icon)
            else:
                self.edit_btn.setText("✏️ Edit Account")
        except:
            self.edit_btn.setText("✏️ Edit Account")
            
        self.edit_btn.setStyleSheet(self._get_edit_button_style())
        self.edit_btn.clicked.connect(self._edit_selected_account)
        layout.addWidget(self.edit_btn)
        
        # Delete Account button
        self.delete_btn = QPushButton()
        self.delete_btn.setText("  Delete Account")
        self.delete_btn.setEnabled(False)  # Disabled until selection
        
        try:
            delete_icon = QIcon("assets/icons/close.svg")
            if not delete_icon.isNull():
                self.delete_btn.setIcon(delete_icon)
            else:
                self.delete_btn.setText("🗑️ Delete Account")
        except:
            self.delete_btn.setText("🗑️ Delete Account")
            
        self.delete_btn.setStyleSheet(self._get_delete_button_style())
        self.delete_btn.clicked.connect(self._delete_selected_account)
        layout.addWidget(self.delete_btn)
        
    def _style_tree(self):
        """Apply modern styling to the tree widget."""
        self.tree.setStyleSheet(f"""
            QTreeWidget {{
                background: transparent;
                border: none;
                color: white;
                font-size: {ResponsiveHelper.scale_size(13, 11, 15)}px;
                selection-background-color: rgba(0, 120, 215, 0.3);
                gridline-color: rgba(255, 255, 255, 0.1);
                outline: none;
            }}
            QTreeWidget::item {{
                border: none;
                padding: 8px 4px;
                border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            }}
            QTreeWidget::item:hover {{
                background: rgba(255, 255, 255, 0.08);
            }}
            QTreeWidget::item:selected {{
                background: rgba(0, 120, 215, 0.3);
                color: white;
            }}
            QTreeWidget::branch:has-siblings:!adjoins-item {{
                border-image: none;
                image: none;
            }}
            QTreeWidget::branch:has-siblings:adjoins-item {{
                border-image: none;
                image: none;
            }}
            QTreeWidget::branch:!has-children:!has-siblings:adjoins-item {{
                border-image: none;
                image: none;
            }}
            QTreeWidget::branch:has-children:!has-siblings:closed,
            QTreeWidget::branch:closed:has-children:has-siblings {{
                image: none;
                border-image: none;
            }}
            QTreeWidget::branch:open:has-children:!has-siblings,
            QTreeWidget::branch:open:has-children:has-siblings {{
                image: none;
                border-image: none;
            }}
            QHeaderView::section {{
                background: rgba(255, 255, 255, 0.1);
                border: none;
                border-bottom: 2px solid rgba(0, 120, 215, 0.6);
                padding: 12px 8px;
                color: white;
                font-size: {ResponsiveHelper.scale_size(12, 10, 14)}px;
                font-weight: 600;
                text-align: left;
            }}
            QHeaderView::section:first {{
                border-top-left-radius: 8px;
            }}
            QHeaderView::section:last {{
                border-top-right-radius: 8px;
            }}
        """)
        
        # Configure tree headers
        header = self.tree.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Code
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)           # Name
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Type
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Level
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Postable
        
    def _load_data(self):
        """Load account data into the tree."""
        self._populate_tree()
        
    def _populate_tree(self):
        """Populate the tree with hierarchical account data."""
        self.tree.clear()
        
        # Get all accounts
        accounts = self.system.get_all_accounts()
        
        # Create items dictionary for quick lookup
        items = {}
        
        # First pass: Create all items
        for name, acc_type, code, parent_code, level, is_postable, description in accounts:
            item = QTreeWidgetItem()
            item.setText(0, code or "")
            item.setText(1, name)
            item.setText(2, acc_type)
            item.setText(3, f"Level {level}")
            item.setText(4, "✓" if is_postable else "✗")
            
            # Store account data in item
            item.setData(0, Qt.ItemDataRole.UserRole, {
                'name': name,
                'type': acc_type,
                'code': code,
                'parent_code': parent_code,
                'level': level,
                'is_postable': is_postable,
                'description': description
            })
            
            # Color coding by level
            level_colors = {
                1: QColor(100, 150, 255),    # Blue for level 1
                2: QColor(150, 200, 100),    # Green for level 2  
                3: QColor(255, 200, 100)     # Orange for level 3
            }
            
            if level in level_colors:
                for col in range(5):
                    item.setForeground(col, level_colors[level])
                    
            # Bold font for non-postable accounts (usually headers)
            if not is_postable:
                font = QFont()
                font.setBold(True)
                for col in range(5):
                    item.setFont(col, font)
            
            items[code] = item
            
        # Second pass: Build hierarchy
        root_items = []
        for code, item in items.items():
            account_data = item.data(0, Qt.ItemDataRole.UserRole)
            parent_code = account_data['parent_code']
            
            if parent_code and parent_code in items:
                items[parent_code].addChild(item)
            else:
                root_items.append(item)
                
        # Add root items to tree
        self.tree.addTopLevelItems(root_items)
        
        # Expand all by default for better visibility
        self.tree.expandAll()
        
    def _filter_by_level(self, level):
        """Filter tree display by level."""
        # Update button states
        for btn_level, btn in self.level_filters.items():
            btn.setChecked(btn_level == level)
            
        # Apply filter
        self._apply_tree_filter(level)
        
    def _apply_tree_filter(self, level):
        """Apply filtering to tree items."""
        def filter_item(item):
            account_data = item.data(0, Qt.ItemDataRole.UserRole)
            if not account_data:
                return False
                
            # Show item based on filter
            if level == "all":
                show = True
            elif level == "postable":
                show = account_data['is_postable']
            else:
                show = account_data['level'] == int(level)
                
            item.setHidden(not show)
            
            # Recursively filter children
            child_visible = False
            for i in range(item.childCount()):
                child = item.child(i)
                if filter_item(child):
                    child_visible = True
                    
            # Show parent if any child is visible
            if child_visible and not show:
                item.setHidden(False)
                return True
                
            return show
            
        # Apply filter to all top-level items
        for i in range(self.tree.topLevelItemCount()):
            filter_item(self.tree.topLevelItem(i))
            
    def _on_tree_selection_changed(self):
        """Handle tree selection changes."""
        selected_items = self.tree.selectedItems()
        
        if selected_items:
            self.edit_btn.setEnabled(True)
            self.delete_btn.setEnabled(True)
            self._update_details_panel(selected_items[0])
        else:
            self.edit_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)
            self._clear_details_panel()
            
    def _update_details_panel(self, item):
        """Update the details panel with selected account info."""
        account_data = item.data(0, Qt.ItemDataRole.UserRole)
        if not account_data:
            return
            
        # Create detailed info display
        info_html = f"""
        <div style="color: white; font-family: Arial, sans-serif;">
            <h3 style="color: #4CAF50; margin-bottom: 16px;">{account_data['name']}</h3>
            
            <p><strong>Account Code:</strong> {account_data['code']}</p>
            <p><strong>Account Type:</strong> {account_data['type']}</p>
            <p><strong>Hierarchy Level:</strong> Level {account_data['level']}</p>
            <p><strong>Postable:</strong> {"Yes" if account_data['is_postable'] else "No"}</p>
            
            {f"<p><strong>Parent Account:</strong> {account_data['parent_code']}</p>" if account_data['parent_code'] else ""}
            
            {f"<div style='margin-top: 16px;'><strong>Description:</strong><br/><em>{account_data['description']}</em></div>" if account_data['description'] else ""}
            
            <div style="margin-top: 20px; padding: 12px; background: rgba(255,255,255,0.05); border-radius: 6px;">
                <small style="color: #CCCCCC;">
                    Level {account_data['level']} accounts are 
                    {"" if account_data['level'] == 1 else "typically "}
                    {"for organizing major account categories" if account_data['level'] == 1 
                     else "for grouping related accounts" if account_data['level'] == 2 
                     else "for detailed transaction recording"}.
                    {"" if account_data['is_postable'] else " This account cannot have direct transactions."}
                </small>
            </div>
        </div>
        """
        
        self.info_label.setText(info_html)
        self.info_label.setTextFormat(Qt.TextFormat.RichText)
        
    def _clear_details_panel(self):
        """Clear the details panel."""
        self.info_label.setText("Select an account to view details")
        self.info_label.setTextFormat(Qt.TextFormat.PlainText)
        
    def _add_account(self):
        """Show dialog to add a new account."""
        dialog = HierarchyAccountDialog(self, system=self.system)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_account_data()
            if data['name']:
                try:
                    self.system.add_account(
                        data['name'], 
                        data['type'],
                        data['code'] or None,
                        data['parent_code'],
                        data['level'],
                        data['is_postable'],
                        data['description']
                    )
                    self._load_data()  # Refresh tree
                except Exception as e:
                    # Could show error dialog here
                    print(f"Error adding account: {e}")
                    
    def _edit_selected_account(self):
        """Edit the currently selected account."""
        selected_items = self.tree.selectedItems()
        if not selected_items:
            return
            
        item = selected_items[0]
        account_data = item.data(0, Qt.ItemDataRole.UserRole)
        if not account_data:
            return
            
        # Convert to tuple format expected by dialog
        data_tuple = (
            account_data['name'],
            account_data['type'], 
            account_data['code'],
            account_data['parent_code'],
            account_data['level'],
            account_data['is_postable'],
            account_data['description']
        )
        
        dialog = HierarchyAccountDialog(self, system=self.system, edit_mode=True, account_data=data_tuple)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_data = dialog.get_account_data()
            if new_data['name']:
                try:
                    self.system.edit_account(
                        account_data['name'],  # old name
                        new_data['name'],
                        new_data['type'],
                        new_data['code'] or None,
                        new_data['parent_code'],
                        new_data['level'],
                        new_data['is_postable'],
                        new_data['description']
                    )
                    self._load_data()  # Refresh tree
                except Exception as e:
                    print(f"Error editing account: {e}")
                    
    def _delete_selected_account(self):
        """Delete the currently selected account."""
        selected_items = self.tree.selectedItems()
        if not selected_items:
            return
            
        item = selected_items[0]
        account_data = item.data(0, Qt.ItemDataRole.UserRole)
        if not account_data:
            return
            
        # TODO: Add confirmation dialog
        try:
            self.system.delete_account(account_data['name'])
            self._load_data()  # Refresh tree
        except Exception as e:
            print(f"Error deleting account: {e}")
    
    def _get_filter_button_style(self):
        """Get filter button styling."""
        return """
            QPushButton {
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 6px;
                padding: 6px 12px;
                color: white;
                font-size: 12px;
                font-weight: 500;
                margin: 0 2px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.15);
                border-color: rgba(255, 255, 255, 0.3);
            }
            QPushButton:checked {
                background: rgba(0, 120, 215, 0.3);
                border-color: rgba(0, 120, 215, 0.5);
                color: white;
            }
        """
        
    def _get_add_button_style(self):
        """Get add button styling."""
        return """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                            stop:0 rgba(46, 125, 50, 0.8), 
                            stop:1 rgba(67, 160, 71, 0.8));
                border: 1px solid rgba(46, 125, 50, 0.6);
                border-radius: 8px;
                padding: 10px 18px;
                color: white;
                font-size: 13px;
                font-weight: 600;
                text-align: left;
                icon-size: 14px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                            stop:0 rgba(46, 125, 50, 1.0), 
                            stop:1 rgba(67, 160, 71, 1.0));
                border-color: rgba(67, 160, 71, 0.8);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                            stop:0 rgba(26, 105, 30, 1.0), 
                            stop:1 rgba(47, 140, 51, 1.0));
            }
        """
        
    def _get_edit_button_style(self):
        """Get edit button styling."""
        return """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                            stop:0 rgba(33, 150, 243, 0.8), 
                            stop:1 rgba(13, 71, 161, 0.8));
                border: 1px solid rgba(33, 150, 243, 0.6);
                border-radius: 8px;
                padding: 10px 18px;
                color: white;
                font-size: 13px;
                font-weight: 500;
                text-align: left;
                icon-size: 14px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                            stop:0 rgba(33, 150, 243, 1.0), 
                            stop:1 rgba(13, 71, 161, 1.0));
                border-color: rgba(33, 150, 243, 0.8);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                            stop:0 rgba(13, 71, 161, 1.0), 
                            stop:1 rgba(33, 150, 243, 1.0));
            }
            QPushButton:disabled {
                background: rgba(255, 255, 255, 0.05);
                border-color: rgba(255, 255, 255, 0.1);
                color: rgba(255, 255, 255, 0.3);
            }
        """
        
    def _get_delete_button_style(self):
        """Get delete button styling."""
        return """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                            stop:0 rgba(211, 47, 47, 0.8), 
                            stop:1 rgba(183, 28, 28, 0.8));
                border: 1px solid rgba(211, 47, 47, 0.6);
                border-radius: 8px;
                padding: 10px 18px;
                color: white;
                font-size: 13px;
                font-weight: 500;
                text-align: left;
                icon-size: 14px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                            stop:0 rgba(211, 47, 47, 1.0), 
                            stop:1 rgba(183, 28, 28, 1.0));
                border-color: rgba(211, 47, 47, 0.8);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                            stop:0 rgba(183, 28, 28, 1.0), 
                            stop:1 rgba(211, 47, 47, 1.0));
            }
            QPushButton:disabled {
                background: rgba(255, 255, 255, 0.05);
                border-color: rgba(255, 255, 255, 0.1);
                color: rgba(255, 255, 255, 0.3);
            }
        """
        
    def _apply_styling(self):
        """Apply glassmorphism styling to the page."""
        GlassmorphismHelper.apply_main_container_effect(self)
        self.setStyleSheet(ModernStyles.get_complete_stylesheet())
