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
from .styles import ModernStyles
from .widgets import PageHeader, DateRangeSelector
from ..common import ResponsiveHelper
from .scrollbar_styles import ModernScrollbarStyles


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
        self.disable_date_selector = False  # Allow subclasses to disable date selector
        # Get font family from ModernStyles
        self.font_family = ModernStyles.get_font_family()
        self._setup_ui()
    
    def get_html_font_family(self):
        """Get the font family string for HTML templates."""
        # Extract just the font name from font-family string for HTML use
        clean_font = self.font_family.replace("'", "").replace('"', '').split(',')[0]
        return f"{clean_font}, Arial, sans-serif"
    
    def _setup_ui(self):
        """Setup the professional document-style UI with modern components."""
        # Base styling for the entire view
        self.setStyleSheet(f"""
            QWidget {{
                background: white;
                color: #1A1A1A;
                font-family: {self.font_family};
            }}
            QPushButton {{
                font-family: {self.font_family};
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
        """)
        
        # Main layout
        layout = QVBoxLayout(self)
        responsive_margin = ResponsiveHelper.scale_size(32, 24, 48)
        layout.setContentsMargins(responsive_margin, 0, responsive_margin, responsive_margin)
        layout.setSpacing(16)
        
        # Page header (following standard pattern)
        self.page_header = PageHeader(self.statement_title, self.statement_subtitle)
        layout.addWidget(self.page_header)
        
        # Date range selector (following standard pattern)
        self.date_selector = DateRangeSelector()
        self.date_selector.dateRangeChanged.connect(self._on_date_range_changed)
        # For Trial Balance and Balance Sheet, always set selector to "All Time" by default
        if getattr(self, "set_date_selector_all_time_by_default", False):
            if hasattr(self.date_selector, "quick_buttons"):
                btn = self.date_selector.quick_buttons.button(4)
                if btn:
                    btn.setChecked(True)
                    self.date_selector._quick_filter_selected()
        layout.addWidget(self.date_selector)
        
        # If this view disables the date selector, do so now
        if getattr(self, "disable_date_selector", False):
            self.date_selector.setDisabled(True)
        
        # Navigation and action buttons bar
        self._setup_navigation_bar(layout)
        
        # Content scroll area with fixed width table
        self._setup_content_area(layout)
        
        # Footer with generation timestamp
        self._setup_footer(layout)
    
    # Removed _setup_header and all date_label logic as it's obsolete with DateRangeSelector and PageHeader.
    def _setup_navigation_bar(self, parent_layout):
        """Setup the navigation bar with back and print buttons."""
        nav_layout = QHBoxLayout()
        
        # Back button with matching ledger styling
        back_btn = QPushButton("◀ Reports")
        back_btn.setFixedSize(140, 36)  # Same size as ledger buttons
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
        back_btn.clicked.connect(self.backToReports.emit)
        nav_layout.addWidget(back_btn)
        
        nav_layout.addStretch()
        
        # Print button with matching ledger styling
        print_btn = QPushButton("Print Report")
        print_btn.setFixedSize(140, 36)  # Same size as ledger buttons
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
        print_btn.clicked.connect(self._print_statement)
        nav_layout.addWidget(print_btn)
        
        parent_layout.addLayout(nav_layout)
    
    def _setup_content_area(self, parent_layout):
        """Setup the content area to fill entire available space like ledger detailed view."""
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        # Remove border and styling to let table fill entire area
        content_scroll_style = """
            QScrollArea {
                border: none;
                background: transparent;
                padding: 0px;
                margin: 0px;
            }
        """ + ModernScrollbarStyles.get_vertical_scrollbar_style()
        scroll_area.setStyleSheet(content_scroll_style)
        
        # Content widget - no margins or padding to fill entire space
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setSpacing(0)  # No spacing between elements
        self.content_layout.setContentsMargins(0, 0, 0, 0)  # No margins to fill entire area
        
        # Set size policy to expand and fill all available space
        self.content_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        scroll_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        scroll_area.setWidget(self.content_widget)
        parent_layout.addWidget(scroll_area)  # Add without any constraints
    
    def _setup_footer(self, parent_layout):
        """Setup the footer section with generation timestamp."""
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
        parent_layout.addLayout(footer_layout)
    
    def _create_statement_table(self, headers):
        """Create a professional statement table exactly matching ledger detailed view structure."""
        # Container widget - exactly matching ledger's _create_transactions_area
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        
        # Set size policy to expand and fill all available space
        container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Table header (stays fixed) - exactly matching ledger
        header = QWidget()
        header.setStyleSheet("""
            background: #1976D2;
            border-radius: 0px;
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(15, 12, 15, 12)
        header_layout.setSpacing(0)
        
        # Create header labels exactly matching ledger style
        for text, width in headers:
            label = QLabel(text)
            label.setStyleSheet("""
                color: white;
                font-weight: 700;
                font-size: 13px;
                background: transparent;
            """)
            if text in ["Amount", "Balance", "Total"] or "$" in text:
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            # Remove fixed width to allow expansion
            if width > 0:
                label.setMinimumWidth(width)
            header_layout.addWidget(label)
            
        container_layout.addWidget(header)
        
        # Scrollable content area - exactly matching ledger
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Set size policy to expand
        scroll.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Use exact same scroll style as ledger - no border, just scrollbar styles
        from ..components.scrollbar_styles import ModernScrollbarStyles
        scroll.setStyleSheet(ModernScrollbarStyles.get_vertical_scrollbar_style())
        
        # Container for table rows - exactly matching ledger's transactions_widget
        content = QWidget()
        content.setObjectName("tableContent")
        content.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.table_content_layout = QVBoxLayout(content)
        self.table_content_layout.setContentsMargins(0, 0, 0, 0)
        self.table_content_layout.setSpacing(0)
        self.table_content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        scroll.setWidget(content)
        container_layout.addWidget(scroll, 1)  # Give scroll area stretch factor like ledger
        
        return container
    
    def _create_table_header(self, headers):
        """This method is no longer used - header creation is now in _create_statement_table."""
        pass
    
    def _add_table_row(self, items, is_total=False, is_subtotal=False, indent_level=0):
        """Add a row to the statement table exactly matching ledger detailed view styling."""
        # Create row frame with fixed height like ledger
        row = QFrame()
        row.setFixedHeight(40)  # Same fixed height as ledger
        
        # Get row index for alternating colors
        row_index = self.table_content_layout.count()
        row_color = "#FAFAFA" if row_index % 2 == 0 else "white"
        
        # Apply styling exactly matching ledger detailed view
        if is_total:
            row.setStyleSheet(f"""
                QFrame {{
                    background: #F8F9FA;
                    border-top: 2px solid #1976D2;
                    border-bottom: 1px solid #E0E0E0;
                    border-radius: 0px;
                    padding: 0px;
                    margin: 0px;
                }}
                QLabel {{
                    color: #1976D2;
                    font-weight: 700;
                    font-size: 14px;
                    background: transparent;
                    border: none;
                }}
            """)
        elif is_subtotal:
            row.setStyleSheet(f"""
                QFrame {{
                    background: #FAFAFA;
                    border-top: 1px solid #BDBDBD;
                    border-bottom: 1px solid #E0E0E0;
                    border-radius: 0px;
                    padding: 0px;
                    margin: 0px;
                }}
                QLabel {{
                    color: #333;
                    font-weight: 600;
                    font-size: 13px;
                    background: transparent;
                    border: none;
                }}
            """)
        else:
            # Regular row - exactly matching ledger style
            row.setStyleSheet(f"""
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
        
        # Create row layout exactly matching ledger
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(15 + indent_level * 20, 10, 15, 10)  # Same margins as ledger
        row_layout.setSpacing(0)
        
        # Add items with same styling as ledger
        for i, (text, width) in enumerate(items):
            label = QLabel(str(text))
            
            # Apply same label styling as ledger
            if is_total:
                # Total row labels already styled by QFrame stylesheet
                pass
            elif is_subtotal:
                # Subtotal row labels already styled by QFrame stylesheet
                pass
            else:
                # Regular row labels - matching ledger font and color
                label.setStyleSheet("color: #333; font-size: 12px; background: transparent; border: none;")
                if i > 0:  # Amount columns get font-weight: 600 like ledger
                    label.setStyleSheet("color: #333; font-size: 12px; font-weight: 600; background: transparent; border: none;")
            
            # Set alignment exactly matching ledger
            if text in ["Amount", "Balance", "Total"] or "$" in str(text) or (i > 0 and not is_total):
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            else:
                label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            
            # Remove fixed width to allow expansion, but set minimum width for proportion
            if width > 0:
                label.setMinimumWidth(width - (indent_level * 20 if i == 0 else 0))
            
            # Set stretch factor for first column to take remaining space
            if i == 0:
                row_layout.addWidget(label, 1)  # Give stretch factor to first column
            else:
                row_layout.addWidget(label)
        
        # Add row to table
        self.table_content_layout.addWidget(row)
        
    def clear_content(self):
        """Clear the content layout."""
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
    # Removed update_date_range and all date_label logic as it's obsolete with DateRangeSelector and PageHeader.
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
        """Generate HTML content for printing."""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{self.statement_title}</title>
            <style>
                body {{ font-family: {self.get_html_font_family()}; margin: 20px; }}
                h1 {{ color: #1976D2; text-align: center; }}
                h2 {{ color: #333; text-align: center; }}
                .date {{ text-align: center; color: #666; margin-bottom: 30px; }}
                table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
                th, td {{ text-align: left; padding: 8px; }}
                tr:nth-child(even) {{ background-color: #f2f2f2; }}
                th {{ background-color: #1976D2; color: white; }}
                .total {{ font-weight: bold; }}
                .footer {{ margin-top: 30px; border-top: 1px solid #ddd; padding-top: 10px; }}
                .footer p {{ color: #666; font-size: 0.8em; text-align: center; }}
            </style>
        </head>
        <body>
            <h1>{self.statement_title}</h1>
            {f"<h2>{self.statement_subtitle}</h2>" if self.statement_subtitle else ""}
            <div class="date">
                {f"Period: {self.from_date.strftime('%B %d, %Y')} to {self.to_date.strftime('%B %d, %Y')}" if self.from_date and self.to_date else ""}
                <br>
                {f"Generated on: {datetime.now().strftime('%B %d, %Y %H:%M')}" }
            </div>
            
            <!-- Content will be customized by subclasses -->
            {self._generate_specific_html_content()}
            
            <div class="footer">
                <p>This report was generated by the Modern Accounting System.</p>
            </div>
        </body>
        </html>
        """

    def _on_date_range_changed(self, from_date, to_date):
        """Handle date range changes from the DateRangeSelector."""
        self.from_date = from_date
        self.to_date = to_date
        
        # Regenerate the report with new date range if system is available
        if hasattr(self, 'system') and self.system:
            # This will be overridden by subclasses to call their specific show method
            self._regenerate_with_new_dates()
    
    def _regenerate_with_new_dates(self):
        """Regenerate the report with current date range. Override in subclasses."""
        pass
    
    def refresh_currency_display(self):
        """Refresh all currency displays when currency symbol changes."""
        try:
            # Re-generate the current statement with updated currency formatting
            self._regenerate_with_new_dates()
        except Exception as e:
            print(f"Error refreshing currency display: {e}")

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


class IncomeStatementView(BaseFinancialStatementView):
    """Income Statement detailed view with professional table layout."""
    
    def __init__(self, parent=None):
        super().__init__("Income Statement", "For the Period Ended")
        
    def show_income_statement(self, system, from_date=None, to_date=None):
        """Display the income statement data in professional table format."""
        self.clear_content()
        self.system = system
        self.from_date = from_date
        self.to_date = to_date
        
        # Optionally update the subtitle with the period
        if from_date and to_date:
            self.page_header.update_subtitle(f"For the Period: {from_date} to {to_date}")
        elif to_date:
            self.page_header.update_subtitle(f"As of: {to_date}")
        else:
            self.page_header.update_subtitle("All Time")
        
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
    
    def _regenerate_with_new_dates(self):
        """Regenerate the income statement with current date range."""
        if self.system:
            # Convert QDate to string if needed
            from_date_str = self.from_date.toString("yyyy-MM-dd") if self.from_date else None
            to_date_str = self.to_date.toString("yyyy-MM-dd") if self.to_date else None
            self.show_income_statement(self.system, from_date_str, to_date_str)
        
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
                body {{ font-family: {self.get_html_font_family()}; margin: 20px; }}
                h1 {{ color: #1976D2; text-align: center; margin-bottom: 5px; }}
                h2 {{ color: #333; text-align: center; margin-top: 0; }}
                .date {{ text-align: center; color: #666; margin-bottom: 30px; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th {{ background: #1976D2; color: white; padding: 12px; }}
                .section-header {{ background: #f5f5f5; font-weight: bold; padding: 10px; }}
                .account {{ padding: 8px 20px; border-bottom: 1px solid #eee; }}
                .total {{ font-weight: bold; background: #f0f8ff; }}
                .amount {{ text-align: right; }}
            </style>
        </head>
        <body>
            <h1>INCOME STATEMENT</h1>
            <h2>For the Period Ended</h2>
            <div class="date">{self._get_date_range_text()}</div>
            
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


class TrialBalanceView(BaseFinancialStatementView):
    """Trial Balance detailed view with professional table layout."""

    def __init__(self, parent=None):
        super().__init__("Trial Balance", "All Accounts")
        self.set_date_selector_all_time_by_default = True  # Always set selector to "All Time" by default

class BalanceSheetView(BaseFinancialStatementView):
    """Balance Sheet detailed view with professional table layout."""
    
    def __init__(self, parent=None):
        super().__init__("Balance Sheet", "Statement of Financial Position")
        self.set_date_selector_all_time_by_default = True  # Always set selector to "All Time" by default
        
    def show_balance_sheet(self, system, as_of_date=None):
        """Display the balance sheet data in professional table format."""
        self.clear_content()
        self.system = system
        self.from_date = None
        self.to_date = as_of_date
        
        # Optionally update the subtitle with the period
        if as_of_date:
            self.page_header.update_subtitle(f"As of: {as_of_date}")
        else:
            self.page_header.update_subtitle("All Time")
        
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
    
    def _regenerate_with_new_dates(self):
        """Regenerate the balance sheet with current date range."""
        if self.system:
            # For balance sheet, we only use the "to_date" (as of date)
            as_of_date_str = self.to_date.toString("yyyy-MM-dd") if self.to_date else None
            self.show_balance_sheet(self.system, as_of_date_str)
        
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
                body {{ font-family: {self.get_html_font_family()}; margin: 20px; }}
                h1 {{ color: #1976D2; text-align: center; margin-bottom: 5px; }}
                h2 {{ color: #333; text-align: center; margin-top: 0; }}
                .date {{ text-align: center; color: #666; margin-bottom: 30px; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th {{ background: #1976D2; color: white; padding: 12px; }}
                .section-header {{ background: #f5f5f5; font-weight: bold; padding: 10px; }}
                .account {{ padding: 8px 20px; border-bottom: 1px solid #eee; }}
                .total {{ font-weight: bold; background: #f0f8ff; }}
                .amount {{ text-align: right; }}
            </style>
        </head>
        <body>
            <h1>BALANCE SHEET</h1>
            <h2>Statement of Financial Position</h2>
            <div class="date">{self._get_date_range_text()}</div>
            
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
        self.from_date = from_date
        self.to_date = to_date
        
        # Optionally update the subtitle with the period
        if from_date and to_date:
            self.page_header.update_subtitle(f"For the Period: {from_date} to {to_date}")
        elif to_date:
            self.page_header.update_subtitle(f"As of: {to_date}")
        else:
            self.page_header.update_subtitle("All Time")
        
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
    
    def _regenerate_with_new_dates(self):
        """Regenerate the cash flow statement with current date range."""
        if self.system:
            from_date_str = self.from_date.toString("yyyy-MM-dd") if self.from_date else None
            to_date_str = self.to_date.toString("yyyy-MM-dd") if self.to_date else None
            self.show_cash_flow_statement(self.system, from_date_str, to_date_str)
        
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
                body {{ font-family: {self.get_html_font_family()}; margin: 20px; }}
                h1 {{ color: #1976D2; text-align: center; margin-bottom: 5px; }}
                h2 {{ color: #333; text-align: center; margin-top: 0; }}
                .date {{ text-align: center; color: #666; margin-bottom: 30px; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th {{ background: #1976D2; color: white; padding: 12px; }}
                .section-header {{ background: #f5f5f5; font-weight: bold; padding: 10px; }}
                .account {{ padding: 8px 20px; border-bottom: 1px solid #eee; }}
                .total {{ font-weight: bold; background: #f0f8ff; }}
                .amount {{ text-align: right; }}
            </style>
        </head>
        <body>
            <h1>CASH FLOW STATEMENT</h1>
            <h2>Statement of Cash Flows</h2>
            <div class="date">{self._get_date_range_text()}</div>
            
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
        self.from_date = from_date
        self.to_date = to_date
        
        # Optionally update the subtitle with the period
        if from_date and to_date:
            self.page_header.update_subtitle(f"For the Period: {from_date} to {to_date}")
        elif to_date:
            self.page_header.update_subtitle(f"As of: {to_date}")
        else:
            self.page_header.update_subtitle("All Time")
        
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
    
    def _regenerate_with_new_dates(self):
        """Regenerate the statement of equity with current date range."""
        if self.system:
            from_date_str = self.from_date.toString("yyyy-MM-dd") if self.from_date else None
            to_date_str = self.to_date.toString("yyyy-MM-dd") if self.to_date else None
            self.show_statement_of_equity(self.system, from_date_str, to_date_str)
        
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
                body {{ font-family: {self.get_html_font_family()}; margin: 20px; }}
                h1 {{ color: #1976D2; text-align: center; margin-bottom: 5px; }}
                h2 {{ color: #333; text-align: center; margin-top: 0; }}
                .date {{ text-align: center; color: #666; margin-bottom: 30px; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th {{ background: #1976D2; color: white; padding: 12px; }}
                .section-header {{ background: #f5f5f5; font-weight: bold; padding: 10px; }}
                .account {{ padding: 8px 20px; border-bottom: 1px solid #eee; }}
                .total {{ font-weight: bold; background: #f0f8ff; }}
                .amount {{ text-align: right; }}
            </style>
        </head>
        <body>
            <h1>STATEMENT OF OWNER'S EQUITY</h1>
            <h2>Changes in Owner's Equity</h2>
            <div class="date">{self._get_date_range_text()}</div>
            
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
