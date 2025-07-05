"""
Dashboard page for the accounting application.
This module contains the main dashboard interface with financial metrics and quick actions.
"""

from ..common import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    ResponsiveHelper, Qt, QScrollArea, QFrame
)
from ...core.utils import format_currency
from ..components.widgets import MetricCard, ActionCard, PageHeader, DateRangeSelector
from ..components.styles import ModernStyles, GlassmorphismHelper
from ..components.mica_effect import MicaEffect


class DashboardPage(QWidget):
    """Main dashboard page with financial overview and quick actions."""
    
    def __init__(self, system, parent=None):
        super().__init__(parent)
        self.system = system
        self._setup_ui()
        self._apply_styling()
        self._load_data()
        
    def _setup_ui(self):
        """Setup the dashboard UI with scrollable content."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Fixed header section (non-scrollable)
        header_section = QFrame()
        header_layout = QVBoxLayout(header_section)
        responsive_margin = ResponsiveHelper.scale_size(32, 24, 48)
        header_layout.setContentsMargins(responsive_margin, 0, responsive_margin, 0)
        header_layout.setSpacing(16)
        
        # Page header
        header = PageHeader("Dashboard", "Financial overview and quick actions")
        header_layout.addWidget(header)
        
        # Date range selector
        self.date_selector = DateRangeSelector(callback=self._on_date_range_changed)
        header_layout.addWidget(self.date_selector)
        
        main_layout.addWidget(header_section)
        
        # Scrollable content section
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        
        # Content widget for scrollable area
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(responsive_margin, 16, responsive_margin, responsive_margin)
        content_layout.setSpacing(20)
        
        # Financial metrics cards in mixed layout
        self._create_mixed_metrics_layout(content_layout)
        
        # Quick actions section
        self._create_actions_section(content_layout)
        
        # Add stretch to push content to top
        content_layout.addStretch()
        
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)
        
    def _create_mixed_metrics_layout(self, content_layout):
        """Create the mixed metrics layout with cards and charts as a 4-column grid, with charts as 2x2 blocks."""
        from PyQt6.QtWidgets import QGridLayout
        grid = QGridLayout()
        grid.setSpacing(ResponsiveHelper.scale_size(20, 16, 28))

        # Metric cards
        self.card_cash = MetricCard("Cash & Cash Equivalents", "0.00", "", clickable=True)
        self.card_net_income = MetricCard("Net Income", "0.00", "", clickable=True)
        self.card_revenue_growth = MetricCard("Revenue Growth", "0.00%", "", clickable=True)
        self.card_expense_growth = MetricCard("Expense Growth", "0.00%", "", clickable=True)
        self.card_liabilities = MetricCard("Liabilities", "0.00", "", clickable=True)
        self.card_working_capital = MetricCard("Working Capital", "0.00", "", clickable=True)
        self.card_gross_margin = MetricCard("Gross Margin", "0.00%", "", clickable=True)
        self.card_operating_margin = MetricCard("Operating Margin", "0.00%", "", clickable=True)
        self.card_receivables = MetricCard("Accounts Receivable", "0.00", "", clickable=True)
        self.card_payables = MetricCard("Accounts Payable", "0.00", "", clickable=True)
        self.card_quick_ratio = MetricCard("Quick Ratio", "0.00", "", clickable=True)
        self.card_debt_equity = MetricCard("Debt-to-Equity", "0.00", "", clickable=True)
        self.card_cash_flow = MetricCard("Cash Flow", "0.00", "", clickable=True)
        self.card_dso = MetricCard("Days Sales Outstanding", "0", "", clickable=True)
        self.card_expenses = MetricCard("Expenses", "0.00", "", clickable=True)
        self.card_revenue = MetricCard("Revenue", "0.00", "", clickable=True)

        # Chart placeholders (replace with real chart widgets later)
        chart1 = QLabel("📊 Revenue vs Expenses Chart\n(2x2 block)")
        chart1.setStyleSheet("""
            QLabel {
                background: rgba(255, 255, 255, 0.1);
                border: 2px dashed rgba(255, 255, 255, 0.3);
                border-radius: 12px;
                color: white;
                padding: 40px;
                font-size: 14px;
                text-align: center;
            }
        """)
        chart1.setMinimumHeight(200)

        chart2 = QLabel("💧 Cash Flow Chart\n(2x2 block)")
        chart2.setStyleSheet(chart1.styleSheet())
        chart2.setMinimumHeight(200)

        # Place widgets in grid (4 columns wide)
        # Row 0
        grid.addWidget(self.card_cash, 0, 0)
        grid.addWidget(self.card_net_income, 0, 1)
        grid.addWidget(chart1, 0, 2, 2, 2)  # 2x2 block at (0,2)
        # Row 1
        grid.addWidget(self.card_revenue_growth, 1, 0)
        grid.addWidget(self.card_expense_growth, 1, 1)
        # Row 2
        grid.addWidget(self.card_liabilities, 2, 0)
        grid.addWidget(self.card_working_capital, 2, 1)
        grid.addWidget(self.card_gross_margin, 2, 2)
        grid.addWidget(self.card_operating_margin, 2, 3)
        # Row 3
        grid.addWidget(self.card_receivables, 3, 0)
        grid.addWidget(self.card_payables, 3, 1)
        grid.addWidget(chart2, 3, 2, 2, 2)  # 2x2 block at (3,2)
        # Row 4
        grid.addWidget(self.card_quick_ratio, 4, 0)
        grid.addWidget(self.card_debt_equity, 4, 1)
        # Row 5
        grid.addWidget(self.card_cash_flow, 5, 0)
        grid.addWidget(self.card_dso, 5, 1)
        grid.addWidget(self.card_expenses, 5, 2)
        grid.addWidget(self.card_revenue, 5, 3)

        content_layout.addLayout(grid)
        
    def _create_actions_section(self, content_layout):
        """Create the quick actions section."""
        # Section title
        actions_title = QLabel("Quick Actions")
        actions_title.setStyleSheet(f"""
            QLabel {{
                color: white;
                font-size: {ResponsiveHelper.scale_size(20, 16, 24)}px;
                font-weight: 600;
                background: transparent;
            }}
        """)
        content_layout.addWidget(actions_title)
        
        # Actions layout
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(ResponsiveHelper.scale_size(20, 16, 28))
        
        # Create action cards
        add_entry_card = ActionCard(
            "Add Journal Entry", 
            "Record a new financial transaction",
            accent_color="#4CAF50"
        )
        add_entry_card.clicked = self._open_journal_entry_dialog
        
        view_reports_card = ActionCard(
            "View Reports",
            "Generate financial reports and analysis", 
            accent_color="#2196F3"
        )
        view_reports_card.clicked = self._open_reports_tab
        
        manage_accounts_card = ActionCard(
            "Manage Accounts",
            "Add, edit, or organize chart of accounts",
            accent_color="#FF9800"
        )
        manage_accounts_card.clicked = self._open_accounts_tab
        
        # Add action cards
        for card in [add_entry_card, view_reports_card, manage_accounts_card]:
            actions_layout.addWidget(card)
            
        actions_layout.addStretch()
        content_layout.addLayout(actions_layout)
        
    def _load_data(self):
        """Load and display financial data."""
        self._update_metrics()
        
    def _update_metrics(self):
        """Update financial metrics cards with current data using group-based reporting."""
        from_date, to_date = self.date_selector.get_date_range()
        from_date_str = from_date.toString("yyyy-MM-dd")
        to_date_str = to_date.toString("yyyy-MM-dd")
        
        # Get financial data using group-based methods
        cash = self._get_cash_balance(from_date_str, to_date_str)
        liabilities = self._get_total_liabilities_group_based(to_date_str)
        revenue = self._get_total_revenue_group_based(from_date_str, to_date_str)
        expenses = self._get_total_expenses_group_based(from_date_str, to_date_str)
        
        # Calculate derived metrics
        net_income = revenue - expenses
        gross_margin = (revenue - self._get_cogs(from_date_str, to_date_str)) / revenue * 100 if revenue > 0 else 0
        operating_margin = net_income / revenue * 100 if revenue > 0 else 0
        
        # Get currency symbol
        symbol = self._get_currency_symbol()
        
        # Update card values using proper currency formatting
        self.card_cash.set_value(format_currency(cash))
        self.card_net_income.set_value(format_currency(net_income))
        self.card_liabilities.set_value(format_currency(liabilities))
        self.card_revenue.set_value(format_currency(revenue))
        self.card_expenses.set_value(format_currency(expenses))
        self.card_gross_margin.set_value(f"{gross_margin:.1f}%")
        self.card_operating_margin.set_value(f"{operating_margin:.1f}%")
        
        # Placeholder values for new metrics (to be implemented)
        self.card_revenue_growth.set_value("0.0%")
        self.card_expense_growth.set_value("0.0%")
        self.card_working_capital.set_value(format_currency(0))
        self.card_receivables.set_value(format_currency(0))
        self.card_payables.set_value(format_currency(0))
        self.card_quick_ratio.set_value("0.00")
        self.card_debt_equity.set_value("0.00")
        self.card_cash_flow.set_value(format_currency(0))
        self.card_dso.set_value("0")
        
        # Update trend indicators
        self._update_trend_indicators(cash, revenue, expenses, liabilities, net_income)
        
    def _update_trend_indicators(self, cash, revenue, expenses, liabilities, net_income):
        """Update trend indicators for cards."""
        # Net Income trend
        if net_income > 0:
            self.card_net_income.set_ticker("↗️ Profitable", "#4CAF50")
        else:
            self.card_net_income.set_ticker("↘️ Loss", "#F44336")
            
        # Revenue vs Expenses trend
        if revenue > expenses:
            self.card_revenue.set_ticker("↗️ Profitable", "#4CAF50")
        else:
            self.card_revenue.set_ticker("↘️ Loss", "#F44336")
            
        # Cash trend
        if cash > 0:
            self.card_cash.set_ticker("💰 Positive", "#4CAF50")
        else:
            self.card_cash.set_ticker("⚠️ Low Cash", "#FF9800")
            
        # Expense ratio
        if expenses > 0:
            expense_ratio = (expenses / revenue * 100) if revenue > 0 else 0
            if expense_ratio < 70:
                self.card_expenses.set_ticker(f"📊 {expense_ratio:.1f}% of revenue", "#4CAF50")
            else:
                self.card_expenses.set_ticker(f"📈 {expense_ratio:.1f}% of revenue", "#FF9800")
                
        # Liabilities trend
        if liabilities > 0:
            self.card_liabilities.set_ticker("📋 Outstanding", "#2196F3")
        else:
            self.card_liabilities.set_ticker("✅ Clear", "#4CAF50")
            
    def _get_cash_balance(self, from_date=None, to_date=None):
        """Get cash balance using group-based reporting."""
        try:
            # Get balance sheet data as of the end date
            if to_date:
                balance_sheet = self.system.generate_group_based_balance_sheet(to_date)
                
                # Look for current assets section which includes cash
                for section in balance_sheet.get('asset_sections', []):
                    if section.get('group') == 'current_asset':
                        # Extract cash from current assets
                        cash_accounts = ['cash', 'bank', 'checking', 'savings', 'petty cash']
                        cash_total = 0.0
                        
                        for account in section.get('accounts', []):
                            account_name = account.get('name', '').lower()
                            if any(cash_type in account_name for cash_type in cash_accounts):
                                cash_total += abs(account.get('balance', 0))
                        
                        return cash_total
                
                # Fallback: get total current assets if cash extraction fails
                for section in balance_sheet.get('asset_sections', []):
                    if section.get('group') == 'current_asset':
                        return section.get('total', 0)
            
            return 0.0
        except Exception as e:
            print(f"Error getting cash balance: {e}")
            return 0.0
        
    def _get_total_liabilities_group_based(self, as_of_date=None):
        """Get total liabilities using group-based balance sheet."""
        try:
            balance_sheet = self.system.generate_group_based_balance_sheet(as_of_date)
            return balance_sheet.get('total_liabilities', 0)
        except Exception as e:
            print(f"Error getting total liabilities: {e}")
            return 0.0
        
    def _get_total_revenue_group_based(self, from_date=None, to_date=None):
        """Get total revenue using group-based income statement."""
        try:
            income_statement = self.system.generate_group_based_income_statement(from_date, to_date)
            return income_statement.get('total_revenue', 0)
        except Exception as e:
            print(f"Error getting total revenue: {e}")
            return 0.0
        
    def _get_total_expenses_group_based(self, from_date=None, to_date=None):
        """Get total expenses using group-based income statement."""
        try:
            income_statement = self.system.generate_group_based_income_statement(from_date, to_date)
            total_cogs = income_statement.get('total_cogs', 0)
            total_operating_expenses = income_statement.get('total_operating_expenses', 0)
            return total_cogs + total_operating_expenses
        except Exception as e:
            print(f"Error getting total expenses: {e}")
            return 0.0
    
    def _get_cogs(self, from_date=None, to_date=None):
        """Get cost of goods sold using group-based income statement."""
        try:
            income_statement = self.system.generate_group_based_income_statement(from_date, to_date)
            return income_statement.get('total_cogs', 0)
        except Exception as e:
            print(f"Error getting COGS: {e}")
            return 0.0
        
    def _get_currency_symbol(self):
        """Get the currency symbol from the main window."""
        mw = self.window()
        return getattr(mw, 'currency_symbol', '$')
        
    def _on_date_range_changed(self, start_date, end_date):
        """Handle date range selection changes."""
        self._update_metrics()
        
    def _open_journal_entry_dialog(self):
        """Switch to the journal tab to add a new entry."""
        main_window = self.window()
        if hasattr(main_window, 'setCurrentIndexByName'):
            main_window.setCurrentIndexByName('Journal')
            # Get the journal page and show the entry form if it has the method
            if hasattr(main_window, 'stack'):
                journal_page = main_window.stack.widget(1)  # Journal is at index 1
                if hasattr(journal_page, '_toggle_entry_section'):
                    # Show the form if it's hidden
                    if hasattr(journal_page, 'entry_form') and not journal_page.entry_form.isVisible():
                        journal_page._toggle_entry_section()
        elif hasattr(main_window, 'stack'):
            main_window.stack.setCurrentIndex(1)  # Journal tab index
            
    def _open_reports_tab(self):
        """Open the reports tab."""
        main_window = self.window()
        if hasattr(main_window, 'setCurrentIndexByName'):
            main_window.setCurrentIndexByName('Reports')
        elif hasattr(main_window, 'stack'):
            main_window.stack.setCurrentIndex(4)  # Reports tab index
            
    def _open_accounts_tab(self):
        """Open the accounts tab."""
        main_window = self.window()
        if hasattr(main_window, 'setCurrentIndexByName'):
            main_window.setCurrentIndexByName('Accounts')
        elif hasattr(main_window, 'stack'):
            main_window.stack.setCurrentIndex(5)  # Accounts tab index
            
    def refresh_currency_display(self):
        """Refresh all currency displays when currency symbol changes."""
        try:
            # Refresh the dashboard metrics
            self._update_metrics()
        except Exception as e:
            print(f"Error refreshing currency display in dashboard: {e}")
        
    def _apply_styling(self):
        """Apply beautiful glassmorphism styling to the dashboard."""
        # Apply glassmorphism styling (removed Mica effect as it's handled by MainWindow)
        
        # Apply main container glassmorphism effect
        GlassmorphismHelper.apply_main_container_effect(self)
        
        # Set the complete modern stylesheet
        self.setStyleSheet(ModernStyles.get_complete_stylesheet())
