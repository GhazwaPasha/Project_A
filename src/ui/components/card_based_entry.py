"""
Card-Based Transaction Entry - Clean Implementation
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QLineEdit, QDateEdit, QFrame, QGridLayout, QSizePolicy, QGraphicsOpacityEffect,
    QMenu
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal, QPropertyAnimation, QEasingCurve, QTimer
from PyQt6.QtGui import QFont
from datetime import datetime
from ..components.widgets import EditableAccountComboBox


class CardBasedTransactionEntry(QFrame):
    """Self-contained transaction entry card with internal labels."""
    
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
                self.accounts = [f"{acc[2]} - {acc[0]}" for acc in accounts_data if acc[5]]
            else:            self.accounts = ["1001 - Cash", "2001 - Accounts Payable"]
        except Exception as e:
            print(f"Error loading accounts: {e}")
            self.accounts = ["1001 - Cash", "2001 - Accounts Payable"]
        
    def _setup_ui(self):
        """Setup the card-based UI."""        # Set fixed size policy to prevent dynamic resizing
        self.setFixedHeight(80)  # Reduced height since no title section
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        
        # Modern compact card styling with fixed dimensions
        self.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 10px;
                padding: 12px 16px;
                margin: 2px 0px;
                min-height: 76px;
                max-height: 76px;
            }
            QFrame:hover {
                background: rgba(255, 255, 255, 0.12);
                border-color: rgba(255, 255, 255, 0.25);
            }
        """)
        
        # Main layout - simplified without title section
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(0)  # No spacing since we only have fields
        
        # Single row field layout with labels above fields
        fields_layout = QHBoxLayout()
        fields_layout.setSpacing(12)
        fields_layout.setContentsMargins(0, 0, 0, 0)  # No extra margins
        
        # Date field
        date_container = QVBoxLayout()
        date_container.setSpacing(3)
        date_container.setContentsMargins(0, 0, 0, 0)
        date_label = QLabel("DATE")
        date_label.setStyleSheet(self._get_single_row_label_style())
        date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        date_label.setFixedHeight(14)  # Ensure label has proper height
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setFixedHeight(28)
        self.date_edit.setFixedWidth(120)
        self.date_edit.setStyleSheet(self._get_single_row_field_style())
        date_container.addWidget(date_label)
        date_container.addWidget(self.date_edit)
        
        # Description field
        desc_container = QVBoxLayout()
        desc_container.setSpacing(3)
        desc_container.setContentsMargins(0, 0, 0, 0)
        desc_label = QLabel("DESCRIPTION")
        desc_label.setStyleSheet(self._get_single_row_label_style())
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setFixedHeight(14)  # Ensure label has proper height
        self.desc_edit = QLineEdit()
        self.desc_edit.setPlaceholderText("Enter description...")
        self.desc_edit.setFixedHeight(28)
        self.desc_edit.setMinimumWidth(180)
        self.desc_edit.setStyleSheet(self._get_single_row_field_style())
        desc_container.addWidget(desc_label)
        desc_container.addWidget(self.desc_edit)
          # Debit account field
        debit_container = QVBoxLayout()
        debit_container.setSpacing(3)
        debit_container.setContentsMargins(0, 0, 0, 0)
        debit_label = QLabel("DEBIT ACCOUNT")
        debit_label.setStyleSheet(self._get_single_row_label_style())
        debit_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        debit_label.setFixedHeight(14)  # Ensure label has proper height
        self.debit_combo = EditableAccountComboBox()
        self.debit_combo.setFixedHeight(28)
        self.debit_combo.setMinimumWidth(120)
        self.debit_combo.setStyleSheet(self._get_single_row_field_style())
        self._populate_account_combo(self.debit_combo)
        debit_container.addWidget(debit_label)
        debit_container.addWidget(self.debit_combo)
        
        # Credit account field
        credit_container = QVBoxLayout()
        credit_container.setSpacing(3)
        credit_container.setContentsMargins(0, 0, 0, 0)
        credit_label = QLabel("CREDIT ACCOUNT")
        credit_label.setStyleSheet(self._get_single_row_label_style())
        credit_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        credit_label.setFixedHeight(14)  # Ensure label has proper height
        self.credit_combo = EditableAccountComboBox()
        self.credit_combo.setFixedHeight(28)
        self.credit_combo.setMinimumWidth(120)
        self.credit_combo.setStyleSheet(self._get_single_row_field_style())
        self._populate_account_combo(self.credit_combo)
        credit_container.addWidget(credit_label)
        credit_container.addWidget(self.credit_combo)
          # Amount field
        amount_container = QVBoxLayout()
        amount_container.setSpacing(3)
        amount_container.setContentsMargins(0, 0, 0, 0)
        amount_label = QLabel("AMOUNT")
        amount_label.setStyleSheet(self._get_single_row_label_style())
        amount_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        amount_label.setFixedHeight(14)  # Ensure label has proper height
        self.amount_edit = QLineEdit()
        self.amount_edit.setPlaceholderText("0.00")
        self.amount_edit.setFixedHeight(28)
        self.amount_edit.setFixedWidth(100)
        self.amount_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.amount_edit.setStyleSheet(self._get_single_row_field_style())
        amount_container.addWidget(amount_label)
        amount_container.addWidget(self.amount_edit)
        
        # Add all containers to the single row layout
        fields_layout.addLayout(date_container)
        fields_layout.addLayout(desc_container, 1)  # Description expands
        fields_layout.addLayout(debit_container)
        fields_layout.addLayout(credit_container)
        fields_layout.addLayout(amount_container)        
        main_layout.addLayout(fields_layout)
          # Set tooltip to indicate right-click functionality
        self.setToolTip("Right-click to delete this transaction entry")
        
    def _get_single_row_label_style(self, field_type=None):
        """Get styling for single row labels."""
        return """
            color: rgba(255, 255, 255, 0.8);
            font-size: 9px;
            font-weight: 700;
            background: transparent;
            border: none;            padding: 1px 2px;
            margin: 0px;
            text-transform: uppercase;
            letter-spacing: 0.8px;
            min-height: 14px;
            max-height: 14px;
        """
        
    def _get_single_row_field_style(self):
        """Get styling for single row input fields."""
        return """
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 5px;
            padding: 4px 6px;
            color: rgba(255, 255, 255, 0.95);
            font-size: 12px;
            font-weight: 400;
            selection-background-color: rgba(100, 150, 255, 0.3);
            min-height: 26px;
            max-height: 26px;
        """
              
    def _populate_account_combo(self, combo):
        """Populate account combo."""
        try:
            combo.setAccountList(self.accounts)
            combo.setPlaceholderText("Select or type account...")
            combo.clear_selection()
        except Exception as e:
            combo.clear()
            for account in self.accounts:
                combo.addItem(account)
                
    def get_entry_data(self):
        """Get the transaction data."""
        return {
            'date': self.date_edit.date().toString('yyyy-MM-dd'),
            'description': self.desc_edit.text().strip(),
            'debit_account': self.debit_combo.currentText().strip(),
            'credit_account': self.credit_combo.currentText().strip(),
            'amount': self.amount_edit.text().strip()
        }
        
    def is_valid(self):
        """Check if entry is valid."""
        data = self.get_entry_data()
        return all([
            data['description'],
            data['debit_account'],
            data['credit_account'],
            data['amount']
        ])
    
    def _has_any_data(self):
        """Check if entry has any data entered."""
        data = self.get_entry_data()
        return any([
            data['description'],
            data['debit_account'] and data['debit_account'] != '-- Select Account --',            data['credit_account'] and data['credit_account'] != '-- Select Account --',
            data['amount']
        ])
    
    def animate_and_remove(self):
        """Animate the card removal with a smooth fade-out effect."""
        # Create opacity effect for animation
        self.opacity_effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.opacity_effect)
        
        # Create fade animation
        self.fade_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_animation.setDuration(250)  # 250ms smooth fade
        self.fade_animation.setStartValue(1.0)
        self.fade_animation.setEndValue(0.0)
        self.fade_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # When animation finishes, emit the remove signal
        self.fade_animation.finished.connect(lambda: self.remove_requested.emit(self))
        
        # Start the animation
        self.fade_animation.start()
        
    def mousePressEvent(self, event):
        """Handle mouse press events for context menu."""
        if event.button() == Qt.MouseButton.RightButton:
            self._show_context_menu(event.globalPosition().toPoint())
        else:
            super().mousePressEvent(event)
    
    def _show_context_menu(self, position):
        """Show context menu with delete option."""
        context_menu = QMenu(self)
        
        # Style the context menu to match the app theme
        context_menu.setStyleSheet("""
            QMenu {
                background: rgba(40, 40, 40, 0.95);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                padding: 4px;
                color: rgba(255, 255, 255, 0.9);
                font-size: 13px;
            }
            QMenu::item {
                background: transparent;
                padding: 8px 16px;
                border-radius: 4px;
                margin: 1px;
            }
            QMenu::item:selected {
                background: rgba(255, 80, 80, 0.3);
                color: rgba(255, 255, 255, 1.0);
            }
            QMenu::item:hover {
                background: rgba(255, 80, 80, 0.5);
            }
        """)
        
        # Add delete action
        delete_action = context_menu.addAction("🗑️ Delete Entry")
        delete_action.triggered.connect(self.animate_and_remove)
        
        # Show the menu at the cursor position
        context_menu.exec(position)
        
    def enterEvent(self, event):
        """Change cursor to indicate right-click functionality."""
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Reset cursor when leaving the card."""
        self.setCursor(Qt.CursorShape.ArrowCursor)
        super().leaveEvent(event)
    
    def clear_entry(self):
        """Clear all entry fields."""
        self.date_edit.setDate(QDate.currentDate())
        self.desc_edit.clear()
        self.debit_combo.setCurrentText("")
        self.credit_combo.setCurrentText("")
        self.amount_edit.clear()
    
    def set_entry_data(self, data):
        """Set entry data from a dictionary."""
        if 'date' in data and data['date']:
            try:
                # Try to parse the date string
                date_str = str(data['date']).strip()
                if date_str:
                    # Handle various date formats
                    for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y/%m/%d']:
                        try:
                            parsed_date = datetime.strptime(date_str, fmt)
                            self.date_edit.setDate(QDate.fromString(parsed_date.strftime('%Y-%m-%d'), 'yyyy-MM-dd'))
                            break
                        except ValueError:
                            continue
            except:
                pass  # Use current date if parsing fails
        
        if 'description' in data:
            self.desc_edit.setText(str(data['description']).strip())
        
        if 'debit_account' in data:
            debit_text = str(data['debit_account']).strip()
            if debit_text:
                self.debit_combo.setTextWithValidation(debit_text)
        
        if 'credit_account' in data:
            credit_text = str(data['credit_account']).strip()
            if credit_text:
                self.credit_combo.setTextWithValidation(credit_text)
        
        if 'amount' in data:
            self.amount_edit.setText(str(data['amount']).strip())
    
    def refresh_accounts(self, new_accounts):
        """Refresh account lists with new accounts."""
        self.accounts = new_accounts
        current_debit = self.debit_combo.currentText()
        current_credit = self.credit_combo.currentText()
        
        self._populate_account_combo(self.debit_combo)
        self._populate_account_combo(self.credit_combo)
        
        # Restore selections if they still exist
        if current_debit:
            self.debit_combo.setCurrentText(current_debit)
        if current_credit:
            self.credit_combo.setCurrentText(current_credit)