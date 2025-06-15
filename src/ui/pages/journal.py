"""
Clean, Professional Journal Page
Simple entry form + clean transaction display
No complexity, no clutter, just what accountants need.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QLineEdit, QComboBox, QFrame, QDateEdit, QMessageBox, 
    QScrollArea, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont
from datetime import datetime
from ...core.accounting_system import AccountingSystem
from ..components.widgets import PageHeader, NonScrollableComboBox
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
        date_label.setStyleSheet("""
            color: rgba(255, 255, 255, 0.9);
            font-weight: 600;
            font-size: 12px;
            background: transparent;
            border: none;
        """)
        
        # Description column
        desc_label = QLabel(self.entry_data.get('description', ''))
        desc_label.setStyleSheet("""
            color: white;
            font-size: 13px;
            background: transparent;
            border: none;
        """)
        
        # From account
        from_label = QLabel(self.entry_data.get('debit_account', ''))
        from_label.setFixedWidth(120)
        from_label.setStyleSheet("""
            color: rgba(255, 255, 255, 0.8);
            font-size: 12px;
            background: transparent;
            border: none;
        """)
        
        # To account  
        to_label = QLabel(self.entry_data.get('credit_account', ''))
        to_label.setFixedWidth(120)
        to_label.setStyleSheet("""
            color: rgba(255, 255, 255, 0.8);
            font-size: 12px;
            background: transparent;
            border: none;
        """)
        
        # Amount
        amount = self.entry_data.get('amount', 0)
        amount_label = QLabel(f"${amount:.2f}")
        amount_label.setFixedWidth(100)
        amount_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        amount_label.setStyleSheet("""
            color: #81C784;
            font-weight: 600;
            font-size: 13px;
            background: transparent;
            border: none;
        """)
        
        layout.addWidget(date_label)
        layout.addWidget(desc_label, 1)  # This will stretch
        layout.addWidget(from_label)
        layout.addWidget(to_label)
        layout.addWidget(amount_label)

class JournalPage(QWidget):
    """Clean, professional journal page."""
    
    def __init__(self, system, parent=None):
        super().__init__(parent)
        self.system = system
        self.is_form_expanded = False  # Form starts collapsed
        self.accounts = []  # Initialize accounts list
        self._load_accounts()  # Load accounts first
        self._setup_ui()
        self._apply_styling()
        self._load_transactions()
        
    def _apply_styling(self):
        """Apply modern glassmorphism styling to the journal page."""
        GlassmorphismHelper.apply_main_container_effect(self)
        self.setStyleSheet(ModernStyles.get_complete_stylesheet())
        
    def _setup_ui(self):
        """Setup the main UI."""
        # Main layout for the page
        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(0)
        
        # Create scroll area for the main content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: rgba(255, 255, 255, 0.1);
                width: 8px;
                border-radius: 4px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.3);
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(255, 255, 255, 0.5);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        # Content widget that goes inside the scroll area
        content_widget = QWidget()
        main_layout = QVBoxLayout(content_widget)
        responsive_margin = ResponsiveHelper.scale_size(32, 24, 48)
        main_layout.setContentsMargins(responsive_margin, responsive_margin, 
                                     responsive_margin, responsive_margin)
        main_layout.setSpacing(ResponsiveHelper.scale_size(32, 24, 48))
        
        # Page header
        header = PageHeader("Journal Entries", "Record and view your accounting transactions")
        main_layout.addWidget(header)
        
        # Action buttons
        self._create_action_buttons(main_layout)
        
        # Entry form
        self._create_collapsible_entry_form(main_layout)
        
        # Transaction list
        self._create_transaction_list(main_layout)
        
        # Set the content widget in the scroll area
        scroll_area.setWidget(content_widget)
        page_layout.addWidget(scroll_area)
    
    def _create_action_buttons(self, main_layout):
        """Create action buttons for bulk entry and CSV import."""
        buttons_frame = QFrame()
        buttons_frame.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.06);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 12px;
            }
        """)
        buttons_layout = QHBoxLayout(buttons_frame)
        buttons_layout.setContentsMargins(20, 15, 20, 15)
        
        # Bulk Entry Button
        bulk_entry_btn = QPushButton("📊 Bulk Entry")
        bulk_entry_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 rgba(52, 152, 219, 0.8), stop:1 rgba(41, 128, 185, 0.8));
                color: white;
                border: 2px solid rgba(255, 255, 255, 0.3);
                border-radius: 12px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
                min-width: 140px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 rgba(52, 152, 219, 1.0), stop:1 rgba(41, 128, 185, 1.0));
                transform: translateY(-2px);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 rgba(41, 128, 185, 0.9), stop:1 rgba(30, 100, 150, 0.9));
            }
        """)
        bulk_entry_btn.clicked.connect(self._open_bulk_entry_page)
        
        # Add spacer
        spacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        
        buttons_layout.addWidget(bulk_entry_btn)
        buttons_layout.addItem(spacer)
        
        main_layout.addWidget(buttons_frame)
    
    def _create_collapsible_entry_form(self, main_layout):
        """Create the collapsible entry form."""
        # Container for the entire form section
        self.form_container = QFrame()
        self.form_container.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.06);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 12px;
            }
        """)
        
        container_layout = QVBoxLayout(self.form_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        
        # Clickable header with expand/collapse functionality
        self.header_frame = QFrame()
        self.header_frame.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.08);
                border: none;
                border-radius: 12px;
                padding: 0px;
            }
            QFrame:hover {
                background: rgba(255, 255, 255, 0.12);
            }
        """)
        self.header_frame.setFixedHeight(60)
        
        # Make the header frame clickable
        self.header_frame.mousePressEvent = self._on_header_click
        self.header_frame.setCursor(Qt.CursorShape.PointingHandCursor)
        
        header_layout = QHBoxLayout(self.header_frame)
        header_layout.setContentsMargins(20, 16, 20, 16)
        header_layout.setSpacing(12)
        
        # Form title and subtitle
        title_container = QVBoxLayout()
        title_container.setSpacing(2)
        
        form_title = QLabel("New Transaction")
        form_title.setStyleSheet("""
            font-size: 16px;
            font-weight: 600;
            color: white;
            background: transparent;
            border: none;
        """)
        
        form_subtitle = QLabel("Add a new journal entry")
        form_subtitle.setStyleSheet("""
            font-size: 12px;
            color: rgba(255, 255, 255, 0.7);
            background: transparent;
            border: none;
        """)
        
        title_container.addWidget(form_title)
        title_container.addWidget(form_subtitle)
        
        # Toggle indicator (subtle arrow) - starts collapsed
        self.toggle_indicator = QLabel("▶")
        self.toggle_indicator.setStyleSheet("""
            font-size: 12px;
            color: rgba(255, 255, 255, 0.6);
            background: transparent;
            border: none;
        """)
        self.toggle_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        header_layout.addLayout(title_container)
        header_layout.addStretch()
        header_layout.addWidget(self.toggle_indicator, 0, Qt.AlignmentFlag.AlignCenter)
        
        container_layout.addWidget(self.header_frame)
        
        # Collapsible content area
        self.form_content = QFrame()
        self.form_content.setStyleSheet("""
            QFrame {
                background: transparent;
                border: none;
                padding: 12px;
            }
        """)
        
        self._create_form_fields()
        container_layout.addWidget(self.form_content)
        
        # Set initial state (collapsed)
        self.form_content.setVisible(self.is_form_expanded)
        
        main_layout.addWidget(self.form_container)
    
    def _create_transaction_list(self, main_layout):
        """Create the transaction display section."""
        # Transaction list container
        list_frame = QFrame()
        list_frame.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.06);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 12px;
            }
        """)
        
        list_layout = QVBoxLayout(list_frame)
        list_layout.setContentsMargins(20, 20, 20, 20)
        list_layout.setSpacing(16)
        
        # Header with transaction count
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)
        
        title_label = QLabel("Recent Transactions")
        title_label.setStyleSheet("""
            font-size: 18px;
            font-weight: 600;
            color: white;
            background: transparent;
            border: none;
        """)
        
        # Transaction count badge
        self.count_label = QLabel("0 entries")
        self.count_label.setStyleSheet("""
            color: rgba(255, 255, 255, 0.7);
            font-size: 12px;
            background: rgba(255, 255, 255, 0.1);
            padding: 4px 8px;
            border-radius: 4px;
        """)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.count_label)
        
        list_layout.addLayout(header_layout)
        
        # Column headers
        self._create_transaction_headers(list_layout)
        
        # Scrollable area for transactions
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMaximumHeight(500)  # Limit height for better proportions
        scroll_area.setMinimumHeight(300)  # Ensure reasonable minimum
        scroll_area.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: rgba(255, 255, 255, 0.1);
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.3);
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(255, 255, 255, 0.4);
            }
        """)
        
        # Container for transaction cards
        self.transactions_container = QWidget()
        self.transactions_layout = QVBoxLayout(self.transactions_container)
        self.transactions_layout.setSpacing(8)
        self.transactions_layout.setContentsMargins(0, 0, 0, 0)
        
        scroll_area.setWidget(self.transactions_container)
        list_layout.addWidget(scroll_area)
        
        main_layout.addWidget(list_frame)
    
    def _get_input_style(self):
        return """
            QLineEdit, QComboBox, QDateEdit {
                background: rgba(255, 255, 255, 0.9);
                border: 2px solid rgba(255, 255, 255, 0.3);
                border-radius: 8px;
                padding: 10px 12px;
                font-size: 13px;
                color: #2c3e50;
                min-height: 20px;
            }
            QLineEdit:focus, QComboBox:focus, QDateEdit:focus {
                border-color: rgba(52, 152, 219, 0.8);
                background: rgba(255, 255, 255, 1.0);
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #7f8c8d;
                margin-right: 5px;
            }
        """
    
    def _load_accounts(self):
        """Load accounts from the accounting system."""
        self.accounts = self.system.get_postable_accounts()
    
    def _populate_account_combo(self, combo):
        """Populate account combo box with available accounts."""
        combo.clear()
        combo.addItem("Select Account...", "")
        for account in self.accounts:
            combo.addItem(account[0], account[0])  # account name
    
    def _load_transactions(self):
        """Load and display transactions."""
        try:
            # Clear existing cards
            for i in reversed(range(self.transactions_layout.count())):
                widget = self.transactions_layout.itemAt(i).widget()
                if widget:
                    widget.setParent(None)
                    
            # Get recent transactions from system
            try:
                entries = self.system.get_recent_journal_entries(20)  # Get last 20 entries
            except Exception as e:
                print(f"Error getting entries from system: {e}")
                entries = []
            
            # Update count
            self.count_label.setText(f"{len(entries)} entries")
            
            if not entries:
                no_data = QLabel("No transactions found. Add your first entry above!")
                no_data.setStyleSheet("""
                    color: rgba(255, 255, 255, 0.6);
                    font-size: 14px;
                    text-align: center;
                    padding: 40px;
                    background: transparent;
                    border: none;
                """)
                no_data.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.transactions_layout.addWidget(no_data)
            else:
                for entry in entries:
                    try:
                        card = TransactionCard(entry)
                        self.transactions_layout.addWidget(card)
                    except Exception as e:
                        print(f"Error creating card for entry {entry}: {e}")
                        continue
                    
            self.transactions_layout.addStretch()
            
        except Exception as e:
            print(f"Error loading transactions: {e}")
            error_label = QLabel(f"Error loading transactions: {str(e)}")
            error_label.setStyleSheet("color: #e74c3c; text-align: center; padding: 20px; background: transparent; border: none;")
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.transactions_layout.addWidget(error_label)
    
    def _save_transaction(self):
        """Save a new transaction."""
        try:
            # Get form data
            date = self.date_edit.date().toString("yyyy-MM-dd")
            description = self.desc_edit.text().strip()
            debit_account = self.from_combo.currentText()
            credit_account = self.to_combo.currentText()
            amount_text = self.amount_edit.text().strip()
            
            # Validate
            if not description:
                QMessageBox.warning(self, "Validation Error", "Please enter a description.")
                return
            
            if not debit_account or debit_account == "Select Account...":
                QMessageBox.warning(self, "Validation Error", "Please select a debit account.")
                return
            
            if not credit_account or credit_account == "Select Account...":
                QMessageBox.warning(self, "Validation Error", "Please select a credit account.")
                return
            
            if debit_account == credit_account:
                QMessageBox.warning(self, "Validation Error", "Debit and credit accounts must be different.")
                return
            
            try:
                amount = float(amount_text)
                if amount <= 0:
                    raise ValueError()
            except ValueError:
                QMessageBox.warning(self, "Validation Error", "Please enter a valid positive amount.")
                return
            
            # Save using accounting system
            success = self.system.add_journal_entry(
                date=date,
                description=description,
                debit_account=debit_account,
                credit_account=credit_account,
                amount=amount
            )
            
            if success:
                # Clear form
                self.desc_edit.clear()
                self.amount_edit.clear()
                self.from_combo.setCurrentIndex(0)
                self.to_combo.setCurrentIndex(0)
                self.date_edit.setDate(QDate.currentDate())
                
                # Reload transactions
                self._load_transactions()
                
                QMessageBox.information(self, "Success", "Transaction saved successfully!")
            else:
                QMessageBox.critical(self, "Error", "Failed to save transaction.")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save transaction: {str(e)}")
    
    def _create_form_fields(self):
        """Create the form fields for transaction entry."""
        form_layout = QVBoxLayout(self.form_content)
        form_layout.setContentsMargins(20, 20, 20, 20)
        form_layout.setSpacing(16)
        
        # Natural language input
        nl_layout = QVBoxLayout()
        nl_layout.setSpacing(8)
        
        nl_label = QLabel("Natural Language Entry")
        nl_label.setStyleSheet("""
            color: rgba(255, 255, 255, 0.9);
            font-weight: 600;
            font-size: 14px;
        """)
        
        nl_input_layout = QHBoxLayout()
        nl_input_layout.setSpacing(8)
        
        self.nl_input = QLineEdit()
        self.nl_input.setPlaceholderText("Describe your transaction (e.g., 'Paid $500 cash for office supplies')")
        self.nl_input.setStyleSheet("""
            QLineEdit {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                padding: 12px 16px;
                color: white;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: rgba(0, 120, 215, 0.6);
                background: rgba(255, 255, 255, 0.12);
            }
        """)
        
        self.parse_btn = QPushButton("✨ Parse")
        self.parse_btn.setStyleSheet("""
            QPushButton {
                background: rgba(155, 89, 182, 0.8);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 20px;
                font-weight: 600;
                font-size: 13px;
            }
            QPushButton:hover {
                background: rgba(155, 89, 182, 1.0);
            }
        """)
        self.parse_btn.clicked.connect(self._parse_with_ai)
        
        nl_input_layout.addWidget(self.nl_input, 1)
        nl_input_layout.addWidget(self.parse_btn)
        
        nl_layout.addWidget(nl_label)
        nl_layout.addLayout(nl_input_layout)
        
        form_layout.addLayout(nl_layout)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background: rgba(255, 255, 255, 0.1); max-height: 1px;")
        form_layout.addWidget(separator)
        
        # Manual entry fields
        manual_label = QLabel("Manual Entry")
        manual_label.setStyleSheet("""
            color: rgba(255, 255, 255, 0.9);
            font-weight: 600;
            font-size: 14px;
        """)
        form_layout.addWidget(manual_label)
        
        # Date field
        date_layout = QHBoxLayout()
        date_label = QLabel("Date:")
        date_label.setFixedWidth(100)
        date_label.setStyleSheet("color: rgba(255, 255, 255, 0.8); font-weight: 500;")
        
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setStyleSheet(self._get_field_style())
        
        date_layout.addWidget(date_label)
        date_layout.addWidget(self.date_edit)
        date_layout.addStretch()
        
        # Description field
        desc_layout = QHBoxLayout()
        desc_label = QLabel("Description:")
        desc_label.setFixedWidth(100)
        desc_label.setStyleSheet("color: rgba(255, 255, 255, 0.8); font-weight: 500;")
        
        self.desc_edit = QLineEdit()
        self.desc_edit.setPlaceholderText("Transaction description")
        self.desc_edit.setStyleSheet(self._get_field_style())
        
        desc_layout.addWidget(desc_label)
        desc_layout.addWidget(self.desc_edit)
        
        # Account fields
        from_layout = QHBoxLayout()
        from_label = QLabel("Debit:")
        from_label.setFixedWidth(100)
        from_label.setStyleSheet("color: rgba(255, 255, 255, 0.8); font-weight: 500;")
        
        self.from_combo = NonScrollableComboBox()
        self.from_combo.setStyleSheet(self._get_field_style())
        self._populate_account_combo(self.from_combo)
        
        from_layout.addWidget(from_label)
        from_layout.addWidget(self.from_combo)
        
        to_layout = QHBoxLayout()
        to_label = QLabel("Credit:")
        to_label.setFixedWidth(100)
        to_label.setStyleSheet("color: rgba(255, 255, 255, 0.8); font-weight: 500;")
        
        self.to_combo = NonScrollableComboBox()
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
        amount_layout.addStretch()
        
        # Add all layouts
        form_layout.addLayout(date_layout)
        form_layout.addLayout(desc_layout)
        form_layout.addLayout(from_layout)
        form_layout.addLayout(to_layout)
        form_layout.addLayout(amount_layout)
        
        # Save button
        save_btn = QPushButton("💾 Save Transaction")
        save_btn.setStyleSheet("""
            QPushButton {
                background: rgba(46, 204, 113, 0.8);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 14px 28px;
                font-weight: 600;
                font-size: 14px;
                margin-top: 10px;
            }
            QPushButton:hover {
                background: rgba(46, 204, 113, 1.0);
            }
        """)
        save_btn.clicked.connect(self._save_transaction)
        
        form_layout.addWidget(save_btn)
    
    def _create_transaction_headers(self, layout):
        """Create the transaction list headers."""
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.05);
                border: none;
                border-radius: 6px;
                padding: 8px;
            }
        """)
        
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(16, 8, 16, 8)
        header_layout.setSpacing(12)
        
        # Date header
        date_header = QLabel("Date")
        date_header.setStyleSheet("color: rgba(255, 255, 255, 0.8); font-weight: 600; font-size: 12px; background: transparent; border: none;")
        date_header.setFixedWidth(80)
        
        # Description header
        desc_header = QLabel("Description")
        desc_header.setStyleSheet("color: rgba(255, 255, 255, 0.8); font-weight: 600; font-size: 12px; background: transparent; border: none;")
        
        # From header
        from_header = QLabel("Debit")
        from_header.setStyleSheet("color: rgba(255, 255, 255, 0.8); font-weight: 600; font-size: 12px; background: transparent; border: none;")
        from_header.setFixedWidth(120)
        
        # To header
        to_header = QLabel("Credit")
        to_header.setStyleSheet("color: rgba(255, 255, 255, 0.8); font-weight: 600; font-size: 12px; background: transparent; border: none;")
        to_header.setFixedWidth(120)
        
        # Amount header
        amount_header = QLabel("Amount")
        amount_header.setStyleSheet("color: #81C784; font-weight: 600; font-size: 12px; background: transparent; border: none;")
        amount_header.setAlignment(Qt.AlignmentFlag.AlignRight)
        amount_header.setFixedWidth(100)
        
        header_layout.addWidget(date_header)
        header_layout.addWidget(desc_header, 1)
        header_layout.addWidget(from_header)
        header_layout.addWidget(to_header)
        header_layout.addWidget(amount_header)
        
        layout.addWidget(header_frame)
    
    def _get_field_style(self):
        """Get styling for form fields."""
        return """
            QLineEdit, QComboBox, QDateEdit {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 6px;
                padding: 10px 12px;
                color: white;
                font-size: 13px;
            }
            QLineEdit:focus, QComboBox:focus, QDateEdit:focus {
                border-color: rgba(0, 120, 215, 0.6);
                background: rgba(255, 255, 255, 0.12);
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 4px solid rgba(255, 255, 255, 0.6);
                margin-right: 4px;
            }
        """
    
    def _on_header_click(self, event):
        """Handle header click to toggle form."""
        self._toggle_form()
        
    def _toggle_form(self):
        """Toggle the form visibility."""
        self.is_form_expanded = not self.is_form_expanded
        self.form_content.setVisible(self.is_form_expanded)
        self.toggle_indicator.setText("▼" if self.is_form_expanded else "▶")
        self._update_header_styling()
        
    def _update_header_styling(self):
        """Update header styling based on expanded state."""
        if self.is_form_expanded:
            self.header_frame.setStyleSheet("""
                QFrame {
                    background: rgba(255, 255, 255, 0.08);
                    border: none;
                    border-top-left-radius: 12px;
                    border-top-right-radius: 12px;
                    padding: 0px;
                }
                QFrame:hover {
                    background: rgba(255, 255, 255, 0.12);
                }
            """)
        else:
            self.header_frame.setStyleSheet("""
                QFrame {
                    background: rgba(255, 255, 255, 0.08);
                    border: none;
                    border-radius: 12px;
                    padding: 0px;
                }
                QFrame:hover {
                    background: rgba(255, 255, 255, 0.12);
                }
            """)
    
    def _parse_with_ai(self):
        """Parse natural language input (placeholder)."""
        QMessageBox.information(self, "AI Parse", "AI parsing feature coming soon!")
    
    def _open_bulk_entry_page(self):
        """Open the bulk entry page."""
        try:
            self.bulk_entry_page = BulkEntryPage(self.system)
            self.bulk_entry_page.show()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open bulk entry page: {str(e)}")