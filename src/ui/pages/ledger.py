"""
Modern General Ledger - Professional Accounting Interface
Card-based design with progressive disclosure and smart filtering
Built for efficiency and clarity in professional accounting workflows
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QLineEdit, QComboBox, QFrame, QScrollArea,
    QSpacerItem, QSizePolicy, QGridLayout, QStackedWidget, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QColor, QPalette
from datetime import datetime, timedelta
from ...core.utils import format_currency
from ...core.events import accounting_events

from ..components.scrollbar_styles import ModernScrollbarStyles
from ..components.widgets import DateRangeSelector, PageHeader
from ..components.styles import ModernStyles, GlassmorphismHelper
from ..common import ResponsiveHelper

class AccountCard(QFrame):
    """Modern card representing an account with balance and activity."""
    
    accountSelected = pyqtSignal(str)  # Account name
    
    def __init__(self, account_data, account_level=1, parent=None):
        super().__init__(parent)
        self.account_data = account_data  # (name, type, code, parent_code)
        self.account_level = account_level
        self.balance = 0.0
        self.transaction_count = 0
        self.is_expanded = False
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup the account card UI."""
        self.setFixedHeight(120)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 8px;
                border-color: rgba(0, 0, 0, 0.3);
                margin: 4px;
            }
            
            QFrame:hover {
                background: rgba(255, 255, 255, 0.12);
                border-color: rgba(255, 255, 255, 0.25);
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)
          # Header row
        header_layout = QHBoxLayout()
        header_layout.setSpacing(4)  # Reduced spacing between tags
        
        # Account code
        code_label = QLabel(self.account_data['code'] or "")
        code_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        code_label.setStyleSheet("""
            color: #64B5F6;
            font-weight: 600;
            font-size: 11px;
            background: rgba(100, 181, 246, 0.2);
            padding: 2px 6px;
            border-radius: 4px;
            border: none;
        """)
        code_label.setFixedWidth(50)
        code_label.setFixedHeight(24)
        header_layout.addWidget(code_label)
        
        # Level tag with color coding
        level_colors = {
            1: {"bg": "rgba(100, 150, 255, 0.2)", "color": "#6496FF"},  # Blue
            2: {"bg": "rgba(150, 200, 100, 0.2)", "color": "#96C864"},  # Green  
            3: {"bg": "rgba(255, 200, 100, 0.2)", "color": "#FFC864"}   # Orange
        }
        
        level_style = level_colors.get(self.account_level, level_colors[1])
        level_label = QLabel(f"lvl. {self.account_level}")
        level_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        level_label.setStyleSheet(f"""
            color: {level_style["color"]};
            font-weight: 600;
            font-size: 11px;
            background: {level_style["bg"]};
            padding: 2px 6px;
            border-radius: 4px;
            border: none;
        """)
        level_label.setFixedWidth(50)
        level_label.setFixedHeight(24)
        level_label.setToolTip(f"Account Level {self.account_level}")
        header_layout.addWidget(level_label)
        
        # Add R/P tags based on account properties
        # R = Reporting account (L1, L2, some L3)
        # P = Postable account (some L2, most L3)
        is_reporting = self.account_level in [1, 2] or self.account_data.get('has_children', False)
        is_postable = self.account_data.get('is_postable', True)
        
        # Reporting tag (R)
        if is_reporting:
            reporting_label = QLabel("R")
            reporting_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            reporting_label.setStyleSheet("""
                color: #FF6B6B;
                font-weight: 700;
                font-size: 11px;
                background: rgba(255, 107, 107, 0.2);
                padding: 2px 6px;
                border-radius: 4px;
                border: none;
            """)
            reporting_label.setFixedWidth(30)
            reporting_label.setFixedHeight(24)
            reporting_label.setToolTip("Reporting Account")
            header_layout.addWidget(reporting_label)
        
        # Postable tag (P)
        if is_postable:
            postable_label = QLabel("P")
            postable_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            postable_label.setStyleSheet("""
                color: #4ECDC4;
                font-weight: 700;
                font-size: 11px;
                background: rgba(78, 205, 196, 0.2);
                padding: 2px 6px;
                border-radius: 4px;
                border: none;
            """)
            postable_label.setFixedWidth(30)
            postable_label.setFixedHeight(24)
            postable_label.setToolTip("Postable Account")
            header_layout.addWidget(postable_label)
        
        header_layout.addStretch()
          # Account type
        type_label = QLabel(self.account_data['type'].title())
        type_label.setStyleSheet("""
            color: rgba(255, 255, 255, 0.6);
            font-size: 11px;
            font-weight: 500;
            background: transparent;
            border: none;
        """)
        header_layout.addWidget(type_label)
        
        layout.addLayout(header_layout)
          # Account name
        name_label = QLabel(self.account_data['name'])
        name_label.setStyleSheet("""
            color: white;
            font-weight: 600;
            font-size: 14px;
            background: transparent;
            border: none;
        """)
        name_label.setWordWrap(True)
        layout.addWidget(name_label)
        
        # Balance row
        balance_layout = QHBoxLayout()
        balance_layout.setSpacing(8)
        
        self.balance_label = QLabel(format_currency(0))
        self.balance_label.setStyleSheet("""
            color: white;
            font-weight: 700;
            font-size: 16px;
            background: transparent;
            border: none;
        """)
        balance_layout.addWidget(self.balance_label)
        
        balance_layout.addStretch()
        
        self.activity_label = QLabel("0 transactions")
        self.activity_label.setStyleSheet("""
            color: rgba(255, 255, 255, 0.5);
            font-size: 11px;
            background: transparent;
            border: none;
        """)
        balance_layout.addWidget(self.activity_label)
        
        layout.addLayout(balance_layout)
        
    def update_balance(self, balance, transaction_count):
        """Update the card with current balance and activity."""
        self.balance = balance
        self.transaction_count = transaction_count
        
        # Format balance with appropriate color
        color = "#81C784" if balance >= 0 else "#F48FB1"
        self.balance_label.setText(format_currency(abs(balance)))
        self.balance_label.setStyleSheet(f"""
            color: {color};
            font-weight: 700;
            font-size: 16px;
            background: transparent;
            border: none;
        """)
        
        # Update activity
        self.activity_label.setText(f"{transaction_count} transactions")
        
    def mousePressEvent(self, event):
        """Handle card click."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.accountSelected.emit(self.account_data['name'])
        super().mousePressEvent(event)


class LedgerDocumentView(QWidget):
    """Full-page ledger document view - professional and printable."""
    
    backToOverview = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.account_name = None
        self.system = None
        self.from_date = None
        self.to_date = None
        # Add font_family attribute for print/preview styling
        from ..components.styles import ModernStyles
        self.font_family = ModernStyles.get_font_family()
        self._setup_ui()
    
    def show_account_details(self, account_name, system, from_date, to_date):
        """Configure and show the ledger for a specific account."""
        self.account_name = account_name
        self.system = system
        self.from_date = from_date
        self.to_date = to_date
        
        # Update the page header subtitle with account name and dynamic date display
        date_text = self._get_date_range_text()
        self.page_header.update_subtitle(f"Account: {account_name} • {date_text}")
        
        self._load_ledger_data()
    
    def _get_date_range_text(self):
        """Get formatted date range text for display."""
        if self.from_date and self.to_date:
            from_str = self.from_date if isinstance(self.from_date, str) else self.from_date.toString("MMMM d, yyyy")
            to_str = self.to_date if isinstance(self.to_date, str) else self.to_date.toString("MMMM d, yyyy")
            return f"{from_str} to {to_str}"
        elif self.to_date:
            to_str = self.to_date if isinstance(self.to_date, str) else self.to_date.toString("MMMM d, yyyy")
            return f"As of {to_str}"
        else:
            return "All Time"
    
    def _get_base_style(self):
        """Get the base style for the document view."""
        return f"""
            QWidget {{
                background: white;
                color: #1A1A1A;
                font-family: {ModernStyles.get_font_family()};
            }}
            QScrollArea {{
                border: 1px solid rgba(0, 0, 0, 0.12);
                background: white;
                padding: 0px;
                margin: 0px;
                border-radius: 8px;
            }}
            QWidget#transactionsContainer {{
                background: white;
                border: none;
                margin: 0px;
                padding: 0px;
            }}
            QPushButton {{
                font-family: {ModernStyles.get_font_family()};
                font-weight: 600;
                border-radius: 8px;
                padding: 10px 20px;
                border: none;
                font-size: 14px;
                min-height: 20px;
            }}
            QFrame {{
                border-radius: 8px;
            }}
        """
    
    def _setup_ui(self):
        """Setup the document-style ledger view."""
        # Set base styling
        self.setStyleSheet(self._get_base_style())
        
        layout = QVBoxLayout(self)
        responsive_margin = ResponsiveHelper.scale_size(32, 24, 48)
        layout.setContentsMargins(responsive_margin, 0, responsive_margin, responsive_margin)
        layout.setSpacing(16)
        
        # Page header (following standard pattern)
        self.page_header = PageHeader("General Ledger", "Detailed account transactions")
        layout.addWidget(self.page_header)
        
        # Date range selector (following standard pattern)
        self.date_selector = DateRangeSelector()
        self.date_selector.dateRangeChanged.connect(self._on_date_range_changed)
        layout.addWidget(self.date_selector)
        
        # Navigation and action buttons bar
        nav_layout = QHBoxLayout()
        
        # Back button with toolbar styling
        back_btn = QPushButton("← Back")
        # Back button with matching refresh button styling
        back_btn = QPushButton("◀ Accounts")
        back_btn.setFixedSize(140, 36)  # Same size as refresh button
        back_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.03);
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 6px;
                padding: 4px 16px;
                color: rgba(255, 255, 255, 0.8);
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.08);
                color: white;
            }
            QPushButton:pressed {
                background: rgba(0, 120, 215, 0.3);
                color: white;
            }
        """)
        back_btn.clicked.connect(self.backToOverview.emit)
        nav_layout.addWidget(back_btn)
        
        nav_layout.addStretch()
        
        # Print button with matching refresh button styling
        print_btn = QPushButton("Print Ledger")
        print_btn.setFixedSize(140, 36)  # Same size as refresh button
        print_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.03);
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 6px;
                padding: 4px 16px;
                color: rgba(255, 255, 255, 0.8);
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.08);
                color: white;
            }
            QPushButton:pressed {
                background: rgba(0, 120, 215, 0.3);
                color: white;
            }
        """)
        print_btn.clicked.connect(self._print_ledger)
        nav_layout.addWidget(print_btn)
        
        layout.addLayout(nav_layout)
        
        # Account summary section
        summary_frame = QFrame()
        summary_frame.setStyleSheet("""
            QFrame {
                background: rgba(245, 245, 245, 0.8);
                border: 1px solid rgba(0, 0, 0, 0.08);
                border-radius: 12px;
                margin: 10px 0px;
            }
        """)
        summary_layout = QHBoxLayout(summary_frame)
        summary_layout.setContentsMargins(24, 18, 24, 18)
        
        self.opening_balance_label = QLabel(f"Opening Balance: {format_currency(0)}")
        self.opening_balance_label.setStyleSheet("color: #333; font-weight: 600; font-size: 14px; background: transparent; border: none;")
        summary_layout.addWidget(self.opening_balance_label)
        
        summary_layout.addStretch()
        
        self.total_debits_label = QLabel(f"Total Debits: {format_currency(0)}")
        self.total_debits_label.setStyleSheet("color: #333; font-weight: 600; font-size: 14px; background: transparent; border: none;")
        summary_layout.addWidget(self.total_debits_label)
        
        summary_layout.addStretch()
        
        self.total_credits_label = QLabel(f"Total Credits: {format_currency(0)}")
        self.total_credits_label.setStyleSheet("color: #333; font-weight: 600; font-size: 14px; background: transparent; border: none;")
        summary_layout.addWidget(self.total_credits_label)
        
        summary_layout.addStretch()
        
        self.closing_balance_label = QLabel(f"Closing Balance: {format_currency(0)}")
        self.closing_balance_label.setStyleSheet("color: #333; font-weight: 700; font-size: 14px; background: transparent; border: none;")
        summary_layout.addWidget(self.closing_balance_label)
        
        layout.addWidget(summary_frame)
        
        # Ledger table
        self.table_widget = QWidget()
        table_layout = QVBoxLayout(self.table_widget)
        table_layout.setContentsMargins(0, 0, 0, 0)
        table_layout.setSpacing(0)
        
        # Table header
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background: #1976D2;
                border: none;
                border-radius: 0px;
            }
        """)
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(15, 12, 15, 12)
        header_layout.setSpacing(0)
        
        headers = [
            ("Date", 100),
            ("Description", 300),
            ("Reference", 120),
            ("Debit", 120),
            ("Credit", 120), 
            ("Balance", 120)
        ]
        
        for header_text, width in headers:
            header_label = QLabel(header_text)
            header_label.setStyleSheet("""
                color: white;
                font-weight: 700;
                font-size: 13px;
                background: transparent;
                border: none;
            """)
            if header_text in ["Debit", "Credit", "Balance"]:
                header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            header_label.setFixedWidth(width)
            header_layout.addWidget(header_label)
            
        table_layout.addWidget(header_frame)
        
        # Create scroll area container
        scroll_container = QWidget()
        scroll_container.setObjectName("scrollContainer")
        scroll_container_layout = QVBoxLayout(scroll_container)
        scroll_container_layout.setContentsMargins(0, 0, 0, 0)
        scroll_container_layout.setSpacing(0)
        
        # Scrollable transaction area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(400)  # Ensure reasonable minimum height
        
        # Transaction content widget
        self.transactions_widget = QWidget()
        self.transactions_widget.setObjectName("transactionsContainer")
        self.transactions_layout = QVBoxLayout(self.transactions_widget)
        self.transactions_layout.setContentsMargins(0, 0, 0, 0)
        self.transactions_layout.setSpacing(0)
        self.transactions_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Modern styling
        scroll_style = """
            QScrollArea {
                border: 1px solid #E0E0E0;
                background: white;
                padding: 0px;
                margin: 0px;
            }
            QWidget#scrollContainer {
                background: white;
                border: none;
                margin: 0px;
                padding: 0px;
            }
            QWidget#transactionsContainer {
                background: white;
                border: none;
                margin: 0px;
                padding: 0px;
            }
        """ + ModernScrollbarStyles.get_vertical_scrollbar_style()
        scroll.setStyleSheet(scroll_style)
        
        # Set up the widget hierarchy
        scroll.setWidget(self.transactions_widget)
        scroll_container_layout.addWidget(scroll)
        table_layout.addWidget(scroll_container)
        
        # Add the table to the main layout with stretch
        layout.addWidget(self.table_widget, 1)
        
        # Footer
        footer_layout = QHBoxLayout()
        
        date_generated = QLabel(f"Generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}")
        date_generated.setStyleSheet("""
            color: #999;
            font-size: 11px;
            font-style: italic;
            background: transparent;
            border: none;        """)
        footer_layout.addWidget(date_generated)
        layout.addLayout(footer_layout)
        
    def _load_ledger_data(self):
        """Load and display ledger transactions."""
        # Don't load data if account is not set yet
        if not self.account_name or not self.system:
            return
            
        try:
            # Get transactions for this account using the get_ledger method
            if self.from_date and self.to_date:
                from_date_str = self.from_date.toString("yyyy-MM-dd")
                to_date_str = self.to_date.toString("yyyy-MM-dd")
                account_entries = self.system.get_ledger(self.account_name, from_date_str, to_date_str)
            else:
                account_entries = self.system.get_ledger(self.account_name)
                
            # Sort by date
            account_entries.sort(key=lambda x: x[0])  # Sort by date
            
            # Calculate running balance and totals
            running_balance = 0.0
            total_debits = 0.0
            total_credits = 0.0
            
            # Clear existing transactions
            while self.transactions_layout.count():
                item = self.transactions_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            
            # Create a container widget to hold all transactions
            transactions_container = QWidget()
            transactions_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            container_layout = QVBoxLayout(transactions_container)
            container_layout.setContentsMargins(0, 0, 0, 0)
            container_layout.setSpacing(0)
            container_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
            
            if not account_entries:
                no_data = QLabel("No transactions found for this account in the selected period.")
                no_data.setStyleSheet("""
                    color: #666;
                    font-size: 16px;
                    text-align: center;
                    padding: 40px;
                    background: transparent;
                    border: none;
                """)
                no_data.setAlignment(Qt.AlignmentFlag.AlignCenter)
                container_layout.addWidget(no_data)
            else:
                for i, entry in enumerate(account_entries):
                    date, description, debit_account, credit_account, amount = entry
                    
                    # Handle account name matching (improved logic)
                    def account_matches(journal_account, target_account_name):
                        """Check if the journal account matches the target account name."""
                        # Direct name match
                        if journal_account == target_account_name:
                            return True
                        
                        # Check if journal account is in "code - name" format
                        if ' - ' in journal_account:
                            parts = journal_account.split(' - ', 1)
                            if len(parts) == 2:
                                j_code, j_name = parts
                                # Match by name (in case code is slightly different)
                                if j_name == target_account_name:
                                    return True
                        
                        # Partial match for cases where formatting might be inconsistent
                        if target_account_name in journal_account or journal_account in target_account_name:
                            return True
                            
                        return False
                    
                    is_debit = account_matches(debit_account, self.account_name)
                    debit_amount = amount if is_debit else 0
                    credit_amount = amount if not is_debit else 0
                    
                    # Update running balance
                    if is_debit:
                        running_balance += amount
                        total_debits += amount
                    else:
                        running_balance -= amount
                        total_credits += amount
                      # Create transaction row with fixed height
                    row_frame = QFrame()
                    row_frame.setFixedHeight(40)  # Fixed height for consistency
                    row_color = "#FAFAFA" if i % 2 == 0 else "white"
                    row_frame.setStyleSheet(f"""
                        QFrame {{
                            background: {row_color};
                            border: none;
                            border-bottom: 1px solid #F0F0F0;
                            padding: 0px;
                            margin: 0px;
                        }}
                        QFrame:hover {{
                            background: #E3F2FD;
                        }}
                    """)
                    
                    row_layout = QHBoxLayout(row_frame)
                    row_layout.setContentsMargins(15, 10, 15, 10)
                    row_layout.setSpacing(0)
                    
                    # Date
                    date_label = QLabel(date)
                    date_label.setStyleSheet("color: #333; font-size: 12px; background: transparent; border: none;")
                    date_label.setFixedWidth(100)
                    row_layout.addWidget(date_label)
                    
                    # Description
                    desc_label = QLabel(description)
                    desc_label.setStyleSheet("color: #333; font-size: 12px; background: transparent; border: none;")
                    desc_label.setFixedWidth(300)
                    desc_label.setWordWrap(True)
                    row_layout.addWidget(desc_label)
                    
                    # Reference (other account)
                    other_account = credit_account if is_debit else debit_account
                    ref_label = QLabel(other_account)
                    ref_label.setStyleSheet("color: #666; font-size: 11px; background: transparent; border: none;")
                    ref_label.setFixedWidth(120)
                    ref_label.setWordWrap(True)
                    row_layout.addWidget(ref_label)
                      # Debit
                    debit_label = QLabel(format_currency(debit_amount) if debit_amount > 0 else "")
                    debit_label.setStyleSheet("color: #333; font-size: 12px; font-weight: 600; background: transparent; border: none;")
                    debit_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    debit_label.setFixedWidth(120)
                    row_layout.addWidget(debit_label)
                    
                    # Credit
                    credit_label = QLabel(format_currency(credit_amount) if credit_amount > 0 else "")
                    credit_label.setStyleSheet("color: #333; font-size: 12px; font-weight: 600; background: transparent; border: none;")
                    credit_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    credit_label.setFixedWidth(120)
                    row_layout.addWidget(credit_label)
                      # Running Balance
                    balance_label = QLabel(format_currency(abs(running_balance)))
                    balance_label.setStyleSheet("color: #333; font-size: 12px; font-weight: 700; background: transparent; border: none;")
                    balance_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    balance_label.setFixedWidth(120)
                    row_layout.addWidget(balance_label)
                    
                    container_layout.addWidget(row_frame)
            
            # Add the transactions container to the main layout
            self.transactions_layout.addWidget(transactions_container)
            
            # Update summary labels
            self.total_debits_label.setText(f"Total Debits: {format_currency(total_debits)}")
            self.total_credits_label.setText(f"Total Credits: {format_currency(total_credits)}")
            self.closing_balance_label.setText(f"Closing Balance: {format_currency(running_balance)}")
            
            # Add stretch at the end
            self.transactions_layout.addStretch()
            
        except Exception as e:
            print(f"Error loading ledger data: {e}")
            error_label = QLabel(f"Error loading ledger data: {str(e)}")
            error_label.setStyleSheet("color: #F44336; background: transparent; border: none;")
            self.transactions_layout.addWidget(error_label)
    
    def _print_ledger(self):
        """Print or export the ledger using Windows native print function."""
        try:
            import tempfile
            import os
            import webbrowser
            from PyQt6.QtGui import QPainter, QPixmap
            
            # Create a temporary HTML file with the ledger content
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
                html_content = self._generate_html_content()
                f.write(html_content)
                temp_file = f.name
            
            # Open the HTML file in the default browser, which will allow printing
            webbrowser.open('file://' + temp_file.replace('\\', '/'))
            
            # Show a message to the user
            QMessageBox.information(self, "Print", 
                "The ledger has been opened in your web browser.\n"
                "Use Ctrl+P or the browser's print menu to print the document.\n"
                "The temporary file will be cleaned up automatically.")
            
            # Clean up the temporary file after a delay
            import threading
            import time
            def cleanup():
                time.sleep(10)  # Wait 10 seconds before cleanup
                try:
                    os.unlink(temp_file)
                except:
                    pass
            
            threading.Thread(target=cleanup, daemon=True).start()
                
        except Exception as e:
            print(f"Print error: {e}")
            QMessageBox.information(self, "Print", 
                f"Unable to open print preview: {str(e)}\n"
                "You can manually copy the ledger content or take a screenshot to print.")
    
    def _generate_html_content(self):
        """Generate HTML content for printing."""
        # Get account information
        account_name = self.account_name or "Account"
        
        # Get date range
        if self.from_date and self.to_date:
            date_range = f"{self.from_date.toString('MMMM d, yyyy')} to {self.to_date.toString('MMMM d, yyyy')}"
        else:
            date_range = "All Time"
        
        # Get summary data
        opening_balance = self.opening_balance_label.text()
        total_debits = self.total_debits_label.text()
        total_credits = self.total_credits_label.text()
        closing_balance = self.closing_balance_label.text()
          # Get transactions (we'll need to recreate this from the system)
        transactions_html = ""
        try:
            if self.system and self.account_name:
                # Use the same get_ledger method we fixed earlier
                if self.from_date and self.to_date:
                    from_date_str = self.from_date.toString("yyyy-MM-dd")
                    to_date_str = self.to_date.toString("yyyy-MM-dd")
                    account_entries = self.system.get_ledger(self.account_name, from_date_str, to_date_str)
                else:
                    account_entries = self.system.get_ledger(self.account_name)
                
                # Sort by date
                account_entries.sort(key=lambda x: x[0])
                
                # Helper function to match accounts (same as in _load_ledger_data)
                def account_matches(stored_account, target_account):
                    if stored_account == target_account:
                        return True
                    # Check if it's in "code - name" format and matches
                    if ' - ' in stored_account and stored_account.endswith(target_account):
                        return True
                    if ' - ' in stored_account and target_account in stored_account:
                        return True
                    return False
                
                # Generate transaction rows
                running_balance = 0.0
                for entry in account_entries:
                    date, description, debit_account, credit_account, amount = entry
                    
                    is_debit = account_matches(debit_account, self.account_name)
                    debit_amount = amount if is_debit else 0
                    credit_amount = amount if not is_debit else 0
                    
                    # Update running balance
                    if is_debit:
                        running_balance += amount
                    else:
                        running_balance -= amount
                    
                    from ...core.utils import format_currency
                    
                    # Create a simple entry ID (since get_ledger doesn't return entry_id)
                    entry_ref = f"JE-{hash(f'{date}{description}{amount}') % 10000:04d}"
                    
                    transactions_html += f"""
                    <tr>
                        <td>{date}</td>
                        <td>{description}</td>
                        <td>{entry_ref}</td>
                        <td style="text-align: center;">{format_currency(debit_amount) if debit_amount > 0 else ''}</td>
                        <td style="text-align: center;">{format_currency(credit_amount) if credit_amount > 0 else ''}</td>
                        <td style="text-align: center;">{format_currency(abs(running_balance))}</td>
                    </tr>
                    """
        except Exception as e:
            transactions_html = f"<tr><td colspan='6'>Error loading transactions: {str(e)}</td></tr>"
        
        # Generate complete HTML
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>General Ledger - {account_name}</title>
            <style>
                body {{
                    font-family: {self.font_family};
                    margin: 40px;
                    color: #333;
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 30px;
                }}
                .title {{
                    font-size: 24px;
                    font-weight: bold;
                    color: #1976D2;
                    margin-bottom: 10px;
                }}
                .account-name {{
                    font-size: 18px;
                    font-weight: 600;
                    margin-bottom: 5px;
                }}
                .date-range {{
                    font-size: 14px;
                    color: #666;
                }}
                .summary {{
                    background: #F5F5F5;
                    border: 1px solid #E0E0E0;
                    border-radius: 8px;
                    padding: 20px;
                    margin: 20px 0;
                    display: flex;
                    justify-content: space-around;
                }}
                .summary-item {{
                    text-align: center;
                    font-weight: 600;
                    font-size: 14px;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 20px;
                }}
                th {{
                    background: #1976D2;
                    color: white;
                    padding: 12px;
                    text-align: left;
                    font-weight: 600;
                }}
                th.center, td.center {{
                    text-align: center;
                }}
                td {{
                    padding: 8px 12px;
                    border-bottom: 1px solid #E0E0E0;
                    font-size: 12px;
                }}
                tr:nth-child(even) {{
                    background-color: #FAFAFA;
                }}
                .footer {{
                    margin-top: 30px;
                    text-align: right;
                    font-size: 11px;
                    color: #999;
                    font-style: italic;
                }}
                @media print {{
                    body {{ margin: 20px; }}
                    .no-print {{ display: none; }}
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <div class="title">GENERAL LEDGER</div>
                <div class="account-name">Account: {account_name}</div>
                <div class="date-range">Period: {date_range}</div>
            </div>
            
            <div class="summary">
                <div class="summary-item">{opening_balance}</div>
                <div class="summary-item">{total_debits}</div>
                <div class="summary-item">{total_credits}</div>
                <div class="summary-item">{closing_balance}</div>
            </div>
            
            <table>
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Description</th>
                        <th>Reference</th>
                        <th class="center">Debit</th>
                        <th class="center">Credit</th>
                        <th class="center">Balance</th>
                    </tr>
                </thead>
                <tbody>
                    {transactions_html}
                </tbody>
            </table>
            
            <div class="footer">
                Generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
            </div>
        </body>
        </html>
        """
        
        return html

    def _on_date_range_changed(self, from_date, to_date):
        """Handle date range changes and reload ledger data."""
        self.from_date = from_date
        self.to_date = to_date
        
        # Update the page header subtitle with the new date range
        if self.account_name:
            date_text = self._get_date_range_text()
            self.page_header.update_subtitle(f"Account: {self.account_name} • {date_text}")
        
        # Reload ledger data with new date range
        self._load_ledger_data()


class TransactionRowCard(QFrame):
    """Individual transaction row in the detail panel."""
    
    def __init__(self, entry_data, account_name):
        super().__init__()
        self.entry_data = entry_data
        self.account_name = account_name
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup the transaction row UI."""
        self.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.03);
                border: 1px solid rgba(0, 0, 0, 0.3);
                border-radius: 8px;
                margin: 1px 0px;
            }
            QFrame:hover {
                background: rgba(255, 255, 255, 0.06);
                border-color: rgba(100, 181, 246, 0.3);
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)
          # Date
        date_label = QLabel(str(self.entry_data['entry_date']))
        date_label.setStyleSheet("color: #90CAF9; font-weight: 500; font-size: 12px; background: transparent; border: none;")
        date_label.setFixedWidth(80)
        layout.addWidget(date_label)
        
        # Description
        desc_label = QLabel(str(self.entry_data['description']))
        desc_label.setStyleSheet("color: white; font-weight: 500; font-size: 12px; background: transparent; border: none;")
        desc_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout.addWidget(desc_label)
          # Other account
        debit_account = self.entry_data.get('debit_account', '')
        credit_account = self.entry_data.get('credit_account', '')
        other_account = credit_account if self.account_name == debit_account else debit_account
        
        other_label = QLabel(other_account)
        other_label.setStyleSheet("color: #FFAB91; font-size: 11px; background: transparent; border: none;")
        other_label.setFixedWidth(120)
        layout.addWidget(other_label)
          # Amount (debit/credit indication)
        amount = float(self.entry_data['amount'])
        is_debit = self.account_name == debit_account
        
        amount_text = f"${amount:,.2f}"
        if is_debit:
            amount_text = f"Dr {amount_text}"
            color = "#81C784"
        else:
            amount_text = f"Cr {amount_text}"
            color = "#F48FB1"
            
        amount_label = QLabel(amount_text)
        amount_label.setStyleSheet(f"color: {color}; font-weight: 600; font-size: 12px; background: transparent; border: none;")
        amount_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        amount_label.setFixedWidth(100)
        layout.addWidget(amount_label)


class LedgerPage(QWidget):
    """Modern General Ledger with card-based interface and smart filtering."""
    def __init__(self, system, parent=None):
        super().__init__(parent)
        self.system = system
        self.account_cards = []
        # Get font family from ModernStyles
        self.font_family = ModernStyles.get_font_family()
        self._setup_ui()
        self._apply_styling()
        self._load_accounts()
        
        # Connect to account change events to refresh when accounts are created/updated/deleted
        accounting_events.accounts_changed.connect(self._on_accounts_changed)
    
    def _apply_styling(self):
        """Apply modern glassmorphism styling to the ledger page."""
        GlassmorphismHelper.apply_main_container_effect(self)
        # Removed global stylesheet that was overriding button styling
    
    def _setup_ui(self):
        """Setup the main ledger UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create stacked widget for switching views
        self.stacked_widget = QStackedWidget()
        
        # Create account overview page
        self.overview_page = self._create_overview_page()
        self.stacked_widget.addWidget(self.overview_page)
        
        # Create ledger document view page  
        self.document_view = LedgerDocumentView()
        self.document_view.backToOverview.connect(self._show_overview)
        self.stacked_widget.addWidget(self.document_view)
        
        layout.addWidget(self.stacked_widget)
        
    def _create_overview_page(self):
        """Create the account overview page."""
        page = QWidget()
        layout = QVBoxLayout(page)
        responsive_margin = ResponsiveHelper.scale_size(32, 24, 48)
        layout.setContentsMargins(responsive_margin, 0,  # Remove top margin
                                 responsive_margin, responsive_margin)
        layout.setSpacing(16)  # Standardized spacing
        
        # Page header
        header = PageHeader("General Ledger", "Account balances and transaction details")
        layout.addWidget(header)
          # Date range selector
        self.date_selector = DateRangeSelector()
        self.date_selector.dateRangeChanged.connect(self._refresh_balances)
        layout.addWidget(self.date_selector)
        
        # Filter bar with search and account type filter
        filter_layout = QHBoxLayout()
        
        self.type_filter = QComboBox()
        self.type_filter.addItems(["All Types", "Asset", "Liability", "Equity", "Income", "Expense"])
        self.type_filter.setStyleSheet("""
            QComboBox {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(0, 0, 0, 0.3);
                border-radius: 8px;
                padding: 8px 16px;
                color: white;
                font-size: 12px;
                font-weight: 500;
                min-height: 32px;
                min-width: 150px;
            }
            QComboBox:hover {
                background: rgba(255, 255, 255, 0.12);
                border: 1px solid rgba(100, 181, 246, 0.3);
            }
            QComboBox:focus {
                background: rgba(100, 181, 246, 0.15);
                border: 1px solid rgba(100, 181, 246, 0.5);
                color: #90CAF9;
            }
            QComboBox::drop-down {
                border: none;
                width: 32px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid rgba(255, 255, 255, 0.7);
                margin-right: 8px;
            }
            QComboBox QAbstractItemView {
                background: rgba(40, 40, 40, 0.95);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                color: white;
                selection-background-color: rgba(100, 181, 246, 0.15);
                selection-color: #90CAF9;
                padding: 4px;
            }
            QComboBox QAbstractItemView::item {
                padding: 8px 16px;
                border: none;
                border-radius: 6px;
                margin: 2px;
                min-height: 24px;
            }
            QComboBox QAbstractItemView::item:hover {
                background: rgba(255, 255, 255, 0.12);
                border: 1px solid rgba(100, 181, 246, 0.3);
            }
            QComboBox QAbstractItemView::item:selected {
                background: rgba(100, 181, 246, 0.15);
                border: 1px solid rgba(100, 181, 246, 0.5);
                color: #90CAF9;
            }
        """)
        self.type_filter.currentTextChanged.connect(self._filter_accounts)
        filter_layout.addWidget(self.type_filter)
        
        filter_layout.addSpacing(4)
        
        # Search box - now next to the type filter
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search accounts...")
        self.search_box.setFixedWidth(250)
        self.search_box.setStyleSheet("""
            QLineEdit {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(0, 0, 0, 0.3);
                border-radius: 8px;
                padding: 8px 16px;
                color: white;
                font-size: 12px;
                font-weight: 500;
                min-height: 32px;
            }
            QLineEdit:hover {
                background: rgba(255, 255, 255, 0.12);
                border: 1px solid rgba(100, 181, 246, 0.3);
            }
            QLineEdit:focus {
                background: rgba(100, 181, 246, 0.15);
                border: 1px solid rgba(100, 181, 246, 0.5);
                color: #90CAF9;
            }
            QLineEdit::placeholder {
                color: rgba(255, 255, 255, 0.6);
            }
        """)
        self.search_box.textChanged.connect(self._filter_accounts)
        filter_layout.addWidget(self.search_box)
        
        filter_layout.addStretch()
        
        # Refresh button with height matching search field
        refresh_btn = QPushButton("Refresh Balances")
        refresh_btn.setFixedSize(140, 48)  # Match search field height (32px min-height + 16px padding)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.03);
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 6px;
                padding: 4px 16px;
                color: rgba(255, 255, 255, 0.8);
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.08);
                color: white;
            }
            QPushButton:pressed {
                background: rgba(0, 120, 215, 0.3);
                color: white;
            }
        """)
        refresh_btn.clicked.connect(self._refresh_balances)
        filter_layout.addWidget(refresh_btn)
        
        layout.addLayout(filter_layout)
          # Accounts scroll area with modern scrollbar
        self.accounts_scroll = QScrollArea()
        self.accounts_scroll.setWidgetResizable(True)
        
        # Apply modern scrollbar styling
        accounts_scroll_style = """
            QScrollArea {
                border: none;
                background: transparent;
            }
        """ + ModernScrollbarStyles.get_vertical_scrollbar_style()
        self.accounts_scroll.setStyleSheet(accounts_scroll_style)
        
        self.accounts_widget = QWidget()
        self.accounts_layout = QGridLayout(self.accounts_widget)
        self.accounts_layout.setContentsMargins(0, 0, 0, 0)
        self.accounts_layout.setSpacing(12)
        
        self.accounts_scroll.setWidget(self.accounts_widget)
        layout.addWidget(self.accounts_scroll)
        
        return page
        
    def _show_overview(self):
        """Switch back to the account overview."""
        self.stacked_widget.setCurrentIndex(0)
        
    def _show_account_details(self, account_name):
        """Show detailed transactions for the selected account in full-page view."""
        from_date, to_date = self.date_selector.get_date_range()
        
        # Set up the document view with the selected account
        self.document_view.show_account_details(account_name, self.system, from_date, to_date)
        
        # Switch to the document view
        self.stacked_widget.setCurrentIndex(1)
        
    def _load_accounts(self):
        """Load all accounts and create cards."""
        try:
            # Only load active accounts - this will automatically exclude deleted accounts
            accounts = self.system.get_chart_of_accounts(active_only=True)
            self.all_accounts = accounts
            self._display_accounts(accounts)
            self._refresh_balances()
        except Exception as e:
            print(f"Error loading accounts: {e}")
    
    def _on_accounts_changed(self):
        """Handle account changes by refreshing the account list."""
        try:
            print("🔄 Ledger page: Refreshing accounts due to account changes...")
            self._load_accounts()
        except Exception as e:
            print(f"❌ Error refreshing accounts in ledger: {e}")
            
    def _display_accounts(self, accounts):
        """Display account cards in a grid."""
        # Clear existing cards
        for card in self.account_cards:
            card.setParent(None)
        self.account_cards.clear()
        
        # Create new cards
        row, col = 0, 0
        max_cols = 3
        
        for account in accounts:
            # account is a dict with all account fields
            account_data = account  # Full account dict
            account_level = account['level']  # level
            
            card = AccountCard(account_data, account_level)
            card.accountSelected.connect(self._show_account_details)
            self.account_cards.append(card)
            
            self.accounts_layout.addWidget(card, row, col)
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
                
        # Add stretch to fill remaining space
        self.accounts_layout.setRowStretch(row + 1, 1)
        
    def _filter_accounts(self):
        """Filter accounts based on search and type filter."""
        search_text = self.search_box.text().lower()
        type_filter = self.type_filter.currentText()
        
        filtered_accounts = []
        for account in self.all_accounts:
            # account is a dict with all account fields
            name, acc_type, code, parent_code = account['name'], account['type'], account['code'], account['parent_code']
            
            # Apply search filter
            if search_text and search_text not in name.lower() and search_text not in (code or "").lower():
                continue
                
            # Apply type filter
            if type_filter != "All Types" and acc_type.lower() != type_filter.lower():
                continue
                
            filtered_accounts.append(account)
            
        self._display_accounts(filtered_accounts)
        self._refresh_balances()
        
    def _refresh_balances(self):
        """Refresh account balances for the selected date range with hierarchical aggregation."""
        from_date, to_date = self.date_selector.get_date_range()
        
        try:
            # Use the new hierarchical balance calculation
            if hasattr(self.system, 'get_hierarchical_account_balances'):
                # Get hierarchical balances (includes parent account aggregation)
                from_date_str = from_date.toString("yyyy-MM-dd")
                to_date_str = to_date.toString("yyyy-MM-dd")
                hierarchical_balances = self.system.get_hierarchical_account_balances(from_date_str, to_date_str)
                
                # Update each account card with hierarchical balance
                for card in self.account_cards:
                    account_name = card.account_data['name']
                    balance_info = hierarchical_balances.get(account_name, {})
                    
                    # Get net balance and transaction count
                    net_balance = balance_info.get('net_balance', 0.0)
                    debit_total = balance_info.get('debit_total', 0.0)
                    credit_total = balance_info.get('credit_total', 0.0)
                    transaction_count = int(debit_total + credit_total)  # Simplified count
                    
                    # Update card with hierarchical balance
                    card.update_balance(net_balance, transaction_count)
                    
                    # Add visual indicator for parent accounts with aggregated balances
                    if balance_info.get('has_children', False):
                        card.setToolTip(f"Parent account with {balance_info.get('child_count', 0)} child accounts\n"
                                      f"Aggregated balance: {net_balance:,.2f}")
                    else:
                        card.setToolTip(f"Direct balance: {net_balance:,.2f}")
                        
            else:
                # Fallback to original method if hierarchical method not available
                self._refresh_balances_fallback(from_date, to_date)
                
        except Exception as e:
            print(f"Error refreshing hierarchical balances: {e}")
            # Fallback to original method
            self._refresh_balances_fallback(from_date, to_date)
    
    def _refresh_balances_fallback(self, from_date, to_date):
        """Fallback method using original balance calculation."""
        try:
            # Get transactions for the date range
            from_date_str = from_date.toString("yyyy-MM-dd")
            to_date_str = to_date.toString("yyyy-MM-dd")
            entries = self.system.get_journal_entries_by_date_range(from_date_str, to_date_str)
            
            # Calculate balances for each account
            account_balances = {}
            account_counts = {}
            
            # Helper function to match account names (handles "code - name" format)
            def find_matching_account_name(journal_account, card_account_name, card_account_code):
                """Check if the journal account matches the card account."""
                # Direct name match
                if journal_account == card_account_name:
                    return True
                
                # Check if journal account is in "code - name" format
                if ' - ' in journal_account:
                    parts = journal_account.split(' - ', 1)
                    if len(parts) == 2:
                        j_code, j_name = parts
                        # Match by code and name
                        if j_code == card_account_code and j_name == card_account_name:
                            return True
                        # Match by name only (in case code is slightly different)
                        if j_name == card_account_name:
                            return True
                
                # Partial match for cases where formatting might be inconsistent
                if card_account_name in journal_account or journal_account in card_account_name:
                    return True
                    
                return False
            
            for entry in entries:
                # Handle both dictionary and tuple formats
                if isinstance(entry, dict):
                    debit_account = entry.get('debit_account', '')
                    credit_account = entry.get('credit_account', '')
                    amount = float(entry.get('amount', 0))
                elif isinstance(entry, (list, tuple)) and len(entry) >= 5:
                    # Tuple format: (date, description, debit_account, credit_account, amount)
                    debit_account = entry[2]
                    credit_account = entry[3]
                    amount = float(entry[4])
                else:
                    continue  # Skip invalid entries
                    
                # Process each account in our cards
                for card in self.account_cards:
                    account_name = card.account_data['name']
                    account_code = card.account_data.get('code', '')
                    
                    # Check if this entry affects this account
                    is_debit_match = find_matching_account_name(debit_account, account_name, account_code)
                    is_credit_match = find_matching_account_name(credit_account, account_name, account_code)
                    
                    if is_debit_match or is_credit_match:
                        if account_name not in account_balances:
                            account_balances[account_name] = 0.0
                            account_counts[account_name] = 0
                        
                        if is_debit_match:
                            account_balances[account_name] += amount
                            account_counts[account_name] += 1
                        
                        if is_credit_match:
                            account_balances[account_name] -= amount
                            account_counts[account_name] += 1
            
            # Update cards with calculated balances
            for card in self.account_cards:
                account_name = card.account_data['name']
                balance = account_balances.get(account_name, 0.0)
                count = account_counts.get(account_name, 0)
                card.update_balance(balance, count)
                
        except Exception as e:
            print(f"Error in fallback balance calculation: {e}")

    def refresh_currency_display(self):
        """Refresh all currency displays when currency symbol changes."""
        try:
            # Refresh account overview balances
            self._refresh_balances()
            
            # Refresh ledger document view if currently displayed
            if hasattr(self, 'document_view') and self.document_view:
                # If we have a current account selected, refresh its display
                if hasattr(self.document_view, 'current_account') and self.document_view.current_account:
                    self.document_view.load_account_ledger(self.document_view.current_account)
                    
        except Exception as e:
            print(f"Error refreshing currency display: {e}")
    
    def set_date_range(self, start_date, end_date):
        """Set the date range programmatically (for AI navigation)."""
        if hasattr(self, 'date_selector') and self.date_selector:
            success = self.date_selector.set_date_range(start_date, end_date)
            if success:
                print(f"✅ Ledger date range set to: {start_date} to {end_date}")
                # Refresh the current view with new date range
                self._refresh_balances()
                return True
            else:
                print(f"❌ Failed to set ledger date range: {start_date} to {end_date}")
                return False
        return False
    
    def show_specific_account(self, account_name):
        """Navigate directly to a specific account's ledger (for AI navigation)."""
        try:
            # First, ensure we have accounts loaded
            if not hasattr(self, 'all_accounts') or not self.all_accounts:
                self._load_accounts()
            
            # Use AI Account Resolver for intelligent matching
            from ...core.ai_account_resolver import AIAccountResolver
            resolver = AIAccountResolver(self.system)
            
            print(f"🔍 AI resolver searching for account: '{account_name}'")
            
            # Find the best match using AI resolver
            best_match = resolver.find_best_match(account_name, min_confidence=0.5)
            
            if best_match:
                print(f"✅ AI resolver found account: '{best_match.account_name}' (confidence: {best_match.confidence:.2f}, type: {best_match.match_type})")
                # Navigate directly to account details
                self._show_account_details(best_match.account_name)
                return True
            else:
                # Fallback: try to find accounts with lower confidence for filtering
                all_matches = resolver.find_matches(account_name, min_confidence=0.3)
                
                if all_matches:
                    print(f"⚠️ No high-confidence match found, showing {len(all_matches)} potential matches in search")
                    # Show the search results by filtering
                    if hasattr(self, 'search_box'):
                        # Use the best partial match for search filtering
                        best_partial = all_matches[0]
                        search_term = best_partial.account_name.split(' ')[0]  # Use first word for broader search
                        self.search_box.setText(search_term)
                        self._filter_accounts()
                    return False
                else:
                    print(f"❌ No accounts found matching: '{account_name}'")
                    # Clear search to show all accounts
                    if hasattr(self, 'search_box'):
                        self.search_box.clear()
                        self._filter_accounts()
                    return False
                
        except Exception as e:
            print(f"❌ Error in AI account navigation: {e}")
            # Fallback to original basic matching
            return self._show_specific_account_fallback(account_name)
    
    def _show_specific_account_fallback(self, account_name):
        """Fallback method using basic string matching if AI resolver fails"""
        try:
            target_account = None
            account_name_lower = account_name.lower()
            
            for account in self.all_accounts:
                # Try exact match first
                if account['name'].lower() == account_name_lower:
                    target_account = account
                    break
                # Try partial match
                elif account_name_lower in account['name'].lower():
                    target_account = account
                    break
                # Try matching by code if provided
                elif account.get('code') and account_name_lower in account.get('code', '').lower():
                    target_account = account
                    break
            
            if target_account:
                print(f"✅ Fallback found account: {target_account['name']}")
                self._show_account_details(target_account['name'])
                return True
            else:
                print(f"❌ Fallback: Account not found: {account_name}")
                if hasattr(self, 'search_box'):
                    self.search_box.setText(account_name)
                    self._filter_accounts()
                return False
                
        except Exception as e:
            print(f"❌ Error in fallback account search: {e}")
            return False

    def _create_transactions_area(self):
        """Create the scrollable transactions area with proper layout."""
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        
        # Table header (stays fixed)
        header = QWidget()
        header.setStyleSheet("""
            background: #1976D2;
            border-radius: 0px;
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(15, 12, 15, 12)
        header_layout.setSpacing(0)
        
        headers = [
            ("Date", 100),
            ("Description", 300),
            ("Reference", 120),
            ("Debit", 120),
            ("Credit", 120),
            ("Balance", 120)
        ]
        
        for header_text, width in headers:
            label = QLabel(header_text)
            label.setStyleSheet("""
                color: white;
                font-weight: 700;
                font-size: 13px;
                background: transparent;
            """)
            if header_text in ["Debit", "Credit", "Balance"]:
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setFixedWidth(width)
            header_layout.addWidget(label)
            
        container_layout.addWidget(header)
        
        # Scrollable transactions area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(ModernScrollbarStyles.get_vertical_scrollbar_style())
        
        # Container for transaction rows
        self.transactions_widget = QWidget()
        self.transactions_widget.setObjectName("transactionsContainer")
        self.transactions_layout = QVBoxLayout(self.transactions_widget)
        self.transactions_layout.setContentsMargins(0, 0, 0, 0)
        self.transactions_layout.setSpacing(0)
        self.transactions_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        scroll.setWidget(self.transactions_widget)
        container_layout.addWidget(scroll, 1)  # Give scroll area stretch factor
        
        return container
