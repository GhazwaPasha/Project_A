"""
Professional Trial Balance Page - Clean Implementation with Improved Layout
Built from scratch to match dashboard/journal/ledger design patterns.
Uses shared components and follows proper accounting standards.
Fixed for proper scrolling and compact design.
"""

from ..common import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, ResponsiveHelper, Qt, QHeaderView, QLineEdit,
    QPushButton, QDate, QButtonGroup, QDateEdit, QFrame
)
from PyQt6.QtWidgets import QScrollArea, QSizePolicy, QGraphicsDropShadowEffect
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtCore import QTimer
from ...core.utils import format_currency
from ..components.scrollbar_styles import ModernScrollbarStyles
from ..components.widgets import PageHeader, ActionCard, DateRangeSelector
from ..components.styles import ModernStyles, GlassmorphismHelper
from ..components.mica_effect import MicaEffect


class TrialBalancePage(QWidget):
    """Professional Trial Balance page with clean, responsive design."""
    
    def __init__(self, system, parent=None):
        super().__init__(parent)
        self.system = system
        
        # Clear any existing layout to prevent overlapping
        if self.layout():
            while self.layout().count():
                child = self.layout().takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
        
        self._setup_ui()
        self._apply_styling()
        # Load data after UI is fully set up to ensure date selector is properly initialized
        QTimer.singleShot(0, self._load_data)
        
    def _setup_ui(self):
        """Setup clean professional trial balance UI without scrolling."""
        # Main layout directly on the widget
        main_layout = QVBoxLayout(self)
        responsive_margin = ResponsiveHelper.scale_size(32, 24, 48)
        main_layout.setContentsMargins(responsive_margin, 0, responsive_margin, 0)
        main_layout.setSpacing(16)  # Standardized spacing
        
        # Page header
        header = PageHeader("Trial Balance", "Verify that total debits equal total credits")
        main_layout.addWidget(header)
        
        # Date range selector - disabled and set to "All Time" for trial balance
        self.date_selector = DateRangeSelector(callback=self._on_date_range_changed)
        # Select "All Time" quick filter by default (button index 4)
        if hasattr(self.date_selector, "quick_buttons"):
            btn = self.date_selector.quick_buttons.button(4)
            if btn:
                btn.setChecked(True)
                self.date_selector._quick_filter_selected()
        
        # Disable the date selector for trial balance (as of date concept)
        self._disable_date_selector()
        
        main_layout.addWidget(self.date_selector)
        
        # Compact balance metrics - only 3 cards
        self._create_compact_balance_metrics(main_layout)
        
        # Professional trial balance table with date info
        self._create_trial_balance_table(main_layout)
        
    def _disable_date_selector(self):
        """Disable the date range selector for trial balance (as of date concept)."""
        # Disable all quick filter buttons
        if hasattr(self.date_selector, "quick_buttons"):
            for button in self.date_selector.quick_buttons.buttons():
                if button:
                    button.setEnabled(False)
        
        # Disable date pickers
        if hasattr(self.date_selector, "from_date"):
            self.date_selector.from_date.setEnabled(False)
        if hasattr(self.date_selector, "to_date"):
            self.date_selector.to_date.setEnabled(False)
        
        # Apply disabled styling
        self.date_selector.setStyleSheet("""
            QWidget {
                opacity: 0.6;
            }
        """)
        
    def _create_compact_balance_metrics(self, main_layout):
        """Create compact balance status metrics - 4 essential cards."""
        # Single row of compact metrics
        metrics_layout = QHBoxLayout()
        metrics_layout.setSpacing(16)  # Standardized spacing        
        # Create compact metric cards
        self.card_balance_status = self._create_compact_card("Balance Status", "Checking...", "")
        self.card_total_debits = self._create_compact_card("Total Debits", "0.00", "")
        self.card_total_credits = self._create_compact_card("Total Credits", "0.00", "")
        self.card_difference = self._create_compact_card("Difference", "0.00", "")
        
        for card in [self.card_balance_status, self.card_total_debits, self.card_total_credits, self.card_difference]:
            metrics_layout.addWidget(card)
            
        # Remove stretch to allow cards to fill the available space
        main_layout.addLayout(metrics_layout)
        
    def _create_compact_card(self, title, value, subtitle):
        """Create a compact metric card with proper sizing to match action cards."""
        card = QFrame()        # Reduced height since we removed the subtitle row
        card.setMinimumHeight(ResponsiveHelper.scale_size(100, 90, 120))
        card.setMaximumHeight(ResponsiveHelper.scale_size(140, 130, 160))
        card.setMinimumWidth(ResponsiveHelper.scale_size(240, 220, 260))
        # Remove maximum width constraint to allow cards to stretch
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Card styling - improved to remove border boxes
        card.setStyleSheet(f"""
            QFrame {{                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(0, 0, 0, 0.3);
                border-radius: 8px;
                margin: 4px;
            }}
            QFrame:hover {{
                background: rgba(255, 255, 255, 0.08);
                border-color: rgba(255, 255, 255, 0.2);
            }}
        """)
        
        # Layout with proper spacing
        layout = QVBoxLayout(card)
        margins = ResponsiveHelper.scale_size(20, 16, 24)
        layout.setContentsMargins(margins, margins, margins, margins)
        layout.setSpacing(ResponsiveHelper.scale_size(8, 6, 12))
        
        # Title - fixed styling to remove border box
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            QLabel {{
                color: rgba(255, 255, 255, 0.7);
                font-size: {ResponsiveHelper.scale_size(13, 11, 15)}px;
                font-weight: 500;
                background: transparent;
                border: none;
                outline: none;
                margin: 0px;
                padding: 0px;
            }}
        """)
        title_label.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        layout.addWidget(title_label)
        
        # Value - fixed styling to remove border box
        value_label = QLabel(value)
        value_label.setStyleSheet(f"""
            QLabel {{
                color: white;
                font-size: {ResponsiveHelper.scale_size(20, 18, 24)}px;
                font-weight: 600;
                background: transparent;
                border: none;
                outline: none;
                margin: 0px;                padding: 0px;
            }}
        """)
        value_label.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        layout.addWidget(value_label)
        
        # Add stretch to push content to top like ActionCard
        layout.addStretch()
        
        # Add drop shadow for better depth (like ActionCard)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(ResponsiveHelper.scale_size(15, 10, 20))
        shadow.setXOffset(0)
        shadow.setYOffset(ResponsiveHelper.scale_size(3, 2, 4))
        shadow.setColor(QColor(0, 0, 0, 60))
        card.setGraphicsEffect(shadow)
        
        # Store references for updates (removed subtitle_label)
        card.title_label = title_label
        card.value_label = value_label
        card.layout = layout
        
        # Simplified set_value function without subtitle
        def set_value_simple(v, s=""):
            value_label.setText(v)
        card.set_value = set_value_simple
        
        # Simplified set_ticker function without subtitle
        def set_ticker_simple(t, color="#FFFFFF"):
            pass  # No subtitle to update
        card.set_ticker = set_ticker_simple
        
        return card
        
    def _create_trial_balance_table(self, main_layout):
        """Create professional trial balance table with date info."""
        # Header with search box and date info (no title)
        header_layout = QHBoxLayout()
        
        # Search box - same as ledger tab
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search accounts...")
        self.search_input.setFixedWidth(250)
        self.search_input.setStyleSheet("""
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
        self.search_input.textChanged.connect(self._filter_accounts)
        header_layout.addWidget(self.search_input)
        
        header_layout.addStretch()
        
        # Print button with same styling and height as info label
        print_btn = QPushButton("Print Trial Balance")
        # Set explicit height to match info label
        button_height = ResponsiveHelper.scale_size(48, 44, 52)
        print_btn.setFixedHeight(button_height)
        print_btn.setStyleSheet(f"""
            QPushButton {{
                color: rgba(255, 255, 255, 0.8);
                font-size: {ResponsiveHelper.scale_size(12, 11, 14)}px;
                font-weight: 500;
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 6px;
                padding: 8px 12px;
                min-width: 120px;
                height: {button_height}px;
            }}
            QPushButton:hover {{
                background: rgba(255, 255, 255, 0.08);
                border-color: rgba(255, 255, 255, 0.2);
            }}
            QPushButton:pressed {{
                background: rgba(255, 255, 255, 0.03);
                border-color: rgba(255, 255, 255, 0.1);
            }}
        """)
        print_btn.clicked.connect(self._print_trial_balance)
        header_layout.addWidget(print_btn)
        
        header_layout.addSpacing(8)
        
        # Date info label with explicit height to match print button
        self.date_info_label = QLabel("")
        self.date_info_label.setFixedHeight(button_height)
        self.date_info_label.setStyleSheet(f"""
            QLabel {{
                color: rgba(255, 255, 255, 0.8);
                font-size: {ResponsiveHelper.scale_size(12, 11, 14)}px;
                font-weight: 500;
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 6px;
                padding: 8px 12px;
                height: {button_height}px;
            }}
        """)
        header_layout.addWidget(self.date_info_label)
        
        main_layout.addLayout(header_layout)
          # Professional table
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Account Name", "Debit", "Credit"])
        
        # Configure intelligent column sizing for better content display
        header = self.table.horizontalHeader()
        if header:
            header.setStretchLastSection(False)  # Don't auto-stretch last column
            
            # Set resize modes for each column
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)           # Account Name (main content)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Debit
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Credit
            
            # Set minimum widths to ensure content is always visible
            header.setMinimumSectionSize(80)   # Minimum for any column
            self.table.setColumnWidth(0, 300)  # Account Name - generous space for names
            self.table.setColumnWidth(1, 150)  # Debit column
            self.table.setColumnWidth(2, 150)  # Credit column
        
        # Hide the vertical header (row numbers) to remove the black box
        vertical_header = self.table.verticalHeader()
        vertical_header.setVisible(False)
          # Dark theme table styling to match UI
        table_style = f"""
            QTableWidget {{
                background: rgba(40, 40, 40, 0.95);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                color: #FFFFFF;
                font-size: {ResponsiveHelper.scale_size(12, 11, 14)}px;
                gridline-color: rgba(255, 255, 255, 0.1);
                selection-background-color: rgba(100, 181, 246, 0.3);
                outline: none;
                alternate-background-color: rgba(255, 255, 255, 0.03);
            }}
            
            QTableWidget::item {{
                padding: 12px 16px;
                border: none;
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                min-height: 32px;
                color: #FFFFFF;
                background: transparent;
            }}
            
            QTableWidget::item:alternate {{
                background: rgba(255, 255, 255, 0.03);
            }}
            
            QTableWidget::item:hover {{
                background: rgba(100, 181, 246, 0.2);
            }}
            
            QTableWidget::item:selected {{
                background: rgba(100, 181, 246, 0.3);
                color: #90CAF9;
            }}
            
            QHeaderView::section {{
                background: rgba(255, 255, 255, 0.08);
                border: none;
                border-right: 1px solid rgba(255, 255, 255, 0.15);
                color: white;
                padding: 12px 16px;
                font-weight: 600;
                font-size: {ResponsiveHelper.scale_size(13, 12, 14)}px;
                min-height: 40px;
                text-align: left;
            }}
            
            QHeaderView::section:last {{
                border-right: none;
            }}
            
            QHeaderView::section:first {{
                border-top-left-radius: 8px;
            }}
            
            QHeaderView::section:last {{
                border-top-right-radius: 8px;
            }}
        """ + ModernScrollbarStyles.get_combined_scrollbar_style()
        
        self.table.setStyleSheet(table_style)
        
        # Disable editing and enable alternating colors
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSortingEnabled(True)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)  # We'll use custom borders instead
        
        # Set size policy to allow the table to expand but respect max height
        self.table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        main_layout.addWidget(self.table)
        
    def _apply_styling(self):
        """Apply consistent styling."""
        MicaEffect.apply_mica(self, dark_mode=True)
        GlassmorphismHelper.apply_main_container_effect(self)
        self.setStyleSheet(ModernStyles.get_complete_stylesheet())
        
    def _load_data(self):
        """Load initial data."""
        self._refresh_data()
        
    def _on_date_range_changed(self, start_date, end_date):
        """Handle date range changes."""
        self._refresh_data()
        
    def _refresh_data(self):
        """Refresh trial balance data."""
        try:
            from_date, to_date = self.date_selector.get_date_range()
            trial_data = self._calculate_trial_balance(from_date, to_date)
            self._update_balance_metrics(trial_data)
            self._update_trial_balance_table(trial_data)
        except Exception as e:
            print(f"Error refreshing trial balance: {e}")
            
    def _calculate_trial_balance(self, from_date, to_date):
        """Calculate trial balance using the hierarchical accounting system method."""
        try:
            # Use the new hierarchical trial balance method
            if hasattr(self.system, 'get_trial_balance'):
                # Get hierarchical trial balance (includes parent account aggregation)
                trial_balance_data = self.system.get_trial_balance()
                
                # Build trial balance data in the format expected by the UI
                trial_accounts = []
                total_debits = 0.0
                total_credits = 0.0
                
                # Process hierarchical trial balance data
                for balance_record in trial_balance_data:
                    account_name = balance_record['name']
                    debit_balance = float(balance_record.get('debit_balance', 0))
                    credit_balance = float(balance_record.get('credit_balance', 0))
                    net_balance = float(balance_record.get('net_balance', 0))
                    has_children = balance_record.get('has_children', False)
                    child_count = balance_record.get('child_count', 0)
                    level = balance_record.get('level', 1)
                    
                    # Only include accounts with activity or significant aggregated balances
                    if (debit_balance > 0 or credit_balance > 0 or 
                        abs(net_balance) >= 0.01 or has_children):
                        
                        # Use the pre-calculated debit and credit balances
                        debit_amount = debit_balance
                        credit_amount = credit_balance
                        total_debits += debit_balance
                        total_credits += credit_balance
                        
                        trial_accounts.append({
                            'name': account_name,
                            'code': balance_record.get('code', ''),
                            'debit': debit_amount,
                            'credit': credit_amount,
                            'level': level,
                            'has_children': has_children,
                            'child_count': child_count,
                            'is_postable': balance_record.get('is_postable', True)
                        })
                
                # Sort by account code for consistent display
                trial_accounts.sort(key=lambda x: x.get('code', '') or x['name'])
                
                difference = abs(total_debits - total_credits)
                is_balanced = difference < 0.01
                
                return {
                    'accounts': trial_accounts,
                    'total_debits': total_debits,
                    'total_credits': total_credits,
                    'difference': difference,
                    'is_balanced': is_balanced,
                    'as_of_date': "Current (Hierarchical)"
                }
            else:
                # Fallback to original method
                return self._calculate_trial_balance_fallback(from_date, to_date)
                
        except Exception as e:
            print(f"Error calculating hierarchical trial balance: {e}")
            # Fallback to original method
            return self._calculate_trial_balance_fallback(from_date, to_date)
    
    def _calculate_trial_balance_fallback(self, from_date, to_date):
        """Fallback method using original trial balance calculation."""
        try:
            # For trial balance, always use "as of date" concept (all time data)
            # This ensures trial balance shows cumulative balances regardless of date filter
            account_balances = self.system.get_trial_balance()
              # Get account metadata for codes and types
            accounts = self.system.get_all_accounts()
            account_info = {}
            for account in accounts:
                # Unpack tuple: (name, type, code, parent_code, level, is_postable, description)
                name, acc_type, code, parent_code, level, is_postable, description = account
                account_info[name] = {
                    'type': acc_type,
                    'code': code or ''
                }
            
            # Build trial balance data in the format expected by the UI
            trial_accounts = []
            total_debits = 0.0
            total_credits = 0.0
            
            # Convert trial balance list to account balances
            for balance_record in account_balances:
                account_name = balance_record['name']
                debit_balance = float(balance_record.get('debit_balance', 0))
                credit_balance = float(balance_record.get('credit_balance', 0))
                net_balance = float(balance_record.get('net_balance', 0))
                
                if abs(net_balance) >= 0.01:  # Only non-zero balances
                    info = account_info.get(account_name, {'type': 'Unknown', 'code': ''})
                    
                    # Use the pre-calculated debit and credit balances
                    debit_amount = debit_balance
                    credit_amount = credit_balance
                    total_debits += debit_balance
                    total_credits += credit_balance
                    
                    trial_accounts.append({
                        'name': account_name,
                        'code': info['code'],
                        'debit': debit_amount,
                        'credit': credit_amount
                    })
            
            # Sort alphabetically by account name
            trial_accounts.sort(key=lambda x: x['name'])
            
            difference = abs(total_debits - total_credits)
            is_balanced = difference < 0.01
            
            return {
                'accounts': trial_accounts,
                'total_debits': total_debits,
                'total_credits': total_credits,
                'difference': difference,
                'is_balanced': is_balanced,
                'as_of_date': "Current"
            }
            
        except Exception as e:
            print(f"Error calculating fallback trial balance: {e}")
            return {
                'accounts': [],
                'total_debits': 0.0,
                'total_credits': 0.0,
                'difference': 0.0,
                'is_balanced': True,
                'as_of_date': "Error"
            }
            
    def _update_balance_metrics(self, trial_data):
        """Update compact metrics cards and date info."""
        symbol = self._get_currency_symbol()
        
        # Balance status (removed emoji)
        if trial_data['is_balanced']:
            self.card_balance_status.set_value("BALANCED", "")
        else:
            self.card_balance_status.set_value("UNBALANCED", "")
          # Amounts - use proper currency formatting
        self.card_total_debits.set_value(format_currency(trial_data['total_debits']))
        self.card_total_credits.set_value(format_currency(trial_data['total_credits']))
        
        # Difference card - use proper currency formatting
        self.card_difference.set_value(format_currency(trial_data['difference']))
        
        # Update date info near the table (not in a card)
        account_count = len(trial_data['accounts'])
        date_text = f"Trial Balance as of {trial_data['as_of_date']} • {account_count} accounts with balances"
        self.date_info_label.setText(date_text)
        
    def _update_trial_balance_table(self, trial_data):
        """Update table with clean professional format - no separator lines."""
        accounts = trial_data['accounts']
        self.table.setRowCount(len(accounts) + 1)  # +1 for totals only (no separator)
        
        # Add account data with consistent row styling
        for row, account in enumerate(accounts):
            # Set consistent row height matching ledger table
            self.table.setRowHeight(row, 40)
            
            # Account name
            name_item = QTableWidgetItem(account['name'])
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 0, name_item)
            
            # Debit
            debit_text = format_currency(account['debit']) if account['debit'] > 0 else ""
            debit_item = QTableWidgetItem(debit_text)
            debit_item.setFlags(debit_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            debit_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 1, debit_item)
            
            # Credit
            credit_text = format_currency(account['credit']) if account['credit'] > 0 else ""
            credit_item = QTableWidgetItem(credit_text)
            credit_item.setFlags(credit_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            credit_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 2, credit_item)
        
        # Totals row with professional styling
        totals_row = len(accounts)
        self.table.setRowHeight(totals_row, 50)  # Slightly taller for totals
        
        # TOTALS label with bold styling
        totals_label = QTableWidgetItem("TOTALS")
        totals_label.setFlags(totals_label.flags() & ~Qt.ItemFlag.ItemIsEditable)
        font = QFont()
        font.setBold(True)
        font.setPointSize(ResponsiveHelper.scale_size(12, 11, 13))
        totals_label.setFont(font)
        totals_label.setBackground(QColor(245, 245, 245))  # Light gray background
        totals_label.setForeground(QColor(51, 51, 51))     # Dark text
        self.table.setItem(totals_row, 0, totals_label)
        
        # Total debits with proper currency formatting
        total_debits_item = QTableWidgetItem(format_currency(trial_data['total_debits']))
        total_debits_item.setFlags(total_debits_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        total_debits_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        total_debits_item.setFont(font)
        total_debits_item.setBackground(QColor(245, 245, 245))
        total_debits_item.setForeground(QColor(51, 51, 51))
        self.table.setItem(totals_row, 1, total_debits_item)
        
        # Total credits with proper currency formatting
        total_credits_item = QTableWidgetItem(format_currency(trial_data['total_credits']))
        total_credits_item.setFlags(total_credits_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        total_credits_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        total_credits_item.setFont(font)
        total_credits_item.setBackground(QColor(245, 245, 245))
        total_credits_item.setForeground(QColor(51, 51, 51))
        self.table.setItem(totals_row, 2, total_credits_item)
        
        # Optimize column sizes after data is loaded
        self._optimize_column_sizes()
        
    def _optimize_column_sizes(self):
        """Intelligently resize columns for optimal content display."""
        # First, auto-resize all columns to fit their content
        for col in range(self.table.columnCount()):
            self.table.resizeColumnToContents(col)
        
        # Get current column widths after auto-resize
        current_widths = [self.table.columnWidth(i) for i in range(self.table.columnCount())]
        
        # Set intelligent minimums and adjustments for each column
        min_widths = [200, 120, 120]  # Account Name, Debit, Credit
        
        # Ensure Account Name column has enough space for long account names
        account_name_extra = 50  # Extra space for longer account names
        current_widths[0] = max(current_widths[0], min_widths[0] + account_name_extra)
        
        # Ensure Debit/Credit columns have enough space for currency formatting
        currency_extra = 30  # Extra space for currency symbols and formatting
        current_widths[1] = max(current_widths[1], min_widths[1] + currency_extra)
        current_widths[2] = max(current_widths[2], min_widths[2] + currency_extra)
        
        # Apply the optimized widths
        for i, width in enumerate(current_widths):
            # Ensure minimum width is respected
            final_width = max(width, min_widths[i])
            self.table.setColumnWidth(i, final_width)
        
    def _filter_accounts(self):
        """Filter accounts by search text."""
        search_text = self.search_input.text().lower()
        
        for row in range(self.table.rowCount() - 1):  # Exclude totals row only (no separator)
            account_name = self.table.item(row, 0).text().lower() if self.table.item(row, 0) else ""
            
            show_row = search_text in account_name
            self.table.setRowHidden(row, not show_row)
            
    def _get_currency_symbol(self):
        """Get currency symbol."""
        try:
            with open('currency.cfg', 'r') as f:
                return f.read().strip()
        except:
            return "$"
            
    def get_current_summary(self):
        """Get summary for external use."""
        try:
            from_date, to_date = self.date_selector.get_date_range()
            trial_data = self._calculate_trial_balance(from_date, to_date)
            return {
                'total_debits': trial_data['total_debits'],
                'total_credits': trial_data['total_credits'],
                'is_balanced': trial_data['is_balanced'],
                'difference': trial_data['difference'],
                'account_count': len(trial_data['accounts'])
            }
        except:
            return None
        
    def refresh_currency_display(self):
        """Refresh all currency displays when currency symbol changes."""
        try:
            # Get current date range and recalculate trial balance
            from_date, to_date = self.date_selector.get_date_range()
            self._refresh_data()
        except Exception as e:
            print(f"Error refreshing currency display: {e}")
    
    def set_date_range(self, start_date, end_date):
        """Set the date range programmatically (for AI navigation)."""
        if hasattr(self, 'date_selector') and self.date_selector:
            success = self.date_selector.set_date_range(start_date, end_date)
            if success:
                print(f"✅ Trial Balance date range set to: {start_date} to {end_date}")
                # Refresh the trial balance with new date range
                self._refresh_data()
                return True
            else:
                print(f"❌ Failed to set Trial Balance date range: {start_date} to {end_date}")
                return False
        return False

    def _print_trial_balance(self):
        """Print or export the trial balance using Windows native print function."""
        try:
            import tempfile
            import os
            import webbrowser
            import time
            import threading
            from datetime import datetime
            
            # Create a temporary HTML file with the trial balance content
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
                html_content = self._generate_trial_balance_html()
                f.write(html_content)
                temp_file = f.name
            
            # Open the HTML file in the default browser, which will allow printing
            webbrowser.open('file://' + temp_file.replace('\\', '/'))
            
            # Show a message to the user
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(self, "Print", 
                "The trial balance has been opened in your web browser.\n"
                "Use Ctrl+P or the browser's print menu to print the document.\n"
                "The temporary file will be cleaned up automatically.")
            
            # Clean up the temporary file after a delay
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
                "You can manually copy the trial balance content or take a screenshot to print.")

    def _generate_trial_balance_html(self):
        """Generate HTML content for printing the trial balance."""
        from datetime import datetime
        
        # Get current trial balance data
        from_date, to_date = self.date_selector.get_date_range()
        trial_data = self._calculate_trial_balance(from_date, to_date)
        
        # Get date range text
        if from_date and to_date:
            date_range = f"{from_date.toString('MMMM d, yyyy')} to {to_date.toString('MMMM d, yyyy')}"
        else:
            date_range = "All Time"
        
        # Generate table rows
        table_rows = ""
        for account in trial_data['accounts']:
            debit_text = format_currency(account['debit']) if account['debit'] > 0 else ""
            credit_text = format_currency(account['credit']) if account['credit'] > 0 else ""
            
            table_rows += f"""
            <tr>
                <td>{account['name']}</td>
                <td style="text-align: right;">{debit_text}</td>
                <td style="text-align: right;">{credit_text}</td>
            </tr>
            """
        
        # Generate complete HTML
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Trial Balance</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
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
                .date-range {{
                    font-size: 16px;
                    color: #666;
                    margin-bottom: 5px;
                }}
                .account-count {{
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
                .summary-value {{
                    font-size: 18px;
                    color: #1976D2;
                    margin-top: 5px;
                }}
                .balanced {{
                    color: #4CAF50;
                }}
                .unbalanced {{
                    color: #F44336;
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
                th.center {{
                    text-align: center;
                }}
                th.right {{
                    text-align: right;
                }}
                td {{
                    padding: 8px 12px;
                    border-bottom: 1px solid #E0E0E0;
                    font-size: 12px;
                }}
                tr:nth-child(even) {{
                    background-color: #FAFAFA;
                }}
                .totals-row {{
                    background: #F5F5F5 !important;
                    font-weight: 600;
                    border-top: 2px solid #1976D2;
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
                <div class="title">TRIAL BALANCE</div>
                <div class="date-range">Period: {date_range}</div>
                <div class="account-count">{len(trial_data['accounts'])} accounts with balances</div>
            </div>
            
            <div class="summary">
                <div class="summary-item">
                    <div>Total Debits</div>
                    <div class="summary-value">{format_currency(trial_data['total_debits'])}</div>
                </div>
                <div class="summary-item">
                    <div>Total Credits</div>
                    <div class="summary-value">{format_currency(trial_data['total_credits'])}</div>
                </div>
                <div class="summary-item">
                    <div>Difference</div>
                    <div class="summary-value">{format_currency(trial_data['difference'])}</div>
                </div>
                <div class="summary-item">
                    <div>Status</div>
                    <div class="summary-value {'balanced' if trial_data['is_balanced'] else 'unbalanced'}">
                        {'BALANCED' if trial_data['is_balanced'] else 'UNBALANCED'}
                    </div>
                </div>
            </div>
            
            <table>
                <thead>
                    <tr>
                        <th>Account Name</th>
                        <th class="right">Debit</th>
                        <th class="right">Credit</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows}
                    <tr class="totals-row">
                        <td><strong>TOTALS</strong></td>
                        <td style="text-align: right;"><strong>{format_currency(trial_data['total_debits'])}</strong></td>
                        <td style="text-align: right;"><strong>{format_currency(trial_data['total_credits'])}</strong></td>
                    </tr>
                </tbody>
            </table>
            
            <div class="footer">
                Generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
            </div>
        </body>
        </html>
        """
        
        return html
