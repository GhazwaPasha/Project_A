"""
Financial Statement Report Views
Professional document-style views for financial statements with print functionality
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFrame, QScrollArea, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from datetime import datetime
from ...core.utils import format_currency


class BaseFinancialStatementView(QWidget):
    """Base class for professional financial statement document views."""
    
    backToReports = pyqtSignal()
    
    def __init__(self, statement_title, statement_subtitle="", parent=None):
        super().__init__(parent)
        self.statement_title = statement_title
        self.statement_subtitle = statement_subtitle
        self.system = None
        self.from_date = None
        self.to_date = None
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup the professional document-style UI."""
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
        title = QLabel(self.statement_title.upper())
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
        
        # Subtitle
        if self.statement_subtitle:
            subtitle = QLabel(self.statement_subtitle)
            subtitle.setStyleSheet("""
                color: #333;
                font-size: 16px;
                font-weight: 500;
                text-align: center;
                background: transparent;
                border: none;
                margin: 5px 0px;
            """)
            subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
            header_layout.addWidget(subtitle)
        
        # Date range
        self.date_label = QLabel("Period: All Time")
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
        
        back_btn = QPushButton("← Back to Reports")
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
        back_btn.clicked.connect(self.backToReports.emit)
        nav_layout.addWidget(back_btn)
        
        nav_layout.addStretch()
        
        # Print button
        print_btn = QPushButton("🖨 Print Statement")
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
        print_btn.clicked.connect(self._print_statement)
        nav_layout.addWidget(print_btn)
        
        layout.addLayout(nav_layout)
        
        # Content scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: 1px solid #E0E0E0;
                background: white;
            }
            QScrollBar:vertical {
                background: #F5F5F5;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: #BDBDBD;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #9E9E9E;
            }
        """)
        
        # Content widget
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setSpacing(30)
        self.content_layout.setContentsMargins(20, 20, 20, 20)
        
        # Add some padding at the top
        top_spacer = QSpacerItem(0, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        self.content_layout.addItem(top_spacer)
        
        scroll_area.setWidget(self.content_widget)
        layout.addWidget(scroll_area)
        
        # Footer
        footer_layout = QHBoxLayout()
        footer_layout.addStretch()
        
        self.date_generated = QLabel(f"Generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}")
        self.date_generated.setStyleSheet("""
            color: #999;
            font-size: 11px;
            font-style: italic;
            background: transparent;
            border: none;
        """)
        footer_layout.addWidget(self.date_generated)
        layout.addLayout(footer_layout)
        
    def _create_statement_table(self, headers):
        """Create a professional statement table."""
        table_widget = QWidget()
        table_layout = QVBoxLayout(table_widget)
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
        
        for header_text, width in headers:
            header_label = QLabel(header_text.upper())
            header_label.setStyleSheet("""
                color: white;
                font-weight: 700;
                font-size: 13px;
                background: transparent;
                border: none;
                letter-spacing: 0.5px;
            """)
            if header_text == "Amount" or "$" in header_text or "Description" in header_text:
                header_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            else:
                header_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            header_label.setFixedWidth(int(width))
            header_layout.addWidget(header_label)
            
        table_layout.addWidget(header_frame)
        
        # Content area for rows
        self.table_content = QWidget()
        self.table_content_layout = QVBoxLayout(self.table_content)
        self.table_content_layout.setContentsMargins(0, 0, 0, 0)
        self.table_content_layout.setSpacing(0)
        
        # Add border frame
        content_frame = QFrame()
        content_frame.setStyleSheet("""
            QFrame {
                border: 1px solid #E0E0E0;
                border-top: none;
                background: white;
            }
        """)
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.addWidget(self.table_content)
        
        table_layout.addWidget(content_frame)
        
        return table_widget
        
    def _add_table_row(self, items, is_total=False, is_subtotal=False, indent_level=0):
        """Add a row to the statement table."""
        row_frame = QFrame()
        
        if is_total:
            row_frame.setStyleSheet("""
                QFrame {
                    background: #F8F9FA;
                    border-top: 2px solid #1976D2;
                    border-bottom: 1px solid #E0E0E0;
                }
            """)
        elif is_subtotal:
            row_frame.setStyleSheet("""
                QFrame {
                    background: #FAFAFA;
                    border-top: 1px solid #BDBDBD;
                    border-bottom: 1px solid #E0E0E0;
                }
            """)
        else:
            row_frame.setStyleSheet("""
                QFrame {
                    background: white;
                    border-bottom: 1px solid #F0F0F0;
                }
                QFrame:hover {
                    background: #F8F9FA;
                }
            """)
        
        row_layout = QHBoxLayout(row_frame)
        row_layout.setContentsMargins(15, 8, 15, 8)
        row_layout.setSpacing(0)
        
        # Add indentation for first column
        if indent_level > 0:
            spacer = QSpacerItem(indent_level * 20, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
            row_layout.addItem(spacer)
        
        for i, (text, width) in enumerate(items):
            label = QLabel(str(text))
            
            if is_total:
                label.setStyleSheet("""
                    color: #1976D2;
                    font-weight: 700;
                    font-size: 14px;
                    background: transparent;
                    border: none;
                """)
            elif is_subtotal:
                label.setStyleSheet("""
                    color: #333;
                    font-weight: 600;
                    font-size: 13px;
                    background: transparent;
                    border: none;
                """)
            else:
                label.setStyleSheet("""
                    color: #444;
                    font-weight: 400;
                    font-size: 13px;
                    background: transparent;
                    border: none;
                """)
            
            # Right-align amounts
            if i > 0 or "Amount" in str(text) or "$" in str(text):
                label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            else:
                label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            
            label.setFixedWidth(int(width))
            row_layout.addWidget(label)
            
        self.table_content_layout.addWidget(row_frame)
        return row_frame
        
    def clear_content(self):
        """Clear the content layout."""
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
    def update_date_range(self, from_date=None, to_date=None):
        """Update the date range display."""
        self.from_date = from_date
        self.to_date = to_date
        
        if from_date and to_date:
            date_range = f"Period: {from_date} to {to_date}"
        elif to_date:
            date_range = f"As of: {to_date}"
        else:
            date_range = "Period: All Time"
            
        self.date_label.setText(date_range)
        
    def _print_statement(self):
        """Print the financial statement using Windows native print function."""
        try:
            import tempfile
            import os
            import webbrowser
            
            # Create a temporary HTML file with the statement content
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
                html_content = self._generate_html_content()
                f.write(html_content)
                temp_file = f.name
            
            # Open the HTML file in the default browser for printing
            webbrowser.open('file://' + temp_file.replace('\\', '/'))
            
            # Show a message to the user
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(self, "Print", 
                f"The {self.statement_title} has been opened in your web browser.\n"
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
                "You can manually copy the statement content or take a screenshot to print.")
    
    def _generate_html_content(self):
        """Generate HTML content for printing - to be implemented by subclasses."""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{self.statement_title}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #1976D2; text-align: center; }}
                h2 {{ color: #333; text-align: center; }}
                .date {{ text-align: center; color: #666; margin-bottom: 30px; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th {{ background: #1976D2; color: white; padding: 10px; text-align: left; }}
                td {{ padding: 8px; border-bottom: 1px solid #ddd; }}
                .total {{ font-weight: bold; background: #f5f5f5; }}
                .amount {{ text-align: right; }}
            </style>
        </head>
        <body>
            <h1>{self.statement_title.upper()}</h1>
            <h2>{self.statement_subtitle}</h2>
            <div class="date">{self.date_label.text()}</div>
            <p>Content to be implemented by subclasses</p>            <div style="text-align: center; margin-top: 50px; color: #999; font-size: 11px;">
                {self.date_generated.text()}
            </div>
        </body>
        </html>
        """

    def refresh_currency_display(self):
        """Refresh currency display when currency symbol changes."""
        # For report views, we need to regenerate the content with the new currency
        # This is typically handled by re-calling the show_* method with the same parameters
        if hasattr(self, 'system') and self.system:
            # This is a placeholder - each subclass should override this method
            # to call its specific show method
            pass


class IncomeStatementView(BaseFinancialStatementView):
    """Income Statement detailed view with professional table layout."""
    
    def __init__(self, parent=None):
        super().__init__("Income Statement", "For the Period Ended")
        
    def show_income_statement(self, system, from_date=None, to_date=None):
        """Display the income statement data in professional table format."""
        self.clear_content()
        self.system = system
        self.update_date_range(from_date, to_date)
        
        # Get data from accounting system
        try:
            data = system.generate_income_statement_breakdown(from_date, to_date)
        except Exception as e:
            print(f"Error generating income statement: {e}")
            return
        
        # Create main table
        headers = [("Account", 400), ("Amount", 200)]
        table = self._create_statement_table(headers)
          # Revenue section
        if data.get('revenues'):
            self._add_table_row([("REVENUE", 400), ("", 200)], is_subtotal=True)
            for account, amount in data.get('revenues', []):
                self._add_table_row([(account, 400), (format_currency(amount), 200)], indent_level=1)
            self._add_table_row([("Total Revenue", 400), (format_currency(data.get('total_revenue', 0)), 200)], is_total=True)
            
        # Cost of Goods Sold
        if data.get('cogs'):
            self._add_table_row([("COST OF GOODS SOLD", 400), ("", 200)], is_subtotal=True)
            for account, amount in data.get('cogs', []):
                self._add_table_row([(account, 400), (format_currency(amount), 200)], indent_level=1)
            self._add_table_row([("Total Cost of Goods Sold", 400), (format_currency(data.get('total_cogs', 0)), 200)], is_total=True)
            
        # Gross Profit
        self._add_table_row([("Gross Profit", 400), (format_currency(data.get('gross_profit', 0)), 200)], is_total=True)
        
        # Operating Expenses
        if data.get('expenses'):
            self._add_table_row([("OPERATING EXPENSES", 400), ("", 200)], is_subtotal=True)
            for account, amount in data.get('expenses', []):
                self._add_table_row([(account, 400), (format_currency(amount), 200)], indent_level=1)
            self._add_table_row([("Total Operating Expenses", 400), (format_currency(data.get('total_expenses', 0)), 200)], is_total=True)
            
        # Net Income
        self._add_table_row([("NET INCOME", 400), (format_currency(data.get('net_income', 0)), 200)], is_total=True)
        
        self.content_layout.addWidget(table)
        
    def _generate_html_content(self):
        """Generate HTML content for Income Statement printing."""
        if not self.system:
            return super()._generate_html_content()
            
        try:
            data = self.system.generate_income_statement_breakdown(self.from_date, self.to_date)
        except:
            return super()._generate_html_content()
            
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Income Statement</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #1976D2; text-align: center; margin-bottom: 5px; }}
                h2 {{ color: #333; text-align: center; margin-top: 0; }}
                .date {{ text-align: center; color: #666; margin-bottom: 30px; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th {{ background: #1976D2; color: white; padding: 12px; }}
                .section-header {{ background: #f5f5f5; font-weight: bold; padding: 10px; }}
                .account {{ padding: 8px 20px; border-bottom: 1px solid #eee; }}
                .total {{ font-weight: bold; background: #f0f8ff; padding: 10px; border-top: 2px solid #1976D2; }}
                .amount {{ text-align: right; }}
            </style>
        </head>
        <body>
            <h1>INCOME STATEMENT</h1>
            <h2>For the Period Ended</h2>
            <div class="date">{self.date_label.text()}</div>
            
            <table>
                <thead>
                    <tr><th>Account</th><th class="amount">Amount</th></tr>
                </thead>
                <tbody>
        """
        
        # Revenue section
        if data.get('revenues'):
            html += '<tr class="section-header"><td>REVENUE</td><td></td></tr>'
            for account, amount in data.get('revenues', []):
                html += f'<tr class="account"><td>{account}</td><td class="amount">{format_currency(amount)}</td></tr>'
            html += f'<tr class="total"><td>Total Revenue</td><td class="amount">{format_currency(data.get("total_revenue", 0))}</td></tr>'
            
        # COGS section
        if data.get('cogs'):
            html += '<tr class="section-header"><td>COST OF GOODS SOLD</td><td></td></tr>'
            for account, amount in data.get('cogs', []):
                html += f'<tr class="account"><td>{account}</td><td class="amount">{format_currency(amount)}</td></tr>'
            html += f'<tr class="total"><td>Total Cost of Goods Sold</td><td class="amount">{format_currency(data.get("total_cogs", 0))}</td></tr>'
            
        # Gross Profit
        html += f'<tr class="total"><td>Gross Profit</td><td class="amount">{format_currency(data.get("gross_profit", 0))}</td></tr>'
        
        # Expenses section
        if data.get('expenses'):
            html += '<tr class="section-header"><td>OPERATING EXPENSES</td><td></td></tr>'
            for account, amount in data.get('expenses', []):
                html += f'<tr class="account"><td>{account}</td><td class="amount">{format_currency(amount)}</td></tr>'
            html += f'<tr class="total"><td>Total Operating Expenses</td><td class="amount">{format_currency(data.get("total_expenses", 0))}</td></tr>'
            
        # Net Income
        html += f'<tr class="total"><td>NET INCOME</td><td class="amount">{format_currency(data.get("net_income", 0))}</td></tr>'
        
        html += f"""
                </tbody>
            </table>
            
            <div style="text-align: center; margin-top: 50px; color: #999; font-size: 11px;">
                {self.date_generated.text()}
            </div>
        </body>
        </html>
        """
        
        return html


class BalanceSheetView(BaseFinancialStatementView):
    """Balance Sheet detailed view with professional table layout."""
    
    def __init__(self, parent=None):
        super().__init__("Balance Sheet", "Statement of Financial Position")
        
    def show_balance_sheet(self, system, as_of_date=None):
        """Display the balance sheet data in professional table format."""
        self.clear_content()
        self.system = system
        self.update_date_range(to_date=as_of_date)
        
        # Get data from accounting system
        try:
            data = system.generate_balance_sheet_breakdown(as_of_date)
        except Exception as e:
            print(f"Error generating balance sheet: {e}")
            return
        
        # Create main table
        headers = [("Account", 400), ("Amount", 200)]
        table = self._create_statement_table(headers)
          # Assets section
        if data.get('assets'):
            self._add_table_row([("ASSETS", 400), ("", 200)], is_subtotal=True)
            for account, amount in data.get('assets', []):
                if amount != 0:
                    self._add_table_row([(account, 400), (format_currency(amount), 200)], indent_level=1)
            self._add_table_row([("Total Assets", 400), (format_currency(data.get('total_assets', 0)), 200)], is_total=True)
            
        # Liabilities section
        if data.get('liabilities'):
            self._add_table_row([("LIABILITIES", 400), ("", 200)], is_subtotal=True)
            for account, amount in data.get('liabilities', []):
                if amount != 0:
                    self._add_table_row([(account, 400), (format_currency(amount), 200)], indent_level=1)
            self._add_table_row([("Total Liabilities", 400), (format_currency(data.get('total_liabilities', 0)), 200)], is_total=True)
            
        # Equity section
        if data.get('equity'):
            self._add_table_row([("EQUITY", 400), ("", 200)], is_subtotal=True)
            for account, amount in data.get('equity', []):
                if amount != 0:
                    self._add_table_row([(account, 400), (format_currency(amount), 200)], indent_level=1)
            self._add_table_row([("Total Equity", 400), (format_currency(data.get('total_equity', 0)), 200)], is_total=True)
            
        self.content_layout.addWidget(table)
        
    def _generate_html_content(self):
        """Generate HTML content for Balance Sheet printing."""
        if not self.system:
            return super()._generate_html_content()
            
        try:
            data = self.system.generate_balance_sheet_breakdown(self.to_date)
        except:
            return super()._generate_html_content()
            
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Balance Sheet</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #1976D2; text-align: center; margin-bottom: 5px; }}
                h2 {{ color: #333; text-align: center; margin-top: 0; }}
                .date {{ text-align: center; color: #666; margin-bottom: 30px; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th {{ background: #1976D2; color: white; padding: 12px; }}
                .section-header {{ background: #f5f5f5; font-weight: bold; padding: 10px; }}
                .account {{ padding: 8px 20px; border-bottom: 1px solid #eee; }}
                .total {{ font-weight: bold; background: #f0f8ff; padding: 10px; border-top: 2px solid #1976D2; }}
                .amount {{ text-align: right; }}
            </style>
        </head>
        <body>
            <h1>BALANCE SHEET</h1>
            <h2>Statement of Financial Position</h2>
            <div class="date">{self.date_label.text()}</div>
            
            <table>
                <thead>
                    <tr><th>Account</th><th class="amount">Amount</th></tr>
                </thead>
                <tbody>
        """
        
        # Assets section
        if data.get('assets'):
            html += '<tr class="section-header"><td>ASSETS</td><td></td></tr>'
            for account, amount in data.get('assets', []):
                if amount != 0:
                    html += f'<tr class="account"><td>{account}</td><td class="amount">{format_currency(amount)}</td></tr>'
            html += f'<tr class="total"><td>Total Assets</td><td class="amount">{format_currency(data.get("total_assets", 0))}</td></tr>'
            
        # Liabilities section
        if data.get('liabilities'):
            html += '<tr class="section-header"><td>LIABILITIES</td><td></td></tr>'
            for account, amount in data.get('liabilities', []):
                if amount != 0:
                    html += f'<tr class="account"><td>{account}</td><td class="amount">{format_currency(amount)}</td></tr>'
            html += f'<tr class="total"><td>Total Liabilities</td><td class="amount">{format_currency(data.get("total_liabilities", 0))}</td></tr>'
            
        # Equity section
        if data.get('equity'):
            html += '<tr class="section-header"><td>EQUITY</td><td></td></tr>'
            for account, amount in data.get('equity', []):
                if amount != 0:
                    html += f'<tr class="account"><td>{account}</td><td class="amount">{format_currency(amount)}</td></tr>'
            html += f'<tr class="total"><td>Total Equity</td><td class="amount">{format_currency(data.get("total_equity", 0))}</td></tr>'
            
        html += f"""
                </tbody>
            </table>
            
            <div style="text-align: center; margin-top: 50px; color: #999; font-size: 11px;">
                {self.date_generated.text()}
            </div>
        </body>
        </html>
        """
        
        return html


class CashFlowStatementView(BaseFinancialStatementView):
    """Cash Flow Statement detailed view with professional table layout."""
    
    def __init__(self, parent=None):
        super().__init__("Cash Flow Statement", "Statement of Cash Flows")
        
    def show_cash_flow_statement(self, system, from_date=None, to_date=None):
        """Display the cash flow statement data in professional table format."""
        self.clear_content()
        self.system = system
        self.update_date_range(from_date, to_date)
        
        # Get data from accounting system
        try:
            data = system.generate_cash_flow_breakdown(from_date, to_date)
        except Exception as e:
            print(f"Error generating cash flow statement: {e}")
            return
        
        # Create main table
        headers = [("Description", 400), ("Amount", 200)]
        table = self._create_statement_table(headers)
          # Operating Activities
        if data.get('operating activities'):
            self._add_table_row([("CASH FLOWS FROM OPERATING ACTIVITIES", 400), ("", 200)], is_subtotal=True)
            for description, amount in data.get('operating activities', []):
                self._add_table_row([(description.title(), 400), (format_currency(amount), 200)], indent_level=1)
            self._add_table_row([("Net Cash from Operating Activities", 400), (format_currency(data.get('net_operating', 0)), 200)], is_total=True)
            
        # Investing Activities
        if data.get('investing activities'):
            self._add_table_row([("CASH FLOWS FROM INVESTING ACTIVITIES", 400), ("", 200)], is_subtotal=True)
            for description, amount in data.get('investing activities', []):
                self._add_table_row([(description.title(), 400), (format_currency(amount), 200)], indent_level=1)
            self._add_table_row([("Net Cash from Investing Activities", 400), (format_currency(data.get('net_investing', 0)), 200)], is_total=True)
            
        # Financing Activities
        if data.get('financing activities'):
            self._add_table_row([("CASH FLOWS FROM FINANCING ACTIVITIES", 400), ("", 200)], is_subtotal=True)
            for description, amount in data.get('financing activities', []):
                self._add_table_row([(description.title(), 400), (format_currency(amount), 200)], indent_level=1)
            self._add_table_row([("Net Cash from Financing Activities", 400), (format_currency(data.get('net_financing', 0)), 200)], is_total=True)
            
        # Net Change in Cash
        self._add_table_row([("NET CHANGE IN CASH", 400), (format_currency(data.get('net_cash_flow', 0)), 200)], is_total=True)
        
        self.content_layout.addWidget(table)
        
    def _generate_html_content(self):
        """Generate HTML content for Cash Flow Statement printing."""
        if not self.system:
            return super()._generate_html_content()
            
        try:
            data = self.system.generate_cash_flow_breakdown(self.from_date, self.to_date)
        except:
            return super()._generate_html_content()
            
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Cash Flow Statement</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #1976D2; text-align: center; margin-bottom: 5px; }}
                h2 {{ color: #333; text-align: center; margin-top: 0; }}
                .date {{ text-align: center; color: #666; margin-bottom: 30px; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th {{ background: #1976D2; color: white; padding: 12px; }}
                .section-header {{ background: #f5f5f5; font-weight: bold; padding: 10px; }}
                .account {{ padding: 8px 20px; border-bottom: 1px solid #eee; }}
                .total {{ font-weight: bold; background: #f0f8ff; padding: 10px; border-top: 2px solid #1976D2; }}
                .amount {{ text-align: right; }}
            </style>
        </head>
        <body>
            <h1>CASH FLOW STATEMENT</h1>
            <h2>Statement of Cash Flows</h2>
            <div class="date">{self.date_label.text()}</div>
            
            <table>
                <thead>
                    <tr><th>Description</th><th class="amount">Amount</th></tr>
                </thead>
                <tbody>
        """
        
        # Operating Activities
        if data.get('operating activities'):
            html += '<tr class="section-header"><td>CASH FLOWS FROM OPERATING ACTIVITIES</td><td></td></tr>'
            for description, amount in data.get('operating activities', []):
                html += f'<tr class="account"><td>{description.title()}</td><td class="amount">{format_currency(amount)}</td></tr>'
            html += f'<tr class="total"><td>Net Cash from Operating Activities</td><td class="amount">{format_currency(data.get("net_operating", 0))}</td></tr>'
            
        # Investing Activities
        if data.get('investing activities'):
            html += '<tr class="section-header"><td>CASH FLOWS FROM INVESTING ACTIVITIES</td><td></td></tr>'
            for description, amount in data.get('investing activities', []):
                html += f'<tr class="account"><td>{description.title()}</td><td class="amount">{format_currency(amount)}</td></tr>'
            html += f'<tr class="total"><td>Net Cash from Investing Activities</td><td class="amount">{format_currency(data.get("net_investing", 0))}</td></tr>'
            
        # Financing Activities
        if data.get('financing activities'):
            html += '<tr class="section-header"><td>CASH FLOWS FROM FINANCING ACTIVITIES</td><td></td></tr>'
            for description, amount in data.get('financing activities', []):
                html += f'<tr class="account"><td>{description.title()}</td><td class="amount">{format_currency(amount)}</td></tr>'
            html += f'<tr class="total"><td>Net Cash from Financing Activities</td><td class="amount">{format_currency(data.get("net_financing", 0))}</td></tr>'
            
        # Net Change
        html += f'<tr class="total"><td>NET CHANGE IN CASH</td><td class="amount">{format_currency(data.get("net_cash_flow", 0))}</td></tr>'
        
        html += f"""
                </tbody>
            </table>
            
            <div style="text-align: center; margin-top: 50px; color: #999; font-size: 11px;">
                {self.date_generated.text()}
            </div>
        </body>
        </html>
        """
        
        return html


class StatementOfEquityView(BaseFinancialStatementView):
    """Statement of Equity detailed view with professional table layout."""
    
    def __init__(self, parent=None):
        super().__init__("Statement of Owner's Equity", "Changes in Owner's Equity")
        
    def show_statement_of_equity(self, system, from_date=None, to_date=None):
        """Display the statement of equity data in professional table format."""
        self.clear_content()
        self.system = system
        self.update_date_range(from_date, to_date)
        
        # Get data from accounting system
        try:
            data = system.generate_statement_of_equity(from_date, to_date)
        except Exception as e:
            print(f"Error generating statement of equity: {e}")
            return
        
        # Create main table
        headers = [("Description", 400), ("Amount", 200)]
        table = self._create_statement_table(headers)
        
        # Beginning Equity
        self._add_table_row([("Owner's Equity - Beginning of Period", 400), (format_currency(data.get('beginning_equity', 0)), 200)], is_total=True)
          # Changes during period
        self._add_table_row([("CHANGES DURING PERIOD", 400), ("", 200)], is_subtotal=True)
        
        # Net Income
        self._add_table_row([("Net Income", 400), (format_currency(data.get('net_income', 0)), 200)], indent_level=1)
        
        # Owner Investments
        if data.get('owner_investments', 0) != 0:
            self._add_table_row([("Owner Investments", 400), (format_currency(data.get('owner_investments', 0)), 200)], indent_level=1)
            
        # Owner Withdrawals
        if data.get('owner_withdrawals', 0) != 0:
            self._add_table_row([("Owner Withdrawals", 400), (format_currency(data.get('owner_withdrawals', 0)), 200)], indent_level=1)
            
        # Total Changes
        self._add_table_row([("Total Changes", 400), (format_currency(data.get('total_changes', 0)), 200)], is_subtotal=True)
        
        # Ending Equity
        self._add_table_row([("Owner's Equity - End of Period", 400), (format_currency(data.get('ending_equity', 0)), 200)], is_total=True)
        
        self.content_layout.addWidget(table)
        
    def _generate_html_content(self):
        """Generate HTML content for Statement of Equity printing."""
        if not self.system:
            return super()._generate_html_content()
            
        try:
            data = self.system.generate_statement_of_equity(self.from_date, self.to_date)
        except:
            return super()._generate_html_content()
            
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Statement of Owner's Equity</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #1976D2; text-align: center; margin-bottom: 5px; }}
                h2 {{ color: #333; text-align: center; margin-top: 0; }}
                .date {{ text-align: center; color: #666; margin-bottom: 30px; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th {{ background: #1976D2; color: white; padding: 12px; }}
                .section-header {{ background: #f5f5f5; font-weight: bold; padding: 10px; }}
                .account {{ padding: 8px 20px; border-bottom: 1px solid #eee; }}
                .total {{ font-weight: bold; background: #f0f8ff; padding: 10px; border-top: 2px solid #1976D2; }}
                .amount {{ text-align: right; }}
            </style>
        </head>
        <body>
            <h1>STATEMENT OF OWNER'S EQUITY</h1>
            <h2>Changes in Owner's Equity</h2>
            <div class="date">{self.date_label.text()}</div>
            
            <table>
                <thead>
                    <tr><th>Description</th><th class="amount">Amount</th></tr>
                </thead>
                <tbody>
        """
        
        # Beginning Equity
        html += f'<tr class="total"><td>Owner\'s Equity - Beginning of Period</td><td class="amount">{format_currency(data.get("beginning_equity", 0))}</td></tr>'
        
        # Changes
        html += '<tr class="section-header"><td>CHANGES DURING PERIOD</td><td></td></tr>'
        html += f'<tr class="account"><td>Net Income</td><td class="amount">{format_currency(data.get("net_income", 0))}</td></tr>'
        
        if data.get('owner_investments', 0) != 0:
            html += f'<tr class="account"><td>Owner Investments</td><td class="amount">{format_currency(data.get("owner_investments", 0))}</td></tr>'
            
        if data.get('owner_withdrawals', 0) != 0:
            html += f'<tr class="account"><td>Owner Withdrawals</td><td class="amount">{format_currency(data.get("owner_withdrawals", 0))}</td></tr>'
            
        html += f'<tr class="total"><td>Total Changes</td><td class="amount">{format_currency(data.get("total_changes", 0))}</td></tr>'
        
        # Ending Equity
        html += f'<tr class="total"><td>Owner\'s Equity - End of Period</td><td class="amount">{format_currency(data.get("ending_equity", 0))}</td></tr>'
        
        html += f"""
                </tbody>
            </table>
            
            <div style="text-align: center; margin-top: 50px; color: #999; font-size: 11px;">
                {self.date_generated.text()}
            </div>
        </body>
        </html>
        """
        
        return html