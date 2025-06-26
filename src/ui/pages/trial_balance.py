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
        self._load_data()
        
    def _setup_ui(self):
        """Setup clean professional trial balance UI with proper scrolling."""        # Create scroll area for better responsiveness with modern scrollbar
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Apply modern scrollbar styling
        scroll_area_style = """
            QScrollArea {
                border: none;
                background: transparent;
            }
        """ + ModernScrollbarStyles.get_combined_scrollbar_style()
        scroll_area.setStyleSheet(scroll_area_style)
        
        # Content widget
        content_widget = QWidget()
        scroll_area.setWidget(content_widget)
          # Main layout for scroll content
        main_layout = QVBoxLayout(content_widget)
        responsive_margin = ResponsiveHelper.scale_size(32, 24, 48)
        main_layout.setContentsMargins(responsive_margin, 0,  # Remove top margin for seamless flow
                                     responsive_margin, responsive_margin)
        main_layout.setSpacing(16)  # Standardized spacing
        
        # Page header
        header = PageHeader("Trial Balance", "Verify that total debits equal total credits")
        main_layout.addWidget(header)
        
        # Date range selector
        self.date_selector = DateRangeSelector(callback=self._on_date_range_changed)
        main_layout.addWidget(self.date_selector)
          # Compact balance metrics - only 3 cards
        self._create_compact_balance_metrics(main_layout)
        
        # Professional trial balance table with date info
        self._create_trial_balance_table(main_layout)
        
        # Push content to top
        main_layout.addStretch()
          # Set up main widget layout
        widget_layout = QVBoxLayout(self)
        widget_layout.setContentsMargins(0, 0, 0, 0)
        widget_layout.addWidget(scroll_area)
        
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
        # Header with title and search box
        header_layout = QHBoxLayout()
        
        title = QLabel("Account Balances")
        title.setStyleSheet(f"""
            QLabel {{
                color: white;                font-size: {ResponsiveHelper.scale_size(20, 16, 24)}px;
                font-weight: 600;
                background: transparent;
            }}
        """)
        header_layout.addWidget(title)
        
        header_layout.addSpacing(4)
        
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
        
        # Date info label (replaces the card)
        self.date_info_label = QLabel("")
        self.date_info_label.setStyleSheet(f"""
            QLabel {{
                color: rgba(255, 255, 255, 0.8);
                font-size: {ResponsiveHelper.scale_size(12, 11, 14)}px;
                font-weight: 500;
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 6px;
                padding: 8px 12px;
            }}
        """)
        header_layout.addWidget(self.date_info_label)
        
        main_layout.addLayout(header_layout)
          # Professional table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Account Name", "Account Code", "Debit", "Credit"])
        
        # Configure headers
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        
        # Configure vertical header for proper row numbering
        vertical_header = self.table.verticalHeader()
        vertical_header.setVisible(True)
        vertical_header.setDefaultSectionSize(ResponsiveHelper.scale_size(45, 40, 50))  # Set proper row height
        vertical_header.setMinimumSectionSize(ResponsiveHelper.scale_size(40, 35, 45))
        vertical_header.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        
        # Style the vertical header for better visibility
        vertical_header.setStyleSheet(f"""
            QHeaderView::section {{
                background: rgba(255, 255, 255, 0.1);
                color: white;
                border: none;
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                border-right: 1px solid rgba(255, 255, 255, 0.2);
                font-weight: 500;
                font-size: {ResponsiveHelper.scale_size(11, 10, 12)}px;
                text-align: center;
                padding: 4px;
                min-width: {ResponsiveHelper.scale_size(40, 35, 45)}px;
            }}
        """)
        
        # Set column widths
        self.table.setColumnWidth(2, ResponsiveHelper.scale_size(120, 100, 140))
        self.table.setColumnWidth(3, ResponsiveHelper.scale_size(120, 100, 140))
          # Professional styling with modern scrollbar
        table_style = f"""
            QTableWidget {{
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(0, 0, 0, 0.3);
                border-radius: 8px;
                color: white;
                font-size: {ResponsiveHelper.scale_size(12, 11, 14)}px;
                gridline-color: rgba(255, 255, 255, 0.1);
                selection-background-color: rgba(100, 181, 246, 0.15);
            }}
            
            QTableWidget::item {{
                padding: 8px 16px;
                border-bottom: 1px solid rgba(255, 255, 255, 0.05);
                min-height: 32px;
                color: rgba(255, 255, 255, 0.9);
            }}
            
            QTableWidget::item:hover {{
                background: rgba(255, 255, 255, 0.12);
                border: 1px solid rgba(100, 181, 246, 0.3);
            }}
            
            QTableWidget::item:selected {{
                background: rgba(100, 181, 246, 0.15);
                border: 1px solid rgba(100, 181, 246, 0.5);
                color: #90CAF9;
            }}
            
            QHeaderView::section {{
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(0, 0, 0, 0.3);
                color: white;
                padding: 8px 16px;
                font-weight: 500;
                font-size: 12px;
                min-height: 32px;
            }}
            
            QHeaderView::section:hover {{
                background: rgba(255, 255, 255, 0.12);
                border: 1px solid rgba(100, 181, 246, 0.3);
            }}
        """ + ModernScrollbarStyles.get_combined_scrollbar_style()
        
        self.table.setStyleSheet(table_style)
        
        # Disable editing
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSortingEnabled(True)        # Set minimum height to show at least 11 rows plus header and totals
        # Calculation: Header(40) + 11 rows(45×11=495) + totals(50) + padding(30) = ~615px
        self.table.setMinimumHeight(ResponsiveHelper.scale_size(615, 560, 670))
        
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
        """Calculate trial balance using the accounting system method."""
        try:
            # Use the accounting system's get_trial_balance method
            if from_date and to_date:
                from_str = from_date.toString("yyyy-MM-dd")
                to_str = to_date.toString("yyyy-MM-dd")
                account_balances = self.system.get_trial_balance(from_str, to_str)
            else:
                account_balances = self.system.get_trial_balance()
              # Get account metadata for codes and types
            accounts = self.system.get_all_accounts()
            account_info = {}
            for account in accounts:
                account_info[account['name']] = {
                    'type': account['type'],
                    'code': account['code'] or ''
                }
            
            # Build trial balance data in the format expected by the UI
            trial_accounts = []
            total_debits = 0.0
            total_credits = 0.0
            
            # Convert trial balance list to account balances
            for balance_record in account_balances:
                account_name = balance_record['name']
                debit_total = float(balance_record['debit_total'])
                credit_total = float(balance_record['credit_total'])
                net_balance = debit_total - credit_total
                
                if abs(net_balance) >= 0.01:  # Only non-zero balances
                    info = account_info.get(account_name, {'type': 'Unknown', 'code': ''})
                    
                    if net_balance > 0:
                        debit_amount = net_balance
                        credit_amount = 0.0
                        total_debits += net_balance
                    else:
                        debit_amount = 0.0
                        credit_amount = abs(net_balance)
                        total_credits += abs(net_balance)
                    
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
                'as_of_date': to_date.toString("MMM d, yyyy") if to_date else "Current"
            }
            
        except Exception as e:
            print(f"Error calculating trial balance: {e}")
            return {
                'accounts': [],
                'total_debits': 0.0,
                'total_credits': 0.0,
                'difference': 0.0,
                'is_balanced': True,
                'as_of_date': "Error"            }
            
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
        date_text = f"As of {trial_data['as_of_date']} • {account_count} accounts with balances"
        self.date_info_label.setText(date_text)
        
    def _update_trial_balance_table(self, trial_data):
        """Update table with clean professional format - no separator lines."""
        accounts = trial_data['accounts']
        self.table.setRowCount(len(accounts) + 1)  # +1 for totals only (no separator)
        
        # Add account data
        for row, account in enumerate(accounts):
            # Set row height explicitly for each row
            self.table.setRowHeight(row, ResponsiveHelper.scale_size(45, 40, 50))
            
            # Account name
            name_item = QTableWidgetItem(account['name'])
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 0, name_item)
            
            # Account code
            code_item = QTableWidgetItem(account['code'])
            code_item.setFlags(code_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            code_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 1, code_item)
            
            # Debit
            debit_text = f"{account['debit']:,.2f}" if account['debit'] > 0 else ""
            debit_item = QTableWidgetItem(debit_text)
            debit_item.setFlags(debit_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            debit_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 2, debit_item)
            
            # Credit
            credit_text = f"{account['credit']:,.2f}" if account['credit'] > 0 else ""
            credit_item = QTableWidgetItem(credit_text)
            credit_item.setFlags(credit_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            credit_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 3, credit_item)
        
        # Totals row (no separator needed)
        totals_row = len(accounts)
        self.table.setRowHeight(totals_row, ResponsiveHelper.scale_size(50, 45, 55))  # Slightly taller for totals
        
        # Style totals row with different background
        totals_label = QTableWidgetItem("TOTALS")
        totals_label.setFlags(totals_label.flags() & ~Qt.ItemFlag.ItemIsEditable)
        font = QFont()
        font.setBold(True)
        totals_label.setFont(font)
        # Add background color to distinguish totals
        totals_label.setBackground(QColor(255, 255, 255, 20))  # Subtle highlight
        self.table.setItem(totals_row, 0, totals_label)
        
        # Empty cell for account code in totals
        empty_item = QTableWidgetItem("")
        empty_item.setFlags(empty_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        empty_item.setBackground(QColor(255, 255, 255, 20))
        self.table.setItem(totals_row, 1, empty_item)
        
        # Total debits
        total_debits_item = QTableWidgetItem(f"{trial_data['total_debits']:,.2f}")
        total_debits_item.setFlags(total_debits_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        total_debits_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        total_debits_item.setFont(font)
        total_debits_item.setBackground(QColor(255, 255, 255, 20))
        self.table.setItem(totals_row, 2, total_debits_item)
        
        # Total credits
        total_credits_item = QTableWidgetItem(f"{trial_data['total_credits']:,.2f}")
        total_credits_item.setFlags(total_credits_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        total_credits_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        total_credits_item.setFont(font)
        total_credits_item.setBackground(QColor(255, 255, 255, 20))
        self.table.setItem(totals_row, 3, total_credits_item)
        
    def _filter_accounts(self):
        """Filter accounts by search text."""
        search_text = self.search_input.text().lower()
        
        for row in range(self.table.rowCount() - 1):  # Exclude totals row only (no separator)
            account_name = self.table.item(row, 0).text().lower() if self.table.item(row, 0) else ""
            account_code = self.table.item(row, 1).text().lower() if self.table.item(row, 1) else ""
            
            show_row = search_text in account_name or search_text in account_code
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
            # Refresh the trial balance with current date range
            from_date, to_date = self.date_selector.get_date_range()
            self._refresh_trial_balance(from_date, to_date)
        except Exception as e:
            print(f"Error refreshing currency display in trial balance: {e}")
