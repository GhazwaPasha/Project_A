"""
Card-Based Bulk Entry Page
Individual entry cards stacked vertically, matching transaction history design
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QLineEdit, QComboBox, QFrame, QDateEdit, QMessageBox, 
    QScrollArea, QSpacerItem, QSizePolicy, QFileDialog, 
    QDialog, QProgressDialog, QGridLayout, QTextEdit, QCheckBox
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor
from datetime import datetime
import csv
import pandas as pd
import os
from ...core.utils import parse_transaction
from ..components.widgets import PageHeader, NonScrollableComboBox, EditableAccountComboBox
from ..components.card_based_entry import CardBasedTransactionEntry
from ..components.styles import ModernStyles, GlassmorphismHelper
from ..common import ResponsiveHelper


class EditableTransactionCard(QFrame):
    """Editable transaction card matching the read-only transaction history design."""
    
    # Signal emitted when this card should be removed
    remove_requested = pyqtSignal(object)
    
    def __init__(self, system, card_number=1, parent=None):
        super().__init__(parent)
        self.system = system
        self.card_number = card_number
        self.accounts = []
        self._load_accounts()
        self._setup_ui()
        
    def _load_accounts(self):
        """Load accounts from the system."""
        try:
            if hasattr(self.system, 'get_all_accounts'):
                accounts_data = self.system.get_all_accounts()
                # accounts_data is a list of tuples: (name, type, code, parent_code, level, is_postable, description)
                self.accounts = [f"{acc[2]} - {acc[0]}" for acc in accounts_data if acc[5]]  # Only postable accounts
            else:
                # Fallback for basic system
                self.accounts = [
                    "1001 - Cash",
                    "1002 - Bank Account", 
                    "1100 - Accounts Receivable",
                    "2001 - Accounts Payable",
                    "3001 - Owner's Equity",
                    "4001 - Sales Revenue",
                    "5001 - Cost of Goods Sold",
                    "6001 - Operating Expenses"
                ]
        except Exception as e:
            print(f"Error loading accounts: {e}")
            self.accounts = ["1001 - Cash", "1002 - Bank Account"]  # Minimal fallback
            
    def _setup_ui(self):
        """Setup the editable transaction card UI - same layout as transaction history."""        # Match the transaction history card styling exactly
        self.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                margin: 1px 0px;
            }
            QFrame:hover {
                background: rgba(255, 255, 255, 0.08);
                border-color: rgba(255, 255, 255, 0.2);
            }        """)        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)  # Match header margins exactly
        layout.setSpacing(8)  # Reduced spacing from 12px to 8px
        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)  # Center vertically        # Date column (100px total width including border/padding)
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setFixedWidth(100)  # Box-sizing will include borders/padding
        self.date_edit.setFixedHeight(34)  # Fixed height to prevent glitches
        self.date_edit.setStyleSheet(self._get_field_style("date"))
        self.date_edit.dateChanged.connect(self._validate_entry)        # Description column (150px total width including border/padding - more usable)
        self.desc_edit = QLineEdit()
        self.desc_edit.setPlaceholderText("Enter description...")
        self.desc_edit.setFixedWidth(150)  # Box-sizing will include borders/padding
        self.desc_edit.setFixedHeight(34)  # Fixed height to prevent glitches
        self.desc_edit.setStyleSheet(self._get_field_style("description"))
        self.desc_edit.textChanged.connect(self._validate_entry)        # Debit account column (205px total width including border/padding - reduced)
        self.debit_combo = EditableAccountComboBox()
        self.debit_combo.setFixedWidth(205)  # Box-sizing will include borders/padding
        self.debit_combo.setFixedHeight(34)  # Fixed height to prevent glitches
        self.debit_combo.setStyleSheet(self._get_field_style("debit"))
        self._populate_account_combo(self.debit_combo)
        self.debit_combo.currentTextChanged.connect(self._validate_entry)        # Credit account column (205px total width including border/padding - reduced)
        self.credit_combo = EditableAccountComboBox()
        self.credit_combo.setFixedWidth(205)  # Box-sizing will include borders/padding
        self.credit_combo.setFixedHeight(34)  # Fixed height to prevent glitches
        self.credit_combo.setStyleSheet(self._get_field_style("credit"))
        self._populate_account_combo(self.credit_combo)
        self.credit_combo.currentTextChanged.connect(self._validate_entry)
          # Amount column (140px total width with better spacing)
        amount_container = QWidget()
        amount_container.setFixedWidth(140)  # Increased for better spacing
        amount_container.setFixedHeight(34)  # Fixed height to prevent glitches
        amount_layout = QHBoxLayout(amount_container)
        amount_layout.setContentsMargins(0, 0, 0, 0)
        amount_layout.setSpacing(6)  # Increased spacing for better button placement
        
        self.amount_edit = QLineEdit()
        self.amount_edit.setPlaceholderText("0.00")
        self.amount_edit.setFixedWidth(114)  # Adjusted for better spacing
        self.amount_edit.setFixedHeight(34)  # Fixed height to prevent glitches
        self.amount_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.amount_edit.setStyleSheet(self._get_field_style("amount"))
        self.amount_edit.textChanged.connect(self._validate_entry)        # Remove button (larger and better positioned)
        remove_btn = QPushButton("✕")
        remove_btn.setFixedSize(20, 20)  # Slightly larger for better usability
        remove_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 100, 100, 0.3);
                border: 1px solid rgba(255, 100, 100, 0.5);
                border-radius: 10px;
                color: white;
                font-weight: bold;
                font-size: 10px;
                margin: 0px;
                padding: 0px;
            }
            QPushButton:hover {
                background: rgba(255, 100, 100, 0.5);
                border-color: rgba(255, 100, 100, 0.8);
            }
        """)
        remove_btn.clicked.connect(lambda: self.remove_requested.emit(self))
        
        amount_layout.addWidget(self.amount_edit)
        amount_layout.addWidget(remove_btn)
          # Add all widgets to main layout (same order as transaction history)        layout.addWidget(self.date_edit)
        layout.addWidget(self.desc_edit)
        layout.addWidget(self.debit_combo)
        layout.addWidget(self.credit_combo)
        layout.addWidget(amount_container)
        
        # Debug: Print field widths to verify changes
        print(f"🔧 DEBUG: Field widths set to:")
        print(f"   Date: {self.date_edit.width()}px")
        print(f"   Description: {self.desc_edit.width()}px")
        print(f"   Debit: {self.debit_combo.width()}px") 
        print(f"   Credit: {self.credit_combo.width()}px")
        print(f"   Amount Container: {amount_container.width()}px")
        
        # Initial validation
        self._validate_entry()
        
    def _populate_account_combo(self, combo):
        """Populate account combo box with available accounts and enable strict validation."""
        try:
            # Use setAccountList for strict validation - only allows accounts from chart of accounts
            combo.setAccountList(self.accounts)
            # Set proper placeholder text            combo.setPlaceholderText("Select or type account...")            # Ensure it starts empty showing only placeholder
            combo.clear_selection()
            
        except Exception as e:
            print(f"Error populating account combo: {e}")
            # Fallback to basic population if setAccountList fails            combo.clear()
            for account in self.accounts:
                combo.addItem(account)
            
    def _get_field_style(self, field_type):
        """Get styling for input fields based on type."""
        base_style = """
            background: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: 6px;
            padding: 4px 8px;
            font-weight: 500;
            font-size: 13px;
            min-height: 20px;
            max-height: 32px;
            line-height: 20px;
        """        # Additional styling for editable combo boxes
        combo_style = """
            QLineEdit {
                background: transparent;
                border: none;
                padding: 0px 0px;
                font-weight: 500;
                font-size: 13px;
                min-height: 20px;
                max-height: 32px;
                line-height: 20px;
            }
            QLineEdit::placeholder {
                color: rgba(255, 255, 255, 0.5);
                font-style: italic;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 3px;
                margin-top: 2px;
                margin-bottom: 2px;
                margin-right: 2px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 6px solid rgba(255, 255, 255, 0.7);
                width: 0px;
                height: 0px;
            }
            QComboBox:focus {
                border-color: rgba(0, 120, 215, 0.8);
                background: rgba(255, 255, 255, 0.12);
            }
            QComboBox QAbstractItemView {
                background: rgba(40, 40, 40, 0.95);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 6px;
                selection-background-color: rgba(0, 120, 215, 0.6);
                color: white;
                padding: 4px;
                font-size: 13px;
            }
            QComboBox QAbstractItemView::item {
                padding: 8px;
                border-radius: 4px;
                margin: 1px;
                min-height: 20px;
            }
            QComboBox QAbstractItemView::item:hover {
                background: rgba(255, 255, 255, 0.1);
            }
        """
        
        if field_type == "date":
            return base_style + """
                color: rgba(255, 255, 255, 0.9);
                QDateEdit::up-button, QDateEdit::down-button {
                    width: 16px;
                    height: 16px;
                    border: none;
                    background: rgba(255, 255, 255, 0.1);
                    border-radius: 2px;
                }
                QDateEdit::up-arrow, QDateEdit::down-arrow {
                    border-left: 3px solid transparent;
                    border-right: 3px solid transparent;
                }
                QDateEdit::up-arrow {
                    border-bottom: 5px solid rgba(255, 255, 255, 0.7);
                }
                QDateEdit::down-arrow {
                    border-top: 5px solid rgba(255, 255, 255, 0.7);
                }
            """
        elif field_type == "description":
            return base_style + """
                color: rgba(255, 255, 255, 0.9);
            """
        elif field_type == "debit":
            return base_style + combo_style + """
                color: rgba(255, 100, 100, 0.9);
            """
        elif field_type == "credit":
            return base_style + combo_style + """
                color: rgba(100, 255, 100, 0.9);
            """
        elif field_type == "amount":
            return base_style + """
                color: rgba(255, 255, 255, 0.9);
                font-weight: 600;
                text-align: right;
            """
        else:
            return base_style + """
                color: rgba(255, 255, 255, 0.9);
            """
    
    def _get_label_style(self, field_type=None):
        """Get styling for field labels in card-based design."""
        base_label_style = """
            color: rgba(255, 255, 255, 0.8);
            font-size: 12px;
            font-weight: 600;
            background: transparent;
            border: none;
            padding: 0px;
            margin-bottom: 4px;
        """
        
        if field_type == "debit":
            return base_label_style + """
                color: rgba(255, 120, 120, 0.9);
            """
        elif field_type == "credit":
            return base_label_style + """
                color: rgba(120, 255, 120, 0.9);
            """
        else:
            return base_label_style

    def _validate_entry(self):
        """Validate the entry and update visual feedback."""
        is_valid = self.is_valid()
        has_data = self._has_any_data()
        
        # Validate individual account fields and apply styling
        self._validate_account_field(self.debit_combo, "debit")
        self._validate_account_field(self.credit_combo, "credit")
        
        # Update overall card border color based on validation
        if is_valid and has_data:
            border_color = "rgba(100, 255, 100, 0.3)"  # Green for valid
        elif has_data and not is_valid:
            border_color = "rgba(255, 100, 100, 0.4)"  # Red for invalid with data
        elif has_data:
            border_color = "rgba(255, 200, 100, 0.3)"  # Yellow for incomplete
        else:
            border_color = "rgba(255, 255, 255, 0.1)"  # Default for empty
            
        self.setStyleSheet(f"""
            QFrame {{
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid {border_color};
                border-radius: 8px;
                margin: 2px 0px;
            }}
            QFrame:hover {{
                background: rgba(255, 255, 255, 0.08);
                border-color: rgba(255, 255, 255, 0.2);
            }}
        """)
    
    def _validate_account_field(self, combo, field_type):
        """Validate individual account field and apply red styling if invalid."""
        account_text = combo.currentText().strip()
        is_valid_account = True
        
        if account_text:
            # Check if account is valid using the combo's validation
            if hasattr(combo, 'isValidAccount'):
                is_valid_account = combo.isValidAccount()
            else:
                # Fallback validation - check if it's in the accounts list
                is_valid_account = account_text in self.accounts
        
        # Apply styling based on validation
        if account_text and not is_valid_account:
            # Red styling for invalid accounts
            invalid_style = self._get_field_style(field_type) + """
                border: 2px solid rgba(255, 100, 100, 0.8) !important;
                background: rgba(255, 100, 100, 0.15) !important;
            """
            combo.setStyleSheet(invalid_style)
        elif not account_text and self._has_any_data():
            # Orange styling for empty required fields when card has data
            empty_style = self._get_field_style(field_type) + """
                border: 2px solid rgba(255, 165, 0, 0.8) !important;
                background: rgba(255, 165, 0, 0.1) !important;
            """
            combo.setStyleSheet(empty_style)
        else:
            # Normal styling for valid fields
            combo.setStyleSheet(self._get_field_style(field_type))
    
    def _has_any_data(self):
        """Check if the card has any data entered."""
        data = self.get_entry_data()
        return any([
            data['description'],
            data['debit_account'],
            data['credit_account'],
            data['amount']
        ])
    
    def get_entry_data(self):
        """Get the entry data from this card."""
        # For editable combo boxes, use currentText() to get typed text
        debit_text = self.debit_combo.currentText().strip()
        credit_text = self.credit_combo.currentText().strip()
        
        # If it's the placeholder text, treat as empty
        if debit_text == "-- Select Account --":
            debit_text = ""
        if credit_text == "-- Select Account --":
            credit_text = ""
        
        return {            'date': self.date_edit.date().toString("yyyy-MM-dd"),
            'description': self.desc_edit.text().strip(),
            'debit_account': debit_text,
            'credit_account': credit_text,
            'amount': self.amount_edit.text().strip()
        }
    
    def set_entry_data(self, data):
        """Set the entry data for this card."""
        if 'date' in data:
            try:
                self.date_edit.setDate(QDate.fromString(data['date'], "yyyy-MM-dd"))
            except:
                self.date_edit.setDate(QDate.currentDate())
        if 'description' in data:
            self.desc_edit.setText(data['description'])
        if 'debit_account' in data and data['debit_account']:
            # Use validation method to match against chart of accounts
            self._set_account_with_validation(self.debit_combo, data['debit_account'])
        if 'credit_account' in data and data['credit_account']:
            # Use validation method to match against chart of accounts
            self._set_account_with_validation(self.credit_combo, data['credit_account'])
        if 'amount' in data:
            self.amount_edit.setText(str(data['amount']))
    
    def clear_entry(self):
        """Clear all fields in this card."""
        self.desc_edit.clear()        # Properly clear editable combo boxes to show placeholder
        self.debit_combo.clear_selection()
        self.credit_combo.clear_selection()
        self.amount_edit.clear()
        self.date_edit.setDate(QDate.currentDate())
    
    def is_valid(self):
        """Check if this card has valid data with strict account validation."""
        data = self.get_entry_data()
        
        # Check basic required fields
        if not all([
            data['description'],
            data['debit_account'],
            data['credit_account'],
            data['amount']
        ]):
            return False
        
        # Check accounts are different
        if data['debit_account'] == data['credit_account']:
            return False
        
        # Validate that accounts exist in chart of accounts
        debit_valid = self._is_account_valid(self.debit_combo)
        credit_valid = self._is_account_valid(self.credit_combo)
        
        return debit_valid and credit_valid
    
    def _is_account_valid(self, combo):
        """Check if the account in the combo box is valid."""
        account_text = combo.currentText().strip()
        if not account_text:
            return False
        
        # Use the combo's built-in validation if available
        if hasattr(combo, 'isValidAccount'):
            return combo.isValidAccount()
        
        # Fallback: check if account exists in our accounts list
        return account_text in self.accounts

    def refresh_accounts(self, accounts):
        """Refresh the account combo boxes with the latest accounts list."""
        self.accounts = accounts
        self._populate_account_combo(self.debit_combo)
        self._populate_account_combo(self.credit_combo)
        
    def _set_account_with_validation(self, combo, account_text):
        """Set account text and trigger validation to find matching accounts."""
        if not account_text:
            return
            
        # Use the enhanced method that triggers validation
        combo.setTextWithValidation(account_text)
            

class BulkEntryPage(QWidget):
    """Card-based bulk entry page matching transaction history design."""
    
    # Signal emitted when entries are saved
    entries_saved = pyqtSignal()
    
    def __init__(self, system, parent=None):
        super().__init__(parent)
        self.system = system
        self.entry_cards = []
        self.next_card_number = 1
        self._setup_ui()
        self._apply_styling()
        self._add_initial_cards()
        
    def _apply_styling(self):
        """Apply modern glassmorphism styling."""
        GlassmorphismHelper.apply_main_container_effect(self)
        self.setStyleSheet(ModernStyles.get_complete_stylesheet())
        
    def _setup_ui(self):
        """Setup the main UI."""
        # Main layout for the page
        page_layout = QVBoxLayout(self)
        # Align with the main page header margins - use zero horizontal margins
        page_layout.setContentsMargins(0, 16, 0, 16)
        page_layout.setSpacing(16)
        
        # Toolbar section
        toolbar_section = self._create_toolbar()
        page_layout.addWidget(toolbar_section)
        
        # Direct cards layout without container frame - cards are independently sized
        self.cards_widget = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_widget)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(8)
        
        # Add stretch at the end to prevent cards from growing
        self.cards_layout.addStretch(1)
        
        # Create scroll area for cards
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea, QWidget#scrollAreaWidgetContents {
                background: transparent;
                border: none;
            }
            QWidget {
                background: transparent;
            }
            QScrollBar:vertical {
                background: rgba(255, 255, 255, 0.1);
                width: 8px;
                border-radius: 4px;
                margin: 0;
            }
        """)
        
        scroll_area.setWidget(self.cards_widget)
        page_layout.addWidget(scroll_area, 1)
        
    def _create_toolbar(self):
        """Create the toolbar section."""
        toolbar_frame = QFrame()
        toolbar_frame.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.06);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 12px;
                margin-bottom: 8px;
            }
        """)
        
        toolbar_layout = QHBoxLayout(toolbar_frame)
        toolbar_layout.setContentsMargins(20, 16, 20, 16)
        toolbar_layout.setSpacing(12)
        
        # Title
        title_label = QLabel("Bulk Entry")
        title_label.setStyleSheet("""
            color: rgba(255, 255, 255, 0.9);
            font-size: 18px;
            font-weight: 600;
            background: transparent;
            border: none;
        """)
        
        # Summary section
        self.summary_label = QLabel("0 entries, $0.00 total")
        self.summary_label.setStyleSheet("""
            color: rgba(255, 255, 255, 0.7);
            font-size: 14px;
            font-weight: 400;
            background: transparent;
            border: none;
        """)
        
        # Buttons
        add_btn = QPushButton("➕ Add Entry")
        add_btn.setStyleSheet(self._get_button_style())
        add_btn.clicked.connect(self._add_new_card)
        
        import_btn = QPushButton("📁 Import CSV/Excel")
        import_btn.setStyleSheet(self._get_button_style())
        import_btn.clicked.connect(self._import_file)
        
        save_all_btn = QPushButton("💾 Save All")
        save_all_btn.setStyleSheet(self._get_button_style(primary=True))
        save_all_btn.clicked.connect(self._save_all_entries)
        
        clear_all_btn = QPushButton("🗑️ Clear All")
        clear_all_btn.setStyleSheet(self._get_button_style(secondary=True))
        clear_all_btn.clicked.connect(self._clear_all_entries)
        
        toolbar_layout.addWidget(title_label)
        toolbar_layout.addWidget(self.summary_label)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(add_btn)
        toolbar_layout.addWidget(import_btn)
        toolbar_layout.addWidget(save_all_btn)
        toolbar_layout.addWidget(clear_all_btn)
        
        return toolbar_frame
    
    def _add_initial_cards(self):
        """Add initial empty cards."""
        for _ in range(3):  # Start with 3 cards
            self._add_new_card()
        
        # Update summary after adding initial cards
        QTimer.singleShot(100, self._update_summary)
            
    def _add_new_card(self):
        """Add a new entry card."""
        card = CardBasedTransactionEntry(self.system, self.next_card_number)
        card.remove_requested.connect(self._remove_card)
        
        # Set size policy to prevent card growth
        card.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        
        # Connect to validation changes for auto-features
        card.desc_edit.textChanged.connect(self._check_auto_add_card)
        card.debit_combo.currentTextChanged.connect(self._check_auto_add_card)
        card.credit_combo.currentTextChanged.connect(self._check_auto_add_card)
        card.amount_edit.textChanged.connect(self._check_auto_add_card)
        
        # Insert before the stretch (which is always at the end)
        self.cards_layout.insertWidget(len(self.entry_cards), card)
        self.entry_cards.append(card)
        self.next_card_number += 1
        
    def _check_auto_add_card(self):
        """Auto-add a new card if the last one has data."""
        if self.entry_cards:
            last_card = self.entry_cards[-1]
            if last_card._has_any_data():
                # Check if we need to add a new card
                all_have_data = all(card._has_any_data() for card in self.entry_cards)
                if all_have_data:
                    self._add_new_card()
          # Update summary whenever data changes
        self._update_summary()
        
    def _update_summary(self):
        """Update the summary display with current entry count and total."""
        valid_entries = [card for card in self.entry_cards if card.is_valid()]
        total_amount = 0.0
        
        for card in valid_entries:
            try:
                amount_text = card.amount_edit.text().strip()
                if amount_text:
                    total_amount += float(amount_text)
            except ValueError:
                pass  # Invalid amount, skip
        
        count = len(valid_entries)
        self.summary_label.setText(f"{count} entries, ${total_amount:,.2f} total")
        
    def _remove_card(self, card):
        """Remove an entry card with proper cleanup."""
        if len(self.entry_cards) > 1:  # Keep at least one card
            # Remove from layout first
            self.cards_layout.removeWidget(card)
            # Remove from our list
            self.entry_cards.remove(card)
            # Clean up the widget
            card.deleteLater()
            # Update numbering and summary
            self._renumber_cards()
            self._update_summary()
        else:
            QMessageBox.information(self, "Cannot Remove", "At least one entry card must remain.")
            
    def _renumber_cards(self):
        """Renumber all cards after removal."""
        for i, card in enumerate(self.entry_cards):
            card.card_number = i + 1
                    
    def _get_button_style(self, primary=False, secondary=False):
        """Get styling for buttons."""
        if primary:
            return """
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                        stop:0 rgba(34, 139, 34, 0.8), stop:1 rgba(0, 100, 0, 0.8));
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 12px 20px;
                    font-size: 14px;
                    font-weight: 600;
                    min-width: 100px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                        stop:0 rgba(34, 139, 34, 1.0), stop:1 rgba(0, 100, 0, 1.0));
                }
            """
        elif secondary:
            return """
                QPushButton {
                    background: rgba(255, 100, 100, 0.3);
                    border: 1px solid rgba(255, 100, 100, 0.5);
                    border-radius: 8px;
                    color: white;
                    padding: 12px 20px;
                    font-size: 14px;
                    font-weight: 500;
                    min-width: 100px;
                }
                QPushButton:hover {
                    background: rgba(255, 100, 100, 0.5);
                    border-color: rgba(255, 100, 100, 0.8);
                }
            """
        else:
            return """
                QPushButton {
                    background: rgba(255, 255, 255, 0.1);
                    border: 1px solid rgba(255, 255, 255, 0.3);
                    border-radius: 8px;
                    color: white;
                    padding: 12px 20px;
                    font-size: 14px;
                    font-weight: 500;
                    min-width: 100px;
                }
                QPushButton:hover {                    background: rgba(255, 255, 255, 0.15);
                    border-color: rgba(255, 255, 255, 0.4);
                }
            """
    
    def _save_all_entries(self):
        """Save all valid entries with enhanced validation feedback."""
        valid_entries = []
        invalid_cards = []
        
        # Validate all cards and collect results
        for i, card in enumerate(self.entry_cards):
            if card.is_valid():
                valid_entries.append(card.get_entry_data())
            elif card._has_any_data():  # Only consider cards with some data as invalid
                invalid_cards.append(i + 1)  # Card numbers start from 1
        
        # Check if there are invalid cards with data
        if invalid_cards:
            invalid_count = len(invalid_cards)
            card_list = ", ".join(map(str, invalid_cards[:5]))  # Show first 5
            if len(invalid_cards) > 5:
                card_list += f", and {len(invalid_cards) - 5} more"
            
            QMessageBox.warning(
                self, 
                "Invalid Entries Detected", 
                f"Cannot save: {invalid_count} entry card(s) have invalid or missing account information.\n\n"
                f"Please check cards: {card_list}\n\n"
                "⚠ Account fields with red borders contain invalid accounts.\n"
                "⚠ Account fields with orange borders are required but empty.\n\n"
                "Only entries with valid accounts from the chart of accounts will be saved."
            )
            return
        
        if not valid_entries:
            QMessageBox.warning(self, "No Valid Entries", "Please fill out at least one complete entry.")
            return
        
        try:
            # Save each entry
            for entry in valid_entries:
                if hasattr(self.system, 'add_journal_entry'):
                    self.system.add_journal_entry(
                        entry['date'],
                        entry['description'],
                        entry['debit_account'],
                        entry['credit_account'],
                        entry['amount']
                    )
            
            QMessageBox.information(self, "Success", f"Successfully saved {len(valid_entries)} entries!")
            
            # Clear all cards after successful save
            self._clear_all_entries()
            
            # Emit signal for refresh
            self.entries_saved.emit()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save entries: {e}")
    
    def _clear_all_entries(self):
        """Clear all entry cards."""
        for card in self.entry_cards:
            card.clear_entry()
        self._update_summary()
    
    def _import_file(self):
        """Import entries from CSV/Excel file with intelligent account matching."""
        try:
            from ..components.enhanced_csv_import import EnhancedCSVImportDialog
            
            # Create and show the enhanced import dialog
            import_dialog = EnhancedCSVImportDialog(self.system, self)
            
            if import_dialog.exec() == QDialog.DialogCode.Accepted:
                # Get processed import data
                import_data = import_dialog.get_import_data()
                summary = import_dialog.get_import_summary()
                
                if not import_data:
                    QMessageBox.warning(self, "No Data", "No valid transactions found to import.")
                    return
                
                # Clear existing cards
                self._clear_all_entries()
                
                # Ensure we have enough cards
                while len(self.entry_cards) < len(import_data):
                    self._add_new_card()
                
                # Populate cards with processed data
                for i, entry_data in enumerate(import_data):
                    if i < len(self.entry_cards):
                        card = self.entry_cards[i]
                        card.set_entry_data(entry_data)
                
                # Show import summary
                total = summary['total_processed']
                skipped = summary['skipped_rows']
                mappings = summary['mappings_used']
                
                summary_msg = f"""
                <h3>Import Completed Successfully!</h3>
                <p><b>Transactions Imported:</b> {total}</p>
                <p><b>Rows Skipped:</b> {skipped}</p>
                <p><b>Account Mappings Applied:</b> {mappings}</p>
                <p><i>All account names have been intelligently matched to your chart of accounts.</i></p>
                """
                
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle("Import Summary")
                msg_box.setTextFormat(Qt.TextFormat.RichText)
                msg_box.setText(summary_msg)
                msg_box.setIcon(QMessageBox.Icon.Information)
                msg_box.exec()
                
                self._update_summary()
                
        except ImportError:
            # Fallback to simple import if enhanced dialog is not available
            self._simple_import_file()
        except Exception as e:
            QMessageBox.critical(self, "Import Error", f"Failed to import file: {e}")
    
    def _simple_import_file(self):
        """Simple CSV/Excel import without account matching (fallback)."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Transactions", "", 
            "Excel files (*.xlsx *.xls);;CSV files (*.csv);;All files (*.*)"
        )
        
        if file_path:
            try:
                # Read the file
                if file_path.endswith(('.xlsx', '.xls')):
                    df = pd.read_excel(file_path)
                else:
                    df = pd.read_csv(file_path)
                
                # Clear existing cards
                self._clear_all_entries()
                
                # Ensure we have enough cards
                while len(self.entry_cards) < len(df):
                    self._add_new_card()
                
                # Populate cards with data
                for i, row in df.iterrows():
                    if i < len(self.entry_cards):
                        card = self.entry_cards[i]
                        card.set_entry_data({
                            'date': str(row.get('Date', '')),
                            'description': str(row.get('Description', '')),
                            'debit_account': str(row.get('Debit Account', '')),
                            'credit_account': str(row.get('Credit Account', '')),
                            'amount': str(row.get('Amount', ''))
                        })
                
                QMessageBox.information(self, "Import Successful", f"Imported {len(df)} entries from file.")
                self._update_summary()
                
            except Exception as e:
                QMessageBox.critical(self, "Import Error", f"Failed to import file: {e}")
    
    def refresh_all_entry_cards_accounts(self, accounts):
        """Refresh the account lists in all entry cards with the latest accounts."""
        for card in self.entry_cards:
            card.refresh_accounts(accounts)
    
    def refresh_accounts_from_system(self):
        """Reload accounts from the system and refresh all entry cards."""
        # Load fresh accounts from the system
        try:
            if hasattr(self.system, 'get_all_accounts'):
                accounts_data = self.system.get_all_accounts()
                # accounts_data is a list of tuples: (name, type, code, parent_code, level, is_postable, description)
                new_accounts = [f"{acc[2]} - {acc[0]}" for acc in accounts_data if acc[5]]  # Only postable accounts
            else:
                # Fallback for basic system
                new_accounts = [
                    "1001 - Cash",
                    "1002 - Bank Account", 
                    "1100 - Accounts Receivable",
                    "2001 - Accounts Payable",
                    "3001 - Owner's Equity",
                    "4001 - Sales Revenue",
                    "5001 - Cost of Goods Sold",
                    "6001 - Operating Expenses"
                ]
            
            # Update the main accounts list and refresh all cards
            self.accounts = new_accounts
            self.refresh_all_entry_cards_accounts(new_accounts)
            
        except Exception as e:
            print(f"Error refreshing accounts: {e}")
