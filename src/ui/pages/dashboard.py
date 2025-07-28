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
from PyQt6.QtWidgets import QGridLayout, QComboBox
from PyQt6.QtGui import QPainter, QColor, QPen, QFont
from ..components.scrollbar_styles import ModernScrollbarStyles
from PyQt6.QtCore import QRectF, QTimer
import time
from collections import defaultdict
from datetime import datetime


class CancellableRequest:
    """A request that can be cancelled to prevent processing."""
    def __init__(self):
        self._cancelled = False
    
    def cancel(self):
        self._cancelled = True
    
    def is_cancelled(self):
        return self._cancelled


class DashboardPage(QWidget):
    """Main dashboard page with financial overview and quick actions."""
    
    def __init__(self, system, parent=None):
        super().__init__(parent)
        self.system = system
        
        # Cache data validation result to avoid repeated calls
        self._cached_has_data = None
        self._last_data_check = 0
        
        # Request management and debouncing
        self._update_timer = QTimer(self)
        self._update_timer.setSingleShot(True)
        self._update_timer.timeout.connect(self._perform_deferred_update)
        self._pending_request = None
        self._pending_dates = None
        self._context_lock = False
        
        # Validate system before proceeding
        if not self.system:
            print("⚠️ Dashboard: No system provided")
            return
        
        self._setup_ui()
        self._apply_styling()
        
        # Load data only if system is valid
        if self.system:
            self._load_data()
        

    

    
    def closeEvent(self, event):
        """Clean up resources when widget is closed."""
        super().closeEvent(event)

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
        self.date_selector = DateRangeSelector(parent=self)
        self.date_selector.dateRangeChanged.connect(self._on_date_range_changed)
        header_layout.addWidget(self.date_selector)
        
        main_layout.addWidget(header_section)
        
        # Scrollable content section
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setStyleSheet(ModernScrollbarStyles.get_vertical_scrollbar_style())
        
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
        """Create the mixed metrics layout with cards in a 4-column grid."""
        grid = QGridLayout()
        grid.setSpacing(ResponsiveHelper.scale_size(20, 16, 28))

        # Metric cards
        self.card_cash = MetricCard("Cash & Cash Equivalents", "0.00", "", clickable=True)
        self.card_net_income = MetricCard("Net Income", "0.00", "", clickable=True)
        self.card_liabilities = MetricCard("Liabilities", "0.00", "", clickable=True)
        self.card_gross_margin = MetricCard("Gross Margin", "0.00%", "", clickable=True)
        self.card_operating_margin = MetricCard("Operating Margin", "0.00%", "", clickable=True)
        self.card_receivables = MetricCard("Accounts Receivable", "0.00", "", clickable=True)
        self.card_payables = MetricCard("Accounts Payable", "0.00", "", clickable=True)
        self.card_quick_ratio = MetricCard("Quick Ratio", "0.00", "", clickable=True)
        self.card_debt_equity = MetricCard("Debt-to-Equity", "0.00", "", clickable=True)
        self.card_current_ratio = MetricCard("Current Ratio", "0.00", "", clickable=True)
        self.card_expenses = MetricCard("Expenses", "0.00", "", clickable=True)
        self.card_revenue = MetricCard("Revenue", "0.00", "", clickable=True)

        # Add cards to grid in 4-column layout
        grid.addWidget(self.card_cash, 0, 0)
        grid.addWidget(self.card_net_income, 0, 1)
        grid.addWidget(self.card_liabilities, 0, 2)
        grid.addWidget(self.card_gross_margin, 0, 3)
        grid.addWidget(self.card_operating_margin, 1, 0)
        grid.addWidget(self.card_receivables, 1, 1)
        grid.addWidget(self.card_payables, 1, 2)
        grid.addWidget(self.card_quick_ratio, 1, 3)
        grid.addWidget(self.card_debt_equity, 2, 0)
        grid.addWidget(self.card_current_ratio, 2, 1)
        grid.addWidget(self.card_expenses, 2, 2)
        grid.addWidget(self.card_revenue, 2, 3)

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
        
        # Actions layout - use grid to occupy full width
        actions_layout = QGridLayout()
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
        
        settings_card = ActionCard(
            "Settings",
            "Configure application preferences and system settings",
            accent_color="#9C27B0"
        )
        settings_card.clicked = self._open_settings_tab
        
        # Add action cards to grid (4 columns)
        actions_layout.addWidget(add_entry_card, 0, 0)
        actions_layout.addWidget(view_reports_card, 0, 1)
        actions_layout.addWidget(manage_accounts_card, 0, 2)
        actions_layout.addWidget(settings_card, 0, 3)
        
        # Set equal stretch for all columns so they occupy full width
        for col in range(4):
            actions_layout.setColumnStretch(col, 1)
            
        content_layout.addLayout(actions_layout)
        


    def _load_data(self):
        """Load dashboard data with progressive loading."""
        try:
            # Validate system is ready
            if not self.system:
                print("⚠️ System not ready for data loading")
                return
            
            # Show loading state immediately
            self._show_loading_state()
            
            # Load data asynchronously to prevent UI blocking
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(100, self._perform_initial_load)
            
        except Exception as e:
            print(f"❌ Error loading dashboard data: {e}")
            self._show_error_state("Failed to initialize")
    
    def _perform_initial_load(self):
        """Perform the initial data load asynchronously."""
        try:
            self._update_metrics()
        except Exception as e:
            print(f"❌ Error in initial load: {e}")
            self._show_error_state("Failed to load initial data")
    

    
    def _update_metrics(self):
        """Update financial metrics cards with current data using group-based reporting."""
        # Create a non-cancellable request for legacy compatibility
        request = CancellableRequest()
        self._update_metrics_with_cancellation(request)
    
    def _update_metrics_with_cancellation(self, request):
        """Update financial metrics cards with cancellation support."""
        try:
            # Check if request was cancelled before starting
            if request.is_cancelled():
                print("🚫 Update cancelled before starting")
                return
            
            # Validate system and date selector
            if not self.system or not hasattr(self, 'date_selector') or not self.date_selector:
                print("⚠️ System or date selector not available")
                return
            
            # Get date range with validation
            try:
                from_date, to_date = self.date_selector.get_date_range()
                if from_date is None or to_date is None:
                    print("⚠️ Invalid date range received")
                    return
                from_date_str = from_date.toString("yyyy-MM-dd")
                to_date_str = to_date.toString("yyyy-MM-dd")
            except Exception as e:
                print(f"❌ Error getting date range: {e}")
                return
            
            # Check cancellation after each major operation
            if request.is_cancelled():
                print("🚫 Update cancelled after date validation")
                return
            
            # Get all dashboard data in a single consolidated call
            dashboard_data = self._get_consolidated_dashboard_data_with_cancellation(from_date_str, to_date_str, to_date_str, request)
            if request.is_cancelled():
                return
            
            if not dashboard_data:
                print("⚠️ No dashboard data received")
                self._show_empty_state()
                return
            
            # Extract data from consolidated response
            balance_sheet = dashboard_data.get('balance_sheet', {})
            income_statement = dashboard_data.get('income_statement', {})
            ratios_data = dashboard_data.get('ratios', {})
            
            # Extract financial metrics
            cash = self._extract_cash_from_balance_sheet(balance_sheet)
            liabilities = balance_sheet.get('total_liabilities', 0)
            revenue = income_statement.get('total_revenue', 0)
            expenses = income_statement.get('total_expenses', 0)
            
            # Calculate derived metrics
            net_income = revenue - expenses
            
            # Extract accounts receivable and payable
            receivables = self._extract_receivables_from_balance_sheet(balance_sheet)
            payables = self._extract_payables_from_balance_sheet(balance_sheet)
            
            if request.is_cancelled():
                return
            
            # Update all card values using consolidated data
            self.card_cash.set_value(format_currency(cash))
            self.card_net_income.set_value(format_currency(net_income))
            self.card_liabilities.set_value(format_currency(liabilities))
            self.card_revenue.set_value(format_currency(revenue))
            self.card_expenses.set_value(format_currency(expenses))
            self.card_receivables.set_value(format_currency(receivables))
            self.card_payables.set_value(format_currency(payables))
            
            # Update ratios from consolidated data
            self._update_ratios_from_consolidated_data(ratios_data)
            
            # Update trend indicators
            self._update_trend_indicators(cash, revenue, expenses, liabilities, net_income)
            
            print("✅ Dashboard metrics updated successfully")
            
        except Exception as e:
            print(f"❌ Error updating metrics: {e}")
            # Show error state instead of empty state
            self._show_error_state("Failed to load data")
        
    def _update_ratio_metrics_from_db(self, from_date, to_date, as_of_date):
        """Update ratio metrics using database function."""
        try:
            # Validate system and database manager
            if not self.system or not hasattr(self.system, 'db_manager') or not self.system.db_manager:
                print("⚠️ System or database manager not available")
                self._set_default_ratios()
                return
            
            # Call database function to get all ratios
            print(f"🔍 Getting ratios from database for period: {from_date} to {to_date}, as of: {as_of_date}")
            
            # Use the database function directly
            result = self.system.db_manager.supabase.rpc(
                'calculate_all_ratios',
                {
                    'p_org_id': self.system.current_organization_id,
                    'p_from_date': from_date,
                    'p_to_date': to_date,
                    'p_as_of_date': as_of_date
                }
            ).execute()
            
            if not result.data:
                print("⚠️ No ratio data returned from database")
                self._set_default_ratios()
                return
            
            ratio_data = result.data[0] if isinstance(result.data, list) else result.data
            print(f"✅ Database ratio calculation successful")
            
            # Extract ratios from the database response
            ratios = ratio_data.get('ratios', {})
            
            # Update Quick Ratio
            liquidity_ratios = ratios.get('liquidity', {})
            quick_ratio_data = liquidity_ratios.get('quick_ratio', {})
            if quick_ratio_data:
                quick_ratio_value = quick_ratio_data.get('value', 0)
                self.card_quick_ratio.set_value(f"{quick_ratio_value:.2f}")
                print(f"✅ Quick ratio updated: {quick_ratio_value:.2f}")
            else:
                self.card_quick_ratio.set_value("0.00")
            
            # Update Current Ratio
            current_ratio_data = liquidity_ratios.get('current_ratio', {})
            if current_ratio_data:
                current_ratio_value = current_ratio_data.get('value', 0)
                self.card_current_ratio.set_value(f"{current_ratio_value:.2f}")
                print(f"✅ Current ratio updated: {current_ratio_value:.2f}")
            else:
                self.card_current_ratio.set_value("0.00")
            
            # Update Debt-to-Equity Ratio
            leverage_ratios = ratios.get('leverage', {})
            debt_equity_data = leverage_ratios.get('debt_to_equity', {})
            if debt_equity_data:
                debt_equity_value = debt_equity_data.get('value', 0)
                self.card_debt_equity.set_value(f"{debt_equity_value:.2f}")
                print(f"✅ Debt-to-equity ratio updated: {debt_equity_value:.2f}")
            else:
                self.card_debt_equity.set_value("0.00")
            
            # Update Profitability Ratios
            profitability_ratios = ratios.get('profitability', {})
            
            # Update Gross Margin
            gross_margin_data = profitability_ratios.get('gross_profit_margin', {})
            if gross_margin_data:
                gross_margin_value = gross_margin_data.get('value', 0)
                self.card_gross_margin.set_value(f"{gross_margin_value:.1f}%")
                print(f"✅ Gross margin updated: {gross_margin_value:.1f}%")
            else:
                self.card_gross_margin.set_value("0.00%")
            
            # Update Operating Margin (using net profit margin)
            net_margin_data = profitability_ratios.get('net_profit_margin', {})
            if net_margin_data:
                net_margin_value = net_margin_data.get('value', 0)
                self.card_operating_margin.set_value(f"{net_margin_value:.1f}%")
                print(f"✅ Operating margin updated: {net_margin_value:.1f}%")
            else:
                self.card_operating_margin.set_value("0.00%")
            
        except Exception as e:
            print(f"❌ Error updating ratio metrics from database: {e}")
            self._set_default_ratios()
    
    def _set_default_ratios(self):
        """Set default values for ratio cards."""
        self.card_quick_ratio.set_value("0.00")
        self.card_debt_equity.set_value("0.00")
        self.card_current_ratio.set_value("0.00")
        self.card_gross_margin.set_value("0.00%")
        self.card_operating_margin.set_value("0.00%")
            
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
            
    def _calculate_running_balance_from_ledger(self, ledger_entries, account_name):
        """Calculate running balance from ledger entries."""
        running_balance = 0.0
        daily_balances = {}
        
        for entry in ledger_entries:
            date, description, debit_account, credit_account, amount = entry
            
            # Determine if this is a debit or credit to our account
            is_debit = (debit_account == account_name or 
                      (debit_account and account_name in debit_account))
            is_credit = (credit_account == account_name or 
                       (credit_account and account_name in credit_account))
            
            if is_debit:
                running_balance += amount
            elif is_credit:
                running_balance -= amount
            
            # Store balance for this date
            daily_balances[date] = running_balance
        
        return daily_balances
    
    def _get_parent_account_balance(self, account_data, as_of_date):
        """Get parent account balance using hierarchical aggregation (same as ledger cards)."""
        try:
            # Use hierarchical account balances (same method as ledger cards)
            hierarchical_balances = self.system.get_hierarchical_account_balances(None, as_of_date)
            
            # Find the account in the hierarchical balances
            account_name = account_data['name']
            balance_info = hierarchical_balances.get(account_name, {})
            
            # Return the net balance (aggregated from children)
            net_balance = balance_info.get('net_balance', 0.0)
            
            # For parent accounts, we want the absolute value for display
            return abs(net_balance)
            
        except Exception as e:
            print(f"❌ Error getting parent account balance for {account_data['name']}: {e}")
            return 0.0
    
    def _get_cash_balance(self, from_date=None, to_date=None):
        """Get cash balance using group-based reporting."""
        try:
            # Validate system
            if not self.system:
                return 0.0
            
            # Get balance sheet data as of the end date
            if to_date:
                balance_sheet = self.system.generate_group_based_balance_sheet(to_date)
                if not balance_sheet:
                    return 0.0
                
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
            # Validate system
            if not self.system:
                return 0.0
            
            balance_sheet = self.system.generate_group_based_balance_sheet(as_of_date)
            if not balance_sheet:
                return 0.0
            
            return balance_sheet.get('total_liabilities', 0)
        except Exception as e:
            print(f"Error getting total liabilities: {e}")
            return 0.0
        
    def _get_total_revenue_group_based(self, from_date=None, to_date=None):
        """Get total revenue using group-based income statement."""
        try:
            # Validate system
            if not self.system:
                return 0.0
            
            income_statement = self.system.generate_group_based_income_statement(from_date, to_date)
            if not income_statement:
                return 0.0
            
            return income_statement.get('total_revenue', 0)
        except Exception as e:
            print(f"Error getting total revenue: {e}")
            return 0.0
        
    def _get_total_expenses_group_based(self, from_date=None, to_date=None):
        """Get total expenses using group-based income statement."""
        try:
            # Validate system
            if not self.system:
                return 0.0
            
            income_statement = self.system.generate_group_based_income_statement(from_date, to_date)
            if not income_statement:
                return 0.0
            
            total_cogs = income_statement.get('total_cogs', 0)
            total_operating_expenses = income_statement.get('total_operating_expenses', 0)
            return total_cogs + total_operating_expenses
        except Exception as e:
            print(f"Error getting total expenses: {e}")
            return 0.0
    
    def _get_cogs(self, from_date=None, to_date=None):
        """Get cost of goods sold using group-based income statement."""
        try:
            # Validate system
            if not self.system:
                return 0.0
            
            income_statement = self.system.generate_group_based_income_statement(from_date, to_date)
            if not income_statement:
                return 0.0
            
            return income_statement.get('total_cogs', 0)
        except Exception as e:
            print(f"Error getting COGS: {e}")
            return 0.0
            
    def _get_accounts_receivable(self, as_of_date=None):
        """Get accounts receivable using group-based balance sheet."""
        try:
            # Validate system
            if not self.system:
                return 0.0
            
            balance_sheet = self.system.generate_group_based_balance_sheet(as_of_date)
            if not balance_sheet:
                return 0.0
            
            # Look for current assets section which includes receivables
            for section in balance_sheet.get('asset_sections', []):
                if section.get('group') == 'current_asset':
                    # Extract receivables from current assets
                    receivable_accounts = ['receivable', 'ar', 'accounts receivable', 'trade receivable']
                    receivable_total = 0.0
                    for account in section.get('accounts', []):
                        account_name = account.get('name', '').lower()
                        if any(receivable_type in account_name for receivable_type in receivable_accounts):
                            receivable_total += abs(account.get('balance', 0))
                        # Also check children recursively
                        receivable_total += self._extract_receivables_from_account_tree(account)
                    return receivable_total
            return 0.0
        except Exception as e:
            print(f"Error getting accounts receivable: {e}")
            return 0.0
            
    def _get_accounts_payable(self, as_of_date=None):
        """Get accounts payable using group-based balance sheet."""
        try:
            # Validate system
            if not self.system:
                return 0.0
            
            balance_sheet = self.system.generate_group_based_balance_sheet(as_of_date)
            if not balance_sheet:
                return 0.0
            
            # Look for current liabilities section which includes payables
            for section in balance_sheet.get('liability_sections', []):
                if section.get('group') == 'current_liability':
                    # Extract payables from current liabilities
                    payable_accounts = ['payable', 'ap', 'accounts payable', 'trade payable']
                    payable_total = 0.0
                    for account in section.get('accounts', []):
                        account_name = account.get('name', '').lower()
                        if any(payable_type in account_name for payable_type in payable_accounts):
                            payable_total += abs(account.get('balance', 0))
                        # Also check children recursively
                        payable_total += self._extract_payables_from_account_tree(account)
                    return payable_total
            return 0.0
        except Exception as e:
            print(f"Error getting accounts payable: {e}")
            return 0.0
            
    def _extract_receivables_from_account_tree(self, account):
        """Extract receivables from account tree recursively."""
        receivable_total = 0.0
        receivable_accounts = ['receivable', 'ar', 'accounts receivable', 'trade receivable']
        
        # Check if this account is a receivable
        account_name = account.get('name', '').lower()
        if any(receivable_type in account_name for receivable_type in receivable_accounts):
            receivable_total += abs(account.get('balance', 0))
        
        # Check children recursively
        for child in account.get('children', []):
            receivable_total += self._extract_receivables_from_account_tree(child)
            
        return receivable_total
        
    def _extract_payables_from_account_tree(self, account):
        """Extract payables from account tree recursively."""
        payable_total = 0.0
        payable_accounts = ['payable', 'ap', 'accounts payable', 'trade payable']
        
        # Check if this account is a payable
        account_name = account.get('name', '').lower()
        if any(payable_type in account_name for payable_type in payable_accounts):
            payable_total += abs(account.get('balance', 0))
        
        # Check children recursively
        for child in account.get('children', []):
            payable_total += self._extract_payables_from_account_tree(child)
            
        return payable_total
        
    def _get_currency_symbol(self):
        """Get the currency symbol from the main window."""
        mw = self.window()
        return getattr(mw, 'currency_symbol', '$')
        
    def _on_date_range_changed(self, start_date, end_date):
        """Handle date range selection changes with debouncing."""
        try:
            # Validate parameters
            if start_date is None or end_date is None:
                print("⚠️ Invalid date range received")
                return
            
            # Validate system is ready
            if not self.system:
                print("⚠️ System not ready for date range update")
                return
            
            # Check if we're in the middle of context switching
            if self._context_lock:
                print("⚠️ Context changing, ignoring date change")
                return
            
            # Protect against widget destruction
            if not self._is_widget_valid():
                print("⚠️ Widget being destroyed, ignoring date change")
                return
            
            # Cancel any pending requests
            if self._pending_request:
                self._pending_request.cancel()
                print("🚫 Cancelled previous request")
            
            # Store the date range for deferred processing
            self._pending_dates = (start_date, end_date)
            
            # Start/restart the debounce timer
            self._update_timer.stop()
            self._update_timer.start(500)  # 500ms debounce
            
            print(f"📅 Date range change queued: {start_date.toString('yyyy-MM-dd')} to {end_date.toString('yyyy-MM-dd')}")
            
        except Exception as e:
            print(f"❌ Error in date range changed handler: {e}")
    
    def _perform_deferred_update(self):
        """Perform the actual update after debouncing period."""
        try:
            # Check if widget is still valid
            if not self._is_widget_valid():
                print("⚠️ Widget destroyed during debounce, skipping update")
                return
            
            # Check if we have pending dates
            if not self._pending_dates:
                print("⚠️ No pending dates for update")
                return
            
            start_date, end_date = self._pending_dates
            
            # Create a new cancellable request
            request = CancellableRequest()
            self._pending_request = request
            
            print(f"🔄 Performing deferred update: {start_date.toString('yyyy-MM-dd')} to {end_date.toString('yyyy-MM-dd')}")
            
            # Show loading state
            self._show_loading_state()
            
            # Perform the actual update
            self._update_metrics_with_cancellation(request)
            
            # Hide loading state
            self._hide_loading_state()
            
        except Exception as e:
            print(f"❌ Error in deferred update: {e}")
            # Show error state on failure
            self._show_error_state("Update failed")
        finally:
            # Always hide loading state and clear pending request
            self._hide_loading_state()
            self._pending_request = None
            self._pending_dates = None
    
    def _is_widget_valid(self):
        """Check if the widget is still valid and not being destroyed."""
        try:
            # Check if widget is visible and has a parent
            if not self.isVisible() or self.parent() is None:
                return False
            
            # Try to access object name (will throw if being destroyed)
            self.objectName()
            return True
        except RuntimeError:
            return False
    
    def _show_empty_state(self):
        """Show appropriate empty state when no data is available."""
        # Set all metrics to zero
        self.card_cash.set_value("0.00")
        self.card_net_income.set_value("0.00")
        self.card_liabilities.set_value("0.00")
        self.card_gross_margin.set_value("0.00%")
        self.card_operating_margin.set_value("0.00%")
        self.card_receivables.set_value("0.00")
        self.card_payables.set_value("0.00")
        self.card_quick_ratio.set_value("0.00")
        self.card_debt_equity.set_value("0.00")
        self.card_current_ratio.set_value("0.00")
        self.card_expenses.set_value("0.00")
        self.card_revenue.set_value("0.00")
        
        print("📊 Dashboard: Showing empty state - no data available")
    
    def _open_journal_entry_dialog(self):
        """Switch to the journal tab to add a new entry."""
        main_window = self.window()
        if main_window and hasattr(main_window, 'setCurrentIndexByName'):
            main_window.setCurrentIndexByName('Journal')
            
    def _open_reports_tab(self):
        """Open the reports tab."""
        main_window = self.window()
        if main_window and hasattr(main_window, 'setCurrentIndexByName'):
            main_window.setCurrentIndexByName('Reports')
            
    def _open_accounts_tab(self):
        """Open the accounts tab."""
        main_window = self.window()
        if main_window and hasattr(main_window, 'setCurrentIndexByName'):
            main_window.setCurrentIndexByName('Accounts')
            
    def _open_settings_tab(self):
        """Open the settings tab."""
        main_window = self.window()
        if main_window and hasattr(main_window, 'setCurrentIndexByName'):
            main_window.setCurrentIndexByName('Settings')
            
    def refresh_data(self):
        """Refresh dashboard data when organization context changes."""
        try:
            print("🔄 Dashboard: Refreshing data due to organization change...")
            
            # Validate system is ready
            if not self.system:
                print("⚠️ System not ready for refresh")
                return
            
            self._load_data()
            
            # Force refresh with new organization data
            if hasattr(self, 'date_selector') and self.date_selector:
                try:
                    from_date, to_date = self.date_selector.get_date_range()
                    if from_date and to_date:
                        print(f"   Date range: {from_date.toString('yyyy-MM-dd')} to {to_date.toString('yyyy-MM-dd')}")
                        print("   ✅ Dashboard refreshed with new organization context")
                    else:
                        print("   ⚠️ Invalid date range, skipping updates")
                except Exception as e:
                    print(f"   ⚠️ Error getting date range: {e}")
            else:
                print("   ⚠️ Date selector not available")
                
        except Exception as e:
            print(f"❌ Error refreshing dashboard data: {e}")
    
    def refresh_organization_context(self, new_system):
        """Update the system reference when organization changes."""
        try:
            print(f"🔄 Dashboard: Updating system reference for new organization...")
            
            # Lock context to prevent date changes during update
            self._context_lock = True
            
            # Cancel any pending requests
            if self._pending_request:
                self._pending_request.cancel()
                print("🚫 Cancelled pending request due to organization change")
            
            # Stop any pending timers
            if hasattr(self, '_update_timer'):
                self._update_timer.stop()
            
            # Clear cache since organization changed
            self._clear_cache()
            
            # Validate new system
            if not new_system:
                print("⚠️ Invalid system provided for organization context update")
                return
            
            self.system = new_system
            self._load_data()
            print("   ✅ Dashboard system reference updated")
            
        except Exception as e:
            print(f"❌ Error updating dashboard system reference: {e}")
        finally:
            # Always unlock context
            self._context_lock = False
        
    def _apply_styling(self):
        """Apply beautiful glassmorphism styling to the dashboard."""
        # Apply main container glassmorphism effect
        GlassmorphismHelper.apply_main_container_effect(self)
        
        # Set the complete modern stylesheet
        self.setStyleSheet(ModernStyles.get_complete_stylesheet())

    def _check_has_data(self):
        """Check if organization has data with caching to reduce repeated calls."""
        current_time = time.time()
        
        # Only check every 10 seconds to avoid excessive calls
        if (self._cached_has_data is None or 
            current_time - self._last_data_check > 10):
            
            if hasattr(self.system, 'data_validator'):
                self._cached_has_data = self.system.data_validator.has_any_data()
                self._last_data_check = current_time
            else:
                self._cached_has_data = True  # Assume data exists if no validator
        
        return self._cached_has_data

    def _get_cash_balance_with_cancellation(self, from_date=None, to_date=None, request=None):
        """Get cash balance using group-based reporting with cancellation support."""
        if request and request.is_cancelled():
            return 0.0
        return self._get_cash_balance(from_date, to_date)
    
    def _get_total_liabilities_group_based_with_cancellation(self, as_of_date=None, request=None):
        """Get total liabilities using group-based balance sheet with cancellation support."""
        if request and request.is_cancelled():
            return 0.0
        return self._get_total_liabilities_group_based(as_of_date)
    
    def _get_total_revenue_group_based_with_cancellation(self, from_date=None, to_date=None, request=None):
        """Get total revenue using group-based income statement with cancellation support."""
        if request and request.is_cancelled():
            return 0.0
        return self._get_total_revenue_group_based(from_date, to_date)
    
    def _get_total_expenses_group_based_with_cancellation(self, from_date=None, to_date=None, request=None):
        """Get total expenses using group-based income statement with cancellation support."""
        if request and request.is_cancelled():
            return 0.0
        return self._get_total_expenses_group_based(from_date, to_date)
    
    def _get_accounts_receivable_with_cancellation(self, as_of_date=None, request=None):
        """Get accounts receivable using group-based balance sheet with cancellation support."""
        if request and request.is_cancelled():
            return 0.0
        return self._get_accounts_receivable(as_of_date)
    
    def _get_accounts_payable_with_cancellation(self, as_of_date=None, request=None):
        """Get accounts payable using group-based balance sheet with cancellation support."""
        if request and request.is_cancelled():
            return 0.0
        return self._get_accounts_payable(as_of_date)
    
    def _update_ratio_metrics_from_db_with_cancellation(self, from_date, to_date, as_of_date, request):
        """Update ratio metrics using database function with cancellation support."""
        if request and request.is_cancelled():
            self._set_default_ratios()
            return
        self._update_ratio_metrics_from_db(from_date, to_date, as_of_date)

    def _get_consolidated_dashboard_data_with_cancellation(self, from_date, to_date, as_of_date, request):
        """Get all dashboard data in a single consolidated database call with caching and retry logic."""
        # Check cache first
        cached_data = self._get_cached_data(from_date, to_date, as_of_date)
        if cached_data:
            return cached_data
        
        max_retries = 3
        retry_delay = 1.0  # seconds
        
        for attempt in range(max_retries):
            try:
                if request and request.is_cancelled():
                    return None
                
                # Validate system and database manager
                if not self.system or not hasattr(self.system, 'db_manager') or not self.system.db_manager:
                    print("⚠️ System or database manager not available")
                    return None
                
                # Use shared database client for better performance
                from ...core.shared_database_manager import get_shared_client
                client = get_shared_client()
                
                if attempt > 0:
                    print(f"🔄 Retry attempt {attempt + 1}/{max_retries} for consolidated dashboard data")
                else:
                    print(f"🔍 Getting consolidated dashboard data for period: {from_date} to {to_date}, as of: {as_of_date}")
                
                # Single RPC call to get all dashboard data
                result = client.rpc(
                    'get_dashboard_data',
                    {
                        'p_org_id': self.system.current_organization_id,
                        'p_from_date': from_date,
                        'p_to_date': to_date,
                        'p_as_of_date': as_of_date
                    }
                ).execute()
                
                if not result.data:
                    print("⚠️ No consolidated data returned from database")
                    if attempt < max_retries - 1:
                        print(f"⏳ Waiting {retry_delay}s before retry...")
                        import time
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                        continue
                    return None
                
                dashboard_data = result.data[0] if isinstance(result.data, list) else result.data
                if attempt > 0:
                    print(f"✅ Consolidated dashboard data retrieved successfully on retry {attempt + 1}")
                else:
                    print(f"✅ Consolidated dashboard data retrieved successfully")
                
                # Cache the successful result
                self._cache_data(from_date, to_date, as_of_date, dashboard_data)
                
                return dashboard_data
                
            except Exception as e:
                print(f"❌ Error getting consolidated dashboard data (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    print(f"⏳ Waiting {retry_delay}s before retry...")
                    import time
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    print(f"❌ All {max_retries} attempts failed")
                    return None
    
    def _extract_cash_from_balance_sheet(self, balance_sheet):
        """Extract cash balance from balance sheet data."""
        try:
            accounts = balance_sheet.get('accounts', [])
            cash_total = 0.0
            
            for account in accounts:
                if account.get('account_type') == 'asset':
                    account_name = account.get('name', '').lower()
                    cash_keywords = ['cash', 'bank', 'checking', 'savings', 'petty cash']
                    if any(keyword in account_name for keyword in cash_keywords):
                        cash_total += abs(account.get('balance', 0))
            
            return cash_total
        except Exception as e:
            print(f"❌ Error extracting cash from balance sheet: {e}")
            return 0.0
    
    def _extract_receivables_from_balance_sheet(self, balance_sheet):
        """Extract accounts receivable from balance sheet data."""
        try:
            accounts = balance_sheet.get('accounts', [])
            receivables_total = 0.0
            
            for account in accounts:
                if account.get('account_type') == 'asset':
                    account_name = account.get('name', '').lower()
                    receivable_keywords = ['receivable', 'ar', 'accounts receivable', 'trade receivable']
                    if any(keyword in account_name for keyword in receivable_keywords):
                        receivables_total += abs(account.get('balance', 0))
            
            return receivables_total
        except Exception as e:
            print(f"❌ Error extracting receivables from balance sheet: {e}")
            return 0.0
    
    def _extract_payables_from_balance_sheet(self, balance_sheet):
        """Extract accounts payable from balance sheet data."""
        try:
            accounts = balance_sheet.get('accounts', [])
            payables_total = 0.0
            
            for account in accounts:
                if account.get('account_type') == 'liability':
                    account_name = account.get('name', '').lower()
                    payable_keywords = ['payable', 'ap', 'accounts payable', 'trade payable']
                    if any(keyword in account_name for keyword in payable_keywords):
                        payables_total += abs(account.get('balance', 0))
            
            return payables_total
        except Exception as e:
            print(f"❌ Error extracting payables from balance sheet: {e}")
            return 0.0
    
    def _update_ratios_from_consolidated_data(self, ratios_data):
        """Update ratio metrics from consolidated ratios data."""
        try:
            ratios = ratios_data.get('ratios', {})
            
            # Update Quick Ratio
            liquidity_ratios = ratios.get('liquidity', {})
            quick_ratio_data = liquidity_ratios.get('quick_ratio', {})
            if quick_ratio_data:
                quick_ratio_value = quick_ratio_data.get('value', 0)
                self.card_quick_ratio.set_value(f"{quick_ratio_value:.2f}")
            else:
                self.card_quick_ratio.set_value("0.00")
            
            # Update Current Ratio
            current_ratio_data = liquidity_ratios.get('current_ratio', {})
            if current_ratio_data:
                current_ratio_value = current_ratio_data.get('value', 0)
                self.card_current_ratio.set_value(f"{current_ratio_value:.2f}")
            else:
                self.card_current_ratio.set_value("0.00")
            
            # Update Debt-to-Equity Ratio
            leverage_ratios = ratios.get('leverage', {})
            debt_equity_data = leverage_ratios.get('debt_to_equity', {})
            if debt_equity_data:
                debt_equity_value = debt_equity_data.get('value', 0)
                self.card_debt_equity.set_value(f"{debt_equity_value:.2f}")
            else:
                self.card_debt_equity.set_value("0.00")
            
            # Update Profitability Ratios
            profitability_ratios = ratios.get('profitability', {})
            
            # Update Gross Margin
            gross_margin_data = profitability_ratios.get('gross_profit_margin', {})
            if gross_margin_data:
                gross_margin_value = gross_margin_data.get('value', 0)
                self.card_gross_margin.set_value(f"{gross_margin_value:.1f}%")
            else:
                self.card_gross_margin.set_value("0.00%")
            
            # Update Operating Margin (using net profit margin)
            net_margin_data = profitability_ratios.get('net_profit_margin', {})
            if net_margin_data:
                net_margin_value = net_margin_data.get('value', 0)
                self.card_operating_margin.set_value(f"{net_margin_value:.1f}%")
            else:
                self.card_operating_margin.set_value("0.00%")
                
            print("✅ Ratios updated from consolidated data")
            
        except Exception as e:
            print(f"❌ Error updating ratios from consolidated data: {e}")
            self._set_default_ratios()

    def _show_loading_state(self):
        """Show loading indicators on metric cards."""
        try:
            # Set loading text on all cards
            loading_cards = [
                self.card_cash, self.card_net_income, self.card_liabilities,
                self.card_revenue, self.card_expenses, self.card_receivables,
                self.card_payables, self.card_quick_ratio, self.card_debt_equity,
                self.card_current_ratio, self.card_gross_margin, self.card_operating_margin
            ]
            
            for card in loading_cards:
                card.set_value("⏳", "")
                card.set_subtitle("Loading...")
            
        except Exception as e:
            print(f"❌ Error showing loading state: {e}")
    
    def _hide_loading_state(self):
        """Hide loading indicators (cards will be updated with real data)."""
        try:
            # Clear loading subtitles
            loading_cards = [
                self.card_cash, self.card_net_income, self.card_liabilities,
                self.card_revenue, self.card_expenses, self.card_receivables,
                self.card_payables, self.card_quick_ratio, self.card_debt_equity,
                self.card_current_ratio, self.card_gross_margin, self.card_operating_margin
            ]
            
            for card in loading_cards:
                card.set_subtitle("")
            
        except Exception as e:
            print(f"❌ Error hiding loading state: {e}")
    
    def _show_error_state(self, error_message="Error loading data"):
        """Show error state on metric cards."""
        try:
            # Set error indicators on all cards
            error_cards = [
                self.card_cash, self.card_net_income, self.card_liabilities,
                self.card_revenue, self.card_expenses, self.card_receivables,
                self.card_payables, self.card_quick_ratio, self.card_debt_equity,
                self.card_current_ratio, self.card_gross_margin, self.card_operating_margin
            ]
            
            for card in error_cards:
                card.set_value("❌", "")
                card.set_subtitle(error_message)
            
        except Exception as e:
            print(f"❌ Error showing error state: {e}")

    def _get_cache_key(self, from_date, to_date, as_of_date):
        """Generate cache key for dashboard data."""
        org_id = self.system.current_organization_id if self.system else "default"
        return f"dashboard_{org_id}_{from_date}_{to_date}_{as_of_date}"
    
    def _get_cached_data(self, from_date, to_date, as_of_date):
        """Get cached dashboard data if available and not expired."""
        try:
            cache_key = self._get_cache_key(from_date, to_date, as_of_date)
            
            # Check if we have cached data
            if hasattr(self, '_data_cache') and cache_key in self._data_cache:
                cached_entry = self._data_cache[cache_key]
                
                # Check if cache is still valid (5 minutes)
                import time
                if time.time() - cached_entry['timestamp'] < 300:  # 5 minutes
                    print(f"✅ Using cached dashboard data")
                    return cached_entry['data']
                else:
                    # Remove expired cache
                    del self._data_cache[cache_key]
                    print(f"🗑️ Removed expired cache entry")
            
            return None
            
        except Exception as e:
            print(f"❌ Error getting cached data: {e}")
            return None
    
    def _cache_data(self, from_date, to_date, as_of_date, data):
        """Cache dashboard data for future use."""
        try:
            if not data:
                return
            
            # Initialize cache if needed
            if not hasattr(self, '_data_cache'):
                self._data_cache = {}
            
            cache_key = self._get_cache_key(from_date, to_date, as_of_date)
            
            # Store data with timestamp
            import time
            self._data_cache[cache_key] = {
                'data': data,
                'timestamp': time.time()
            }
            
            # Limit cache size (keep only last 10 entries)
            if len(self._data_cache) > 10:
                # Remove oldest entry
                oldest_key = min(self._data_cache.keys(), 
                               key=lambda k: self._data_cache[k]['timestamp'])
                del self._data_cache[oldest_key]
                print(f"🗑️ Removed oldest cache entry to maintain size limit")
            
            print(f"💾 Cached dashboard data")
            
        except Exception as e:
            print(f"❌ Error caching data: {e}")
    
    def _clear_cache(self):
        """Clear all cached dashboard data."""
        try:
            if hasattr(self, '_data_cache'):
                self._data_cache.clear()
                print(f"🗑️ Dashboard cache cleared")
        except Exception as e:
            print(f"❌ Error clearing cache: {e}")
