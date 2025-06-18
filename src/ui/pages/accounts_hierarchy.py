"""
Enhanced Chart of Accounts page with 3-level hierarchy system.
This module provides an intuitive hierarchical UI for managing account structure.
"""

from ..common import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QTreeWidget, QTreeWidgetItem, QHeaderView, QLineEdit, QGridLayout,
    QComboBox, QCheckBox, QTextEdit, QSplitter, QGroupBox,
    Qt, QColor, QIcon, QFont, QSize, QSizePolicy,
    ResponsiveHelper
)
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QAbstractItemView, QStackedWidget, QMessageBox,
    QGraphicsDropShadowEffect, QSpacerItem
)
from ..components.styles import ModernStyles, GlassmorphismHelper
from ..components.widgets import PageHeader


class AccountFormCard(QFrame):
    """Modern card-based form for adding/editing accounts."""
    
    formSubmitted = pyqtSignal(dict)  # Emits the form data when submitted
    formCancelled = pyqtSignal()      # Emits when form is cancelled
    
    def __init__(self, system=None, edit_mode=False, account_data=None, parent=None):
        super().__init__(parent)
        self.system = system
        self.edit_mode = edit_mode
        self.account_data = account_data
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup the card UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # Title section
        title_text = "Edit Account" if self.edit_mode else "Add New Account"
        title = QLabel(title_text)
        title.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 18px;
                font-weight: 600;
            }
        """)
        layout.addWidget(title)
        
        # Form fields
        self._create_form_fields(layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(self._get_cancel_button_style())
        cancel_btn.clicked.connect(self._on_cancel)
        
        save_text = "Update" if self.edit_mode else "Add"
        save_btn = QPushButton(save_text)
        save_btn.setStyleSheet(self._get_save_button_style())
        save_btn.clicked.connect(self._on_submit)
        
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
        
        # Apply card styling
        self.setStyleSheet("""
            AccountFormCard {
                background: rgba(0, 0, 0, 0.2);
                border: 1px solid rgba(0, 0, 0, 0.6);
                border-radius: 4px;
            }
        """)
        
        # Pre-fill data if editing
        if self.edit_mode and self.account_data:
            self._populate_edit_data()
            
    def _create_form_fields(self, layout):
        """Create form input fields."""
        form_layout = QGridLayout()
        form_layout.setSpacing(12)
        row = 0
        
        # Account Name
        name_label = QLabel("Account Name")
        name_label.setStyleSheet(self._get_label_style())
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter account name")
        self.name_edit.setStyleSheet(self._get_input_style())
        form_layout.addWidget(name_label, row, 0)
        form_layout.addWidget(self.name_edit, row, 1)
        row += 1
        
        # Account Code
        code_label = QLabel("Account Code")
        code_label.setStyleSheet(self._get_label_style())
        self.code_edit = QLineEdit()
        self.code_edit.setPlaceholderText("Auto-generated if empty")
        self.code_edit.setStyleSheet(self._get_input_style())
        form_layout.addWidget(code_label, row, 0)
        form_layout.addWidget(self.code_edit, row, 1)
        row += 1
        
        # Account Type
        type_label = QLabel("Account Type")
        type_label.setStyleSheet(self._get_label_style())
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Asset", "Liability", "Equity", "Revenue", "Expense"])
        self.type_combo.setStyleSheet(self._get_combo_style())
        form_layout.addWidget(type_label, row, 0)
        form_layout.addWidget(self.type_combo, row, 1)
        row += 1
        
        # Level
        level_label = QLabel("Level")
        level_label.setStyleSheet(self._get_label_style())
        self.level_combo = QComboBox()
        self.level_combo.addItems([
            "Level 1 - Major Category",
            "Level 2 - Sub Category",
            "Level 3 - Detail Account"
        ])
        self.level_combo.setStyleSheet(self._get_combo_style())
        self.level_combo.currentIndexChanged.connect(self._on_level_changed)
        form_layout.addWidget(level_label, row, 0)
        form_layout.addWidget(self.level_combo, row, 1)
        row += 1
        
        # Parent Account
        parent_label = QLabel("Parent Account")
        parent_label.setStyleSheet(self._get_label_style())
        self.parent_combo = QComboBox()
        self.parent_combo.setStyleSheet(self._get_combo_style())
        form_layout.addWidget(parent_label, row, 0)
        form_layout.addWidget(self.parent_combo, row, 1)
        row += 1
        
        # Postable Checkbox
        self.postable_check = QCheckBox("Allow transactions to be posted to this account")
        self.postable_check.setStyleSheet("""
            QCheckBox {
                color: rgba(255, 255, 255, 0.9);
                font-size: 13px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 1px solid rgba(0, 0, 0, 0.6);
                border-radius: 3px;
                background: rgba(0, 0, 0, 0.2);
            }
            QCheckBox::indicator:checked {
                background: rgba(0, 120, 215, 1.0);
                border-color: rgba(0, 0, 0, 0.6);
            }
            QCheckBox::indicator:hover {
                border-color: rgba(0, 120, 215, 0.8);
            }
        """)
        form_layout.addWidget(self.postable_check, row, 0, 1, 2)
        
        # Add form layout to main layout
        layout.addLayout(form_layout)
        
        # Update parent options
        self._update_parent_options()
        
    def _get_label_style(self):
        return """
            QLabel {
                color: rgba(255, 255, 255, 0.9);
                font-size: 13px;
                font-weight: 500;
            }
        """
        
    def _get_input_style(self):
        return """
            QLineEdit {
                background: rgba(0, 0, 0, 0.2);
                border: 1px solid rgba(0, 0, 0, 0.6);
                border-radius: 4px;
                padding: 8px 12px;
                color: white;
                font-size: 13px;
            }
            QLineEdit:focus {
                background: rgba(0, 0, 0, 0.3);
                border: 1px solid rgba(0, 120, 215, 0.7);
            }
            QLineEdit:hover {
                background: rgba(0, 0, 0, 0.25);
                border: 1px solid rgba(0, 0, 0, 0.7);
            }
        """
        
    def _get_combo_style(self):
        return """
            QComboBox {
                background: rgba(0, 0, 0, 0.2);
                border: 1px solid rgba(0, 0, 0, 0.6);
                border-radius: 4px;
                padding: 8px 12px;
                color: white;
                font-size: 13px;
            }
            QComboBox:hover {
                background: rgba(0, 0, 0, 0.25);
                border: 1px solid rgba(0, 0, 0, 0.7);
            }
            QComboBox:focus {
                border: 1px solid rgba(0, 120, 215, 0.7);
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: url(assets/icons/minimize.svg);
                width: 12px;
                height: 12px;
            }
            QComboBox QAbstractItemView {
                background: rgb(32, 32, 32);
                border: 1px solid rgba(0, 0, 0, 0.6);
                border-radius: 4px;
                selection-background-color: rgba(0, 120, 215, 0.4);
            }
        """
        
    def _get_cancel_button_style(self):
        return """
            QPushButton {
                background: rgba(0, 0, 0, 0.2);
                border: 1px solid rgba(0, 0, 0, 0.6);
                border-radius: 4px;
                padding: 8px 20px;
                color: white;
                font-size: 13px;
                min-width: 80px;
            }
            QPushButton:hover {
                background: rgba(0, 0, 0, 0.3);
                border: 1px solid rgba(0, 0, 0, 0.7);
            }
        """
        
    def _get_save_button_style(self):
        return """
            QPushButton {
                background: rgba(0, 120, 215, 0.9);
                border: 1px solid rgba(0, 0, 0, 0.6);
                border-radius: 4px;
                padding: 8px 20px;
                color: white;
                font-size: 13px;
                font-weight: 600;
                min-width: 80px;
            }
            QPushButton:hover {
                background: rgba(0, 120, 215, 1.0);
                border: 1px solid rgba(0, 0, 0, 0.7);
            }
        """
    
    def _on_level_changed(self):
        """Handle hierarchy level change."""
        level = self.level_combo.currentIndex() + 1
        
        # Level 1 accounts cannot be postable (they are category headers)
        if level == 1:
            self.postable_check.setChecked(False)
            self.postable_check.setEnabled(False)
        else:
            self.postable_check.setEnabled(True)
            
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
            
            for name, acc_type, code, parent_code, acc_level, is_postable, _ in potential_parents:
                # Only show accounts of the same type and appropriate level
                if acc_type == self.type_combo.currentText() and acc_level < level:
                    indent = "  " * (acc_level - 1)
                    display_text = f"{indent}{code} - {name}"
                    self.parent_combo.addItem(display_text, code)
    
    def set_account_data(self, account_data):
        """Set form data for editing."""
        if not account_data:
            return
            
        self.name_edit.setText(account_data['name'])
        self.code_edit.setText(account_data['code'] or "")
        
        # Set account type
        type_index = self.type_combo.findText(account_data['type'])
        if type_index >= 0:
            self.type_combo.setCurrentIndex(type_index)
            
        # Set level
        if account_data['level'] and 1 <= account_data['level'] <= 3:
            self.level_combo.setCurrentIndex(account_data['level'] - 1)
            
        # Set postable status
        self.postable_check.setChecked(account_data['is_postable'])
        
        # Update parent options and set parent
        self._update_parent_options()
        if account_data['parent_code']:
            for i in range(self.parent_combo.count()):
                if self.parent_combo.itemData(i) == account_data['parent_code']:
                    self.parent_combo.setCurrentIndex(i)
                    break
                    
    def _on_submit(self):
        """Handle form submission."""
        data = {
            'name': self.name_edit.text().strip(),
            'type': self.type_combo.currentText(),
            'code': self.code_edit.text().strip(),
            'parent_code': self.parent_combo.currentData() or None,
            'level': self.level_combo.currentIndex() + 1,
            'is_postable': self.postable_check.isChecked()
        }
        
        if self.edit_mode and self.account_data:
            data['old_name'] = self.account_data['name']
            
        self.formSubmitted.emit(data)
        
    def _on_cancel(self):
        """Handle form cancellation."""
        self.formCancelled.emit()
    

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
        layout.setSpacing(ResponsiveHelper.scale_size(32, 24, 48))
        
        # Page header with enhanced description
        header = PageHeader(
            "Chart of Accounts", 
            "Manage your 3-level account hierarchy: Major Types → Primary Categories → Sub-accounts"
        )
        layout.addWidget(header)
        
        # Create toolbar first
        self._create_toolbar(layout)
        
        # Create main content area
        self._create_content_area(layout)
        
    def _create_content_area(self, layout):
        """Create the main content area with splitter."""
        # Use splitter for resizable panels
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        
        # Left panel - Hierarchy tree
        self._create_hierarchy_panel(splitter)
        
        # Right panel - Account details/form
        self.details_panel = AccountDetailsPanel(system=self.system)
        splitter.addWidget(self.details_panel)
        
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
                border: none;
                margin-bottom: 8px;
                padding: 0px;
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
        
    def _create_toolbar(self, layout):
        """Create enhanced toolbar with hierarchy-specific actions."""
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setSpacing(16)
        toolbar_layout.setContentsMargins(0, 8, 0, 8)
        
        # Create level filter buttons
        self._create_level_filters(toolbar_layout)
        
        toolbar_layout.addStretch()
        
        # Action buttons
        self._create_action_buttons(toolbar_layout)
        
        layout.addLayout(toolbar_layout)
        
    def _create_level_filters(self, layout):
        """Create modern level filter buttons."""
        # Level filter buttons
        self.level_filters = {}
        levels = [
            ("All", "all"),
            ("Level 1", "1"), 
            ("Level 2", "2"),
            ("Level 3", "3"),
            ("Postable", "postable")
        ]
        
        filter_group = QFrame()
        filter_group.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.03);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 8px;
                padding: 4px;
            }
        """)
        
        filter_layout = QHBoxLayout(filter_group)
        filter_layout.setSpacing(4)
        filter_layout.setContentsMargins(4, 4, 4, 4)
        
        for label, level in levels:
            btn = QPushButton(label)
            btn.setCheckable(True)
            if level == "all":
                btn.setChecked(True)
            btn.setStyleSheet(self._get_filter_button_style())
            btn.clicked.connect(lambda checked, l=level: self._filter_by_level(l))
            self.level_filters[level] = btn
            filter_layout.addWidget(btn)
            
        layout.addWidget(filter_group)
        
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
        
    def _add_account(self):
        """Show form to add a new account."""
        self.details_panel.show_form(edit_mode=False)
        
    def _edit_selected_account(self):
        """Edit the currently selected account."""
        selected_items = self.tree.selectedItems()
        if not selected_items:
            return
            
        item = selected_items[0]
        account_data = item.data(0, Qt.ItemDataRole.UserRole)
        if not account_data:
            return
            
        self.details_panel.show_form(edit_mode=True, account_data=account_data)
        
    def _delete_selected_account(self):
        """Delete the currently selected account."""
        selected_items = self.tree.selectedItems()
        if not selected_items:
            return
            
        item = selected_items[0]
        account_data = item.data(0, Qt.ItemDataRole.UserRole)
        if not account_data:
            return
            
        # Check if account has children
        if item.childCount() > 0:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setText("Cannot delete account with sub-accounts")
            msg.setInformativeText("Please delete or reassign all sub-accounts first.")
            msg.setWindowTitle("Delete Account")
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg.exec()
            return
            
        # Show confirmation dialog
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Question)
        msg.setText(f"Delete account '{account_data['name']}'?")
        msg.setInformativeText("This action cannot be undone.")
        msg.setWindowTitle("Delete Account")
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg.setDefaultButton(QMessageBox.StandardButton.No)
        
        if msg.exec() == QMessageBox.StandardButton.Yes:
            try:
                self.system.delete_account(account_data['name'])
                self._load_data()  # Refresh tree
                self.details_panel.show_info(None)  # Clear details panel
            except Exception as e:
                error_msg = QMessageBox()
                error_msg.setIcon(QMessageBox.Icon.Critical)
                error_msg.setText("Error deleting account")
                error_msg.setInformativeText(str(e))
                error_msg.setWindowTitle("Error")
                error_msg.setStandardButtons(QMessageBox.StandardButton.Ok)
                error_msg.exec()
                
    def _on_tree_selection_changed(self):
        """Handle tree selection changes."""
        selected_items = self.tree.selectedItems()
        
        if selected_items:
            self.edit_btn.setEnabled(True)
            self.delete_btn.setEnabled(True)
            account_data = selected_items[0].data(0, Qt.ItemDataRole.UserRole)
            self.details_panel.show_info(account_data)
        else:
            self.edit_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)
            self.details_panel.show_info(None)
            
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
        
    def _style_tree(self):
        """Apply modern styling to the tree widget."""
        self.tree.setStyleSheet(f"""
            QTreeWidget {{
                background: rgba(0, 0, 0, 0.2);
                border: 1px solid rgba(0, 0, 0, 0.6);
                border-radius: 4px;
                color: white;
                font-size: {ResponsiveHelper.scale_size(13, 11, 15)}px;
                selection-background-color: rgba(0, 120, 215, 0.25);
                gridline-color: rgba(0, 0, 0, 0.6);
                outline: none;
                padding: 4px;
            }}
            QTreeWidget::item {{
                border: none;
                padding: 8px;
                margin: 2px 4px;
                border-radius: 4px;
            }}
            QTreeWidget::item:hover {{
                background: rgba(255, 255, 255, 0.05);
            }}
            QTreeWidget::item:selected {{
                background: rgba(0, 120, 215, 0.25);
                color: white;
            }}
            QTreeWidget::item:selected:hover {{
                background: rgba(0, 120, 215, 0.35);
            }}
            QTreeWidget::branch:has-children {{
                background: transparent;
                border-image: none;
                padding-left: 4px;
            }}
            QTreeWidget::branch:has-children:!has-siblings:closed,
            QTreeWidget::branch:closed:has-children:has-siblings {{
                image: url(assets/icons/maximize.svg);
            }}
            QTreeWidget::branch:open:has-children:!has-siblings,
            QTreeWidget::branch:open:has-children:has-siblings {{
                image: url(assets/icons/minimize.svg);
            }}
            QHeaderView::section {{
                background: rgba(0, 0, 0, 0.3);
                border: none;
                border-bottom: 1px solid rgba(0, 0, 0, 0.6);
                padding: 12px;
                color: rgba(255, 255, 255, 0.9);
                font-size: {ResponsiveHelper.scale_size(12, 10, 14)}px;
                font-weight: 600;
            }}
            QHeaderView::section:first {{
                border-top-left-radius: 4px;
                padding-left: 16px;
            }}
            QHeaderView::section:last {{
                border-top-right-radius: 4px;
            }}
            QScrollBar:vertical {{
                width: 12px;
                background: transparent;
                margin: 0;
            }}
            QScrollBar::handle:vertical {{
                background: rgba(255, 255, 255, 0.2);
                border-radius: 6px;
                min-height: 40px;
                margin: 2px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: rgba(255, 255, 255, 0.3);
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
            }}
            QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical,
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: transparent;
            }}
        """)
        
    def _get_filter_button_style(self):
        """Get Windows 11 style filter button styling."""
        return """
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                color: rgba(255, 255, 255, 0.8);
                font-size: 13px;
                font-weight: 500;
                margin: 0;
                min-width: 70px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.08);
                color: white;
            }
            QPushButton:checked {
                background: rgba(0, 120, 215, 0.3);
                color: white;
            }
            QPushButton:checked:hover {
                background: rgba(0, 120, 215, 0.4);
            }
        """
        
    def _get_add_button_style(self):
        """Get Windows 11 style add button styling."""
        return """
            QPushButton {
                background: rgba(0, 120, 215, 0.9);
                border: 1px solid rgba(0, 0, 0, 0.6);
                border-radius: 4px;
                padding: 8px 20px;
                color: white;
                font-size: 13px;
                font-weight: 600;
                text-align: left;
                icon-size: 16px;
            }
            QPushButton:hover {
                background: rgba(0, 120, 215, 1.0);
                border: 1px solid rgba(0, 0, 0, 0.7);
            }
            QPushButton:pressed {
                background: rgba(0, 100, 195, 1.0);
                border: 1px solid rgba(0, 0, 0, 0.8);
            }
        """
        
    def _get_edit_button_style(self):
        """Get Windows 11 style edit button styling."""
        return """
            QPushButton {
                background: rgba(0, 0, 0, 0.2);
                border: 1px solid rgba(0, 0, 0, 0.6);
                border-radius: 4px;
                padding: 8px 20px;
                color: white;
                font-size: 13px;
                font-weight: 500;
                text-align: left;
                icon-size: 16px;
            }
            QPushButton:hover {
                background: rgba(0, 0, 0, 0.3);
                border: 1px solid rgba(0, 0, 0, 0.7);
            }
            QPushButton:pressed {
                background: rgba(0, 0, 0, 0.4);
                border: 1px solid rgba(0, 0, 0, 0.8);
            }
            QPushButton:disabled {
                background: rgba(0, 0, 0, 0.1);
                border: 1px solid rgba(0, 0, 0, 0.4);
                color: rgba(255, 255, 255, 0.3);
            }
        """
        
    def _get_delete_button_style(self):
        """Get Windows 11 style delete button styling."""
        return """
            QPushButton {
                background: rgba(0, 0, 0, 0.2);
                border: 1px solid rgba(0, 0, 0, 0.6);
                border-radius: 4px;
                padding: 8px 20px;
                color: rgba(255, 69, 58, 0.9);
                font-size: 13px;
                font-weight: 500;
                text-align: left;
                icon-size: 16px;
            }
            QPushButton:hover {
                background: rgba(255, 69, 58, 0.1);
                border: 1px solid rgba(255, 69, 58, 0.3);
                color: rgba(255, 69, 58, 1.0);
            }
            QPushButton:pressed {
                background: rgba(255, 69, 58, 0.15);
                border: 1px solid rgba(255, 69, 58, 0.4);
            }
            QPushButton:disabled {
                background: rgba(0, 0, 0, 0.1);
                border: 1px solid rgba(0, 0, 0, 0.4);
                color: rgba(255, 69, 58, 0.4);
            }
        """
        
    def _apply_styling(self):
        """Apply glassmorphism styling to the page."""
        GlassmorphismHelper.apply_main_container_effect(self)
        self.setStyleSheet(ModernStyles.get_complete_stylesheet())


class AccountDetailsPanel(QStackedWidget):
    """A stacked widget that switches between account info and account form."""
    
    def __init__(self, system=None, parent=None):
        super().__init__(parent)
        self.system = system
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup the stacked widget UI."""
        # Create the info card
        self.info_card = self._create_info_widget()
        self.addWidget(self.info_card)
        
        # Create the form card (initially hidden)
        self.form_card = None
        
        # Set initial widget
        self.setCurrentWidget(self.info_card)
        
    def show_form(self, edit_mode=False, account_data=None):
        """Show the account form."""
        # Create new form if needed
        if not self.form_card:
            self.form_card = AccountFormCard(
                system=self.system,
                edit_mode=edit_mode,
                account_data=account_data
            )
            self.form_card.formSubmitted.connect(self._on_form_submitted)
            self.form_card.formCancelled.connect(self._on_form_cancelled)
            self.addWidget(self.form_card)
        
        # Update form data if editing
        if edit_mode and account_data:
            self.form_card.set_account_data(account_data)
            
        # Show the form
        self.setCurrentWidget(self.form_card)
        
    def show_info(self, account_data=None):
        """Show the account info card."""
        if account_data:
            self._update_info(account_data)
        self.setCurrentWidget(self.info_card)
        
    def _create_info_widget(self):
        """Create widget to display selected account information."""
        info_frame = QFrame()
        info_frame.setStyleSheet("""
            QFrame {
                background: rgba(0, 0, 0, 0.2);
                border: 1px solid rgba(0, 0, 0, 0.6);
                border-radius: 4px;
                padding: 16px;
                max-height: 200px;
            }
        """)
        
        layout = QVBoxLayout(info_frame)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Info content
        self.info_label = QLabel()
        self.info_label.setStyleSheet("""
            QLabel {
                background: transparent;
                border: none;
                text-align: center;
            }
        """)
        self.info_label.setWordWrap(True)
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self.info_label)
        
        # Set initial empty state
        self._clear_info()
        
        return info_frame
        
    def _update_info(self, account_data):
        """Update the info panel with selected account info."""
        if not account_data:
            self._clear_info()
            return
            
        level_colors = {
            1: "#4CAF50",  # Green for level 1
            2: "#2196F3",  # Blue for level 2
            3: "#FF9800"   # Orange for level 3
        }
        
        level_color = level_colors.get(account_data['level'], "#FFFFFF")
        
        # Create detailed info display with modern Windows 11 styling
        info_html = f"""
        <div style="color: white; font-family: Segoe UI, Arial, sans-serif;">
            <div style="margin-bottom: 16px;">
                <h3 style="color: {level_color}; margin: 0 0 4px 0; font-size: 20px; font-weight: 600;">
                    {account_data['name']}
                </h3>
                <div style="color: rgba(255,255,255,0.7); font-size: 13px;">
                    {account_data['code']}
                </div>
            </div>
            
            <div style="display: grid; grid-template-columns: auto 1fr; gap: 12px; align-items: center;">
                <div style="color: rgba(255,255,255,0.7); font-weight: 500;">Type</div>
                <div style="color: white;">{account_data['type']}</div>
                
                <div style="color: rgba(255,255,255,0.7); font-weight: 500;">Level</div>
                <div style="color: white;">Level {account_data['level']}</div>
                
                <div style="color: rgba(255,255,255,0.7); font-weight: 500;">Postable</div>
                <div style="color: white;">{"Yes" if account_data['is_postable'] else "No"}</div>
                
                {f'''<div style="color: rgba(255,255,255,0.7); font-weight: 500;">Parent</div>
                <div style="color: white;">{account_data['parent_code']}</div>''' if account_data['parent_code'] else ""}
            </div>
        </div>
        """
        
        self.info_label.setText(info_html)
        self.info_label.setTextFormat(Qt.TextFormat.RichText)
        
    def _clear_info(self):
        """Clear the info panel with a modern empty state."""
        empty_html = """
        <div style="color: rgba(255,255,255,0.5); font-family: Segoe UI, Arial, sans-serif; text-align: center;">
            <div style="margin-bottom: 16px; opacity: 0.7;">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M2 17L12 22L22 17" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M2 12L12 17L22 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
            </div>
            <div style="font-size: 15px; font-weight: 500; margin-bottom: 8px;">
                No Account Selected
            </div>
            <div style="font-size: 13px; color: rgba(255,255,255,0.4);">
                Select an account from the list to view its details
            </div>
        </div>
        """
        self.info_label.setText(empty_html)
        self.info_label.setTextFormat(Qt.TextFormat.RichText)
        
    def _on_form_submitted(self, data):
        """Handle form submission."""
        try:
            if self.form_card.edit_mode:
                self.system.edit_account(
                    data['old_name'],
                    data['name'],
                    data['type'],
                    data['code'] or None,
                    data['parent_code'],
                    data['level'],
                    data['is_postable'],
                    ""  # No description in new design
                )
            else:
                self.system.add_account(
                    data['name'],
                    data['type'],
                    data['code'] or None,
                    data['parent_code'],
                    data['level'],
                    data['is_postable'],
                    ""  # No description in new design
                )
            
            # Switch back to info view and refresh parent page
            self.show_info()
            if isinstance(self.parent(), HierarchicalAccountsPage):
                self.parent()._load_data()
        except Exception as e:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setText("Error saving account")
            msg.setInformativeText(str(e))
            msg.setWindowTitle("Error")
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg.exec()
        
    def _on_form_cancelled(self):
        """Handle form cancellation."""
