"""
Card-Based Transaction Entry - Clean Implementation
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QLineEdit, QDateEdit, QFrame, QGridLayout, QSizePolicy, QGraphicsOpacityEffect,
    QMenu
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal, QPropertyAnimation, QEasingCurve
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
        self.accounts = []  # Initialize empty accounts list
        self._setup_ui()
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        
    def _setup_ui(self):
        """Setup the card-based UI."""
        # Set fixed size policy to prevent dynamic resizing
        self.setFixedHeight(80)  # Reduced height since no title section
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        
        # Modern compact card styling with fixed dimensions
        self.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(0, 0, 0, 0.3);
                border-radius: 8px;
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
        self.debit_combo.setMinimumWidth(160)
        self.debit_combo.setStyleSheet(self._get_single_row_field_style())
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
        self.credit_combo.setMinimumWidth(160)
        self.credit_combo.setStyleSheet(self._get_single_row_field_style())
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
            background: rgba(255, 255, 255, 0.1);            border: 1px solid rgba(0, 0, 0, 0.3);
            border-radius: 4px;
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
        
    def set_entry_data(self, data):
        """Set the transaction data."""
        date_str = data.get('date', '')
        if date_str:
            try:
                # Attempt to parse multiple date formats
                dt = datetime.strptime(date_str, '%Y-%m-%d')
                self.date_edit.setDate(QDate(dt))
            except ValueError:
                try:
                    dt = datetime.strptime(date_str, '%m/%d/%Y')
                    self.date_edit.setDate(QDate(dt))
                except ValueError:
                    self.date_edit.setDate(QDate.currentDate()) # Fallback
        else:            self.date_edit.setDate(QDate.currentDate())

        self.desc_edit.setText(data.get('description', ''))
        self.debit_combo.setTextWithValidation(data.get('debit_account', ''))
        self.credit_combo.setTextWithValidation(data.get('credit_account', ''))
        self.amount_edit.setText(str(data.get('amount', '')))

        # After setting data, explicitly trigger validation and styling updates        self.update_ui_and_validation()

    def update_ui_and_validation(self):
        """Force an update of the UI and re-apply validation styling."""
        # Force refresh of combo boxes to ensure they display the correct values
        self.debit_combo.force_refresh()
        self.credit_combo.force_refresh()
        
        # Apply validation styling
        self.apply_incomplete_styling()
        
        # Force repaint of the entire card
        self.update()
        self.repaint()
    
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
    
    def has_incomplete_data(self):
        """Check if card has some data but is incomplete (missing required fields)."""
        try:
            if not self._has_any_data():
                return False  # Completely empty cards are not incomplete
            
            data = self.get_entry_data()
            # Improved validation logic with better field checking
            description_valid = bool(data['description'].strip())
            
            # Safe validation for debit account
            debit_text = data['debit_account'].strip()
            debit_valid = (debit_text and 
                          debit_text != '-- Select Account --')
            if hasattr(self.debit_combo, 'isValidAccount'):
                try:
                    debit_valid = debit_valid and self.debit_combo.isValidAccount()
                except:
                    pass  # If validation fails, use basic check
            
            # Safe validation for credit account  
            credit_text = data['credit_account'].strip()
            credit_valid = (credit_text and 
                           credit_text != '-- Select Account --')
            if hasattr(self.credit_combo, 'isValidAccount'):
                try:
                    credit_valid = credit_valid and self.credit_combo.isValidAccount()
                except:
                    pass  # If validation fails, use basic check
            
            amount_text = data['amount'].strip()
            amount_valid = bool(amount_text and amount_text != '0' and amount_text != '0.00')
            
            return not all([description_valid, debit_valid, credit_valid, amount_valid])
        except Exception as e:
            print(f"❌ Error checking incomplete data: {e}")
            return False  # If we can't validate, assume it's complete
    
    def apply_incomplete_styling(self):
        """Apply yellow outline to empty fields when card has incomplete data."""
        try:
            if not self.has_incomplete_data():
                self.clear_validation_styling()
                return
                
            data = self.get_entry_data()
            
            # Apply yellow styling to empty fields - with improved field checking
            if not data['description'].strip():
                self._apply_yellow_border(self.desc_edit)
            else:
                self._clear_field_styling(self.desc_edit)
                
            # Improved debit account validation with better checking
            debit_text = data['debit_account'].strip()
            debit_invalid = (not debit_text or debit_text == '-- Select Account --')
            
            # If we have text, validate it properly
            if debit_text and hasattr(self.debit_combo, 'isValidAccount'):
                try:
                    # Check if the combo box considers this valid
                    is_valid = self.debit_combo.isValidAccount()
                    print(f"🔍 Debit account '{debit_text}' validation: {is_valid}")
                    if is_valid:
                        debit_invalid = False
                    else:
                        # Additional check - if it's in our valid accounts list, it's valid
                        if hasattr(self.debit_combo, 'valid_accounts'):
                            debit_invalid = debit_text not in self.debit_combo.valid_accounts
                            print(f"🔍 Checking against valid_accounts: {not debit_invalid}")
                except Exception as e:
                    # If validation fails, use basic text check
                    print(f"❌ Debit validation error: {e}")
                    debit_invalid = not debit_text or debit_text == '-- Select Account --'
            elif debit_text:
                print(f"🔍 Debit combo doesn't have isValidAccount method, text: '{debit_text}'")
            
            if debit_invalid:
                print(f"🟡 Applying yellow border to debit account")
                self._apply_yellow_border(self.debit_combo)
            else:
                print(f"⚪ Clearing styling for debit account")
                self._clear_field_styling(self.debit_combo)
                
            # Improved credit account validation with better checking
            credit_text = data['credit_account'].strip()
            credit_invalid = (not credit_text or credit_text == '-- Select Account --')
            
            # If we have text, validate it properly
            if credit_text and hasattr(self.credit_combo, 'isValidAccount'):
                try:
                    # Check if the combo box considers this valid
                    if self.credit_combo.isValidAccount():
                        credit_invalid = False
                    else:
                        # Additional check - if it's in our valid accounts list, it's valid
                        if hasattr(self.credit_combo, 'valid_accounts'):
                            credit_invalid = credit_text not in self.credit_combo.valid_accounts
                except Exception as e:
                    # If validation fails, use basic text check
                    credit_invalid = not credit_text or credit_text == '-- Select Account --'
            
            if credit_invalid:
                self._apply_yellow_border(self.credit_combo)
            else:
                self._clear_field_styling(self.credit_combo)
                
            # Amount validation with better empty checking
            amount_text = data['amount'].strip()
            if not amount_text or amount_text == '0' or amount_text == '0.00':
                self._apply_yellow_border(self.amount_edit)
            else:
                self._clear_field_styling(self.amount_edit)
        except Exception as e:
            print(f"❌ Error applying validation styling: {e}")
            # On error, just clear all styling
            try:
                self.clear_validation_styling()
            except:
                pass
    
    def clear_validation_styling(self):
        """Clear any validation-related styling from all fields."""
        base_style = self._get_single_row_field_style()
        self.desc_edit.setStyleSheet(base_style)
        self.debit_combo.setStyleSheet(base_style)
        self.credit_combo.setStyleSheet(base_style)
        self.amount_edit.setStyleSheet(base_style)
    
    def clear_entry(self):
        """Clear all fields in the entry card."""
        self.date_edit.setDate(QDate.currentDate())
        self.desc_edit.clear()
        self.debit_combo.clear_selection()
        self.credit_combo.clear_selection()
        self.amount_edit.clear()
        self.clear_validation_styling()
    
    def _apply_yellow_border(self, widget):
        """Apply yellow border to indicate missing required field."""
        if hasattr(widget, 'setStyleSheet'):
            base_style = self._get_base_style_for_widget(widget)
            yellow_style = base_style + """                border: 1px solid rgba(255, 193, 7, 0.9) !important;
                background: rgba(255, 193, 7, 0.1) !important;
            """
            widget.setStyleSheet(yellow_style)
    
    def _clear_field_styling(self, widget):
        """Clear validation styling and restore normal styling."""
        if hasattr(widget, 'setStyleSheet'):
            base_style = self._get_base_style_for_widget(widget)
            widget.setStyleSheet(base_style)
    
    def _get_base_style_for_widget(self, widget):
        """Get the base style for a widget type."""
        if widget == self.desc_edit or widget == self.amount_edit:
            return self._get_single_row_field_style()
        elif isinstance(widget, EditableAccountComboBox):
            return self._get_single_row_field_style()
        else:
            return self._get_single_row_field_style()
    
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
                background: rgba(40, 40, 40, 0.95);                border: 1px solid rgba(0, 0, 0, 0.3);
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
    
    def refresh_accounts(self, new_accounts):
        """Refresh the account lists when accounts change."""
        try:
            self.accounts = new_accounts
            
            # Save current selections
            current_debit = self.debit_combo.currentText()
            current_credit = self.credit_combo.currentText()
            
            # Update the account lists
            self._populate_account_combo(self.debit_combo)
            self._populate_account_combo(self.credit_combo)
            
            # Restore selections if they still exist
            if current_debit in new_accounts:
                self.debit_combo.setCurrentText(current_debit)
            if current_credit in new_accounts:
                self.credit_combo.setCurrentText(current_credit)
                
        except Exception as e:
            print(f"Error refreshing accounts in card: {e}")
    
    def _is_account_valid(self, account_text):
        """Check if an account exists in the system."""
        if not account_text or not account_text.strip():
            return False
        
        try:
            # Check if account exists in the system
            all_accounts = self.system.get_postable_accounts()
            formatted_accounts = [f"{acc['code']} - {acc['name']}" for acc in all_accounts]
            
            return account_text.strip() in formatted_accounts
        except:
            return False
    
    def connect_validation_updates(self, validation_callback=None):
        """Connect field changes to validation updates for immediate feedback."""
        try:
            # Store the validation callback for later use if provided
            if validation_callback:
                self._validation_callback = validation_callback
            
            # Disconnect any existing connections first to avoid duplicates
            self._disconnect_validation_signals()
            
            # Connect all field changes to our unified handler
            if hasattr(self, 'desc_edit') and self.desc_edit:
                self.desc_edit.textChanged.connect(self._on_field_changed)
            if hasattr(self, 'debit_combo') and self.debit_combo:
                self.debit_combo.currentTextChanged.connect(self._on_field_changed)
            if hasattr(self, 'credit_combo') and self.credit_combo:
                self.credit_combo.currentTextChanged.connect(self._on_field_changed)
            if hasattr(self, 'amount_edit') and self.amount_edit:
                self.amount_edit.textChanged.connect(self._on_field_changed)
        except Exception as e:
            print(f"❌ Error connecting validation updates: {e}")
    
    def _disconnect_validation_signals(self):
        """Safely disconnect validation signals to avoid duplicates."""
        try:
            if hasattr(self, 'desc_edit') and self.desc_edit:
                self.desc_edit.textChanged.disconnect(self._on_field_changed)
            if hasattr(self, 'debit_combo') and self.debit_combo:
                self.debit_combo.currentTextChanged.disconnect(self._on_field_changed)
            if hasattr(self, 'credit_combo') and self.credit_combo:
                self.credit_combo.currentTextChanged.disconnect(self._on_field_changed)
            if hasattr(self, 'amount_edit') and self.amount_edit:
                self.amount_edit.textChanged.disconnect(self._on_field_changed)
        except:
            pass  # Ignore if signals weren't connected
    
    def _on_field_changed(self):
        """Handle immediate field change to clear validation styling if field becomes valid and trigger full validation."""
        try:
            sender = self.sender()
            
            # Debug: Print which field changed
            field_name = "unknown"
            if sender == self.desc_edit:
                field_name = "description"
            elif sender == self.debit_combo:
                field_name = "debit_account"
            elif sender == self.credit_combo:
                field_name = "credit_account"
            elif sender == self.amount_edit:
                field_name = "amount"
            
            print(f"🔄 Field changed in card {self.card_number}: {field_name}")
            
            # Immediately apply validation styling to all fields
            # This ensures that invalid fields (like manual deletions) show yellow immediately
            self.apply_incomplete_styling()
            
            # Also trigger the parent validation callback if available
            if hasattr(self, '_validation_callback') and self._validation_callback:
                self._validation_callback()
            
        except Exception as e:
            print(f"❌ Error in field change handler: {e}")
    
    def manual_validation_test(self):
        """Manual test method to verify validation is working correctly."""
        print(f"📋 Testing validation for card {self.card_number}:")
        
        data = self.get_entry_data()
        print(f"   • Description: '{data['description']}' ({'✅ Valid' if data['description'].strip() else '❌ Empty'})")
        print(f"   • Debit Account: '{data['debit_account']}' ({'✅ Valid' if data['debit_account'].strip() and data['debit_account'] != '-- Select Account --' else '❌ Invalid'})")
        print(f"   • Credit Account: '{data['credit_account']}' ({'✅ Valid' if data['credit_account'].strip() and data['credit_account'] != '-- Select Account --' else '❌ Invalid'})")
        print(f"   • Amount: '{data['amount']}' ({'✅ Valid' if data['amount'].strip() and data['amount'] not in ['0', '0.00'] else '❌ Invalid'})")
        
        has_any_data = self._has_any_data()
        has_incomplete = self.has_incomplete_data()
        print(f"   • Has any data: {has_any_data}")
        print(f"   • Has incomplete data: {has_incomplete}")
        
        if has_incomplete:
            print("   🟡 Applying yellow styling...")
            self.apply_incomplete_styling()
        else:
            print("   ⚪ Clearing styling...")
            self.clear_validation_styling()