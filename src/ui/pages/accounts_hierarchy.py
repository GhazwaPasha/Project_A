"""
Enhanced Chart of Accounts page with 3-level hierarchy system.
This module provides an intuitive hierarchical UI for managing account structure.
"""

import traceback
from ..common import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QTreeWidget, QTreeWidgetItem, QHeaderView, QLineEdit, QGridLayout,
    QComboBox, QCheckBox, QTextEdit, QSplitter, QGroupBox,
    Qt, QColor, QIcon, QFont, QSize, QSizePolicy,
    QApplication, QCompleter, QStringListModel, QMessageBox,
    QScrollArea, QSpacerItem, QTabWidget, QStackedWidget,
    QButtonGroup, QFileDialog, QTableWidget, QTableWidgetItem,
    QAbstractScrollArea, QDialog
)
from PyQt6.QtCore import pyqtSignal, QTimer
from PyQt6.QtWidgets import QGraphicsDropShadowEffect, QProgressDialog
from PyQt6.QtGui import QPalette, QPixmap, QPainter

from ...core.events import accounting_events
from ..components.scrollbar_styles import ModernScrollbarStyles
from ..components.widgets import PageHeader
from ..components.styles import ModernStyles, GlassmorphismHelper
from .dashboard import ResponsiveHelper


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
        self.title_label = QLabel(title_text)
        self.title_label.setObjectName('form_title')
        self.title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 18px;
                font-weight: 600;
            }
        """)
        layout.addWidget(self.title_label)
        
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
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 8px;
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
        self.code_edit.setPlaceholderText("Enter account code")
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
        self.type_combo.currentTextChanged.connect(self._update_parent_options)
        self.type_combo.currentTextChanged.connect(self._update_group_options)
        form_layout.addWidget(type_label, row, 0)
        form_layout.addWidget(self.type_combo, row, 1)
        row += 1
        
        # Group
        group_label = QLabel("Group")
        group_label.setStyleSheet(self._get_label_style())
        self.group_combo = QComboBox()
        self.group_combo.setStyleSheet(self._get_combo_style())
        self.group_combo.currentTextChanged.connect(self._on_group_changed)
        form_layout.addWidget(group_label, row, 0)
        form_layout.addWidget(self.group_combo, row, 1)
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
        self.parent_input = QLineEdit()
        self.parent_input.setPlaceholderText("Type to search parent accounts...")
        self.parent_input.setStyleSheet(self._get_input_style())
        
        # Create completer for smart suggestions
        self.parent_completer = QCompleter()
        self.parent_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.parent_completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.parent_completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.parent_completer.setMaxVisibleItems(10)
        
        # Style the completer popup for better visibility
        popup = self.parent_completer.popup()
        popup.setStyleSheet("""
            QListView {
                background: rgba(30, 30, 30, 0.95);
                color: white;
                border: 1px solid rgba(0, 120, 215, 0.5);
                border-radius: 4px;
                font-size: 13px;
                selection-background-color: rgba(0, 120, 215, 0.3);
                outline: none;
            }
            QListView::item {
                padding: 6px;
                border: none;
            }
            QListView::item:hover {
                background: rgba(0, 120, 215, 0.2);
            }
        """)
        
        self.parent_input.setCompleter(self.parent_completer)
        
        # Connect signals for validation and updating
        self.parent_input.textChanged.connect(self._validate_parent_account)
        
        form_layout.addWidget(parent_label, row, 0)
        form_layout.addWidget(self.parent_input, row, 1)
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
        
        # Update parent options and initialize group options
        self._update_parent_options()
        
        # Initialize group options for the default account type
        default_type = self.type_combo.currentText()
        if default_type:
            self._update_group_options(default_type)
        
    def _get_label_style(self):
        return """
            QLabel {
                color: rgba(255, 255, 255, 0.9);
                font-size: 13px;
                font-weight: 500;
            }
        """
        
    def _get_input_style(self):
        return """            QLineEdit {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
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
        return """            QComboBox {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
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
    
    def _on_group_changed(self):
        """Handle group selection changes."""
        # This method can be used for any group-specific logic
        # For now, it's just a placeholder
        pass
        
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
        """Update parent account suggestions based on selected level and type."""
        if not self.system:
            return
            
        # Check if system has organization context
        if hasattr(self.system, 'current_organization_id'):
            org_id = getattr(self.system, 'current_organization_id', None)
            if not org_id:
                return
            
        level = self.level_combo.currentIndex() + 1
        current_type = self.type_combo.currentText()
        
        # Update group options based on account type
        self._update_group_options(current_type)
        
        if level == 1:
            # Level 1 accounts have no parent
            self.parent_input.setEnabled(False)
            self.parent_input.setPlaceholderText("Level 1 accounts have no parent")
            self.parent_input.clear()
        else:
            self.parent_input.setEnabled(True)
            self.parent_input.setPlaceholderText("Type to search parent accounts...")
            
            # Get all accounts and filter for potential parents
            try:
                all_accounts = self.system.get_chart_of_accounts(active_only=False)
                
                if not all_accounts:
                    # Update completer with empty list
                    model = QStringListModel([])
                    self.parent_completer.setModel(model)
                    return
                
                # Helper function to calculate level if not present
                def calculate_account_level(account, all_accs):
                    """Calculate account level based on parent hierarchy."""
                    if isinstance(account, dict):
                        parent_id = account.get('parent_id')
                        if not parent_id:
                            return 1
                        
                        # Find parent account
                        for acc in all_accs:
                            if isinstance(acc, dict) and acc.get('id') == parent_id:
                                return calculate_account_level(acc, all_accs) + 1
                        return 1
                    return 1
                
                # Build list of eligible parent accounts
                eligible_parents = []
                for account in all_accounts:
                    try:
                        # Handle both dict and tuple formats
                        if isinstance(account, dict):
                            name = account.get('name', '')
                            acc_type = account.get('account_type', '') or account.get('type', '')
                            code = account.get('code', '')
                            
                            # Try to get level from account, calculate if missing
                            acc_level = account.get('level')
                            if acc_level is None:
                                acc_level = calculate_account_level(account, all_accs)
                        else:
                            # Tuple format: (name, type, code, parent_code, level, is_postable, description)
                            if len(account) >= 5:
                                name, acc_type, code, parent_code, acc_level = account[:5]
                            else:
                                continue
                        
                        # Only show accounts of the same type and lower level (potential parents)
                        if (acc_type and acc_type.lower() == current_type.lower() and 
                            acc_level < level and name.strip() and code.strip()):
                            display_text = f"{code} - {name}"
                            eligible_parents.append(display_text)
                            
                    except Exception as acc_error:
                        continue
                
                # Update completer with eligible parents
                model = QStringListModel(eligible_parents)
                self.parent_completer.setModel(model)
                
                # If we have eligible parents but the completer popup is not visible, 
                # we might need to force it to refresh
                if eligible_parents and hasattr(self.parent_completer, 'popup'):
                    self.parent_completer.popup().hide()  # Reset popup state
                    
            except Exception as e:
                print(f"Error loading parent accounts: {e}")
                import traceback
                traceback.print_exc()
                # Clear completer on error
                model = QStringListModel([])
                self.parent_completer.setModel(model)
    
    def _update_group_options(self, account_type):
        """Update group options based on account type."""
        if not self.system:
            return
            
        # Get group options for the account type
        group_options = self.system.get_group_options_by_type(account_type)
        
        # Clear and repopulate the group combo box
        self.group_combo.clear()
        self.group_combo.addItems(group_options)
        
        # Set default to "None"
        none_index = self.group_combo.findText("None")
        if none_index >= 0:
            self.group_combo.setCurrentIndex(none_index)
    
    def _validate_parent_account(self):
        """Validate the entered parent account."""
        if not self.parent_input.isEnabled():
            return True
            
        text = self.parent_input.text().strip()
        if not text:
            # Empty is allowed (no parent)
            self._set_parent_validation_style(True)
            return True
        
        # Check if the entered text matches any of the eligible parents
        model = self.parent_completer.model()
        if model:
            for i in range(model.rowCount()):
                item_text = model.data(model.index(i, 0))
                if item_text and (text == item_text or text.lower() in item_text.lower()):
                    self._set_parent_validation_style(True)
                    return True
        
        # Invalid parent account
        self._set_parent_validation_style(False)
        return False
    
    def _set_parent_validation_style(self, is_valid):
        """Set validation styling for parent input."""
        if is_valid:
            self.parent_input.setStyleSheet(self._get_input_style())
        else:
            # Add red border for invalid input
            invalid_style = self._get_input_style().replace(
                "border: 1px solid rgba(255, 255, 255, 0.1);",
                "border: 2px solid rgba(255, 99, 71, 0.8);"
            )
            self.parent_input.setStyleSheet(invalid_style)
    
    def set_account_data(self, account_data):
        """Set form data for editing."""
        if not account_data:
            return
            
        self.name_edit.setText(account_data['name'])
        self.code_edit.setText(account_data['code'] or "")
        self.account_data = account_data  # Store for edit mode
        
        # Set account type - capitalize to match combo box options
        account_type = account_data.get('type', '') or account_data.get('account_type', '')
        if account_type:
            account_type = account_type.capitalize()
        type_index = self.type_combo.findText(account_type)
        if type_index >= 0:
            self.type_combo.setCurrentIndex(type_index)
            # Update group options based on the account type
            self._update_group_options(account_type)
            
        # Store group value to restore later
        group = account_data.get('group', '')
        print(f"🔍 DEBUG: Setting group for account '{account_data['name']}': '{group}'")
            
        # Set level
        if account_data['level'] and 1 <= account_data['level'] <= 3:
            self.level_combo.setCurrentIndex(account_data['level'] - 1)
            
        # Set postable status
        self.postable_check.setChecked(account_data['is_postable'])
        
        # Update parent options and set parent (this will reset group combo to "None")
        self._update_parent_options()
        if account_data.get('parent_code'):
            # Find the parent account and set it in the input field
            try:
                all_accounts = self.system.get_chart_of_accounts(active_only=False)
                for account in all_accounts:
                    if isinstance(account, dict):
                        code = account.get('code', '')
                        name = account.get('name', '')
                    else:
                        # Tuple format
                        if len(account) >= 3:
                            name, acc_type, code = account[:3]
                        else:
                            continue
                    
                    if code == account_data['parent_code']:
                        self.parent_input.setText(f"{code} - {name}")
                        break
            except Exception as e:
                print(f"Error setting parent account: {e}")
                self.parent_input.setText(account_data['parent_code'])
                
        # Now restore the group value AFTER _update_parent_options has been called
        if group:
            group_display = self.system.get_group_display_name(group)
            print(f"🔍 DEBUG: Restoring group display name: '{group_display}'")
            group_index = self.group_combo.findText(group_display)
            print(f"🔍 DEBUG: Group index in combo: {group_index}")
            if group_index >= 0:
                self.group_combo.setCurrentIndex(group_index)
                print(f"🔍 DEBUG: Group combo restored to index {group_index}")
            else:
                print(f"🔍 DEBUG: Group '{group_display}' not found in combo options: {[self.group_combo.itemText(i) for i in range(self.group_combo.count())]}")
        else:
            print(f"🔍 DEBUG: No group value for account '{account_data['name']}'")
                    
    def reset_form(self):
        """Reset the form to its initial state."""
        self.name_edit.clear()
        self.code_edit.clear()
        self.type_combo.setCurrentIndex(0)
        self.group_combo.clear()
        self.level_combo.setCurrentIndex(0)
        self.parent_input.clear()
        self.postable_check.setChecked(True)
        self.account_data = None
        self._update_parent_options()
        
    def _on_submit(self):
        """Handle form submission."""
        # Validate required fields
        if not self.name_edit.text().strip():
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setText("Account name is required")
            msg.setWindowTitle("Validation Error")
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg.exec()
            return
        
        # Validate parent account if required
        level = self.level_combo.currentIndex() + 1
        parent_text = self.parent_input.text().strip()
        parent_code = None
        
        if level > 1:
            if not parent_text:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Icon.Warning)
                msg.setText("Parent account is required for this level")
                msg.setWindowTitle("Validation Error")
                msg.setStandardButtons(QMessageBox.StandardButton.Ok)
                msg.exec()
                return
            
            # Validate parent account
            if not self._validate_parent_account():
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Icon.Warning)
                msg.setText("Invalid parent account. Please select from the suggested accounts.")
                msg.setWindowTitle("Validation Error")
                msg.setStandardButtons(QMessageBox.StandardButton.Ok)
                msg.exec()
                return
            
            # Extract parent code from the input (format: "CODE - NAME")
            if " - " in parent_text:
                parent_code = parent_text.split(" - ")[0].strip()
            else:
                parent_code = parent_text  # Fallback if format is different
            
        data = {
            'name': self.name_edit.text().strip(),
            'type': self.type_combo.currentText(),
            'code': self.code_edit.text().strip(),
            'parent_code': parent_code,
            'level': level,
            'is_postable': self.postable_check.isChecked(),
            'group': self.system.get_group_key_from_display(self.group_combo.currentText())
        }
        
        # Debug logging
        print(f"🔍 DEBUG: Form submission data: {data}")
        print(f"🔍 DEBUG: Group combo text: '{self.group_combo.currentText()}'")
        print(f"🔍 DEBUG: Group key from display: '{data['group']}'")
        
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
        
        # Connect to account change events
        accounting_events.accounts_changed.connect(self._refresh_account_data)
    
    def _refresh_account_data(self):
        """Refresh account data when accounts change."""
        try:
            self._load_data()
        except Exception as e:
            print(f"Error refreshing account data: {e}")
            
    def refresh_currency_display(self):
        """Refresh currency formatting (for consistency with other pages)."""
        # This page doesn't display currency directly, so this is a no-op
        pass
    
    def _setup_ui(self):
        """Setup the enhanced accounts page UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create main accounts overview page
        self.overview_page = self._create_overview_page()
        layout.addWidget(self.overview_page)

    def _create_overview_page(self):
        """Create the main accounts overview page."""
        page = QWidget()
        layout = QVBoxLayout(page)
        responsive_margin = ResponsiveHelper.scale_size(32, 24, 48)
        layout.setContentsMargins(responsive_margin, 0,  # Remove top margin
                                responsive_margin, responsive_margin)
        layout.setSpacing(16)  # Standardized spacing
        
        # Page header with enhanced description
        header = PageHeader(
            "Chart of Accounts", 
            "Manage your 3-level account hierarchy: Major Types → Primary Categories → Sub-accounts"
        )
        layout.addWidget(header)
        
        # Create toolbar first
        self._create_toolbar(layout)
        
        # Create main content area with splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        
        # Create tree widget
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Code", "Account Name", "Type", "Group", "Level", "Postable"])
        self.tree.setRootIsDecorated(True)
        self.tree.setAnimated(True)
        self.tree.setIndentation(20)
        
        # Configure column sizing for better content display
        header = self.tree.header()
        if header:
            header.setStretchLastSection(False)  # Don't auto-stretch last column
            
            # Set resize modes for each column
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Code
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)           # Account Name (main content)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Type
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Group
            header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Level
            header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Postable
            
            # Set minimum widths to ensure content is always visible
            header.setMinimumSectionSize(60)   # Minimum for any column
            self.tree.setColumnWidth(0, 80)    # Code column - fixed reasonable width
            self.tree.setColumnWidth(1, 250)   # Account Name - larger for hierarchy display
            self.tree.setColumnWidth(2, 80)    # Type column
            self.tree.setColumnWidth(3, 120)   # Group column
            self.tree.setColumnWidth(4, 80)    # Level column  
            self.tree.setColumnWidth(5, 70)    # Postable column
        
        # Modern tree styling with shared scrollbar
        tree_style = """
            QTreeWidget {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 8px;
                color: white;
                font-size: 13px;
                selection-background-color: rgba(0, 120, 215, 0.25);
                gridline-color: transparent;
                outline: none;
                padding: 8px;
            }
            QTreeWidget::item {
                border: none;
                padding: 8px;
                margin: 2px 4px;
                border-radius: 4px;
            }
            QTreeWidget::item:hover {
                background: rgba(255, 255, 255, 0.05);
            }
            QTreeWidget::item:selected {
                background: rgba(0, 120, 215, 0.25);
                color: white;
            }
            QTreeWidget::item:selected:hover {
                background: rgba(0, 120, 215, 0.35);
            }
            QHeaderView::section {
                background: rgba(255, 255, 255, 0.08);
                border: none;
                border-bottom: 1px solid rgba(255, 255, 255, 0.05);
                padding: 12px;
                color: rgba(255, 255, 255, 0.9);
                font-size: 12px;
                font-weight: 600;
            }
            QHeaderView::section:first {
                border-top-left-radius: 8px;
                padding-left: 16px;
            }
            QHeaderView::section:last {
                border-top-right-radius: 8px;
            }
        """ + ModernScrollbarStyles.get_vertical_scrollbar_style()
        
        self.tree.setStyleSheet(tree_style)
        
        # Connect tree selection
        self.tree.itemSelectionChanged.connect(self._on_tree_selection_changed)
        self.tree.itemDoubleClicked.connect(self._edit_selected_account)
        
        splitter.addWidget(self.tree)
        
        # Right panel - Account details/form
        self.details_panel = AccountDetailsPanel(system=self.system)
        splitter.addWidget(self.details_panel)
        
        # Set splitter proportions (70% tree, 30% details)
        splitter.setSizes([700, 300])
        
        layout.addWidget(splitter, stretch=1)
        
        return page

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
                border: 1px solid rgba(255, 255, 255, 0.05);
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

    def _show_overview(self):
        """Show the main accounts overview page."""
        pass

    def _create_action_buttons(self, layout):
        """Create action buttons."""
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)
        
        # Refresh button
        refresh_btn = QPushButton()
        refresh_btn.setText("🔄 Refresh")
        refresh_btn.setStyleSheet(self._get_add_button_style())
        refresh_btn.clicked.connect(self._refresh_data)
        button_layout.addWidget(refresh_btn)
        
        # Add Account button
        self.add_btn = QPushButton()
        self.add_btn.setText("➕ Add Account")
        self.add_btn.setStyleSheet(self._get_add_button_style())
        self.add_btn.clicked.connect(self._add_account)
        button_layout.addWidget(self.add_btn)
        
        # Edit Account button
        self.edit_btn = QPushButton()
        self.edit_btn.setText("✏️ Edit Account")
        self.edit_btn.setStyleSheet(self._get_edit_button_style())
        self.edit_btn.clicked.connect(self._edit_selected_account)
        self.edit_btn.setEnabled(False)
        button_layout.addWidget(self.edit_btn)
        
        # Delete Account button
        self.delete_btn = QPushButton()
        self.delete_btn.setText("🗑️ Delete Account")
        self.delete_btn.setStyleSheet(self._get_delete_button_style())
        self.delete_btn.clicked.connect(self._delete_selected_account)
        self.delete_btn.setEnabled(False)
        button_layout.addWidget(self.delete_btn)
        
        # Add spacing
        button_layout.addSpacing(16)
        
        layout.addLayout(button_layout)
    
    def _refresh_data(self):
        """Refresh the chart of accounts data."""
        # Force a database refresh
        if hasattr(self.system, 'refresh_connection'):
            self.system.refresh_connection()
            
        # Save current selection and expanded state
        selected_items = self.tree.selectedItems()
        selected_code = None
        if selected_items:
            selected_code = selected_items[0].data(0, Qt.ItemDataRole.UserRole)['code']
            
        # Reload data
        self._load_data()
        
        # If there was a selection, try to restore it
        if selected_code:
            root = self.tree.invisibleRootItem()
            for i in range(root.childCount()):
                self._find_and_select_item(root.child(i), selected_code)
                
        # Show a brief success message
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setText("Chart of Accounts refreshed successfully")
        msg.setWindowTitle("Refresh Complete")
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        # Add custom styling to the message box
        msg.setStyleSheet("""
            QMessageBox {
                background-color: rgb(32, 32, 32);
                color: white;
            }
            QMessageBox QLabel {
                color: white;
            }
            QPushButton {
                background: rgba(0, 120, 215, 0.9);
                border: 1px solid rgba(0, 0, 0, 0.6);
                border-radius: 4px;
                padding: 6px 16px;
                color: white;
                font-size: 13px;
            }
            QPushButton:hover {
                background: rgba(0, 120, 215, 1.0);
                border: 1px solid rgba(0, 0, 0, 0.7);
            }
        """)
        msg.exec()
                
    def _find_and_select_item(self, item, code):
        """Recursively find and select an item by its code."""
        if item.data(0, Qt.ItemDataRole.UserRole)['code'] == code:
            self.tree.setCurrentItem(item)
            return True
            
        for i in range(item.childCount()):
            if self._find_and_select_item(item.child(i), code):
                return True
        return False
    
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
                result = self.system.delete_account(account_data['name'])
                self._load_data()  # Refresh tree
                self.details_panel.show_info(None)  # Clear details panel
                
                # Emit accounts changed event to refresh all UI components
                accounting_events.accounts_changed.emit()
                
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
        # Store current selection
        selected_items = self.tree.selectedItems()
        selected_code = None
        if selected_items:
            selected_code = selected_items[0].data(0, Qt.ItemDataRole.UserRole)['code']
            
        # Store expanded state
        expanded_items = []
        def store_expanded_state(item):
            if item.isExpanded():
                expanded_items.append(item.data(0, Qt.ItemDataRole.UserRole)['code'])
            for i in range(item.childCount()):
                store_expanded_state(item.child(i))
                
        for i in range(self.tree.topLevelItemCount()):
            store_expanded_state(self.tree.topLevelItem(i))
            
        # Clear and repopulate
        self.tree.clear()
        
        try:
            # Get all accounts with fresh data (only active accounts for display)
            accounts = self.system.get_chart_of_accounts(active_only=True)
            
            # Create items dictionary for quick lookup
            items = {}
            
            # First pass: Create all items
            for account in accounts:
                # Handle dictionary format from get_chart_of_accounts
                name = account.get('name', '')
                acc_type = account.get('account_type', '') or account.get('type', '')  # Support both field names
                code = account.get('code', '')
                parent_id = account.get('parent_id')
                description = account.get('description', '')
                is_active = account.get('is_active', True)
                
                # Use enhanced fields from get_chart_of_accounts - these should always be present
                level = account.get('level', 1)  # Default to level 1 if missing
                parent_code = account.get('parent_code', '')
                is_postable = account.get('is_postable', True)
                
                # Get group data with inheritance
                group = account.get('group', '')
                group_inherited = account.get('group_inherited', False)
                
                # Format group display
                if group:
                    group_display = self.system.get_group_display_name(group)
                    if group_inherited:
                        group_display += " (inherited)"
                else:
                    group_display = "None"
                
                item = QTreeWidgetItem()
                item.setText(0, code or "")
                item.setText(1, name)
                item.setText(2, acc_type.capitalize() if acc_type else "")
                item.setText(3, group_display)
                item.setText(4, f"Level {level}")
                item.setText(5, "✓" if is_postable else "✗")
                
                # Store account data in item
                item.setData(0, Qt.ItemDataRole.UserRole, {
                    'name': name,
                    'account_type': acc_type,  # Use consistent field name
                    'type': acc_type,  # Keep for backward compatibility
                    'code': code,
                    'parent_code': parent_code,
                    'level': level,
                    'is_postable': is_postable,
                    'description': description,
                    'group': group,
                    'group_inherited': group_inherited
                })
                
                # Color coding by level
                level_colors = {
                    1: QColor(100, 150, 255),    # Blue for level 1
                    2: QColor(150, 200, 100),    # Green for level 2  
                    3: QColor(255, 200, 100)     # Orange for level 3
                }
                
                if level in level_colors:
                    for col in range(6):  # Updated to 6 columns
                        item.setForeground(col, level_colors[level])
                        
                # Bold font for non-postable accounts (usually headers)
                if not is_postable:
                    font = QFont()
                    font.setBold(True)
                    for col in range(6):  # Updated to 6 columns
                        item.setFont(col, font)
                
                # Italic font for inherited groups
                if group_inherited:
                    font = QFont()
                    font.setItalic(True)
                    item.setFont(3, font)  # Group column
                
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
            
            # Restore expanded state
            def restore_expanded_state(item):
                code = item.data(0, Qt.ItemDataRole.UserRole)['code']
                if code in expanded_items:
                    item.setExpanded(True)
                if code == selected_code:
                    self.tree.setCurrentItem(item)
                for i in range(item.childCount()):
                    restore_expanded_state(item.child(i))
                    
            for i in range(self.tree.topLevelItemCount()):
                restore_expanded_state(self.tree.topLevelItem(i))
                
            # Expand all if no previous state
            if not expanded_items:
                self.tree.expandAll()

            # --- Expand all items ---
            def expand_all_items(item):
                item.setExpanded(True)
                for i in range(item.childCount()):
                    expand_all_items(item.child(i))
            for i in range(self.tree.topLevelItemCount()):
                expand_all_items(self.tree.topLevelItem(i))

            # --- Intelligent column sizing ---
            self._optimize_column_sizes()

            # --- Restore expanded state ---
            for i in range(self.tree.topLevelItemCount()):
                restore_expanded_state(self.tree.topLevelItem(i))
                
        except Exception as e:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setText("Error loading accounts")
            msg.setInformativeText(str(e))
            msg.setWindowTitle("Error")
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg.exec()
    
    def _optimize_column_sizes(self):
        """Intelligently resize columns for optimal content display."""
        # First, auto-resize all columns to fit their content
        for col in range(self.tree.columnCount()):
            self.tree.resizeColumnToContents(col)
        
        # Get current column widths after auto-resize
        current_widths = [self.tree.columnWidth(i) for i in range(self.tree.columnCount())]
        
        # Set intelligent minimums and adjustments for each column
        min_widths = [80, 200, 80, 120, 80, 70]  # Code, Account Name, Type, Group, Level, Postable
        
        # Ensure Account Name column has enough space for hierarchical content
        # Add extra space for indentation (20px per level * 3 levels + padding)
        account_name_extra = 80  # Extra space for hierarchy indentation
        current_widths[1] = max(current_widths[1], min_widths[1] + account_name_extra)
        
        # Apply the optimized widths
        for i, width in enumerate(current_widths):
            # Ensure minimum width is respected
            final_width = max(width, min_widths[i])
            self.tree.setColumnWidth(i, final_width)
            
    def _style_tree(self):
        """Apply modern styling to the tree widget."""
        tree_style = f"""
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
        """ + ModernScrollbarStyles.get_vertical_scrollbar_style()
        
        self.tree.setStyleSheet(tree_style)
        
    def _get_filter_button_style(self):
        """Get Windows 11 style filter button styling."""
        return """
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 6px;
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
                background: rgba(100, 181, 246, 0.15);
                border: 1px solid rgba(100, 181, 246, 0.3);
                border-radius: 8px;
                padding: 8px 16px;
                color: #90CAF9;
                font-size: 12px;
                font-weight: 600;
                text-align: left;
                icon-size: 16px;
                min-height: 32px;
            }
            QPushButton:hover {
                background: rgba(100, 181, 246, 0.2);
                border: 1px solid rgba(100, 181, 246, 0.5);
            }
            QPushButton:pressed {
                background: rgba(100, 181, 246, 0.1);
                border: 1px solid rgba(100, 181, 246, 0.4);
            }
        """
        
    def _get_edit_button_style(self):
        """Get Windows 11 style edit button styling."""
        return """
            QPushButton {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(0, 0, 0, 0.3);
                border-radius: 8px;
                padding: 8px 16px;
                color: white;
                font-size: 12px;
                font-weight: 500;
                text-align: left;
                icon-size: 16px;
                min-height: 32px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.12);
                border: 1px solid rgba(255, 255, 255, 0.4);
            }
            QPushButton:pressed {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.3);
            }
            QPushButton:disabled {
                background: rgba(255, 255, 255, 0.03);
                border: 1px solid rgba(255, 255, 255, 0.1);
                color: rgba(255, 255, 255, 0.3);
            }
        """
        
    def _get_delete_button_style(self):
        """Get Windows 11 style delete button styling."""
        return """
            QPushButton {
                background: rgba(255, 69, 58, 0.08);
                border: 1px solid rgba(255, 69, 58, 0.2);
                border-radius: 8px;
                padding: 8px 16px;
                color: rgba(255, 69, 58, 0.9);
                font-size: 12px;
                font-weight: 500;
                text-align: left;
                icon-size: 16px;
                min-height: 32px;
            }
            QPushButton:hover {
                background: rgba(255, 69, 58, 0.15);
                border: 1px solid rgba(255, 69, 58, 0.4);
                color: rgb(255, 69, 58);
            }
            QPushButton:pressed {
                background: rgba(255, 69, 58, 0.1);
                border: 1px solid rgba(255, 69, 58, 0.3);
            }
            QPushButton:disabled {
                background: rgba(255, 69, 58, 0.05);
                border: 1px solid rgba(255, 69, 58, 0.1);
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
        self.is_form_active = False
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup the stacked widget UI."""
        # Create the info card
        self.info_card = self._create_info_widget()
        self.addWidget(self.info_card)
        
        # Create the form card immediately to ensure it's always available
        self.form_card = AccountFormCard(system=self.system)
        self.form_card.formSubmitted.connect(self._on_form_submitted)
        self.form_card.formCancelled.connect(self._on_form_cancelled)
        self.addWidget(self.form_card)
        
        # Set initial widget
        self.setCurrentWidget(self.info_card)
        
    def show_form(self, edit_mode=False, account_data=None):
        """Show the account form."""
        self.is_form_active = True
        
        # Reset form for new entry or update for editing
        self.form_card.reset_form()
        
        if edit_mode and account_data:
            self.form_card.set_account_data(account_data)
            self.form_card.edit_mode = True
        else:
            self.form_card.edit_mode = False
        
        # Update the form title
        title_text = "Edit Account" if edit_mode else "Add New Account"
        if hasattr(self.form_card, 'title_label'):
            self.form_card.title_label.setText(title_text)
        
        # Show the form
        self.setCurrentWidget(self.form_card)
        
    def show_info(self, account_data=None):
        """Show the account info card."""
        if not self.is_form_active:  # Only update info if form isn't active
            if account_data:
                self._update_info(account_data)
            self.setCurrentWidget(self.info_card)
            
    def _on_form_submitted(self, data):
        """Handle form submission."""
        try:
            # Start by verifying account doesn't already exist (only check active accounts)
            existing_accounts = [acc['name'] for acc in self.system.get_chart_of_accounts(active_only=True)]
            if not self.form_card.edit_mode and data['name'] in existing_accounts:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Icon.Warning)
                msg.setText("Account already exists")
                msg.setInformativeText("An account with this name already exists. Please use a different name.")
                msg.setWindowTitle("Duplicate Account")
                msg.setStandardButtons(QMessageBox.StandardButton.Ok)
                msg.exec()
                return

            # Get the parent_id if parent_code is provided (only from active accounts)
            parent_id = None
            if data['parent_code']:
                all_accounts = self.system.get_chart_of_accounts(active_only=True)
                for account in all_accounts:
                    if isinstance(account, dict) and account.get('code') == data['parent_code']:
                        parent_id = account.get('id')
                        break

            if self.form_card.edit_mode:
                # Use the unified system's update_account method directly
                account_id = None
                all_accounts = self.system.get_chart_of_accounts(active_only=False)
                for account in all_accounts:
                    if isinstance(account, dict) and account.get('name') == data['old_name']:
                        account_id = account.get('id')
                        break
                
                if account_id:
                    updates = {
                        'name': data['name'],
                        'account_type': data['type'],
                        'code': data['code'] or None,
                        'parent_id': parent_id,
                        'is_postable': data['is_postable'],
                        'description': "",
                        'group': data.get('group', '')
                    }
                    
                    # Access the base system for database operations
                    if hasattr(self.system, 'base_system'):
                        success = self.system.base_system.update_account(account_id, updates)
                    else:
                        success = self.system.update_account(account_id, updates)
                        
                    if not success:
                        raise Exception("Failed to update account in database")
                    
                    # Force sync after account update
                    try:
                        if hasattr(self.system, 'base_system'):
                            sync_result = self.system.base_system.force_sync()
                        else:
                            sync_result = self.system.force_sync()
                        
                        if sync_result.get('success'):
                            pass  # Sync successful
                        else:
                            pass  # Sync failed but don't fail the update
                    except Exception as sync_error:
                        # Don't fail the account update for sync errors
                        pass
                else:
                    raise Exception(f"Account '{data['old_name']}' not found")
            else:
                # Create new account using the unified system's create_account method
                account_data = {
                    'name': data['name'],
                    'account_type': data['type'],
                    'code': data['code'] or None,
                    'parent_id': parent_id,
                    'is_postable': data['is_postable'],
                    'description': "",
                    'group': data.get('group', '')
                }
                
                # Access the base system for database operations
                try:
                    # Check connectivity status
                    if hasattr(self.system, 'base_system'):
                        result = self.system.base_system.create_account(account_data)
                    else:
                        result = self.system.create_account(account_data)
                    
                    # Check if account creation was successful
                    creation_successful = False
                    
                    if not result:
                        raise Exception("Failed to create account in database - no result returned")
                    elif isinstance(result, dict):
                        # Check for explicit success indicators
                        if result.get('id') or result.get('success', False):
                            creation_successful = True
                        elif result.get('error'):
                            raise Exception(f"Account creation failed: {result.get('error')}")
                        else:
                            # If no clear success/error indicator, consider it successful if we got a result
                            creation_successful = True
                    else:
                        # For non-dict results, assume success if we got something
                        creation_successful = True
                    
                    if creation_successful:
                        # Check if account was queued and force sync if online
                        is_queued = isinstance(result, dict) and result.get('queued', False)
                        if is_queued:
                            try:
                                if hasattr(self.system, 'base_system'):
                                    sync_result = self.system.base_system.force_sync()
                                else:
                                    sync_result = self.system.force_sync()
                                
                                if sync_result and sync_result.get('success'):
                                    synced_ops = sync_result.get('synced_operations', 0)
                                    # If sync was successful and no operations were synced, 
                                    # it might indicate the creation didn't work
                                    if synced_ops == 0:
                                        # Verify the account actually exists by checking the system
                                        try:
                                            accounts = self.system.get_chart_of_accounts(active_only=True)
                                            account_exists = any(acc.get('name') == data['name'] for acc in accounts)
                                            if not account_exists:
                                                raise Exception("Account creation failed - account not found in system after sync")
                                        except Exception as verify_error:
                                            raise Exception("Account creation may have failed - unable to verify account exists")
                                else:
                                    pass  # Sync failed but don't fail account creation
                            except Exception as sync_error:
                                import traceback
                                traceback.print_exc()
                                # Don't fail the account creation for sync errors, but warn the user
                                pass
                        else:
                            pass  # Account was not queued, should be immediately available
                    else:
                        raise Exception("Account creation failed - invalid result received")
                        
                except Exception as create_error:
                    import traceback
                    traceback.print_exc()
                    raise Exception(f"Failed to create account in database: {create_error}")
            
            # Switch back to info view
            self.is_form_active = False
            self.show_info()

            # Emit accounts changed event to refresh all UI components
            accounting_events.accounts_changed.emit()

            # Refresh parent page
            parent = self.parent()
            if hasattr(parent, '_load_data'):
                parent._load_data()

            # Show success message with sync status
            action = "updated" if self.form_card.edit_mode else "created"
            success_msg = f"Account '{data['name']}' {action} successfully"
            
            # Add sync status to message if available
            if not self.form_card.edit_mode and result and isinstance(result, dict):
                is_queued = result.get('queued', False)
                if is_queued:
                    try:
                        if hasattr(self.system, 'base_system'):
                            sync_result = self.system.base_system.force_sync()
                        else:
                            sync_result = self.system.force_sync()
                        
                        if sync_result and sync_result.get('success'):
                            synced_ops = sync_result.get('synced_operations', 0)
                            if synced_ops > 0:
                                success_msg += f"\n✅ Synced to database ({synced_ops} operations)"
                            else:
                                success_msg += "\n⚠️ Synced to database (0 operations - account may already exist)"
                        else:
                            success_msg += "\n⚠️ Queued for sync when online"
                    except:
                        success_msg += "\n⚠️ Queued for sync when online"
                else:
                    success_msg += "\n✅ Saved to database"
            
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setText(success_msg)
            msg.setWindowTitle("Success")
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg.exec()

        except Exception as e:
            # Ensure the form remains active so user can retry
            self.is_form_active = True
            
            # Create error message
            error_msg = str(e)
            action = "updating" if self.form_card.edit_mode else "creating"
            
            # Make error message more user-friendly
            if "sync" in error_msg.lower() and "0 operations" in error_msg:
                error_msg = f"Account creation failed: The account was not successfully saved to the database. This might be due to a duplicate name or invalid data."
            elif "not found in system" in error_msg:
                error_msg = f"Account creation failed: The account could not be verified in the system after creation."
            elif "no result returned" in error_msg:
                error_msg = f"Account creation failed: No response received from the database."
            else:
                error_msg = f"Error {action} account: {error_msg}"
            
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setText(error_msg)
            msg.setWindowTitle("Account Creation Failed" if not self.form_card.edit_mode else "Account Update Failed")
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg.exec()
            import traceback
            traceback.print_exc()
            
    def _on_form_cancelled(self):
        """Handle form cancellation."""
        self.is_form_active = False
        self.show_info()
        
    def _create_info_widget(self):
        """Create widget to display selected account information."""
        info_frame = QFrame()
        info_frame.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 8px;
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
        
    def _clear_info(self):
        """Clear the info panel with a modern empty state."""
        empty_html = """
        <div style="color: rgba(255,255,255,0.5); font-family: {ModernStyles.get_font_family()}; text-align: center;">
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
        <div style="color: white; font-family: {ModernStyles.get_font_family()};">
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
                <div style="color: white;">{(account_data.get('account_type') or account_data.get('type', '')).capitalize()}</div>
                
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

    def _calculate_level(self, account, all_accounts, visited=None):
        """Calculate hierarchy level for an account"""
        if visited is None:
            visited = set()
        
        acc_id = account['id']
        if acc_id in visited:  # Prevent infinite loops
            return 1
        visited.add(acc_id)
        
        parent_id = account.get('parent_id')
        if not parent_id:
            return 1  # Root level
        
        # Find parent account
        parent_acc = next((acc for acc in all_accounts if acc['id'] == parent_id), None)
        if not parent_acc:
            return 1
        
        return self._calculate_level(parent_acc, all_accounts, visited) + 1
    
    def _get_parent_code(self, parent_id, all_accounts):
        """Get parent account code from parent_id"""
        if not parent_id:
            return ''
        
        parent_acc = next((acc for acc in all_accounts if acc['id'] == parent_id), None)
        return parent_acc.get('code', '') if parent_acc else ''
    
    def _is_postable(self, account, all_accounts):
        """Determine if account is postable (leaf accounts that can have transactions)"""
        acc_id = account['id']
        
        # Check if this account has any children
        has_children = any(acc.get('parent_id') == acc_id for acc in all_accounts)
        
        # If it has no children, it's a leaf account and is postable
        return not has_children
