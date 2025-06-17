"""
Clean, Professional Journal Page with Tab System
Refactored to eliminate code duplication and vestigial components
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QLineEdit, QFrame, QDateEdit, QMessageBox, 
    QScrollArea, QSizePolicy, QTabWidget
)
from PyQt6.QtCore import Qt, QDate
from datetime import datetime
from ...core.accounting_system import AccountingSystem
from ..components.widgets import PageHeader, EditableAccountComboBox
from ..components.styles import ModernStyles, GlassmorphismHelper
from ..common import ResponsiveHelper
from .bulk_entry import BulkEntryPage


class TransactionCard(QFrame):
    """Read-only transaction display card."""
    
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
                min-height: 50px;
            }
            QFrame:hover {
                background: rgba(255, 255, 255, 0.08);
                border-color: rgba(255, 255, 255, 0.2);
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)        # Common style for consistent alignment
        base_style = "color: rgba(255, 255, 255, 0.9); font-weight: 500; font-size: 14px; background: transparent; border: none;"
        date_style = "color: rgba(255, 255, 255, 0.7); font-weight: 500; font-size: 14px; background: transparent; border: none;"
        amount_style = "color: rgba(255, 255, 255, 0.9); font-weight: bold; font-size: 14px; background: transparent; border: none;"
        
        # Date column
        date_value = self.entry_data.get('date', 'N/A')
        date_label = QLabel(str(date_value))
        date_label.setFixedWidth(80)
        date_label.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        date_label.setStyleSheet(date_style)
        
        # Description column
        desc_value = self.entry_data.get('description', 'No description')
        desc_label = QLabel(str(desc_value))
        desc_label.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        desc_label.setStyleSheet(base_style)
        desc_label.setWordWrap(True)
        
        # Debit account column
        debit_account = self.entry_data.get('debit_account', 'N/A')
        debit_label = QLabel(str(debit_account))
        debit_label.setFixedWidth(140)
        debit_label.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        debit_label.setStyleSheet(base_style)
        
        # Credit account column
        credit_account = self.entry_data.get('credit_account', 'N/A')
        credit_label = QLabel(str(credit_account))
        credit_label.setFixedWidth(140)
        credit_label.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        credit_label.setStyleSheet(base_style)
        
        # Amount column
        amount = self.entry_data.get('amount', 0)
        # Format amount properly - handle both string and float
        if isinstance(amount, (int, float)):
            amount_str = f"${amount:,.2f}"
        else:
            try:
                amount_str = f"${float(amount):,.2f}"
            except (ValueError, TypeError):
                amount_str = f"${amount}"
        
        amount_label = QLabel(amount_str)
        amount_label.setFixedWidth(100)
        amount_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)
        amount_label.setStyleSheet(amount_style)
        
        layout.addWidget(date_label)
        layout.addWidget(desc_label, 1)  # This will stretch
        layout.addWidget(debit_label)
        layout.addWidget(credit_label)
        layout.addWidget(amount_label)


class JournalPage(QWidget):
    """Tabbed journal page with single entry and bulk entry tabs."""
    
    def __init__(self, system, parent=None):
        super().__init__(parent)
        self.system = system
        self._setup_ui()
        self._apply_styling()
        
    def _apply_styling(self):
        """Apply modern glassmorphism styling."""
        GlassmorphismHelper.apply_main_container_effect(self)
        self.setStyleSheet(self._get_tab_style() + ModernStyles.get_complete_stylesheet())
        
    def _setup_ui(self):
        """Setup the tabbed interface."""
        main_layout = QVBoxLayout(self)
        responsive_margin = ResponsiveHelper.scale_size(32, 24, 48)
        main_layout.setContentsMargins(responsive_margin, responsive_margin, 
                                     responsive_margin, responsive_margin)
        main_layout.setSpacing(ResponsiveHelper.scale_size(32, 24, 48))
        
        # Page header
        header = PageHeader("Journal Entry", "Record and manage your financial transactions")
        main_layout.addWidget(header)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(self._get_tab_style())
        
        # Single entry tab
        self.single_entry_tab = SingleEntryTab(self.system)
        self.tab_widget.addTab(self.single_entry_tab, "Single Entry")
        
        # Bulk entry tab
        self.bulk_entry_tab = BulkEntryPage(self.system)
        self.tab_widget.addTab(self.bulk_entry_tab, "Bulk Entry")
        
        # Set default tab
        self.tab_widget.setCurrentIndex(0)
        
        main_layout.addWidget(self.tab_widget, 1)
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
                padding: 6px 12px;
                font-weight: 500;
                font-size: 12px;
                margin-right: 8px;
                min-width: 80px;
            }
            
            QTabBar::tab:hover {
                background: rgba(255, 255, 255, 0.2);
                border-color: rgba(255, 255, 255, 0.3);
            }
            
            QTabBar::tab:selected {
                background: rgba(100, 181, 246, 0.3);
                border-color: #64B5F6;
                color: #64B5F6;
            }
            
            QTabBar::tab:first {
                margin-left: 0;
            }
        """


class SingleEntryTab(QWidget):
    """Clean single entry tab with form and transaction history."""
    
    def __init__(self, system, parent=None):
        super().__init__(parent)
        self.system = system
        self.accounts = []
        self._load_accounts()
        self._setup_ui()
        self._load_transactions()
        
    def _load_accounts(self):
        """Load accounts from the system."""
        try:
            if hasattr(self.system, 'get_all_accounts'):
                accounts_data = self.system.get_all_accounts()
                self.accounts = [f"{acc[2]} - {acc[0]}" for acc in accounts_data if acc[5]]
            else:
                # No fallback accounts - system must have proper chart of accounts
                self.accounts = []
                print("Warning: System does not have get_all_accounts method")
        except Exception as e:
            print(f"Error loading accounts: {e}")
            # No fallback accounts - system must have proper chart of accounts
            self.accounts = []
        
    def _setup_ui(self):
        """Setup the single entry tab UI with fixed top section and scrollable transactions."""
        tab_layout = QVBoxLayout(self)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.setSpacing(0)
        
        # Main container (no scroll area - fixed content)
        main_container = QWidget()
        main_layout = QVBoxLayout(main_container)
        main_layout.setContentsMargins(0, ResponsiveHelper.scale_size(24, 16, 32),
                                     0, ResponsiveHelper.scale_size(24, 16, 32))
        main_layout.setSpacing(ResponsiveHelper.scale_size(24, 16, 32))
          # Entry form (fixed at top)
        self.entry_form = self._create_entry_form()
        main_layout.addWidget(self.entry_form)
        
        # Transaction History Header (fixed)
        header_label = QLabel("Transaction History")
        header_label.setStyleSheet("""
            color: rgba(255, 255, 255, 0.9);
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 8px;
            background: transparent;
            border: none;
        """)
        main_layout.addWidget(header_label)
        
        # Column headers (fixed)
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
        
        headers = [
            ("DATE", 80, "rgba(255, 255, 255, 0.8)"),
            ("DESCRIPTION", None, "rgba(255, 255, 255, 0.8)"),
            ("DEBIT ACCOUNT", 140, "rgba(255, 255, 255, 0.8)"),
            ("CREDIT ACCOUNT", 140, "rgba(255, 255, 255, 0.8)"),
            ("AMOUNT", 100, "rgba(255, 255, 255, 0.8)")
        ]
        
        for text, width, color in headers:
            header = QLabel(text)
            if width:
                header.setFixedWidth(width)
                if text == "AMOUNT":
                    header.setAlignment(Qt.AlignmentFlag.AlignRight)
            header.setStyleSheet(f"color: {color}; font-weight: 600; font-size: 12px; background: transparent; border: none;")
            headers_layout.addWidget(header, 0 if width else 1)
        
        main_layout.addWidget(headers_frame)
        
        # Add the fixed content to main layout
        tab_layout.addWidget(main_container)        # Scrollable transactions area
        self.transactions_scroll = QScrollArea()
        self.transactions_scroll.setWidgetResizable(True)
        self.transactions_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.transactions_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.transactions_scroll.setStyleSheet("""
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
            QWidget { background: transparent; }
        """)
        
        # Transactions container widget (scrollable content)
        self.transactions_widget = QWidget()
        self.transactions_layout = QVBoxLayout(self.transactions_widget)
        self.transactions_layout.setContentsMargins(0, 0, 0, ResponsiveHelper.scale_size(24, 16, 32))
        self.transactions_layout.setSpacing(8)        
        self.transactions_scroll.setWidget(self.transactions_widget)
        tab_layout.addWidget(self.transactions_scroll, 1)  # This takes remaining space

    def _create_entry_form(self):
        """Create expandable entry form."""
        from PyQt6.QtCore import QPropertyAnimation, QEasingCurve
        from PyQt6.QtWidgets import QGridLayout
        from ..components.shared_styles import get_field_style, get_button_style, get_label_style
        
        # Main container
        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.08);
                border-radius: 10px;
                border: none;
            }
        """)
        container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header with toggle
        header = QFrame()
        header.setStyleSheet("background: rgba(255,255,255,0.1); border-radius: 10px;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(18, 12, 18, 12)
        header_layout.setSpacing(8)
        
        title = QLabel("New Transaction")
        title.setStyleSheet("color: white; font-size: 15px; font-weight: 600; background: transparent;")
        
        toggle_btn = QLabel()
        toggle_btn.setStyleSheet("""
            QLabel {
                border: none;
                background: transparent;
                font-size: 18px;
                color: white;
            }
        """)
        toggle_btn.setText("▶")
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(toggle_btn)

        # Collapsible content
        content = QFrame()
        content.setStyleSheet("background: transparent;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(18, 8, 18, 18)
        content_layout.setSpacing(12)

        # Form fields grid
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(2)        # Labels
        labels = ["DATE", "DESCRIPTION", "DEBIT ACCOUNT", "CREDIT ACCOUNT", "AMOUNT"]
        for i, text in enumerate(labels):
            label = QLabel(text)
            label.setStyleSheet(get_label_style())
            label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            grid.addWidget(label, 0, i)        # Input fields
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setFixedHeight(28)
        self.date_edit.setFixedWidth(120)
        self.date_edit.setStyleSheet(get_field_style("date"))
        
        self.desc_edit = QLineEdit()
        self.desc_edit.setPlaceholderText("Enter description...")
        self.desc_edit.setMinimumWidth(180)
        self.desc_edit.setMaximumWidth(200)
        self.desc_edit.setStyleSheet(get_field_style("description"))
        
        self.debit_combo = EditableAccountComboBox()
        self.debit_combo.setMinimumWidth(160)
        self.debit_combo.setMaximumWidth(200)
        self.debit_combo.setStyleSheet(get_field_style("debit"))
        self._populate_account_combo(self.debit_combo)
        
        self.credit_combo = EditableAccountComboBox()
        self.credit_combo.setMinimumWidth(160)
        self.credit_combo.setMaximumWidth(200)
        self.credit_combo.setStyleSheet(get_field_style("credit"))
        self._populate_account_combo(self.credit_combo)
        
        self.amount_edit = QLineEdit()
        self.amount_edit.setPlaceholderText("0.00")
        self.amount_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.amount_edit.setFixedWidth(120)
        self.amount_edit.setStyleSheet(get_field_style("amount"))
        
        fields = [self.date_edit, self.desc_edit, self.debit_combo, self.credit_combo, self.amount_edit]
        for i, field in enumerate(fields):
            grid.addWidget(field, 1, i)        # Add AI entry row directly to the main grid for perfect alignment
        # AI input field spans from Date column (0) to Description column (1) - exactly matching their combined width
        self.nl_input = QLineEdit()
        self.nl_input.setPlaceholderText("Describe your transaction in plain English...")
        # Remove any width constraints to let it fill the full span of Date + Description columns
        self.nl_input.setStyleSheet(get_field_style("description").replace("max-width: 200px;", "").replace("min-width: 180px;", ""))
        grid.addWidget(self.nl_input, 2, 0, 1, 2)  # row 2, span columns 0-1 (Date + Description)        # Parse button in Debit column (2)
        parse_btn = QPushButton("Interpret")
        parse_btn.setStyleSheet(get_button_style(compact=True))
        parse_btn.clicked.connect(self._parse_transaction)
        grid.addWidget(parse_btn, 2, 2)  # row 2, column 2
        
        # Save button in Credit column (3)
        save_btn = QPushButton("Save")
        save_btn.setStyleSheet(get_button_style(primary=True, compact=True))
        save_btn.clicked.connect(self._save_entry)
        grid.addWidget(save_btn, 2, 3)  # row 2, column 3
        
        # Clear button in Amount column (4)
        clear_btn = QPushButton("Clear")
        clear_btn.setStyleSheet(get_button_style(secondary=True, compact=True))
        clear_btn.clicked.connect(self._clear_form)
        grid.addWidget(clear_btn, 2, 4)  # row 2, column 4

        content_layout.addLayout(grid)

        # Setup animation
        content.setVisible(False)
        layout.addWidget(content)

        animation = QPropertyAnimation(content, b"maximumHeight")
        animation.setDuration(250)
        animation.setEasingCurve(QEasingCurve.Type.InOutCubic)

        def toggle():
            # Check current visibility to determine state
            expanded = content.isVisible()
            toggle_btn.setText("▶" if expanded else "▼")
            
            animation.stop()
            try:
                animation.finished.disconnect()
            except TypeError:
                pass
            
            if not expanded:  # Currently collapsed, so expand
                content.setVisible(True)
                content.setMaximumHeight(16777215)
                content_height = content.sizeHint().height()
                animation.setStartValue(0)
                animation.setEndValue(content_height)
                animation.start()
            else:  # Currently expanded, so collapse
                current_height = content.height()
                animation.setStartValue(current_height)
                animation.setEndValue(0)
                animation.finished.connect(lambda: content.setVisible(False))
                animation.start()

        def header_toggle():
            toggle()
        
        # Only connect header click to toggle function (not the triangle icon)
        header.mousePressEvent = lambda event: header_toggle()

        layout.insertWidget(0, header)
        return container
    
    def _populate_account_combo(self, combo):
        """Populate account combo box."""
        combo.setAccountList(self.accounts)
        combo.setPlaceholderText("Select or type account...")
        combo.clear_selection()
    
    def _parse_transaction(self):
        """Parse natural language transaction."""
        nl_text = self.nl_input.text().strip()
        if not nl_text:
            QMessageBox.warning(self, "Missing Input", "Please enter a description to parse.")
            return
        try:
            from ...core.utils import parse_transaction
            parsed = parse_transaction(nl_text, valid_accounts=self.accounts, system=self.system)
            self.date_edit.setDate(QDate.fromString(parsed['date'], 'yyyy-MM-dd'))
            self.desc_edit.setText(parsed['description'])
            self.debit_combo.setCurrentText(parsed['debit_account'])
            self.credit_combo.setCurrentText(parsed['credit_account'])
            self.amount_edit.setText(str(parsed['amount']))
        except Exception as e:
            QMessageBox.critical(self, "Parse Error", f"Could not parse entry: {e}")

    def _save_entry(self):
        """Save the journal entry."""
        try:
            date = self.date_edit.date().toString("yyyy-MM-dd")
            description = self.desc_edit.text().strip()
            debit_account = self.debit_combo.currentText().strip()
            credit_account = self.credit_combo.currentText().strip()
            amount = self.amount_edit.text().strip()
            
            # Validation
            if not all([description, debit_account, credit_account, amount]):
                QMessageBox.warning(self, "Validation Error", "Please fill in all fields.")
                return
                
            if debit_account == credit_account:
                QMessageBox.warning(self, "Validation Error", "Debit and Credit accounts cannot be the same.")
                return
                
            try:
                float(amount)
            except ValueError:
                QMessageBox.warning(self, "Validation Error", "Please enter a valid amount.")
                return
            
            # Save to system
            if hasattr(self.system, 'add_journal_entry'):
                entry_id = self.system.add_journal_entry(date, description, debit_account, credit_account, amount)
            
            QMessageBox.information(self, "Success", "Transaction saved successfully!")
            self._clear_form()
            
            # Refresh transactions with improved timing
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(100, self._load_transactions)  # Small delay to ensure DB operations complete
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save transaction: {e}")
    
    def _clear_form(self):
        """Clear all form fields."""
        self.desc_edit.clear()
        self.debit_combo.clear_selection()
        self.credit_combo.clear_selection()
        self.amount_edit.clear()
        self.date_edit.setDate(QDate.currentDate())
        self.nl_input.clear()
        
    def _create_transactions_section(self):
        """This method is no longer used - transactions are now directly in main layout."""
        pass
    def _load_transactions(self):
        """Load and display recent transactions."""
        # Clear existing transactions
        for i in reversed(range(self.transactions_layout.count())):
            item = self.transactions_layout.itemAt(i)
            if item:
                widget = item.widget()
                if widget:
                    self.transactions_layout.removeWidget(widget)
                    widget.deleteLater()
                else:
                    # It's a spacer item
                    self.transactions_layout.removeItem(item)
        
        try:
            if hasattr(self.system, 'get_recent_journal_entries'):
                transactions = self.system.get_recent_journal_entries(limit=10)
                
                if transactions:
                    for transaction in transactions:
                        card = TransactionCard(transaction)
                        card.show()  # Ensure card is visible
                        self.transactions_layout.addWidget(card)
                else:
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
            
            # Add spacer to push content to top
            from PyQt6.QtWidgets import QSpacerItem
            spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
            self.transactions_layout.addItem(spacer)
            
            # Force comprehensive layout update
            self.transactions_widget.updateGeometry()
            self.transactions_layout.update()
            
            # Also update the parent widgets
            if self.transactions_widget.parent():
                self.transactions_widget.parent().updateGeometry()
                self.transactions_widget.parent().update()
            
            # Force a repaint of the entire widget
            self.transactions_widget.repaint()
            
            # Ensure scroll area shows the top (newest entries)
            if hasattr(self, 'transactions_scroll'):
                self.transactions_scroll.verticalScrollBar().setValue(0)
                self.transactions_scroll.ensureVisible(0, 0)
            
        except Exception as e:
            print(f"Error loading transactions: {e}")
            error_label = QLabel("Error loading transactions. Please try again.")
            error_label.setStyleSheet("""
                color: rgba(255, 100, 100, 0.8);
                font-size: 14px;
                text-align: center;
                padding: 40px;
            """)
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.transactions_layout.addWidget(error_label)
