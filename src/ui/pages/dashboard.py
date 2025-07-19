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


class DashboardPage(QWidget):
    """Main dashboard page with financial overview and quick actions."""
    
    def __init__(self, system, parent=None):
        super().__init__(parent)
        self.system = system
        
        # Cache data validation result to avoid repeated calls
        self._cached_has_data = None
        self._last_data_check = 0
        
        # Track if widget is being destroyed
        self._is_destroying = False
        
        # Debounce timer for date range changes
        self._debounce_timer = QTimer(self)  # Set parent to self for auto-deletion
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.timeout.connect(self._debounced_date_range_update)
        
        self._setup_ui()
        self._apply_styling()
        self._load_data()
        
        # Final safety check
        self._validate_initialization()
    
    def _validate_initialization(self):
        """Validate that all critical components are properly initialized."""
        try:
            critical_components = [
                'date_selector'
            ]
            
            missing_components = []
            for component in critical_components:
                if not hasattr(self, component):
                    missing_components.append(component)
                elif not self._is_widget_valid(component):
                    missing_components.append(f"{component} (invalid)")
            
            if missing_components:
                print(f"⚠️ Dashboard initialization warning - missing/invalid components: {missing_components}")
            else:
                print("✅ Dashboard initialization completed successfully")
                
        except Exception as e:
            print(f"❌ Error during dashboard initialization validation: {e}")
    
    def closeEvent(self, event):
        """Clean up resources when widget is closed."""
        self._cleanup_resources()
        super().closeEvent(event)
    
    def _disconnect_signals(self):
        """Disconnect all signals safely."""
        signals_to_disconnect = [
            (self.date_selector, 'dateRangeChanged')
        ]
        
        for widget, signal_name in signals_to_disconnect:
            if hasattr(widget, signal_name):
                try:
                    getattr(widget, signal_name).disconnect()
                except:
                    pass
    
    def _cleanup_resources(self):
        """Clean up all resources to prevent memory leaks and crashes."""
        try:
            self._is_destroying = True
            
            # Disconnect all signals to prevent callbacks after destruction
            self._disconnect_signals()
            
            try:
                if hasattr(self, '_debounce_timer') and self._debounce_timer:
                    self._debounce_timer.timeout.disconnect()
                    self._debounce_timer.stop()
            except:
                pass
            
            print("✅ Dashboard resources cleaned up")
            
        except Exception as e:
            print(f"⚠️ Error during dashboard cleanup: {e}")
    
    def _is_widget_valid(self, widget_name):
        """Check if a widget exists and is valid."""
        if self._is_destroying:
            return False
        
        widget = getattr(self, widget_name, None)
        if widget is None:
            return False
        
        try:
            # Special handling for DateRangeSelector
            if widget_name == 'date_selector' and hasattr(widget, 'is_valid'):
                return widget.is_valid()
            
            # Test if widget is still valid
            widget.objectName()
            return True
        except:
            return False

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
        
    def _setup_default_accounts(self):
        """Set up default Revenue and Expense accounts for comparison."""
        try:
            # Check if widget is still valid
            if self._is_destroying:
                print("⚠️ Dashboard is being destroyed, skipping default account setup")
                return
            
            # Check if combo boxes are valid
            if not self._is_widget_valid('account1_combo') or not self._is_widget_valid('account2_combo'):
                print("⚠️ Account combo boxes are invalid, skipping default account setup")
                return
            
            accounts = self.system.get_chart_of_accounts(active_only=True)
            
            # Find default accounts
            revenue_account = None
            expense_account = None
            
            for account in accounts:
                account_name = account['name'].lower()
                if 'revenue' in account_name or 'income' in account_name:
                    revenue_account = account['name']
                elif 'expense' in account_name or 'cost' in account_name:
                    expense_account = account['name']
            
            # Set defaults if found
            if revenue_account:
                self.account1_combo.setCurrentText(revenue_account)
                print(f"✅ Set default account1: {revenue_account}")
            
            if expense_account:
                self.account2_combo.setCurrentText(expense_account)
                print(f"✅ Set default account2: {expense_account}")
            
            # If no specific accounts found, use first two accounts
            if not revenue_account and not expense_account and len(accounts) >= 2:
                self.account1_combo.setCurrentIndex(0)
                self.account2_combo.setCurrentIndex(1)
                print("✅ Set first two accounts as defaults")
                
        except Exception as e:
            print(f"❌ Error setting default accounts: {e}")

    def _load_data(self):
        """Load dashboard data and set up default accounts."""
        self._update_metrics()
        self._setup_default_accounts()
    

    
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
        
        # Update card values using proper currency formatting
        self.card_cash.set_value(format_currency(cash))
        self.card_net_income.set_value(format_currency(net_income))
        self.card_liabilities.set_value(format_currency(liabilities))
        self.card_revenue.set_value(format_currency(revenue))
        self.card_expenses.set_value(format_currency(expenses))
        
        # Calculate and update ratios using the financial ratio calculator
        self._update_ratio_metrics(to_date_str)
        
        # Get accounts receivable and payable data
        receivables = self._get_accounts_receivable(to_date_str)
        payables = self._get_accounts_payable(to_date_str)
        
        # Update receivables and payables cards
        self.card_receivables.set_value(format_currency(receivables))
        self.card_payables.set_value(format_currency(payables))
        
        # Update trend indicators
        self._update_trend_indicators(cash, revenue, expenses, liabilities, net_income)
        
    def _update_ratio_metrics(self, as_of_date):
        """Update ratio metrics using the financial ratio calculator."""
        try:
            # Import the financial ratio calculator
            from src.core.financial_ratios import FinancialRatioCalculator
            from datetime import datetime
            
            # Convert string date to date object
            if isinstance(as_of_date, str):
                as_of_date = datetime.strptime(as_of_date, '%Y-%m-%d').date()
            
            # Create ratio calculator instance
            ratio_calculator = FinancialRatioCalculator(self.system.db_manager, self.system)
            
            # Calculate all ratios
            print(f"🔍 Calculating ratios for date: {as_of_date}")
            ratio_data = ratio_calculator.calculate_all_ratios(as_of_date)
            
            if 'error' in ratio_data:
                print(f"❌ Error calculating ratios: {ratio_data['error']}")
                # Set default values on error
                self.card_quick_ratio.set_value("0.00")
                self.card_debt_equity.set_value("0.00")
                self.card_current_ratio.set_value("0.00")
                self.card_gross_margin.set_value("0.00%")
                self.card_operating_margin.set_value("0.00%")
                return
            
            print(f"✅ Ratio calculation successful: {ratio_data.keys()}")
            
            # Extract ratios from the calculated data
            ratios = ratio_data.get('ratios', {})
            print(f"📊 Available ratio categories: {list(ratios.keys())}")
            
            # Update Quick Ratio
            liquidity_ratios = ratios.get('liquidity', {})
            print(f"💧 Liquidity ratios available: {list(liquidity_ratios.keys())}")
            quick_ratio_data = liquidity_ratios.get('quick_ratio', {})
            if quick_ratio_data:
                quick_ratio_value = quick_ratio_data.get('value', 0)
                self.card_quick_ratio.set_value(f"{quick_ratio_value:.2f}")
                print(f"✅ Quick ratio updated: {quick_ratio_value:.2f}")
            else:
                self.card_quick_ratio.set_value("0.00")
                print("⚠️ No quick ratio data available")
            
            # Update Current Ratio
            current_ratio_data = liquidity_ratios.get('current_ratio', {})
            if current_ratio_data:
                current_ratio_value = current_ratio_data.get('value', 0)
                self.card_current_ratio.set_value(f"{current_ratio_value:.2f}")
                print(f"✅ Current ratio updated: {current_ratio_value:.2f}")
            else:
                self.card_current_ratio.set_value("0.00")
                print("⚠️ No current ratio data available")
            
            # Update Debt-to-Equity Ratio
            leverage_ratios = ratios.get('leverage', {})
            print(f"⚖️ Leverage ratios available: {list(leverage_ratios.keys())}")
            debt_equity_data = leverage_ratios.get('debt_to_equity', {})
            if debt_equity_data:
                debt_equity_value = debt_equity_data.get('value', 0)
                self.card_debt_equity.set_value(f"{debt_equity_value:.2f}")
                print(f"✅ Debt-to-equity ratio updated: {debt_equity_value:.2f}")
            else:
                self.card_debt_equity.set_value("0.00")
                print("⚠️ No debt-to-equity ratio data available")
            
            # Update Profitability Ratios (Gross Margin and Operating Margin)
            profitability_ratios = ratios.get('profitability', {})
            print(f"💰 Profitability ratios available: {list(profitability_ratios.keys())}")
            
            # Update Gross Margin
            gross_margin_data = profitability_ratios.get('gross_profit_margin', {})
            if gross_margin_data:
                gross_margin_value = gross_margin_data.get('value', 0)
                self.card_gross_margin.set_value(f"{gross_margin_value:.1f}%")
                print(f"✅ Gross margin updated: {gross_margin_value:.1f}%")
            else:
                self.card_gross_margin.set_value("0.00%")
                print("⚠️ No gross margin data available")
            
            # Update Operating Margin (using net profit margin as proxy)
            net_margin_data = profitability_ratios.get('net_profit_margin', {})
            if net_margin_data:
                net_margin_value = net_margin_data.get('value', 0)
                self.card_operating_margin.set_value(f"{net_margin_value:.1f}%")
                print(f"✅ Operating margin updated: {net_margin_value:.1f}%")
            else:
                self.card_operating_margin.set_value("0.00%")
                print("⚠️ No operating margin data available")
            
        except Exception as e:
            print(f"❌ Error updating ratio metrics: {e}")
            # Set default values on error
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
            
    def _get_accounts_receivable(self, as_of_date=None):
        """Get accounts receivable using group-based balance sheet."""
        try:
            balance_sheet = self.system.generate_group_based_balance_sheet(as_of_date)
            
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
            balance_sheet = self.system.generate_group_based_balance_sheet(as_of_date)
            
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
        """Handle date range selection changes with smart data validation and debouncing."""
        try:
            # Validate date parameters
            if start_date is None or end_date is None:
                print("⚠️ Invalid date range received - start_date or end_date is None")
                return
            
            # Check if widget is still valid
            if self._is_destroying or not self._is_widget_valid('date_selector'):
                print("⚠️ Widget is being destroyed or invalid, skipping date range update")
                return
            
            print(f"📅 Date range changed: {start_date.toString('yyyy-MM-dd')} to {end_date.toString('yyyy-MM-dd')}")
            
            # Debounce the update to prevent rapid successive calls
            self._debounce_timer.stop()
            self._debounce_timer.start(300)  # 300ms debounce delay
            
        except Exception as e:
            print(f"❌ Error in date range changed handler: {e}")
    
    def _debounced_date_range_update(self):
        """Perform the actual date range update with debouncing."""
        try:
            # Check if widget is still valid
            if self._is_destroying or not self._is_widget_valid('date_selector'):
                print("⚠️ Widget is being destroyed or invalid, skipping date range update")
                return
            
            # Get current date range
            from_date, to_date = self.date_selector.get_date_range()
            if from_date is None or to_date is None:
                print("⚠️ Invalid date range, showing empty state")
                # Show empty state immediately
                self._show_empty_state()
                return
            
            # Update metrics immediately (fast)
            self._update_metrics()
            
        except Exception as e:
            print(f"❌ Error in debounced date range update: {e}")
    
    def _show_empty_state(self):
        """Show appropriate empty state when no data is available."""
        try:
            # Check if widget is still valid
            if self._is_destroying:
                print("⚠️ Dashboard is being destroyed, skipping empty state")
                return
            
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
            
        except Exception as e:
            print(f"❌ Error showing empty state: {e}")
    
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
            # Check if widget is still valid
            if self._is_destroying:
                print("⚠️ Dashboard is being destroyed, skipping refresh")
                return
            
            print("🔄 Dashboard: Refreshing data due to organization change...")
            self._load_data()
            
            # Set up default accounts for new organization
            self._setup_default_accounts()
            
            # Force refresh with new organization data
            if self._is_widget_valid('date_selector'):
                from_date, to_date = self.date_selector.get_date_range()
                if from_date and to_date:
                    print(f"   Date range: {from_date.toString('yyyy-MM-dd')} to {to_date.toString('yyyy-MM-dd')}")
                    print("   ✅ Dashboard refreshed with new organization context")
                else:
                    print("   ⚠️ Invalid date range, skipping updates")
            else:
                print("   ⚠️ Date selector is invalid, skipping updates")
                
        except Exception as e:
            print(f"❌ Error refreshing dashboard data: {e}")
    
    def refresh_organization_context(self, new_system):
        """Update the system reference when organization changes."""
        try:
            # Check if widget is still valid
            if self._is_destroying:
                print("⚠️ Dashboard is being destroyed, skipping organization context update")
                return
            
            print(f"🔄 Dashboard: Updating system reference for new organization...")
            self.system = new_system
            self._load_data()
            
            # Set up default accounts for new organization
            self._setup_default_accounts()
            
            print("   ✅ Dashboard system reference updated")
        except Exception as e:
            print(f"❌ Error updating dashboard system reference: {e}")
        
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
