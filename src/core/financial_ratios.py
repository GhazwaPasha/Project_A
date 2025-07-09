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
    
        # Initialize database calculations adapter
        from .database_calculations import DatabaseCalculations
        # Get the Supabase client from the accounting system or db_manager
        if accounting_system and hasattr(accounting_system, 'supabase'):
            self.db_calculations = DatabaseCalculations(accounting_system.supabase)
        elif hasattr(db_manager, 'supabase'):
            self.db_calculations = DatabaseCalculations(db_manager.supabase)
        else:
            # Create Supabase client directly
            from supabase import create_client
            from src.core.config import DatabaseConfig
            DatabaseConfig.validate_config()
            supabase_client = create_client(
                DatabaseConfig.SUPABASE_URL,
                DatabaseConfig.SUPABASE_ANON_KEY
            )
            self.db_calculations = DatabaseCalculations(supabase_client)
    
    def calculate_all_ratios(self, as_of_date: date = None, from_date: date = None, to_date: date = None) -> Dict[str, Any]:
        """Calculate all financial ratios using optimized database function."""
        if as_of_date is None:
            as_of_date = date.today()
        
        if from_date is None:
            from_date = as_of_date.replace(month=1, day=1)  # Start of year
        
        if to_date is None:
            to_date = as_of_date
        
        try:
            # Get organization ID
            org_id = self.accounting_system.current_organization_id if self.accounting_system else None
            if not org_id:
                return {'error': 'No organization ID available'}
            
            # Check if we have any data before expensive calculation
            if hasattr(self.accounting_system, 'data_validator'):
                if not self.accounting_system.data_validator.has_any_data(org_id):
                    return {'error': 'No data available for ratio calculation'}
            
            # Use optimized database function to calculate all ratios in one call
            ratios_data = self.db_calculations.calculate_all_ratios(
                org_id=org_id,
                from_date=from_date,
                to_date=to_date,
                as_of_date=as_of_date
            )
            
            if not ratios_data:
                return {'error': 'Failed to calculate ratios from database'}
            
            # Add calculation metadata
            ratios_data['calculation_date'] = as_of_date.isoformat()
            ratios_data['from_date'] = from_date.isoformat()
            ratios_data['to_date'] = to_date.isoformat()
            ratios_data['organization_id'] = org_id
            
            # Generate alerts based on calculated ratios
            alerts = self._generate_ratio_alerts(ratios_data)
            ratios_data['alerts'] = alerts
            
            # Calculate summary metrics
            summary = self._calculate_ratio_summary(ratios_data)
            ratios_data['summary'] = summary
            
            return ratios_data
            
        except Exception as e:
            self.logger.error(f"Error calculating ratios from database: {e}")
            return {'error': f'Ratio calculation error: {str(e)}'}
    
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
    
    def calculate_historical_ratios(self, start_date: date, end_date: date, 
                                  period_type: str = 'monthly') -> Dict[str, Any]:
        """Calculate historical ratios for multiple periods efficiently."""
        try:
            historical_data = {}
            
            # Generate periods based on period_type
            periods = self._generate_historical_periods(start_date, end_date, period_type)
            
            for period in periods:
                period_start = period['start_date']
                period_end = period['end_date']
                period_key = period['key']
                
                # Calculate ratios for this period
                period_ratios = self.calculate_all_ratios(
                    as_of_date=period_end,
                    from_date=period_start,
                    to_date=period_end
                )
                
                if 'error' not in period_ratios:
                    historical_data[period_key] = period_ratios
                else:
                    print(f"Warning: Failed to calculate ratios for period {period_key}")
                    historical_data[period_key] = {'error': period_ratios['error']}
            
            return {
                'historical_data': historical_data,
                'periods': periods,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'period_type': period_type
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating historical ratios: {e}")
            return {'error': f'Historical ratio calculation error: {str(e)}'}
    
    def _generate_historical_periods(self, start_date: date, end_date: date, 
                                   period_type: str) -> List[Dict[str, Any]]:
        """Generate historical periods for ratio calculation."""
        periods = []
        current_date = start_date.replace(day=1)  # Start from beginning of month
        
        while current_date <= end_date:
            # Calculate period end date
            if period_type == 'monthly':
                # Last day of current month
                if current_date.month == 12:
                    period_end = current_date.replace(year=current_date.year + 1, month=1, day=1) - timedelta(days=1)
                else:
                    period_end = current_date.replace(month=current_date.month + 1, day=1) - timedelta(days=1)
                
                period_key = current_date.strftime('%Y-%m')
                
            elif period_type == 'quarterly':
                # Calculate quarter end
                quarter = (current_date.month - 1) // 3 + 1
                quarter_end_month = quarter * 3
                if quarter_end_month == 12:
                    period_end = current_date.replace(year=current_date.year + 1, month=1, day=1) - timedelta(days=1)
                else:
                    period_end = current_date.replace(month=quarter_end_month + 1, day=1) - timedelta(days=1)
                
                period_key = f"{current_date.year}-Q{quarter}"
                
            else:  # yearly
                period_end = current_date.replace(year=current_date.year + 1, month=1, day=1) - timedelta(days=1)
                period_key = str(current_date.year)
            
            # Ensure period end doesn't exceed the overall end date
            if period_end > end_date:
                period_end = end_date
            
            periods.append({
                'key': period_key,
                'start_date': current_date,
                'end_date': period_end,
                'label': period_key
            })
            
            # Move to next period
            if period_type == 'monthly':
                if current_date.month == 12:
                    current_date = current_date.replace(year=current_date.year + 1, month=1)
                else:
                    current_date = current_date.replace(month=current_date.month + 1)
            elif period_type == 'quarterly':
                if quarter == 4:
                    current_date = current_date.replace(year=current_date.year + 1, month=1)
                else:
                    current_date = current_date.replace(month=quarter * 3 + 1)
            else:  # yearly
                current_date = current_date.replace(year=current_date.year + 1)
        
        return periods
    
    def _get_financial_statement_data(self, as_of_date: date) -> Optional[Dict[str, Any]]:
        """Get financial statement data for ratio calculations using group-based categorization."""
        try:
            if not self.accounting_system:
                return None
            
            # Get group-based balance sheet data
            balance_sheet = self.accounting_system.generate_group_based_balance_sheet(
                as_of_date.strftime('%Y-%m-%d')
            )
            
            # Get group-based income statement data (last 12 months)
            year_start = as_of_date.replace(month=1, day=1)
            income_statement = self.accounting_system.generate_group_based_income_statement(
                year_start.strftime('%Y-%m-%d'),
                as_of_date.strftime('%Y-%m-%d')
            )
            
            # Extract data from group-based sections
            current_assets = self._get_group_balance('current_asset', balance_sheet)
            current_liabilities = self._get_group_balance('current_liability', balance_sheet)
            cash = self._extract_cash_from_current_assets(balance_sheet)
            inventory = self._extract_inventory_from_other_assets(balance_sheet)
            receivables = self._extract_receivables_from_current_assets(balance_sheet)
            payables = self._extract_payables_from_current_liabilities(balance_sheet)
            long_term_debt = self._get_group_balance('long_term_liability', balance_sheet)
            
            # Get totals from group-based statements
            total_assets = balance_sheet.get('total_assets', 0)
            total_liabilities = balance_sheet.get('total_liabilities', 0)
            total_equity = balance_sheet.get('total_equity', 0)
            total_revenue = income_statement.get('total_revenue', 0)
            total_cogs = income_statement.get('total_cogs', 0)
            gross_profit = income_statement.get('gross_profit', 0)
            total_operating_expenses = income_statement.get('total_operating_expenses', 0)
            net_income = income_statement.get('net_income', 0)
            
            # Debug logging
            self.logger.info(f"Financial data extraction - Current Assets: {current_assets}, Current Liabilities: {current_liabilities}")
            self.logger.info(f"Financial data extraction - Cash: {cash}, Inventory: {inventory}, Receivables: {receivables}")
            self.logger.info(f"Financial data extraction - Payables: {payables}, Long-term Debt: {long_term_debt}")
            self.logger.info(f"Financial data extraction - Total Assets: {total_assets}, Total Liabilities: {total_liabilities}")
            self.logger.info(f"Financial data extraction - Total Revenue: {total_revenue}, Net Income: {net_income}")
            
            financial_data = {
                # Balance Sheet Items
                'total_assets': total_assets,
                'total_liabilities': total_liabilities,
                'total_equity': total_equity,
                
                # Income Statement Items
                'total_revenue': total_revenue,
                'total_cogs': total_cogs,
                'gross_profit': gross_profit,
                'total_expenses': total_operating_expenses,
                'net_income': net_income,
                
                # Extract group-based data for specific calculations
                'cash': cash,
                'current_assets': current_assets,
                'current_liabilities': current_liabilities,
                'inventory': inventory,
                'accounts_receivable': receivables,
                'accounts_payable': payables,
                'long_term_debt': long_term_debt,
                
                # Period information
                'period_days': (as_of_date - year_start).days + 1,
                'as_of_date': as_of_date
            }
            
            return financial_data
            
        except Exception as e:
            self.logger.error(f"Failed to get financial statement data: {e}")
            return None
    
    def _calculate_ratios_from_financial_data(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate all financial ratios from group-based financial data."""
        try:
            ratios = {
                'liquidity': {},
                'profitability': {},
                'leverage': {},
                'efficiency': {},
                'market': {}
            }
            
            # Extract values from financial data
            current_assets = financial_data.get('current_assets', 0)
            current_liabilities = financial_data.get('current_liabilities', 0)
            cash = financial_data.get('cash', 0)
            inventory = financial_data.get('inventory', 0)
            receivables = financial_data.get('accounts_receivable', 0)
            payables = financial_data.get('accounts_payable', 0)
            long_term_debt = financial_data.get('long_term_debt', 0)
            total_assets = financial_data.get('total_assets', 0)
            total_liabilities = financial_data.get('total_liabilities', 0)
            total_equity = financial_data.get('total_equity', 0)
            total_revenue = financial_data.get('total_revenue', 0)
            gross_profit = financial_data.get('gross_profit', 0)
            net_income = financial_data.get('net_income', 0)
            period_days = financial_data.get('period_days', 365)
            
            # Calculate Liquidity Ratios
            if current_liabilities > 0:
                ratios['liquidity']['current_ratio'] = {
                    'value': current_assets / current_liabilities,
                    'formula': 'Current Assets / Current Liabilities',
                    'description': 'Measures ability to pay short-term obligations'
                }
                
                quick_assets = current_assets - inventory
                ratios['liquidity']['quick_ratio'] = {
                    'value': quick_assets / current_liabilities,
                    'formula': '(Current Assets - Inventory) / Current Liabilities',
                    'description': 'Measures ability to pay short-term obligations without inventory'
                }
                
                ratios['liquidity']['cash_ratio'] = {
                    'value': cash / current_liabilities,
                    'formula': 'Cash / Current Liabilities',
                    'description': 'Measures ability to pay short-term obligations with cash only'
                }
            else:
                ratios['liquidity']['current_ratio'] = {'value': float('inf'), 'formula': 'Current Assets / Current Liabilities', 'description': 'No current liabilities'}
                ratios['liquidity']['quick_ratio'] = {'value': float('inf'), 'formula': '(Current Assets - Inventory) / Current Liabilities', 'description': 'No current liabilities'}
                ratios['liquidity']['cash_ratio'] = {'value': float('inf'), 'formula': 'Cash / Current Liabilities', 'description': 'No current liabilities'}
            
            # Working Capital
            ratios['liquidity']['working_capital'] = {
                'value': current_assets - current_liabilities,
                'formula': 'Current Assets - Current Liabilities',
                'description': 'Net working capital available for operations'
            }
            
            # Calculate Profitability Ratios
            if total_revenue > 0:
                ratios['profitability']['gross_profit_margin'] = {
                    'value': (gross_profit / total_revenue) * 100,
                    'formula': '(Gross Profit / Revenue) × 100',
                    'description': 'Percentage of revenue retained after cost of goods sold'
                }
                
                ratios['profitability']['net_profit_margin'] = {
                    'value': (net_income / total_revenue) * 100,
                    'formula': '(Net Income / Revenue) × 100',
                    'description': 'Percentage of revenue retained as net income'
                }
            else:
                ratios['profitability']['gross_profit_margin'] = {'value': 0, 'formula': '(Gross Profit / Revenue) × 100', 'description': 'No revenue'}
                ratios['profitability']['net_profit_margin'] = {'value': 0, 'formula': '(Net Income / Revenue) × 100', 'description': 'No revenue'}
            
            if total_assets > 0:
                ratios['profitability']['return_on_assets'] = {
                    'value': (net_income / total_assets) * 100,
                    'formula': '(Net Income / Total Assets) × 100',
                    'description': 'Return generated on total assets'
                }
            else:
                ratios['profitability']['return_on_assets'] = {'value': 0, 'formula': '(Net Income / Total Assets) × 100', 'description': 'No assets'}
            
            if total_equity > 0:
                ratios['profitability']['return_on_equity'] = {
                    'value': (net_income / total_equity) * 100,
                    'formula': '(Net Income / Total Equity) × 100',
                    'description': 'Return generated on shareholders equity'
                }
            else:
                ratios['profitability']['return_on_equity'] = {'value': 0, 'formula': '(Net Income / Total Equity) × 100', 'description': 'No equity'}
            
            # Calculate Leverage Ratios
            if total_equity > 0:
                ratios['leverage']['debt_to_equity'] = {
                    'value': total_liabilities / total_equity,
                    'formula': 'Total Liabilities / Total Equity',
                    'description': 'Proportion of debt financing relative to equity'
                }
            else:
                ratios['leverage']['debt_to_equity'] = {'value': float('inf'), 'formula': 'Total Liabilities / Total Equity', 'description': 'No equity'}
            
            if total_assets > 0:
                ratios['leverage']['debt_ratio'] = {
                    'value': total_liabilities / total_assets,
                    'formula': 'Total Liabilities / Total Assets',
                    'description': 'Proportion of assets financed by debt'
                }
                
                ratios['leverage']['equity_ratio'] = {
                    'value': total_equity / total_assets,
                    'formula': 'Total Equity / Total Assets',
                    'description': 'Proportion of assets financed by equity'
                }
            else:
                ratios['leverage']['debt_ratio'] = {'value': 0, 'formula': 'Total Liabilities / Total Assets', 'description': 'No assets'}
                ratios['leverage']['equity_ratio'] = {'value': 0, 'formula': 'Total Equity / Total Assets', 'description': 'No assets'}
            
            # Calculate Efficiency Ratios
            if total_assets > 0:
                ratios['efficiency']['asset_turnover'] = {
                    'value': total_revenue / total_assets,
                    'formula': 'Revenue / Total Assets',
                    'description': 'Revenue generated per dollar of assets'
                }
            else:
                ratios['efficiency']['asset_turnover'] = {'value': 0, 'formula': 'Revenue / Total Assets', 'description': 'No assets'}
            
            if inventory > 0:
                ratios['efficiency']['inventory_turnover'] = {
                    'value': (financial_data.get('total_cogs', 0) / inventory) if inventory > 0 else 0,
                    'formula': 'Cost of Goods Sold / Average Inventory',
                    'description': 'Number of times inventory is sold and replaced'
                }
            else:
                ratios['efficiency']['inventory_turnover'] = {'value': 0, 'formula': 'Cost of Goods Sold / Average Inventory', 'description': 'No inventory'}
            
            if receivables > 0:
                ratios['efficiency']['receivables_turnover'] = {
                    'value': total_revenue / receivables,
                    'formula': 'Revenue / Accounts Receivable',
                    'description': 'Number of times receivables are collected'
                }
                
                ratios['efficiency']['days_sales_outstanding'] = {
                    'value': (receivables / total_revenue) * period_days,
                    'formula': '(Accounts Receivable / Revenue) × Days in Period',
                    'description': 'Average days to collect receivables'
                }
            else:
                ratios['efficiency']['receivables_turnover'] = {'value': 0, 'formula': 'Revenue / Accounts Receivable', 'description': 'No receivables'}
                ratios['efficiency']['days_sales_outstanding'] = {'value': 0, 'formula': '(Accounts Receivable / Revenue) × Days in Period', 'description': 'No receivables'}
            
            return ratios
            
        except Exception as e:
            self.logger.error(f"Error calculating ratios from financial data: {e}")
            return {}
    
    def _get_group_balance(self, group_name: str, balance_sheet: Dict) -> float:
        """Get total balance for a specific account group from group-based balance sheet."""
        try:
            # Debug logging
            self.logger.info(f"Looking for group '{group_name}' in balance sheet")
            self.logger.info(f"Available asset sections: {[s.get('group', 'unknown') for s in balance_sheet.get('asset_sections', [])]}")
            self.logger.info(f"Available liability sections: {[s.get('group', 'unknown') for s in balance_sheet.get('liability_sections', [])]}")
            self.logger.info(f"Available equity sections: {[s.get('group', 'unknown') for s in balance_sheet.get('equity_sections', [])]}")
            
            # Look for the group in asset sections
            for section in balance_sheet.get('asset_sections', []):
                if section.get('group') == group_name:
                    total = section.get('total', 0)
                    self.logger.info(f"Found group '{group_name}' in asset sections with total: {total}")
                    return total
            
            # Look for the group in liability sections
            for section in balance_sheet.get('liability_sections', []):
                if section.get('group') == group_name:
                    total = section.get('total', 0)
                    self.logger.info(f"Found group '{group_name}' in liability sections with total: {total}")
                    return total
            
            # Look for the group in equity sections
            for section in balance_sheet.get('equity_sections', []):
                if section.get('group') == group_name:
                    total = section.get('total', 0)
                    self.logger.info(f"Found group '{group_name}' in equity sections with total: {total}")
                    return total
            
            self.logger.warning(f"Group '{group_name}' not found in any section")
            return 0.0
            
        except Exception as e:
            self.logger.error(f"Failed to get balance for group {group_name}: {e}")
            return 0.0
    
    def _extract_cash_from_current_assets(self, balance_sheet: Dict) -> float:
        """Extract cash balance from current assets section."""
        try:
            for section in balance_sheet.get('asset_sections', []):
                if section.get('group') == 'current_asset':
                    accounts = section.get('accounts', [])
                    cash_total = 0.0
                    for account in accounts:
                        # Look for cash-related accounts in the hierarchy
                        if self._is_cash_account(account):
                            cash_total += account.get('balance', 0)
                        # Also check children recursively
                        cash_total += self._extract_cash_from_account_tree(account)
                    return cash_total
            return 0.0
        except Exception as e:
            self.logger.error(f"Failed to extract cash: {e}")
            return 0.0
    
    def _extract_inventory_from_other_assets(self, balance_sheet: Dict) -> float:
        """Extract inventory balance from other assets section."""
        try:
            for section in balance_sheet.get('asset_sections', []):
                if section.get('group') == 'other_asset':
                    accounts = section.get('accounts', [])
                    inventory_total = 0.0
                    for account in accounts:
                        # Look for inventory-related accounts in the hierarchy
                        if self._is_inventory_account(account):
                            inventory_total += account.get('balance', 0)
                        # Also check children recursively
                        inventory_total += self._extract_inventory_from_account_tree(account)
                    return inventory_total
            return 0.0
        except Exception as e:
            self.logger.error(f"Failed to extract inventory: {e}")
            return 0.0
    
    def _extract_receivables_from_current_assets(self, balance_sheet: Dict) -> float:
        """Extract accounts receivable from current assets section."""
        try:
            for section in balance_sheet.get('asset_sections', []):
                if section.get('group') == 'current_asset':
                    accounts = section.get('accounts', [])
                    receivables_total = 0.0
                    for account in accounts:
                        # Look for receivable-related accounts in the hierarchy
                        if self._is_receivable_account(account):
                            receivables_total += account.get('balance', 0)
                        # Also check children recursively
                        receivables_total += self._extract_receivables_from_account_tree(account)
                    return receivables_total
            return 0.0
        except Exception as e:
            self.logger.error(f"Failed to extract receivables: {e}")
            return 0.0
    
    def _extract_payables_from_current_liabilities(self, balance_sheet: Dict) -> float:
        """Extract accounts payable from current liabilities section."""
        try:
            for section in balance_sheet.get('liability_sections', []):
                if section.get('group') == 'current_liability':
                    accounts = section.get('accounts', [])
                    payables_total = 0.0
                    for account in accounts:
                        # Look for payable-related accounts in the hierarchy
                        if self._is_payable_account(account):
                            payables_total += account.get('balance', 0)
                        # Also check children recursively
                        payables_total += self._extract_payables_from_account_tree(account)
                    return payables_total
            return 0.0
        except Exception as e:
            self.logger.error(f"Failed to extract payables: {e}")
            return 0.0
    
    def _is_cash_account(self, account: Dict) -> bool:
        """Check if account is a cash account."""
        name = account.get('name', '').lower()
        return any(keyword in name for keyword in ['cash', 'bank', 'checking', 'savings', 'money market'])
    
    def _is_inventory_account(self, account: Dict) -> bool:
        """Check if account is an inventory account."""
        name = account.get('name', '').lower()
        return any(keyword in name for keyword in ['inventory', 'stock', 'goods'])
    
    def _is_receivable_account(self, account: Dict) -> bool:
        """Check if account is a receivable account."""
        name = account.get('name', '').lower()
        return any(keyword in name for keyword in ['receivable', 'ar', 'accounts receivable'])
    
    def _is_payable_account(self, account: Dict) -> bool:
        """Check if account is a payable account."""
        name = account.get('name', '').lower()
        return any(keyword in name for keyword in ['payable', 'ap', 'accounts payable'])
    
    def _extract_cash_from_account_tree(self, account: Dict) -> float:
        """Recursively extract cash from account tree."""
        total = 0.0
        children = account.get('children', [])
        for child in children:
            if self._is_cash_account(child):
                total += child.get('balance', 0)
            total += self._extract_cash_from_account_tree(child)
        return total
    
    def _extract_inventory_from_account_tree(self, account: Dict) -> float:
        """Recursively extract inventory from account tree."""
        total = 0.0
        children = account.get('children', [])
        for child in children:
            if self._is_inventory_account(child):
                total += child.get('balance', 0)
            total += self._extract_inventory_from_account_tree(child)
        return total
    
    def _extract_receivables_from_account_tree(self, account: Dict) -> float:
        """Recursively extract receivables from account tree."""
        total = 0.0
        children = account.get('children', [])
        for child in children:
            if self._is_receivable_account(child):
                total += child.get('balance', 0)
            total += self._extract_receivables_from_account_tree(child)
        return total
    
    def _extract_payables_from_account_tree(self, account: Dict) -> float:
        """Recursively extract payables from account tree."""
        total = 0.0
        children = account.get('children', [])
        for child in children:
            if self._is_payable_account(child):
                total += child.get('balance', 0)
            total += self._extract_payables_from_account_tree(child)
        return total
    
    def _calculate_liquidity_ratios(self, financial_data: Dict[str, Any]) -> Dict[str, Dict]:
        """Calculate liquidity ratios."""
        ratios = {}
        
        # Debug logging
        self.logger.info(f"Calculating liquidity ratios - Current Assets: {financial_data.get('current_assets', 0)}, Current Liabilities: {financial_data.get('current_liabilities', 0)}")
        
        # Current Ratio
        current_assets = financial_data.get('current_assets', 0)
        current_liabilities = financial_data.get('current_liabilities', 0)
        
        if current_liabilities > 0:
            current_ratio = current_assets / current_liabilities
            ratios['current_ratio'] = {
                'value': float(current_ratio),
                'description': 'Current Assets / Current Liabilities',
                'interpretation': 'Ability to pay short-term debts',
                'unit': 'ratio'
            }
            self.logger.info(f"Current Ratio calculated: {current_ratio}")
        else:
            self.logger.warning(f"Current Ratio not calculated - Current Liabilities is {current_liabilities}")
        
        # Quick Ratio (Acid Test)
        if current_liabilities > 0:
            inventory = financial_data.get('inventory', 0)
            quick_assets = current_assets - inventory
            quick_ratio = quick_assets / current_liabilities
            ratios['quick_ratio'] = {
                'value': float(quick_ratio),
                'description': '(Current Assets - Inventory) / Current Liabilities',
                'interpretation': 'Ability to pay short-term debts without selling inventory',
                'unit': 'ratio'
            }
            self.logger.info(f"Quick Ratio calculated: {quick_ratio} (Quick Assets: {quick_assets}, Inventory: {inventory})")
        else:
            self.logger.warning(f"Quick Ratio not calculated - Current Liabilities is {current_liabilities}")
        
        # Cash Ratio
        if current_liabilities > 0:
            cash = financial_data.get('cash', 0)
            cash_ratio = cash / current_liabilities
            ratios['cash_ratio'] = {
                'value': float(cash_ratio),
                'description': 'Cash / Current Liabilities',
                'interpretation': 'Ability to pay short-term debts with cash only',
                'unit': 'ratio'
            }
            self.logger.info(f"Cash Ratio calculated: {cash_ratio} (Cash: {cash})")
        else:
            self.logger.warning(f"Cash Ratio not calculated - Current Liabilities is {current_liabilities}")
        
        # Working Capital (always calculate this)
        working_capital = current_assets - current_liabilities
        ratios['working_capital'] = {
            'value': float(working_capital),
            'description': 'Current Assets - Current Liabilities',
            'interpretation': 'Available short-term financial resources',
            'unit': 'currency'
        }
        self.logger.info(f"Working Capital calculated: {working_capital}")
        
        self.logger.info(f"Liquidity ratios calculated: {list(ratios.keys())}")
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
        
        # Handle the new database function format
        if 'liquidity' in ratios or 'profitability' in ratios or 'leverage' in ratios or 'efficiency' in ratios:
            # New format with categories
            for category_name, category_ratios in ratios.items():
                if isinstance(category_ratios, dict):
                    for ratio_name, ratio_value in category_ratios.items():
                        if ratio_name in critical_thresholds:
                            thresholds = critical_thresholds[ratio_name]
                            
                            # Handle both dict format and direct value format
                            if isinstance(ratio_value, dict):
                                value = ratio_value.get('value', 0)
                            else:
                                value = float(ratio_value) if ratio_value is not None else 0
                            
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
        else:
            # Old format - handle as before
            for category_name, category_ratios in ratios.items():
                if isinstance(category_ratios, dict):
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
        try:
            summary = {
                'total_ratios': 0,
                'categories': {},
                'overall_health': 'GOOD'
            }
            
            # Handle new database function format
            if 'liquidity' in ratios or 'profitability' in ratios or 'leverage' in ratios or 'efficiency' in ratios:
                for category_name, category_ratios in ratios.items():
                    if isinstance(category_ratios, dict):
                        category_count = len(category_ratios)
                        summary['categories'][category_name] = category_count
                        summary['total_ratios'] += category_count
            else:
                # Handle old format
                for category_name, category_ratios in ratios.items():
                    if isinstance(category_ratios, dict):
                        category_count = len(category_ratios)
                        summary['categories'][category_name] = category_count
                        summary['total_ratios'] += category_count
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error calculating ratio summary: {e}")
            return {'total_ratios': 0, 'categories': {}, 'overall_health': 'UNKNOWN'}
    
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
