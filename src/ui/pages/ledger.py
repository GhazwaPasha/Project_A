"""
Modern General Ledger - Professional Accounting Interface
Card-based design with progressive disclosure and smart filtering
Built for efficiency and clarity in professional accounting workflows
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QLineEdit, QComboBox, QFrame, QScrollArea,
    QSpacerItem, QSizePolicy, QGridLayout, QStackedWidget
)
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QTimer
from PyQt6.QtGui import QFont, QColor, QPalette
from datetime import datetime, timedelta
from ...core.utils import format_currency

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
                border: 1px solid rgba(255, 255, 255, 0.12);                border-radius: 8px;
                border-color: rgba(0, 0, 0, 0.3);
                margin: 4px;
            }            QFrame:hover {
                background: rgba(255, 255, 255, 0.12);
                border-color: rgba(255, 255, 255, 0.25);
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)
          # Header row
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)
        
        # Account code
        code_label = QLabel(self.account_data[2] or "")
        code_label.setStyleSheet("""
            color: #64B5F6;
            font-weight: 600;
            font-size: 11px;
            background: rgba(100, 181, 246, 0.2);
            padding: 2px 6px;
            border-radius: 4px;
            border: none;        """)
        code_label.setFixedWidth(50)
        header_layout.addWidget(code_label)
        
        # Level tag with color coding
        level_colors = {
            1: {"bg": "rgba(100, 150, 255, 0.2)", "color": "#6496FF"},  # Blue
            2: {"bg": "rgba(150, 200, 100, 0.2)", "color": "#96C864"},  # Green  
            3: {"bg": "rgba(255, 200, 100, 0.2)", "color": "#FFC864"}   # Orange
        }
        
        level_style = level_colors.get(self.account_level, level_colors[1])
        level_label = QLabel(f"lvl. {self.account_level}")
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
        level_label.setToolTip(f"Account Level {self.account_level}")
        header_layout.addWidget(level_label)
        
        header_layout.addStretch()
        
        # Account type
        type_label = QLabel(self.account_data[1].title())
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
        name_label = QLabel(self.account_data[0])
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
        
        self.balance_label = QLabel("$0.00")
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
            self.accountSelected.emit(self.account_data[0])
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
        self._setup_ui()
        
    def show_account_details(self, account_name, system, from_date, to_date):
        """Configure and show the ledger for a specific account."""
        self.account_name = account_name
        self.system = system
        self.from_date = from_date
        self.to_date = to_date
        
        # Update the account title
        self.account_title.setText(f"Account: {account_name}")
        
        # Update date range if provided
        if from_date and to_date:
            date_range = f"Period: {from_date.toString('MMMM d, yyyy')} to {to_date.toString('MMMM d, yyyy')}"
            self.date_label.setText(date_range)
        
        self._load_ledger_data()
        
    def _setup_ui(self):
        """Setup the document-style ledger view."""
        self.setStyleSheet("""
            QWidget {
                background: white;
                color: black;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(20)
        
        # Header section
        header_layout = QVBoxLayout()
        header_layout.setSpacing(8)
        
        # Company/Title
        title = QLabel("GENERAL LEDGER")
        title.setStyleSheet("""
            color: #1976D2;
            font-size: 24px;
            font-weight: 700;
            text-align: center;
            background: transparent;
            border: none;
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(title)
        
        # Account name
        self.account_title = QLabel(f"Account: {self.account_name}")
        self.account_title.setStyleSheet("""
            color: #333;
            font-size: 18px;
            font-weight: 600;
            text-align: center;
            background: transparent;
            border: none;
            margin: 10px 0px;
        """)
        self.account_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(self.account_title)
        
        # Date range
        if self.from_date and self.to_date:
            date_range = f"Period: {self.from_date.toString('MMMM d, yyyy')} to {self.to_date.toString('MMMM d, yyyy')}"
        else:
            date_range = "Period: All Time"
            
        self.date_label = QLabel(date_range)
        self.date_label.setStyleSheet("""
            color: #666;
            font-size: 14px;
            text-align: center;
            background: transparent;
            border: none;
        """)
        self.date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(self.date_label)
        
        layout.addLayout(header_layout)
        
        # Navigation bar
        nav_layout = QHBoxLayout()
        
        back_btn = QPushButton("← Back to Account Overview")
        back_btn.setStyleSheet("""
            QPushButton {
                background: #1976D2;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 600;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #1565C0;
            }
            QPushButton:pressed {
                background: #0D47A1;
            }
        """)
        back_btn.clicked.connect(self.backToOverview.emit)
        nav_layout.addWidget(back_btn)
        
        nav_layout.addStretch()
        
        # Print button
        print_btn = QPushButton("🖨 Print Ledger")
        print_btn.setStyleSheet("""
            QPushButton {
                background: #4CAF50;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 600;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #45A049;
            }
            QPushButton:pressed {
                background: #388E3C;
            }
        """)
        print_btn.clicked.connect(self._print_ledger)
        nav_layout.addWidget(print_btn)
        
        layout.addLayout(nav_layout)
        
        # Account summary section
        summary_frame = QFrame()
        summary_frame.setStyleSheet("""
            QFrame {
                background: #F5F5F5;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                margin: 10px 0px;
            }
        """)
        summary_layout = QHBoxLayout(summary_frame)
        summary_layout.setContentsMargins(20, 15, 20, 15)
        
        self.opening_balance_label = QLabel("Opening Balance: $0.00")
        self.opening_balance_label.setStyleSheet("color: #333; font-weight: 600; font-size: 14px; background: transparent; border: none;")
        summary_layout.addWidget(self.opening_balance_label)
        
        summary_layout.addStretch()
        
        self.total_debits_label = QLabel("Total Debits: $0.00")
        self.total_debits_label.setStyleSheet("color: #333; font-weight: 600; font-size: 14px; background: transparent; border: none;")
        summary_layout.addWidget(self.total_debits_label)
        
        summary_layout.addStretch()
        
        self.total_credits_label = QLabel("Total Credits: $0.00")
        self.total_credits_label.setStyleSheet("color: #333; font-weight: 600; font-size: 14px; background: transparent; border: none;")
        summary_layout.addWidget(self.total_credits_label)
        
        summary_layout.addStretch()
        
        self.closing_balance_label = QLabel("Closing Balance: $0.00")
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
                border-radius: 4px 4px 0px 0px;
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
          # Scrollable transaction area with modern scrollbar
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        # Apply modern scrollbar styling
        scroll_style = """
            QScrollArea {
                border: 1px solid #E0E0E0;
                background: white;
            }
        """ + ModernScrollbarStyles.get_vertical_scrollbar_style()
        scroll.setStyleSheet(scroll_style)
        
        self.transactions_widget = QWidget()
        self.transactions_layout = QVBoxLayout(self.transactions_widget)
        self.transactions_layout.setContentsMargins(0, 0, 0, 0)
        self.transactions_layout.setSpacing(0)
        
        scroll.setWidget(self.transactions_widget)
        table_layout.addWidget(scroll)
        
        layout.addWidget(self.table_widget)
        
        # Footer
        footer_layout = QHBoxLayout()
        footer_layout.addStretch()
        
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
            for i in reversed(range(self.transactions_layout.count())):
                child = self.transactions_layout.itemAt(i).widget()
                if child:
                    child.setParent(None)
            
            if not account_entries:
                no_data = QLabel("No transactions found for this account in the selected period.")
                no_data.setStyleSheet("""
                    color: #666;
                    font-size: 16px;
                    text-align: center;
                    padding: 40px;                    background: transparent;
                    border: none;
                """)
                no_data.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.transactions_layout.addWidget(no_data)
            else:
                for i, entry in enumerate(account_entries):
                    date, description, debit_account, credit_account, amount = entry
                    
                    # Handle account name matching (accounts stored as "code - name" format)
                    def account_matches(stored_account, target_account):
                        if stored_account == target_account:
                            return True
                        # Check if it's in "code - name" format and matches
                        if ' - ' in stored_account and stored_account.endswith(target_account):
                            return True
                        if ' - ' in stored_account and target_account in stored_account:
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
                    
                    # Create transaction row
                    row_frame = QFrame()
                    row_color = "#FAFAFA" if i % 2 == 0 else "white"
                    row_frame.setStyleSheet(f"""
                        QFrame {{
                            background: {row_color};
                            border: none;
                            border-bottom: 1px solid #F0F0F0;
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
                    
                    self.transactions_layout.addWidget(row_frame)
            
            # Update summary
            self.opening_balance_label.setText("Opening Balance: $0.00")  # Would need historical data
            self.total_debits_label.setText(f"Total Debits: {format_currency(total_debits)}")
            self.total_credits_label.setText(f"Total Credits: {format_currency(total_credits)}")
            self.closing_balance_label.setText(f"Closing Balance: {format_currency(abs(running_balance))}")
            
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
            from PyQt6.QtWidgets import QMessageBox
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
            from PyQt6.QtWidgets import QMessageBox
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
                    font-family: 'Segoe UI', Arial, sans-serif;
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
        date_label = QLabel(str(self.entry_data[1]))
        date_label.setStyleSheet("color: #90CAF9; font-weight: 500; font-size: 12px; background: transparent; border: none;")
        date_label.setFixedWidth(80)
        layout.addWidget(date_label)
        
        # Description
        desc_label = QLabel(str(self.entry_data[2]))
        desc_label.setStyleSheet("color: white; font-weight: 500; font-size: 12px; background: transparent; border: none;")
        desc_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout.addWidget(desc_label)
        
        # Other account
        debit_account = self.entry_data[3]
        credit_account = self.entry_data[4]
        other_account = credit_account if self.account_name == debit_account else debit_account
        
        other_label = QLabel(other_account)
        other_label.setStyleSheet("color: #FFAB91; font-size: 11px; background: transparent; border: none;")
        other_label.setFixedWidth(120)
        layout.addWidget(other_label)
        
        # Amount (debit/credit indication)
        amount = float(self.entry_data[5])
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
        self._setup_ui()
        self._apply_styling()
        self._load_accounts()
        
    def _apply_styling(self):
        """Apply modern glassmorphism styling to the ledger page."""
        GlassmorphismHelper.apply_main_container_effect(self)
        self.setStyleSheet(ModernStyles.get_complete_stylesheet())
        
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
        layout.setContentsMargins(responsive_margin, responsive_margin, 
                                 responsive_margin, responsive_margin)
        layout.setSpacing(ResponsiveHelper.scale_size(32, 24, 48))
        
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
        
        # Refresh button
        refresh_btn = QPushButton("Refresh Balances")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(0, 0, 0, 0.3);
                border-radius: 8px;
                padding: 8px 16px;
                color: white;
                font-size: 12px;
                font-weight: 500;
                min-height: 32px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.12);
                border: 1px solid rgba(100, 181, 246, 0.3);
            }
            QPushButton:pressed {
                background: rgba(100, 181, 246, 0.15);
                border: 1px solid rgba(100, 181, 246, 0.5);
                color: #90CAF9;
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
            accounts = self.system.get_all_accounts()
            self.all_accounts = accounts
            self._display_accounts(accounts)
            self._refresh_balances()
        except Exception as e:
            print(f"Error loading accounts: {e}")
            
    def _display_accounts(self, accounts):
        """Display account cards in a grid."""
        # Clear existing cards
        for card in self.account_cards:
            card.setParent(None)
        self.account_cards.clear()          # Create new cards
        row, col = 0, 0
        max_cols = 3
        
        for account in accounts:
            # account is (name, type, code, parent_code, level, is_postable, description)
            account_data = account[:4]  # (name, type, code, parent_code)
            account_level = account[4]  # level
            
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
            # account is (name, type, code, parent_code, level, is_postable, description)
            name, acc_type, code, parent_code = account[:4]
            
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
        """Refresh account balances for the selected date range."""
        from_date, to_date = self.date_selector.get_date_range()
        
        try:
            # Get transactions for the date range
            from_date_str = from_date.toString("yyyy-MM-dd")
            to_date_str = to_date.toString("yyyy-MM-dd")
            entries = self.system.get_journal_entries_by_date_range(from_date_str, to_date_str)
            
            # Calculate balances for each account
            account_balances = {}
            account_counts = {}
            
            # Helper function to match account names (handles "code - name" format)
            def find_matching_account_name(stored_account, account_name):
                """Check if the stored account matches the account name."""
                if stored_account == account_name:
                    return True
                # Check if it's in "code - name" format
                if ' - ' in stored_account and stored_account.endswith(account_name):
                    return True
                if ' - ' in stored_account and account_name in stored_account:
                    return True
                return False
            
            for entry in entries:
                if len(entry) >= 6:
                    debit_account = entry[3]
                    credit_account = entry[4]
                    amount = float(entry[5])
                    
                    # Process each account in our cards
                    for card in self.account_cards:
                        account_name = card.account_data[0]
                        
                        # Check if this entry affects this account
                        is_debit_match = find_matching_account_name(debit_account, account_name)
                        is_credit_match = find_matching_account_name(credit_account, account_name)
                        
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
            
            # Update card balances
            for card in self.account_cards:
                account_name = card.account_data[0]
                balance = account_balances.get(account_name, 0.0)
                count = account_counts.get(account_name, 0)
                card.update_balance(balance, count)
                
        except Exception as e:
            print(f"Error refreshing balances: {e}")
