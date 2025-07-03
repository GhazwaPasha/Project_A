"""
Financial Statement Report Views
Professional document-style views for financial statements with print functionality
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFrame, QScrollArea, QSpacerItem, QSizePolicy, QTabWidget
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from datetime import datetime
from ...core.utils import format_currency
from .styles import ModernStyles
from .widgets import PageHeader, DateRangeSelector, MetricCard
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
    
    def _add_table_row(self, items, is_total=False, is_subtotal=False, indent_level=0, status_color=None):
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
                if status_color and i == 3:  # Status column (4th column)
                    label.setStyleSheet(f"color: {status_color}; font-size: 12px; font-weight: 600; background: transparent; border: none;")
                else:
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
        
    def _add_hierarchical_accounts(self, accounts, indent_level=0):
        """Add hierarchical account nodes to the table."""
        for account in accounts:
            # Handle both old tuple format and new hierarchical format
            if isinstance(account, tuple):
                # Old format: (account_name, amount)
                account_name, amount = account
                self._add_table_row([(account_name, 400), (format_currency(amount), 200)], indent_level=indent_level)
            else:
                # New hierarchical format: account object
                account_name = account.get('name', '')
                balance = account.get('balance', 0.0)
                children = account.get('children', [])
                level = account.get('level', 3)
                
                # For hierarchical display:
                # - Parent accounts (level 1-2) should be shown as headers without amounts
                # - Leaf accounts (level 3) should show amounts
                if level < 3 and children:
                    # Parent account - show as header without amount
                    self._add_table_row([(account_name, 400), ("", 200)], indent_level=indent_level, is_subtotal=True)
                    # Add children recursively
                    self._add_hierarchical_accounts(children, indent_level + 1)
                else:
                    # Leaf account or account without children - show with amount
                    self._add_table_row([(account_name, 400), (format_currency(balance), 200)], indent_level=indent_level)
                    # If it has children, add them too (shouldn't happen for level 3, but just in case)
                    if children:
                        self._add_hierarchical_accounts(children, indent_level + 1)
    
    def _generate_hierarchical_html(self, accounts, indent_level=0):
        """Generate HTML for hierarchical account nodes."""
        html = ""
        for account in accounts:
            # Handle both old tuple format and new hierarchical format
            if isinstance(account, tuple):
                # Old format: (account_name, amount)
                account_name, amount = account
                indent_style = f"padding-left: {indent_level * 20}px;" if indent_level > 0 else ""
                html += f'<tr class="account"><td style="{indent_style}">{account_name}</td><td class="amount">{format_currency(amount)}</td></tr>'
            else:
                # New hierarchical format: account object
                account_name = account.get('name', '')
                balance = account.get('balance', 0.0)
                children = account.get('children', [])
                level = account.get('level', 3)
                
                # For hierarchical display:
                # - Parent accounts (level 1-2) should be shown as headers without amounts
                # - Leaf accounts (level 3) should show amounts
                indent_style = f"padding-left: {indent_level * 20}px;" if indent_level > 0 else ""
                
                if level < 3 and children:
                    # Parent account - show as header without amount
                    html += f'<tr class="section-header"><td style="{indent_style}">{account_name}</td><td></td></tr>'
                    # Add children recursively
                    html += self._generate_hierarchical_html(children, indent_level + 1)
                else:
                    # Leaf account or account without children - show with amount
                    html += f'<tr class="account"><td style="{indent_style}">{account_name}</td><td class="amount">{format_currency(balance)}</td></tr>'
                    # If it has children, add them too (shouldn't happen for level 3, but just in case)
                    if children:
                        html += self._generate_hierarchical_html(children, indent_level + 1)
        
        return html
    
    def _calculate_tree_total(self, tree):
        """Calculate total balance for a hierarchical tree.
        Only count leaf accounts (level 3) to avoid double-counting."""
        total = 0.0
        for node in tree:
            # If this is a leaf account (level 3) or has no children, count its balance
            if node.get('level', 3) == 3 or not node.get('children', []):
                total += node.get('balance', 0.0)
            else:
                # For parent accounts, only count children (avoid double-counting)
                total += self._calculate_tree_total(node.get('children', []))
        return total
        
    def clear_content(self):
        """Clear the content layout."""
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if child and child.widget() is not None:
                widget = child.widget()
                if widget:
                    widget.deleteLater()
        
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
            <div id="content-placeholder">Content will be generated by subclasses</div>
            
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
            print(f"Income statement data: {data}")
            print(f"Revenues: {data.get('revenues', [])}")
            print(f"COGS: {data.get('cogs', [])}")
            print(f"Expenses: {data.get('expenses', [])}")
        except Exception as e:
            print(f"Error generating income statement: {e}")
            return
        
        # Create main table
        headers = [("Account", 400), ("Amount", 200)]
        table = self._create_statement_table(headers)
          # Revenue section
        if data.get('revenues'):
            self._add_table_row([("REVENUE", 400), ("", 200)], is_subtotal=True)
            self._add_hierarchical_accounts(data.get('revenues', []), indent_level=1)
            self._add_table_row([("Total Revenue", 400), (format_currency(data.get('total_revenue', 0)), 200)], is_total=True)
        else:
            # Add placeholder if no revenue data
            self._add_table_row([("REVENUE", 400), ("", 200)], is_subtotal=True)
            self._add_table_row([("No revenue data available", 400), ("", 200)], indent_level=1)
            self._add_table_row([("Total Revenue", 400), (format_currency(0), 200)], is_total=True)
            
        # Cost of Goods Sold
        if data.get('cogs'):
            self._add_table_row([("COST OF GOODS SOLD", 400), ("", 200)], is_subtotal=True)
            self._add_hierarchical_accounts(data.get('cogs', []), indent_level=1)
            self._add_table_row([("Total Cost of Goods Sold", 400), (format_currency(data.get('total_cogs', 0)), 200)], is_total=True)
        else:
            # Add placeholder if no COGS data
            self._add_table_row([("COST OF GOODS SOLD", 400), ("", 200)], is_subtotal=True)
            self._add_table_row([("No COGS data available", 400), ("", 200)], indent_level=1)
            self._add_table_row([("Total Cost of Goods Sold", 400), (format_currency(0), 200)], is_total=True)
            
        # Gross Profit
        self._add_table_row([("Gross Profit", 400), (format_currency(data.get('gross_profit', 0)), 200)], is_total=True)
        
        # Operating Expenses
        if data.get('expenses'):
            self._add_table_row([("OPERATING EXPENSES", 400), ("", 200)], is_subtotal=True)
            self._add_hierarchical_accounts(data.get('expenses', []), indent_level=1)
            self._add_table_row([("Total Operating Expenses", 400), (format_currency(data.get('total_expenses', 0)), 200)], is_total=True)
        else:
            # Add placeholder if no expenses data
            self._add_table_row([("OPERATING EXPENSES", 400), ("", 200)], is_subtotal=True)
            self._add_table_row([("No expenses data available", 400), ("", 200)], indent_level=1)
            self._add_table_row([("Total Operating Expenses", 400), (format_currency(0), 200)], is_total=True)
            
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
            html += self._generate_hierarchical_html(data.get('revenues', []), indent_level=1)
            html += f'<tr class="total"><td>Total Revenue</td><td class="amount">{format_currency(data.get("total_revenue", 0))}</td></tr>'
            
        # COGS section
        if data.get('cogs'):
            html += '<tr class="section-header"><td>COST OF GOODS SOLD</td><td></td></tr>'
            html += self._generate_hierarchical_html(data.get('cogs', []), indent_level=1)
            html += f'<tr class="total"><td>Total Cost of Goods Sold</td><td class="amount">{format_currency(data.get("total_cogs", 0))}</td></tr>'
            
        # Gross Profit
        html += f'<tr class="total"><td>Gross Profit</td><td class="amount">{format_currency(data.get("gross_profit", 0))}</td></tr>'
        
        # Expenses section
        if data.get('expenses'):
            html += '<tr class="section-header"><td>OPERATING EXPENSES</td><td></td></tr>'
            html += self._generate_hierarchical_html(data.get('expenses', []), indent_level=1)
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
            
            # Handle classified assets structure
            if data.get('is_classified'):
                for asset_section in data.get('assets', []):
                    section_name = asset_section.get('name', '')
                    section_accounts = asset_section.get('accounts', [])
                    
                    if section_accounts:
                        self._add_table_row([(section_name, 400), ("", 200)], is_subtotal=True)
                        self._add_hierarchical_accounts(section_accounts, indent_level=1)
                        
                        # Calculate section total
                        section_total = self._calculate_tree_total(section_accounts)
                        self._add_table_row([(f"Total {section_name}", 400), (format_currency(section_total), 200)], is_total=True)
            else:
                # Fallback to old structure
                self._add_hierarchical_accounts(data.get('assets', []), indent_level=1)
            
            self._add_table_row([("Total Assets", 400), (format_currency(data.get('total_assets', 0)), 200)], is_total=True)
            
        # Liabilities section
        if data.get('liabilities'):
            self._add_table_row([("LIABILITIES", 400), ("", 200)], is_subtotal=True)
            
            # Handle classified liabilities structure
            if data.get('is_classified'):
                for liability_section in data.get('liabilities', []):
                    section_name = liability_section.get('name', '')
                    section_accounts = liability_section.get('accounts', [])
                    
                    if section_accounts:
                        self._add_table_row([(section_name, 400), ("", 200)], is_subtotal=True)
                        self._add_hierarchical_accounts(section_accounts, indent_level=1)
                        
                        # Calculate section total
                        section_total = self._calculate_tree_total(section_accounts)
                        self._add_table_row([(f"Total {section_name}", 400), (format_currency(section_total), 200)], is_total=True)
            else:
                # Fallback to old structure
                self._add_hierarchical_accounts(data.get('liabilities', []), indent_level=1)
            
            self._add_table_row([("Total Liabilities", 400), (format_currency(data.get('total_liabilities', 0)), 200)], is_total=True)
            
        # Equity section
        if data.get('equity'):
            self._add_table_row([("EQUITY", 400), ("", 200)], is_subtotal=True)
            self._add_hierarchical_accounts(data.get('equity', []), indent_level=1)
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
            html += self._generate_hierarchical_html(data.get('assets', []), indent_level=1)
            html += f'<tr class="total"><td>Total Assets</td><td class="amount">{format_currency(data.get("total_assets", 0))}</td></tr>'
            
        # Liabilities section
        if data.get('liabilities'):
            html += '<tr class="section-header"><td>LIABILITIES</td><td></td></tr>'
            html += self._generate_hierarchical_html(data.get('liabilities', []), indent_level=1)
            html += f'<tr class="total"><td>Total Liabilities</td><td class="amount">{format_currency(data.get("total_liabilities", 0))}</td></tr>'
            
        # Equity section
        if data.get('equity'):
            html += '<tr class="section-header"><td>EQUITY</td><td></td></tr>'
            html += self._generate_hierarchical_html(data.get('equity', []), indent_level=1)
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


class RatioAnalysisView(BaseFinancialStatementView):
    """Comprehensive ratio analysis view with card-based dashboard."""
    
    def __init__(self, parent=None):
        super().__init__("Financial Ratio Analysis", "Comprehensive Financial Metrics")
        self.ratio_data = None
        self.current_category = "Liquidity"
        
        # Make the main content area transparent
        self.setStyleSheet("background: transparent;")
        
        # Override the header to include tabs
        self._setup_custom_header()
        self._setup_ratio_cards()
        
    def _setup_navigation_bar(self, parent_layout):
        """Override base navigation to include tabs in center."""
        from PyQt6.QtWidgets import QHBoxLayout, QPushButton
        
        nav_layout = QHBoxLayout()
        
        # Back button
        back_btn = QPushButton("◀ Reports")
        back_btn.setFixedSize(140, 36)
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
        """)
        back_btn.clicked.connect(self.backToReports.emit)
        nav_layout.addWidget(back_btn)
        
        nav_layout.addStretch()
        
        # Tab container in center
        self._create_tab_container(nav_layout)
        
        nav_layout.addStretch()
        
        # Print button
        print_btn = QPushButton("Print Report")
        print_btn.setFixedSize(140, 36)
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
        """)
        print_btn.clicked.connect(self._print_statement)
        nav_layout.addWidget(print_btn)
        
        parent_layout.addLayout(nav_layout)
    
    def _setup_custom_header(self):
        """Override the base navigation to add tabs in the center."""
        # This is now handled by overriding _setup_navigation_bar
        pass
    
    def _create_tab_container(self, parent_layout):
        """Create the tab container with buttons."""
        from PyQt6.QtWidgets import QHBoxLayout, QPushButton, QFrame
        
        # Tab container frame
        tab_container = QFrame()
        tab_container.setStyleSheet(f"""
            QFrame {{
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: {ResponsiveHelper.scale_size(8, 6, 10)}px;
                padding: {ResponsiveHelper.scale_size(4, 3, 6)}px;
            }}
        """)
        
        tab_layout = QHBoxLayout(tab_container)
        tab_layout.setContentsMargins(ResponsiveHelper.scale_size(4, 3, 6), ResponsiveHelper.scale_size(4, 3, 6),
                                     ResponsiveHelper.scale_size(4, 3, 6), ResponsiveHelper.scale_size(4, 3, 6))
        tab_layout.setSpacing(ResponsiveHelper.scale_size(4, 3, 6))
        
        # Tab buttons
        self.tab_buttons = []
        tab_names = ["Liquidity", "Profitability", "Leverage", "Efficiency", "Market"]
        
        for i, tab_name in enumerate(tab_names):
            button = QPushButton(tab_name)
            button.setCheckable(True)
            if i == 0:  # Default to first tab
                button.setChecked(True)
            button.setStyleSheet(self._get_tab_button_style())
            button.clicked.connect(lambda checked, idx=i: self._switch_tab(idx))
            self.tab_buttons.append(button)
            tab_layout.addWidget(button)
        
        parent_layout.addWidget(tab_container)
    
    def _get_tab_button_style(self):
        """Get tab button styling."""
        return f"""
            QPushButton {{
                background: transparent;
                border: none;
                border-radius: {ResponsiveHelper.scale_size(6, 5, 8)}px;
                padding: {ResponsiveHelper.scale_size(8, 6, 10)}px {ResponsiveHelper.scale_size(16, 12, 20)}px;
                color: rgba(255, 255, 255, 0.8);
                font-size: {ResponsiveHelper.scale_size(13, 11, 15)}px;
                font-weight: 500;
                margin: 0;
                min-width: {ResponsiveHelper.scale_size(70, 60, 80)}px;
            }}
            QPushButton:hover {{
                background: rgba(255, 255, 255, 0.08);
                color: white;
            }}
            QPushButton:checked {{
                background: rgba(0, 120, 215, 0.3);
                color: white;
            }}
            QPushButton:checked:hover {{
                background: rgba(0, 120, 215, 0.4);
            }}
        """
    
    def _setup_ratio_cards(self):
        """Setup the main content area with ratio cards."""
        from PyQt6.QtWidgets import QGridLayout, QWidget
        
        # Clear existing content
        self.clear_content()
        
        # Create cards container
        self.cards_container = QWidget()
        self.cards_layout = QGridLayout(self.cards_container)
        self.cards_layout.setSpacing(ResponsiveHelper.scale_size(20, 16, 24))
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        
        # Add cards container to main content
        self.content_layout.addWidget(self.cards_container)
        
        # Add summary section
        self._setup_summary_ui()
        
        self.content_layout.addStretch()
        
        # Load initial ratio cards for Liquidity tab
        self._load_ratio_cards_for_category("Liquidity")
    
    def _setup_summary_ui(self):
        """Create the summary section with financial insights."""
        from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel
        
        # Summary container with ActionCard-style styling
        summary_container = QFrame()
        summary_container.setStyleSheet(f"""
            QFrame {{
                background: rgba(33, 150, 243, 0.1);
                border: 1px solid rgba(0, 0, 0, 0.3);
                border-radius: {ResponsiveHelper.scale_size(12, 10, 16)}px;
                margin: {ResponsiveHelper.scale_size(20, 16, 24)}px 0;
                padding: {ResponsiveHelper.scale_size(24, 20, 32)}px;
            }}
            QFrame:hover {{
                background: rgba(33, 150, 243, 0.15);
                border: 1px solid rgba(33, 150, 243, 0.4);
            }}
        """)
        
        layout = QVBoxLayout(summary_container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(ResponsiveHelper.scale_size(16, 12, 20))
        
        # Summary title
        title_label = QLabel("Financial Analysis Summary")
        title_label.setStyleSheet(f"""
            QLabel {{
                color: white;
                font-size: {ResponsiveHelper.scale_size(20, 18, 24)}px;
                font-weight: 600;
                background: transparent;
                border: none;
                outline: none;
                margin: 0px;
                padding: 0px;
            }}
        """)
        layout.addWidget(title_label)
        
        # Summary description
        self.summary_desc_label = QLabel("The financial ratios indicate a strong and healthy financial position. The company demonstrates:")
        self.summary_desc_label.setStyleSheet(f"""
            QLabel {{
                color: rgba(255, 255, 255, 0.8);
                font-size: {ResponsiveHelper.scale_size(14, 12, 16)}px;
                font-weight: 400;
                background: transparent;
                border: none;
                outline: none;
                margin: 0px;
                padding: 0px;
                line-height: 1.5;
            }}
        """)
        self.summary_desc_label.setWordWrap(True)
        layout.addWidget(self.summary_desc_label)
        
        # Layout for key points
        self.summary_points_layout = QVBoxLayout()
        layout.addLayout(self.summary_points_layout)
        
        # Add to main content layout
        self.content_layout.addWidget(summary_container)
    
    def _load_ratio_cards_for_category(self, category):
        """Load ratio cards for the specified category."""
        self.current_category = category
        # Clear existing cards
        for i in reversed(range(self.cards_layout.count())):
            item = self.cards_layout.itemAt(i)
            if item:
                widget = item.widget()
                if widget:
                    widget.setParent(None)
        
        # Get ratios for the selected category from the stored data
        ratios = self.ratio_data.get(category, []) if self.ratio_data else []
        
        # Create cards for the selected category
        if not ratios:
            # Display a message if no data is available
            no_data_label = QLabel(f"No {category.lower()} ratios available to display.")
            no_data_label.setStyleSheet("color: white; font-size: 14px;")
            no_data_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.cards_layout.addWidget(no_data_label, 0, 0, 1, 2) # Span across 2 columns
            return

        for i, ratio in enumerate(ratios):
            card = self._create_ratio_card(ratio)
            row = i // 2  # 2 cards per row
            col = i % 2
            self.cards_layout.addWidget(card, row, col)
    
    def _create_ratio_card(self, ratio_data):
        """Create a single ratio card matching ActionCard design."""
        from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QGraphicsDropShadowEffect, QSizePolicy
        from PyQt6.QtGui import QColor
        from PyQt6.QtCore import Qt
        
        card = QFrame()
        
        # Apply ActionCard-style glassmorphism with accent color
        status_color = self._get_status_color(ratio_data["status"])
        accent_rgb = self._hex_to_rgb(status_color)
        border_radius = ResponsiveHelper.scale_size(8, 6, 10)
        
        card.setStyleSheet(f"""
            QFrame {{
                background: rgba({accent_rgb[0]}, {accent_rgb[1]}, {accent_rgb[2]}, 0.1);
                border: 1px solid rgba(0, 0, 0, 0.3);
                border-radius: {border_radius}px;
                margin: 4px;
            }}
            QFrame:hover {{
                background: rgba({accent_rgb[0]}, {accent_rgb[1]}, {accent_rgb[2]}, 0.15);
                border: 1px solid rgba({accent_rgb[0]}, {accent_rgb[1]}, {accent_rgb[2]}, 0.4);
            }}
        """)
        
        # Set ActionCard-style dimensions
        card.setMinimumHeight(ResponsiveHelper.scale_size(140, 120, 160))
        card.setMaximumHeight(ResponsiveHelper.scale_size(200, 180, 220))
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Add ActionCard-style drop shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(ResponsiveHelper.scale_size(20, 15, 30))
        shadow.setXOffset(0)
        shadow.setYOffset(ResponsiveHelper.scale_size(4, 2, 6))
        shadow.setColor(QColor(0, 0, 0, 80))
        card.setGraphicsEffect(shadow)
        
        # Layout with ActionCard-style margins
        layout = QVBoxLayout(card)
        margins = ResponsiveHelper.scale_size(24, 20, 32)
        layout.setContentsMargins(margins, margins, margins, margins)
        layout.setSpacing(ResponsiveHelper.scale_size(12, 8, 16))
        
        # Title (ratio name) - ActionCard style
        name_label = QLabel(ratio_data["name"])
        name_label.setStyleSheet(f"""
            QLabel {{
                color: white;
                font-size: {ResponsiveHelper.scale_size(16, 14, 18)}px;
                font-weight: 600;
                background: transparent;
                border: none;
                outline: none;
                margin: 0px;
                padding: 0px;
            }}
        """)
        name_label.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        layout.addWidget(name_label)
        
        # Value with trend - main content
        value_layout = QHBoxLayout()
        value_layout.setSpacing(ResponsiveHelper.scale_size(8, 6, 10))
        
        # Value (large, prominent)
        value_label = QLabel(ratio_data["value"])
        value_label.setStyleSheet(f"""
            QLabel {{
                color: white;
                font-size: {ResponsiveHelper.scale_size(24, 20, 28)}px;
                font-weight: 700;
                background: transparent;
                border: none;
                outline: none;
                margin: 0px;
                padding: 0px;
            }}
        """)
        value_label.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        value_layout.addWidget(value_label)
        
        value_layout.addStretch()
        
        # Trend indicator
        trend_label = QLabel(ratio_data["trend"])
        trend_label.setStyleSheet(f"""
            QLabel {{
                color: rgba(255, 255, 255, 0.8);
                font-size: {ResponsiveHelper.scale_size(18, 16, 20)}px;
                background: transparent;
                border: none;
                outline: none;
                margin: 0px;
                padding: 0px;
            }}
        """)
        trend_label.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        value_layout.addWidget(trend_label)
        
        layout.addLayout(value_layout)
        
        # Status and target info - ActionCard description style
        info_text = f"{ratio_data['status']} • Target: {ratio_data['target']}"
        info_label = QLabel(info_text)
        info_label.setStyleSheet(f"""
            QLabel {{
                color: rgba(255, 255, 255, 0.7);
                font-size: {ResponsiveHelper.scale_size(13, 11, 15)}px;
                font-weight: 400;
                background: transparent;
                border: none;
                outline: none;
                margin: 0px;
                padding: 0px;
                margin-top: {ResponsiveHelper.scale_size(4, 2, 6)}px;
            }}
        """)
        info_label.setWordWrap(True)
        info_label.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        layout.addWidget(info_label)
        
        # Interpretation as secondary description
        interpretation_label = QLabel(ratio_data["interpretation"])
        interpretation_label.setStyleSheet(f"""
            QLabel {{
                color: rgba(255, 255, 255, 0.6);
                font-size: {ResponsiveHelper.scale_size(12, 10, 14)}px;
                font-weight: 400;
                background: transparent;
                border: none;
                outline: none;
                margin: 0px;
                padding: 0px;
                margin-top: {ResponsiveHelper.scale_size(2, 1, 3)}px;
            }}
        """)
        interpretation_label.setWordWrap(True)
        interpretation_label.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        layout.addWidget(interpretation_label)
        
        # Add stretch like ActionCard
        layout.addStretch()
        
        return card
    
    def _hex_to_rgb(self, hex_color):
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def _switch_tab(self, tab_index):
        """Switch to the specified tab and load corresponding ratio cards."""
        if 0 <= tab_index < len(self.tab_buttons):
            # Update button checked states
            for i, button in enumerate(self.tab_buttons):
                button.setChecked(i == tab_index)
            
            # Load cards for the selected category
            categories = ["Liquidity", "Profitability", "Leverage", "Efficiency", "Market"]
            if tab_index < len(categories):
                self.current_category = categories[tab_index]
                self._load_ratio_cards_for_category(self.current_category)
                

                
    def _get_status_color(self, status):
        """Get color for ratio status."""
        status_colors = {
            "Good": "#4CAF50",      # Green
            "Warning": "#FF9800",   # Orange
            "Critical": "#F44336",  # Red
            "Info": "#2196F3"       # Blue
        }
        return status_colors.get(status, "#757575")
        
    def show_ratio_analysis(self, ratio_data: dict, summary_points: list):
        """Load actual ratio data and update the view."""
        self.ratio_data = ratio_data
        self.summary_points = summary_points
        
        # Reload the currently selected tab with new data
        self._load_ratio_cards_for_category(self.current_category)
        self._update_summary_section()

    def _update_summary_section(self):
        """Update the summary section with dynamic points."""
        # Clear existing points
        for i in reversed(range(self.summary_points_layout.count())):
            item = self.summary_points_layout.itemAt(i)
            if item and item.widget():
                item.widget().deleteLater()

        # Add new points
        for point in self.summary_points:
            point_label = QLabel(f"• {point}")
            point_label.setStyleSheet(f"""
                QLabel {{
                    color: rgba(255, 255, 255, 0.9);
                    font-size: {ResponsiveHelper.scale_size(13, 11, 15)}px;
                    font-weight: 400;
                    background: transparent;
                    border: none;
                    outline: none;
                    margin: 0px;
                    padding: {ResponsiveHelper.scale_size(4, 3, 6)}px 0px;
                    margin-left: {ResponsiveHelper.scale_size(16, 12, 20)}px;
                }}
            """)
            point_label.setWordWrap(True)
            self.summary_points_layout.addWidget(point_label)
        
    def _generate_html_content(self):
        """Generate HTML content for printing/export."""
        html = f"""
        <html>
        <head>
            <style>
                body {{ 
                    font-family: {self.get_html_font_family()}; 
                    margin: 40px;
                    background: white;
                    color: #333;
                }}
                h1 {{ color: #1976D2; border-bottom: 2px solid #1976D2; padding-bottom: 10px; }}
                h2 {{ color: #1976D2; margin-top: 30px; border-bottom: 1px solid #ddd; padding-bottom: 5px; }}
                .ratio-grid {{ 
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                    gap: 20px;
                    margin: 20px 0;
                }}
                .ratio-card {{ 
                    border: 1px solid #ddd; 
                    padding: 20px; 
                    border-radius: 8px;
                    background: #f9f9f9;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                .ratio-name {{ 
                    font-size: 18px;
                    font-weight: 600;
                    color: #1976D2;
                    margin-bottom: 10px;
                }}
                .ratio-value {{ 
                    font-size: 28px;
                    font-weight: 700;
                    color: #333;
                    margin-bottom: 8px;
                }}
                .ratio-target {{ 
                    color: #666;
                    font-size: 14px;
                    margin-bottom: 8px;
                }}
                .ratio-interpretation {{ 
                    color: #555;
                    font-size: 13px;
                    line-height: 1.4;
                }}
                .status-Good {{ color: #4CAF50; font-weight: 600; }}
                .status-Warning {{ color: #FF9800; font-weight: 600; }}
                .status-Critical {{ color: #F44336; font-weight: 600; }}
                .status-Info {{ color: #2196F3; font-weight: 600; }}
                .category-section {{ margin-bottom: 40px; }}
                .summary-section {{ 
                    margin-top: 40px; 
                    padding: 20px; 
                    background: #f0f8ff; 
                    border-radius: 8px; 
                    border-left: 4px solid #1976D2; 
                }}
                .summary-section h3 {{ margin-top: 0; color: #1976D2; }}
                .summary-section ul {{ padding-left: 20px; margin: 0; }}
                .summary-section li {{ margin-bottom: 8px; }}
            </style>
        </head>
        <body>
            <h1>Financial Ratio Analysis Report</h1>
            <p><strong>Generated on:</strong> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
        """

        if not self.ratio_data:
            html += "<p>No financial ratio data available to generate a report.</p>"
        else:
            for category, ratios in self.ratio_data.items():
                if not ratios:
                    continue
                
                html += f"""
                <div class="category-section">
                    <h2>{category} Ratios</h2>
                    <div class="ratio-grid">
                """
                for ratio in ratios:
                    html += f"""
                        <div class="ratio-card">
                            <div class="ratio-name">{ratio['name']}</div>
                            <div class="ratio-value">{ratio['value']}</div>
                            <div class="ratio-target">Target: {ratio['target']} | <span class="status-{ratio['status']}">{ratio['status']}</span> | {ratio['trend']}</div>
                            <div class="ratio-interpretation">{ratio['interpretation']}</div>
                        </div>
                    """
                html += "</div></div>"

        if self.summary_points:
            html += """
            <div class="summary-section">
                <h3>Summary</h3>
                <ul>
            """
            for point in self.summary_points:
                html += f"<li>{point}</li>"
            html += "</ul></div>"

        html += "</body></html>"
        return html
