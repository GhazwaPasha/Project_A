"""
Enhanced Financial Ratios and KPI Calculator with Real-time Monitoring
"""

import uuid
from datetime import datetime, date, timedelta
from decimal import Decimal
import logging
import math
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

class RatioCategory(Enum):
    LIQUIDITY = "LIQUIDITY"
    PROFITABILITY = "PROFITABILITY"
    EFFICIENCY = "EFFICIENCY"
    LEVERAGE = "LEVERAGE"

class RatioStatus(Enum):
    NORMAL = "NORMAL"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"

@dataclass
class FinancialRatio:
    """Financial ratio data structure."""
    name: str
    category: RatioCategory
    value: Decimal
    target: Optional[Decimal]
    status: RatioStatus
    variance_pct: Optional[float]
    trend: Optional[str]

@dataclass
class RatioAlert:
    """Ratio alert data structure."""
    ratio_name: str
    current_value: Decimal
    threshold_value: Decimal
    alert_type: str
    message: str

class FinancialRatioCalculator:
    """Advanced financial ratio calculator with real-time monitoring."""
    
    def __init__(self, db_manager, accounting_system=None):
        self.db_manager = db_manager
        self.accounting_system = accounting_system
        self.logger = logging.getLogger(__name__)
    
    def calculate_all_ratios(self, as_of_date: date = None) -> Dict[str, Any]:
        """Calculate all financial ratios for a given date."""
        if as_of_date is None:
            as_of_date = date.today()
        
        # Get financial statement data
        financial_data = self._get_financial_statement_data(as_of_date)
        
        if not financial_data:
            return {'error': 'Insufficient financial data for ratio calculation'}
        
        # Calculate ratios by category
        liquidity_ratios = self._calculate_liquidity_ratios(financial_data)
        profitability_ratios = self._calculate_profitability_ratios(financial_data)
        efficiency_ratios = self._calculate_efficiency_ratios(financial_data)
        leverage_ratios = self._calculate_leverage_ratios(financial_data)
        
        # Combine all ratios
        all_ratios = {
            'liquidity': liquidity_ratios,
            'profitability': profitability_ratios,
            'efficiency': efficiency_ratios,
            'leverage': leverage_ratios
        }
        
        # Generate alerts
        alerts = self._generate_ratio_alerts(all_ratios)
        
        # Calculate summary metrics
        summary = self._calculate_ratio_summary(all_ratios)
        
        return {
            'calculation_date': as_of_date.isoformat(),
            'ratios': all_ratios,
            'alerts': alerts,
            'summary': summary,
            'financial_data_used': self._sanitize_financial_data(financial_data)
        }
    
    def calculate_ratio_trends(self, months: int = 12) -> Dict[str, Any]:
        """Calculate ratio trends over specified months."""
        trend_data = {}
        
        for i in range(months):
            calculation_date = date.today() - timedelta(days=30 * i)
            month_ratios = self.calculate_all_ratios(calculation_date)
            
            if 'error' not in month_ratios:
                period_key = calculation_date.strftime('%Y-%m')
                trend_data[period_key] = month_ratios['ratios']
        
        # Calculate trend directions
        trend_analysis = self._analyze_ratio_trends(trend_data)
        
        return {
            'trend_data': trend_data,
            'trend_analysis': trend_analysis,
            'period_months': months
        }
    
    def monitor_ratio_thresholds(self, as_of_date: date = None) -> List[RatioAlert]:
        """Monitor ratios against predefined thresholds and generate alerts."""
        current_ratios = self.calculate_all_ratios(as_of_date)
        
        if 'error' in current_ratios:
            return []
        
        alerts = []
        
        # Get ratio definitions with thresholds
        ratio_definitions = self._get_ratio_definitions()
        
        for category_name, category_ratios in current_ratios['ratios'].items():
            for ratio_name, ratio_data in category_ratios.items():
                ratio_def = ratio_definitions.get(ratio_name)
                
                if ratio_def and ratio_data.get('value') is not None:
                    alert = self._check_ratio_threshold(
                        ratio_name, ratio_data['value'], ratio_def
                    )
                    if alert:
                        alerts.append(alert)
        
        # Save alerts to database
        self._save_ratio_alerts(alerts, as_of_date)
        
        return alerts
    
    def create_ratio_dashboard_data(self, as_of_date: date = None) -> Dict[str, Any]:
        """Create comprehensive data for ratio dashboard."""
        current_ratios = self.calculate_all_ratios(as_of_date)
        trends = self.calculate_ratio_trends(6)  # 6 months of trends
        alerts = self.monitor_ratio_thresholds(as_of_date)
        
        # Calculate key performance indicators
        kpi_summary = self._calculate_kpi_summary(current_ratios)
        
        # Get industry benchmarks (if available)
        benchmarks = self._get_industry_benchmarks()
        
        return {
            'current_ratios': current_ratios,
            'trends': trends,
            'alerts': alerts,
            'kpi_summary': kpi_summary,
            'benchmarks': benchmarks,
            'last_updated': datetime.now().isoformat()
        }
    
    def _get_financial_statement_data(self, as_of_date: date) -> Optional[Dict[str, Any]]:
        """Get financial statement data for ratio calculations."""
        try:
            if not self.accounting_system:
                return None
            
            # Get balance sheet data
            balance_sheet = self.accounting_system.generate_balance_sheet_breakdown(
                as_of_date.strftime('%Y-%m-%d')
            )
            
            # Get income statement data (last 12 months)
            year_start = as_of_date.replace(month=1, day=1)
            income_statement = self.accounting_system.generate_income_statement_breakdown(
                year_start.strftime('%Y-%m-%d'),
                as_of_date.strftime('%Y-%m-%d')
            )
            
            # Calculate derived values
            financial_data = {
                # Balance Sheet Items
                'total_assets': balance_sheet.get('total_assets', 0),
                'total_liabilities': balance_sheet.get('total_liabilities', 0),
                'total_equity': balance_sheet.get('total_equity', 0),
                
                # Income Statement Items
                'total_revenue': income_statement.get('total_revenue', 0),
                'total_cogs': income_statement.get('total_cogs', 0),
                'gross_profit': income_statement.get('gross_profit', 0),
                'total_expenses': income_statement.get('total_expenses', 0),
                'net_income': income_statement.get('net_income', 0),
                
                # Detailed account balances for specific calculations
                'cash': self._get_account_balance(['Cash', 'Cash in Hand', 'Cash at Bank'], balance_sheet),
                'current_assets': self._get_current_assets(balance_sheet),
                'current_liabilities': self._get_current_liabilities(balance_sheet),
                'inventory': self._get_account_balance(['Inventory'], balance_sheet),
                'accounts_receivable': self._get_account_balance(['Accounts Receivable'], balance_sheet),
                'accounts_payable': self._get_account_balance(['Accounts Payable'], balance_sheet),
                'long_term_debt': self._get_long_term_debt(balance_sheet),
                
                # Period information
                'period_days': (as_of_date - year_start).days + 1,
                'as_of_date': as_of_date
            }
            
            return financial_data
            
        except Exception as e:
            self.logger.error(f"Failed to get financial statement data: {e}")
            return None
    
    def _calculate_liquidity_ratios(self, financial_data: Dict[str, Any]) -> Dict[str, Dict]:
        """Calculate liquidity ratios."""
        ratios = {}
        
        # Current Ratio
        if financial_data['current_liabilities'] > 0:
            current_ratio = financial_data['current_assets'] / financial_data['current_liabilities']
            ratios['current_ratio'] = {
                'value': float(current_ratio),
                'description': 'Current Assets / Current Liabilities',
                'interpretation': 'Ability to pay short-term debts',
                'unit': 'ratio'
            }
        
        # Quick Ratio (Acid Test)
        if financial_data['current_liabilities'] > 0:
            quick_assets = financial_data['current_assets'] - financial_data['inventory']
            quick_ratio = quick_assets / financial_data['current_liabilities']
            ratios['quick_ratio'] = {
                'value': float(quick_ratio),
                'description': '(Current Assets - Inventory) / Current Liabilities',
                'interpretation': 'Ability to pay short-term debts without selling inventory',
                'unit': 'ratio'
            }
        
        # Cash Ratio
        if financial_data['current_liabilities'] > 0:
            cash_ratio = financial_data['cash'] / financial_data['current_liabilities']
            ratios['cash_ratio'] = {
                'value': float(cash_ratio),
                'description': 'Cash / Current Liabilities',
                'interpretation': 'Ability to pay short-term debts with cash only',
                'unit': 'ratio'
            }
        
        # Working Capital
        working_capital = financial_data['current_assets'] - financial_data['current_liabilities']
        ratios['working_capital'] = {
            'value': float(working_capital),
            'description': 'Current Assets - Current Liabilities',
            'interpretation': 'Available short-term financial resources',
            'unit': 'currency'
        }
        
        return ratios
    
    def _calculate_profitability_ratios(self, financial_data: Dict[str, Any]) -> Dict[str, Dict]:
        """Calculate profitability ratios."""
        ratios = {}
        
        # Gross Profit Margin
        if financial_data['total_revenue'] > 0:
            gross_margin = (financial_data['gross_profit'] / financial_data['total_revenue']) * 100
            ratios['gross_profit_margin'] = {
                'value': float(gross_margin),
                'description': '(Gross Profit / Revenue) * 100',
                'interpretation': 'Percentage of revenue remaining after direct costs',
                'unit': 'percentage'
            }
        
        # Net Profit Margin
        if financial_data['total_revenue'] > 0:
            net_margin = (financial_data['net_income'] / financial_data['total_revenue']) * 100
            ratios['net_profit_margin'] = {
                'value': float(net_margin),
                'description': '(Net Income / Revenue) * 100',
                'interpretation': 'Percentage of revenue remaining as profit',
                'unit': 'percentage'
            }
        
        # Return on Assets (ROA)
        if financial_data['total_assets'] > 0:
            roa = (financial_data['net_income'] / financial_data['total_assets']) * 100
            ratios['return_on_assets'] = {
                'value': float(roa),
                'description': '(Net Income / Total Assets) * 100',
                'interpretation': 'How efficiently assets generate profit',
                'unit': 'percentage'
            }
        
        # Return on Equity (ROE)
        if financial_data['total_equity'] > 0:
            roe = (financial_data['net_income'] / financial_data['total_equity']) * 100
            ratios['return_on_equity'] = {
                'value': float(roe),
                'description': '(Net Income / Total Equity) * 100',
                'interpretation': 'Return to shareholders on their investment',
                'unit': 'percentage'
            }
        
        return ratios
    
    def _calculate_efficiency_ratios(self, financial_data: Dict[str, Any]) -> Dict[str, Dict]:
        """Calculate efficiency ratios."""
        ratios = {}
        
        # Asset Turnover
        if financial_data['total_assets'] > 0:
            asset_turnover = financial_data['total_revenue'] / financial_data['total_assets']
            ratios['asset_turnover'] = {
                'value': float(asset_turnover),
                'description': 'Revenue / Total Assets',
                'interpretation': 'How efficiently assets generate revenue',
                'unit': 'times'
            }
        
        # Inventory Turnover
        if financial_data['inventory'] > 0:
            inventory_turnover = financial_data['total_cogs'] / financial_data['inventory']
            ratios['inventory_turnover'] = {
                'value': float(inventory_turnover),
                'description': 'Cost of Goods Sold / Average Inventory',
                'interpretation': 'How quickly inventory is sold',
                'unit': 'times'
            }
            
            # Days Sales in Inventory
            days_in_inventory = 365 / inventory_turnover if inventory_turnover > 0 else 0
            ratios['days_sales_inventory'] = {
                'value': float(days_in_inventory),
                'description': '365 / Inventory Turnover',
                'interpretation': 'Average days to sell inventory',
                'unit': 'days'
            }
        
        # Receivables Turnover
        if financial_data['accounts_receivable'] > 0:
            receivables_turnover = financial_data['total_revenue'] / financial_data['accounts_receivable']
            ratios['receivables_turnover'] = {
                'value': float(receivables_turnover),
                'description': 'Revenue / Average Accounts Receivable',
                'interpretation': 'How quickly receivables are collected',
                'unit': 'times'
            }
            
            # Days Sales Outstanding
            days_sales_outstanding = 365 / receivables_turnover if receivables_turnover > 0 else 0
            ratios['days_sales_outstanding'] = {
                'value': float(days_sales_outstanding),
                'description': '365 / Receivables Turnover',
                'interpretation': 'Average days to collect receivables',
                'unit': 'days'
            }
        
        # Payables Turnover
        if financial_data['accounts_payable'] > 0:
            payables_turnover = financial_data['total_cogs'] / financial_data['accounts_payable']
            ratios['payables_turnover'] = {
                'value': float(payables_turnover),
                'description': 'Cost of Goods Sold / Average Accounts Payable',
                'interpretation': 'How quickly payables are paid',
                'unit': 'times'
            }
            
            # Days Payable Outstanding
            days_payable_outstanding = 365 / payables_turnover if payables_turnover > 0 else 0
            ratios['days_payable_outstanding'] = {
                'value': float(days_payable_outstanding),
                'description': '365 / Payables Turnover',
                'interpretation': 'Average days to pay suppliers',
                'unit': 'days'
            }
        
        return ratios
    
    def _calculate_leverage_ratios(self, financial_data: Dict[str, Any]) -> Dict[str, Dict]:
        """Calculate leverage ratios."""
        ratios = {}
        
        # Debt-to-Equity Ratio
        if financial_data['total_equity'] > 0:
            debt_to_equity = financial_data['total_liabilities'] / financial_data['total_equity']
            ratios['debt_to_equity'] = {
                'value': float(debt_to_equity),
                'description': 'Total Liabilities / Total Equity',
                'interpretation': 'Financial leverage and risk',
                'unit': 'ratio'
            }
        
        # Debt Ratio
        if financial_data['total_assets'] > 0:
            debt_ratio = financial_data['total_liabilities'] / financial_data['total_assets']
            ratios['debt_ratio'] = {
                'value': float(debt_ratio),
                'description': 'Total Liabilities / Total Assets',
                'interpretation': 'Proportion of assets financed by debt',
                'unit': 'ratio'
            }
        
        # Equity Ratio
        if financial_data['total_assets'] > 0:
            equity_ratio = financial_data['total_equity'] / financial_data['total_assets']
            ratios['equity_ratio'] = {
                'value': float(equity_ratio),
                'description': 'Total Equity / Total Assets',
                'interpretation': 'Proportion of assets financed by equity',
                'unit': 'ratio'
            }
        
        # Times Interest Earned (if interest expense data available)
        # This would require interest expense tracking
        
        return ratios
    
    def _generate_ratio_alerts(self, ratios: Dict[str, Dict]) -> List[Dict[str, Any]]:
        """Generate alerts based on ratio values."""
        alerts = []
        
        # Define critical thresholds
        critical_thresholds = {
            'current_ratio': {'min': 1.0, 'warning': 1.5},
            'quick_ratio': {'min': 0.5, 'warning': 1.0},
            'cash_ratio': {'min': 0.1, 'warning': 0.2},
            'gross_profit_margin': {'min': 10.0, 'warning': 20.0},
            'net_profit_margin': {'min': 0.0, 'warning': 5.0},
            'debt_to_equity': {'max': 2.0, 'warning': 1.5},
            'debt_ratio': {'max': 0.8, 'warning': 0.6}
        }
        
        for category_name, category_ratios in ratios.items():
            for ratio_name, ratio_data in category_ratios.items():
                if ratio_name in critical_thresholds and 'value' in ratio_data:
                    thresholds = critical_thresholds[ratio_name]
                    value = ratio_data['value']
                    
                    alert = None
                    
                    # Check minimum thresholds
                    if 'min' in thresholds:
                        if value < thresholds['min']:
                            alert = {
                                'type': 'CRITICAL',
                                'ratio': ratio_name,
                                'category': category_name,
                                'value': value,
                                'threshold': thresholds['min'],
                                'message': f"{ratio_name.replace('_', ' ').title()} ({value:.2f}) is below critical minimum ({thresholds['min']})"
                            }
                        elif value < thresholds.get('warning', thresholds['min']):
                            alert = {
                                'type': 'WARNING',
                                'ratio': ratio_name,
                                'category': category_name,
                                'value': value,
                                'threshold': thresholds['warning'],
                                'message': f"{ratio_name.replace('_', ' ').title()} ({value:.2f}) is below warning level ({thresholds['warning']})"
                            }
                    
                    # Check maximum thresholds
                    if 'max' in thresholds:
                        if value > thresholds['max']:
                            alert = {
                                'type': 'CRITICAL',
                                'ratio': ratio_name,
                                'category': category_name,
                                'value': value,
                                'threshold': thresholds['max'],
                                'message': f"{ratio_name.replace('_', ' ').title()} ({value:.2f}) exceeds critical maximum ({thresholds['max']})"
                            }
                        elif value > thresholds.get('warning', thresholds['max']):
                            alert = {
                                'type': 'WARNING',
                                'ratio': ratio_name,
                                'category': category_name,
                                'value': value,
                                'threshold': thresholds['warning'],
                                'message': f"{ratio_name.replace('_', ' ').title()} ({value:.2f}) exceeds warning level ({thresholds['warning']})"
                            }
                    
                    if alert:
                        alerts.append(alert)
        
        return alerts
    
    def _get_account_balance(self, account_names: List[str], balance_sheet: Dict) -> float:
        """Get total balance for specified account names."""
        total = 0
        
        # Check assets
        for account, balance in balance_sheet.get('assets', []):
            if any(name.lower() in account.lower() for name in account_names):
                total += balance
        
        # Check liabilities
        for account, balance in balance_sheet.get('liabilities', []):
            if any(name.lower() in account.lower() for name in account_names):
                total += balance
        
        return total
    
    def _get_current_assets(self, balance_sheet: Dict) -> float:
        """Calculate current assets from balance sheet."""
        current_asset_indicators = [
            'cash', 'receivable', 'inventory', 'prepaid', 'short-term'
        ]
        
        current_assets = 0
        for account, balance in balance_sheet.get('assets', []):
            if any(indicator in account.lower() for indicator in current_asset_indicators):
                current_assets += balance
        
        return current_assets
    
    def _get_current_liabilities(self, balance_sheet: Dict) -> float:
        """Calculate current liabilities from balance sheet."""
        current_liability_indicators = [
            'payable', 'accrued', 'short-term', 'current', 'tax payable'
        ]
        
        current_liabilities = 0
        for account, balance in balance_sheet.get('liabilities', []):
            if any(indicator in account.lower() for indicator in current_liability_indicators):
                current_liabilities += balance
        
        return current_liabilities
    
    def _get_long_term_debt(self, balance_sheet: Dict) -> float:
        """Calculate long-term debt from balance sheet."""
        long_term_indicators = ['long-term', 'mortgage', 'bond', 'note payable']
        
        long_term_debt = 0
        for account, balance in balance_sheet.get('liabilities', []):
            if any(indicator in account.lower() for indicator in long_term_indicators):
                long_term_debt += balance
        
        return long_term_debt
    
    def _sanitize_financial_data(self, financial_data: Dict) -> Dict:
        """Remove sensitive details and keep summary for transparency."""
        return {
            'total_assets': financial_data['total_assets'],
            'total_liabilities': financial_data['total_liabilities'],
            'total_equity': financial_data['total_equity'],
            'total_revenue': financial_data['total_revenue'],
            'net_income': financial_data['net_income'],
            'calculation_period_days': financial_data['period_days']
        }
    
    def _analyze_ratio_trends(self, trend_data: Dict) -> Dict[str, Any]:
        """Analyze trends in ratio data."""
        # This would implement trend analysis algorithms
        # For now, return placeholder
        return {
            'improving_ratios': [],
            'declining_ratios': [],
            'stable_ratios': []
        }
    
    def _get_ratio_definitions(self) -> Dict[str, Dict]:
        """Get ratio definitions from database."""
        # This would fetch from the financial_ratios table
        # For now, return empty dict
        return {}
    
    def _check_ratio_threshold(self, ratio_name: str, value: float, definition: Dict) -> Optional[RatioAlert]:
        """Check if ratio exceeds thresholds."""
        # Implementation for threshold checking
        return None
    
    def _save_ratio_alerts(self, alerts: List, as_of_date: date):
        """Save alerts to database."""
        # Implementation for saving alerts
        pass
    
    def _calculate_ratio_summary(self, ratios: Dict) -> Dict[str, Any]:
        """Calculate a summary from the ratios."""
        # Placeholder implementation
        return {}
    
    def _calculate_kpi_summary(self, ratios: Dict) -> Dict[str, Any]:
        """Calculate key performance indicators summary."""
        return {
            'overall_health_score': 0,  # Placeholder
            'risk_level': 'MODERATE',    # Placeholder
            'key_strengths': [],         # Placeholder
            'areas_of_concern': []       # Placeholder
        }
    
    def _get_industry_benchmarks(self) -> Dict[str, Any]:
        """Get industry benchmark data."""
        return {}  # Placeholder
