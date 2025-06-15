"""
Dashboard page for the accounting application.
This module contains the main dashboard interface with financial metrics and quick actions.
"""

from ..common import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    ResponsiveHelper, Qt
)
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
        """Setup the dashboard UI."""
        # Main layout with responsive margins
        main_layout = QVBoxLayout(self)
        responsive_margin = ResponsiveHelper.scale_size(32, 24, 48)
        main_layout.setContentsMargins(responsive_margin, responsive_margin, 
                                     responsive_margin, responsive_margin)
        main_layout.setSpacing(ResponsiveHelper.scale_size(32, 24, 48))
        
        # Page header
        header = PageHeader("Dashboard", "Financial overview and quick actions")
        main_layout.addWidget(header)
          # Date range selector with ledger-style quick filters
        self.date_selector = DateRangeSelector(callback=self._on_date_range_changed)
        main_layout.addWidget(self.date_selector)
        
        # Financial metrics cards
        self._create_metrics_section(main_layout)
        
        # Quick actions section
        self._create_actions_section(main_layout)
        
        # Add stretch to push content to top
        main_layout.addStretch()
        
    def _create_metrics_section(self, main_layout):
        """Create the financial metrics cards section."""
        # Metrics grid layout
        metrics_layout = QHBoxLayout()
        metrics_layout.setSpacing(ResponsiveHelper.scale_size(20, 16, 28))
        
        # Create metric cards
        self.card_cash = MetricCard("Cash & Cash Equivalents", "0.00", "", clickable=True)
        self.card_revenue = MetricCard("Revenue", "0.00", "", clickable=True)
        self.card_expenses = MetricCard("Expenses", "0.00", "", clickable=True)
        self.card_liabilities = MetricCard("Liabilities", "0.00", "", clickable=True)
        
        # Add cards to layout
        for card in [self.card_cash, self.card_revenue, self.card_expenses, self.card_liabilities]:
            metrics_layout.addWidget(card)
            
        main_layout.addLayout(metrics_layout)
        
    def _create_actions_section(self, main_layout):
        """Create the quick actions section."""
        # Section title
        actions_title = QLabel("Quick Actions")
        actions_title.setStyleSheet(f"""
            QLabel {{
                color: white;
                font-size: {ResponsiveHelper.scale_size(20, 16, 24)}px;
                font-weight: 600;
                background: transparent;
                margin-bottom: {ResponsiveHelper.scale_size(16, 12, 20)}px;
            }}
        """)
        main_layout.addWidget(actions_title)
        
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
        main_layout.addLayout(actions_layout)
        
    def _load_data(self):
        """Load and display financial data."""
        self._update_metrics()
        
    def _update_metrics(self):
        """Update financial metrics cards with current data."""
        from_date, to_date = self.date_selector.get_date_range()
        from_date_str = from_date.toString("yyyy-MM-dd")
        to_date_str = to_date.toString("yyyy-MM-dd")
        
        # Get financial data
        cash = self._get_balance('Cash', from_date_str, to_date_str)
        liabilities = self._get_total_liabilities(from_date_str, to_date_str)
        revenue = self._get_total_revenue(from_date_str, to_date_str, abs_value=True)
        expenses = self._get_total_expenses(from_date_str, to_date_str)
        
        # Get currency symbol
        symbol = self._get_currency_symbol()
        
        # Update card values
        self.card_cash.set_value(f"{cash:,.2f}", symbol)
        self.card_revenue.set_value(f"{revenue:,.2f}", symbol)
        self.card_expenses.set_value(f"{expenses:,.2f}", symbol)
        self.card_liabilities.set_value(f"{liabilities:,.2f}", symbol)
        
        # Update trend indicators
        self._update_trend_indicators(cash, revenue, expenses, liabilities)
        
    def _update_trend_indicators(self, cash, revenue, expenses, liabilities):
        """Update trend indicators for cards."""
        # Simplified trend calculation
        if revenue > expenses:
            self.card_revenue.set_ticker("↗️ Profitable", "#4CAF50")
        else:
            self.card_revenue.set_ticker("↘️ Loss", "#F44336")
            
        if cash > 0:
            self.card_cash.set_ticker("💰 Positive", "#4CAF50")
        else:
            self.card_cash.set_ticker("⚠️ Low Cash", "#FF9800")
            
        if expenses > 0:
            expense_ratio = (expenses / revenue * 100) if revenue > 0 else 0
            if expense_ratio < 70:
                self.card_expenses.set_ticker(f"📊 {expense_ratio:.1f}% of revenue", "#4CAF50")
            else:
                self.card_expenses.set_ticker(f"📈 {expense_ratio:.1f}% of revenue", "#FF9800")
                
        if liabilities > 0:
            self.card_liabilities.set_ticker("📋 Outstanding", "#2196F3")
        else:
            self.card_liabilities.set_ticker("✅ Clear", "#4CAF50")
            
    def _get_balance(self, account_name, from_date=None, to_date=None):
        """Get balance for a specific account in date range."""
        balance = self.system.get_trial_balance(from_date, to_date)
        return balance.get(account_name, 0.0)
        
    def _get_total_liabilities(self, from_date=None, to_date=None):
        """Calculate total liabilities."""
        accounts = self.system.get_all_accounts()
        balance = self.system.get_trial_balance(from_date, to_date)
        total = 0.0
        for name, acc_type, code, parent_code, level, is_postable, description in accounts:
            if acc_type == 'Liability':
                total += balance.get(name, 0.0)
        return total
        
    def _get_total_revenue(self, from_date=None, to_date=None, abs_value=True):
        """Calculate total revenue."""
        accounts = self.system.get_all_accounts()
        balance = self.system.get_trial_balance(from_date, to_date)
        total = 0.0
        for name, acc_type, code, parent_code, level, is_postable, description in accounts:
            if acc_type in ('Revenue', 'Income'):
                val = balance.get(name, 0.0)
                total += abs(val) if abs_value else val
        return total
        
    def _get_total_expenses(self, from_date=None, to_date=None, abs_value=True):
        """Calculate total expenses."""
        accounts = self.system.get_all_accounts()
        balance = self.system.get_trial_balance(from_date, to_date)
        total = 0.0
        for name, acc_type, code, parent_code, level, is_postable, description in accounts:
            if acc_type == 'Expense':
                val = balance.get(name, 0.0)
                total += abs(val) if abs_value and val < 0 else val
        return total
        
    def _get_currency_symbol(self):
        """Get the currency symbol from the main window."""
        mw = self.window()
        return getattr(mw, 'currency_symbol', '$')
        
    def _on_date_range_changed(self):
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
        """Refresh all currency displays when currency changes."""
        self._update_metrics()
        
    def _apply_styling(self):
        """Apply beautiful glassmorphism styling to the dashboard."""        # Apply glassmorphism styling (removed Mica effect as it's handled by MainWindow)
        
        # Apply main container glassmorphism effect
        GlassmorphismHelper.apply_main_container_effect(self)
        
        # Set the complete modern stylesheet
        self.setStyleSheet(ModernStyles.get_complete_stylesheet())
