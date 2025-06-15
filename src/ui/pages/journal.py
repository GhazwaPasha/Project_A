"""
Clean, Professional Journal Page with Tab System
Single entry form + bulk entry in tabs, clean transaction display
No complexity, no clutter, just what accountants need.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QLineEdit, QComboBox, QFrame, QDateEdit, QMessageBox, 
    QScrollArea, QSpacerItem, QSizePolicy, QTabWidget
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont
from datetime import datetime
from ...core.accounting_system import AccountingSystem
from ..components.widgets import PageHeader, NonScrollableComboBox, EditableAccountComboBox
from ..components.styles import ModernStyles, GlassmorphismHelper
from ..common import ResponsiveHelper
from .bulk_entry import BulkEntryPage

class TransactionCard(QFrame):
    """A clean card for displaying a transaction."""
    
    def __init__(self, entry_data):
        super().__init__()
        self.entry_data = entry_data
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup the transaction card UI."""
        self.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                margin: 2px 0px;
            }
            QFrame:hover {
                background: rgba(255, 255, 255, 0.08);
                border-color: rgba(255, 255, 255, 0.2);
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)
          # Date column
        date_label = QLabel(self.entry_data.get('date', ''))
        date_label.setFixedWidth(80)
        date_label.setStyleSheet("color: rgba(255, 255, 255, 0.7); font-weight: 500; background: transparent; border: none;")
        
        # Description column
        desc_label = QLabel(self.entry_data.get('description', ''))
        desc_label.setStyleSheet("color: rgba(255, 255, 255, 0.9); font-weight: 500; background: transparent; border: none;")
        desc_label.setWordWrap(True)
        
        # From account column (Debit)
        from_account = self.entry_data.get('from_account', '')
        from_label = QLabel(from_account)
        from_label.setFixedWidth(140)
        from_label.setStyleSheet("color: rgba(255, 100, 100, 0.9); font-weight: 500; background: transparent; border: none;")
        
        # To account column (Credit)
        to_account = self.entry_data.get('to_account', '')
        to_label = QLabel(to_account)
        to_label.setFixedWidth(140)
        to_label.setStyleSheet("color: rgba(100, 255, 100, 0.9); font-weight: 500; background: transparent; border: none;")
        
        # Amount column
        amount = self.entry_data.get('amount', '0.00')
        amount_label = QLabel(f"${amount}")
        amount_label.setFixedWidth(100)
        amount_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        amount_label.setStyleSheet("color: rgba(255, 255, 255, 0.9); font-weight: bold; font-size: 14px; background: transparent; border: none;")
        
        layout.addWidget(date_label)
        layout.addWidget(desc_label, 1)  # This will stretch
        layout.addWidget(from_label)
        layout.addWidget(to_label)
        layout.addWidget(amount_label)


class JournalPage(QWidget):
    """Tabbed journal page with single entry and bulk entry tabs."""
    
    def __init__(self, system, parent=None):
        super().__init__(parent)
        self.system = system
        self._setup_ui()
        self._apply_styling()
        
    def _apply_styling(self):
        """Apply modern glassmorphism styling to the tabbed journal page."""
        GlassmorphismHelper.apply_main_container_effect(self)
        self.setStyleSheet(self._get_tab_style() + ModernStyles.get_complete_stylesheet())
        
    def _setup_ui(self):
        """Setup the tabbed interface."""
        # Main layout with responsive margins
        main_layout = QVBoxLayout(self)
        responsive_margin = ResponsiveHelper.scale_size(32, 24, 48)
        main_layout.setContentsMargins(responsive_margin, responsive_margin, 
                                     responsive_margin, responsive_margin)
        main_layout.setSpacing(ResponsiveHelper.scale_size(32, 24, 48))
        
        # Create the page header with descriptive subtext
        header = PageHeader("Journal Entry", "Record and manage your financial transactions")
        main_layout.addWidget(header)
        
        # Create the tab widget with proper spacing
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(self._get_tab_style())
        
        # Create and add the single entry tab
        self.single_entry_tab = SingleEntryTab(self.system)
        self.tab_widget.addTab(self.single_entry_tab, "Single Entry")
        
        # Create and add the bulk entry tab
        self.bulk_entry_tab = BulkEntryPage(self.system)
        self.tab_widget.addTab(self.bulk_entry_tab, "Bulk Entry")
        
        # Set default tab
        self.tab_widget.setCurrentIndex(0)  # Single entry is default
        
        # Add tab widget to main layout
        main_layout.addWidget(self.tab_widget, 1)  # Give it a stretch factor of 1
        
        # Add stretch to ensure proper spacing
        main_layout.addStretch()
    
    def _get_tab_style(self):
        """Get the styling for the tab widget."""
        return """
            QTabWidget::pane {
                border: none;
                background: transparent;
                margin-top: 2px;
            }
            
            QTabBar::tab {
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                color: white;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: 500;
                font-size: 13px;
                margin-right: 8px;
                min-width: 100px;
                max-width: 160px;
            }
            
            QTabBar::tab:hover {
                background: rgba(255, 255, 255, 0.2);
                border-color: rgba(255, 255, 255, 0.3);
            }
            
            QTabBar::tab:selected {
                background: rgba(100, 181, 246, 0.3);
                border-color: #64B5F6;
                color: #64B5F6;
                font-weight: 600;
            }
            
            QTabBar::tab:first {
                margin-left: 0;
            }
        """


class SingleEntryTab(QWidget):
    """Single journal entry tab containing the form and transaction history."""
    
    def __init__(self, system, parent=None):
        super().__init__(parent)
        self.system = system
        self.is_form_expanded = False  # Form starts collapsed
        self.accounts = []  # Initialize accounts list
        self._load_accounts()  # Load accounts first
        self._setup_ui()
        self._load_transactions()
        
    def _setup_ui(self):
        """Setup the single entry tab UI."""
        # Main layout for the tab
        tab_layout = QVBoxLayout(self)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.setSpacing(0)
        
        # Create scroll area for the main content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea, QWidget#scrollAreaWidgetContents {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: rgba(255, 255, 255, 0.1);
                width: 8px;
                border-radius: 4px;
                margin: 0;
            }
            QWidget {
                background: transparent;
            }
        """)
        
        # Main container widget for scroll area
        main_container = QWidget()
        main_layout = QVBoxLayout(main_container)
        # Use consistent spacing from dashboard
        main_layout.setContentsMargins(ResponsiveHelper.scale_size(32, 24, 48),
                                     ResponsiveHelper.scale_size(24, 16, 32),
                                     ResponsiveHelper.scale_size(32, 24, 48),
                                     ResponsiveHelper.scale_size(24, 16, 32))
        main_layout.setSpacing(ResponsiveHelper.scale_size(24, 16, 32))
        
        # Entry form section (collapsible)
        self.entry_form_container = self._create_entry_form()
        main_layout.addWidget(self.entry_form_container)
        
        # Add some spacing between form and transactions
        spacer = QWidget()
        spacer.setFixedHeight(ResponsiveHelper.scale_size(16, 12, 24))
        main_layout.addWidget(spacer)
        
        # Transactions section with title
        transactions_label = QLabel("Recent Transactions")
        transactions_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.9);
                font-size: 16px;
                font-weight: 600;
                background: transparent;
                padding-bottom: 8px;
            }
        """)
        main_layout.addWidget(transactions_label)
        
        # Transactions section
        transactions_section = self._create_transactions_section()
        main_layout.addWidget(transactions_section, 1)  # Allow it to expand
        
        # Set the container as the scroll area widget
        scroll_area.setWidget(main_container)
        tab_layout.addWidget(scroll_area)

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

    def _create_entry_form(self):
        """Create the entry form section."""
        # Container for the entire form section
        form_container = QFrame()
        form_container.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.06);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 12px;
                margin-bottom: 8px;
            }
        """)
        
        container_layout = QVBoxLayout(form_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        
        # Clickable header with expand/collapse functionality
        self.header_frame = QFrame()
        self.header_frame.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.08);
                border: none;
                border-radius: 12px;
                padding: 16px;
            }
            QFrame:hover {
                background: rgba(255, 255, 255, 0.12);
            }
        """)
        self.header_frame.mousePressEvent = self._toggle_form
        self.header_frame.setCursor(Qt.CursorShape.PointingHandCursor)
        
        header_layout = QHBoxLayout(self.header_frame)
        header_layout.setContentsMargins(20, 16, 20, 16)
        
        # Title and expand/collapse indicator
        self.header_title = QLabel("💰 Add New Transaction")
        self.header_title.setStyleSheet("""
            color: rgba(255, 255, 255, 0.9);
            font-size: 18px;
            font-weight: 600;
        """)
        
        self.expand_indicator = QLabel("▶")  # Collapsed by default
        self.expand_indicator.setStyleSheet("""
            color: rgba(255, 255, 255, 0.7);
            font-size: 16px;
            font-weight: bold;
        """)
        
        header_layout.addWidget(self.header_title)
        header_layout.addStretch()
        header_layout.addWidget(self.expand_indicator)
        
        container_layout.addWidget(self.header_frame)
        
        # Form content (initially hidden)
        self.form_content = QFrame()
        self.form_content.setStyleSheet("""
            QFrame {
                background: transparent;
                border: none;
                padding: 0px;
            }
        """)
        self.form_content.setVisible(False)  # Start collapsed
        
        self._create_form_fields()
        container_layout.addWidget(self.form_content)
        
        return form_container
        
    def _create_form_fields(self):
        """Create the form input fields."""
        form_layout = QVBoxLayout(self.form_content)
        form_layout.setContentsMargins(24, 16, 24, 24)
        form_layout.setSpacing(20)
        
        # Date field
        date_layout = QHBoxLayout()
        date_label = QLabel("Date:")
        date_label.setFixedWidth(100)
        date_label.setStyleSheet("color: rgba(255, 255, 255, 0.8); font-weight: 500;")
        
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setStyleSheet(self._get_field_style())
        
        date_layout.addWidget(date_label)
        date_layout.addWidget(self.date_edit)
        
        # Description field
        desc_layout = QHBoxLayout()
        desc_label = QLabel("Description:")
        desc_label.setFixedWidth(100)
        desc_label.setStyleSheet("color: rgba(255, 255, 255, 0.8); font-weight: 500;")
        
        self.desc_edit = QLineEdit()
        self.desc_edit.setPlaceholderText("Enter transaction description...")
        self.desc_edit.setStyleSheet(self._get_field_style())
        
        desc_layout.addWidget(desc_label)
        desc_layout.addWidget(self.desc_edit)
        
        # Account fields
        from_layout = QHBoxLayout()
        from_label = QLabel("Debit:")
        from_label.setFixedWidth(100)
        from_label.setStyleSheet("color: rgba(255, 255, 255, 0.8); font-weight: 500;")
        self.from_combo = EditableAccountComboBox()
        self.from_combo.setStyleSheet(self._get_field_style())
        self._populate_account_combo(self.from_combo)
        
        from_layout.addWidget(from_label)
        from_layout.addWidget(self.from_combo)
        
        to_layout = QHBoxLayout()
        to_label = QLabel("Credit:")
        to_label.setFixedWidth(100)
        to_label.setStyleSheet("color: rgba(255, 255, 255, 0.8); font-weight: 500;")
        
        self.to_combo = EditableAccountComboBox()
        self.to_combo.setStyleSheet(self._get_field_style())
        self._populate_account_combo(self.to_combo)
        
        to_layout.addWidget(to_label)
        to_layout.addWidget(self.to_combo)
        
        # Amount field
        amount_layout = QHBoxLayout()
        amount_label = QLabel("Amount:")
        amount_label.setFixedWidth(100)
        amount_label.setStyleSheet("color: rgba(255, 255, 255, 0.8); font-weight: 500;")
        
        self.amount_edit = QLineEdit()
        self.amount_edit.setPlaceholderText("0.00")
        self.amount_edit.setStyleSheet(self._get_field_style())
        
        amount_layout.addWidget(amount_label)
        amount_layout.addWidget(self.amount_edit)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("💾 Save Entry")
        self.save_btn.setStyleSheet(self._get_button_style())
        self.save_btn.clicked.connect(self._save_entry)
        
        self.clear_btn = QPushButton("🗑️ Clear")
        self.clear_btn.setStyleSheet(self._get_button_style(secondary=True))
        self.clear_btn.clicked.connect(self._clear_form)
        
        buttons_layout.addWidget(self.save_btn)
        buttons_layout.addWidget(self.clear_btn)
        buttons_layout.addStretch()
          # Add all layouts to form
        form_layout.addLayout(date_layout)
        form_layout.addLayout(desc_layout)
        form_layout.addLayout(from_layout)
        form_layout.addLayout(to_layout)
        form_layout.addLayout(amount_layout)
        form_layout.addLayout(buttons_layout)
        
    def _populate_account_combo(self, combo):
        """Populate account combo box with available accounts and enable strict validation."""
        # Use setAccountList for strict validation - only allows accounts from chart of accounts
        combo.setAccountList(self.accounts)
        # Set proper placeholder text
        combo.setPlaceholderText("Select or type account...")
        # Ensure it starts empty showing only placeholder
        combo.clear_selection()
    
    def _get_field_style(self):
        """Get styling for input fields."""
        return """
            QLineEdit, QComboBox, QDateEdit {
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                padding: 12px 16px;
                color: white;
                font-size: 14px;
                min-height: 20px;
            }
            QLineEdit:focus, QComboBox:focus, QDateEdit:focus {
                background: rgba(255, 255, 255, 0.15);
                border-color: rgba(0, 120, 215, 0.6);
            }
            QLineEdit::placeholder {
                color: rgba(255, 255, 255, 0.5);
                font-style: italic;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: none;
                border: none;
            }
        """
        
    def _get_button_style(self, secondary=False):
        """Get styling for buttons."""
        if secondary:
            return """
                QPushButton {
                    background: rgba(255, 255, 255, 0.1);
                    border: 1px solid rgba(255, 255, 255, 0.3);
                    border-radius: 8px;
                    color: white;
                    padding: 12px 24px;
                    font-size: 14px;
                    font-weight: 500;
                    min-width: 100px;
                }
                QPushButton:hover {
                    background: rgba(255, 255, 255, 0.15);
                    border-color: rgba(255, 255, 255, 0.4);
                }
            """
        else:
            return """
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                        stop:0 rgba(34, 139, 34, 0.8), stop:1 rgba(0, 100, 0, 0.8));
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 12px 24px;
                    font-size: 14px;
                    font-weight: 600;
                    min-width: 120px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                        stop:0 rgba(34, 139, 34, 1.0), stop:1 rgba(0, 100, 0, 1.0));
                }
            """
    
    def _toggle_form(self, event):
        """Toggle the form visibility."""
        self.is_form_expanded = not self.is_form_expanded
        self.form_content.setVisible(self.is_form_expanded)
        
        if self.is_form_expanded:
            self.expand_indicator.setText("▼")
            self.header_title.setText("💰 Add New Transaction (Click to collapse)")
        else:
            self.expand_indicator.setText("▶")
            self.header_title.setText("💰 Add New Transaction (Click to expand)")
    
    def _save_entry(self):
        """Save the journal entry."""
        try:
            # Get form data
            date = self.date_edit.date().toString("yyyy-MM-dd")
            description = self.desc_edit.text().strip()
            
            # For editable combo boxes, use currentText() to get typed text
            from_account = self.from_combo.currentText().strip()
            to_account = self.to_combo.currentText().strip()
            
            # If it's the placeholder text, treat as empty
            if from_account == "-- Select Account --":
                from_account = ""
            if to_account == "-- Select Account --":
                to_account = ""
                
            amount = self.amount_edit.text().strip()
            
            # Validate input
            if not all([description, from_account, to_account, amount]):
                QMessageBox.warning(self, "Validation Error", 
                                  "Please fill in all fields.")
                return
                
            if from_account == to_account:
                QMessageBox.warning(self, "Validation Error", 
                                  "Debit and Credit accounts cannot be the same.")
                return
                
            try:
                float(amount)
            except ValueError:
                QMessageBox.warning(self, "Validation Error", 
                                  "Please enter a valid amount.")
                return
            
            # Save to system
            if hasattr(self.system, 'add_journal_entry'):
                self.system.add_journal_entry(date, description, from_account, to_account, amount)
              # Show success message
            QMessageBox.information(self, "Success", "Transaction saved successfully!")
            
            # Clear form and refresh transactions
            self._clear_form()
            self._load_transactions()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save transaction: {e}")
    
    def _clear_form(self):
        """Clear all form fields."""
        self.desc_edit.clear()
        # Properly clear editable combo boxes to show placeholder
        self.from_combo.clear_selection()
        self.to_combo.clear_selection()
        self.amount_edit.clear()
        self.date_edit.setDate(QDate.currentDate())
        
    def _create_transactions_section(self):
        """Create the transactions history section."""
        section_frame = QFrame()
        section_frame.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.06);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 12px;
            }
        """)
        
        section_layout = QVBoxLayout(section_frame)
        section_layout.setContentsMargins(24, 20, 24, 24)
        section_layout.setSpacing(16)        # Header
        header_label = QLabel("Transaction History")
        header_label.setStyleSheet("""
            color: rgba(255, 255, 255, 0.9);
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 8px;
            background: transparent;
            border: none;
        """)
        section_layout.addWidget(header_label)
        
        # Column headers
        headers_frame = QFrame()
        headers_frame.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 8px;
                margin-bottom: 8px;
            }
        """)
        
        headers_layout = QHBoxLayout(headers_frame)
        headers_layout.setContentsMargins(16, 8, 16, 8)
        headers_layout.setSpacing(12)
          # Column header labels
        date_header = QLabel("Date")
        date_header.setFixedWidth(80)
        date_header.setStyleSheet("color: rgba(255, 255, 255, 0.8); font-weight: 600; font-size: 12px; background: transparent; border: none;")
        
        desc_header = QLabel("Description")
        desc_header.setStyleSheet("color: rgba(255, 255, 255, 0.8); font-weight: 600; font-size: 12px; background: transparent; border: none;")
        
        debit_header = QLabel("Debit Account")
        debit_header.setFixedWidth(140)
        debit_header.setStyleSheet("color: rgba(255, 100, 100, 0.8); font-weight: 600; font-size: 12px; background: transparent; border: none;")
        
        credit_header = QLabel("Credit Account")
        credit_header.setFixedWidth(140)
        credit_header.setStyleSheet("color: rgba(100, 255, 100, 0.8); font-weight: 600; font-size: 12px; background: transparent; border: none;")
        
        amount_header = QLabel("Amount")
        amount_header.setFixedWidth(100)
        amount_header.setAlignment(Qt.AlignmentFlag.AlignRight)
        amount_header.setStyleSheet("color: rgba(255, 255, 255, 0.8); font-weight: 600; font-size: 12px; background: transparent; border: none;")
        
        headers_layout.addWidget(date_header)
        headers_layout.addWidget(desc_header, 1)  # This will stretch
        headers_layout.addWidget(debit_header)
        headers_layout.addWidget(credit_header)
        headers_layout.addWidget(amount_header)
        
        section_layout.addWidget(headers_frame)
        
        # Transactions container with scroll
        self.transactions_container = QScrollArea()
        self.transactions_container.setWidgetResizable(True)
        self.transactions_container.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.transactions_container.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
        """)
        
        # Create transactions list widget
        self.transactions_widget = QWidget()
        self.transactions_layout = QVBoxLayout(self.transactions_widget)
        self.transactions_layout.setContentsMargins(0, 0, 0, 0)
        self.transactions_layout.setSpacing(8)
        
        self.transactions_container.setWidget(self.transactions_widget)
        section_layout.addWidget(self.transactions_container, 1)
        
        return section_frame
        
    def _load_transactions(self):
        """Load and display recent transactions."""
        # Clear existing transactions
        for i in reversed(range(self.transactions_layout.count())):
            child = self.transactions_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        try:
            # Get recent transactions from system
            if hasattr(self.system, 'get_recent_journal_entries'):
                transactions = self.system.get_recent_journal_entries(limit=10)
                
                if transactions:
                    for transaction in transactions:
                        card = TransactionCard(transaction)
                        self.transactions_layout.addWidget(card)
                else:
                    # Show empty state
                    empty_label = QLabel("No transactions yet. Add your first transaction above!")
                    empty_label.setStyleSheet("""
                        color: rgba(255, 255, 255, 0.6);
                        font-size: 14px;
                        font-style: italic;
                        text-align: center;
                        padding: 40px;
                    """)
                    empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.transactions_layout.addWidget(empty_label)
            
            # Add spacer at the end
            spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
            self.transactions_layout.addItem(spacer)
            
        except Exception as e:
            print(f"Error loading transactions: {e}")
            # Show error state
            error_label = QLabel("Error loading transactions. Please try again.")
            error_label.setStyleSheet("""
                color: rgba(255, 100, 100, 0.8);
                font-size: 14px;
                text-align: center;
                padding: 40px;
            """)
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.transactions_layout.addWidget(error_label)
