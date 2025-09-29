"""
Advanced Cash Flow Management and Classification System
"""

import uuid
from datetime import datetime, date, timedelta
from decimal import Decimal
import logging
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

class CashFlowCategory(Enum):
    OPERATING = "OPERATING"
    INVESTING = "INVESTING" 
    FINANCING = "FINANCING"

@dataclass
class CashFlowItem:
    """Cash flow item data structure."""
    account_code: str
    account_name: str
    amount: Decimal
    category: CashFlowCategory
    subcategory: str
    description: str
    transaction_date: date

@dataclass
class CashFlowAnalysis:
    """Cash flow analysis results."""
    operating_cash_flow: Decimal
    investing_cash_flow: Decimal
    financing_cash_flow: Decimal
    net_cash_flow: Decimal
    cash_conversion_cycle: Optional[float]
    free_cash_flow: Optional[Decimal]

class AdvancedCashFlowManager:
    """Advanced cash flow management with intelligent classification."""
    
    def __init__(self, db_manager, accounting_system=None):
        self.db_manager = db_manager
        self.accounting_system = accounting_system
        self.logger = logging.getLogger(__name__)
    
    def classify_transaction(self, account_code: str, account_name: str, 
                           description: str, amount: Decimal) -> CashFlowCategory:
        """Intelligently classify a transaction into cash flow categories."""
        
        # First check explicit classifications
        explicit_category = self._get_account_classification(account_code)
        if explicit_category:
            return CashFlowCategory(explicit_category)
        
        # Use intelligent classification based on account type and keywords
        account_name_lower = account_name.lower()
        description_lower = description.lower() if description else ""
        
        # Operating Activities - Primary business operations
        operating_indicators = [
            # Revenue indicators
            'revenue', 'sales', 'income', 'service', 'fees', 'commission',
            # Expense indicators  
            'salary', 'wage', 'rent', 'utilities', 'insurance', 'supplies',
            'advertising', 'marketing', 'professional', 'maintenance',
            # Working capital indicators
            'receivable', 'payable', 'inventory', 'prepaid', 'accrued',
            'customer', 'supplier', 'vendor'
        ]
        
        # Investing Activities - Long-term assets and investments
        investing_indicators = [
            'equipment', 'machinery', 'building', 'land', 'vehicle',
            'computer', 'furniture', 'asset', 'investment', 'security',
            'bond', 'stock', 'acquisition', 'disposal', 'sale of equipment',
            'purchase of equipment', 'depreciation', 'amortization'
        ]
        
        # Financing Activities - Capital structure changes
        financing_indicators = [
            'loan', 'debt', 'mortgage', 'bond', 'note payable',
            'capital', 'equity', 'stock', 'dividend', 'distribution',
            'owner', 'shareholder', 'investment', 'withdrawal',
            'borrowing', 'repayment', 'principal', 'financing'
        ]
        
        # Check for investing activities first (more specific)
        if any(indicator in account_name_lower or indicator in description_lower 
               for indicator in investing_indicators):
            return CashFlowCategory.INVESTING
        
        # Check for financing activities
        if any(indicator in account_name_lower or indicator in description_lower 
               for indicator in financing_indicators):
            return CashFlowCategory.FINANCING
        
        # Default to operating activities
        return CashFlowCategory.OPERATING
    
    def generate_enhanced_cash_flow_statement(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """Generate enhanced cash flow statement with detailed analysis."""
        
        # Get all cash transactions for the period
        cash_transactions = self._get_cash_transactions(start_date, end_date)
        
        # Classify transactions
        operating_items = []
        investing_items = []
        financing_items = []
        
        for transaction in cash_transactions:
            category = self.classify_transaction(
                transaction['account_code'],
                transaction['account_name'], 
                transaction['description'],
                transaction['amount']
            )
            
            cash_flow_item = CashFlowItem(
                account_code=transaction['account_code'],
                account_name=transaction['account_name'],
                amount=transaction['amount'],
                category=category,
                subcategory=self._determine_subcategory(transaction, category),
                description=transaction['description'],
                transaction_date=transaction['transaction_date']
            )
            
            if category == CashFlowCategory.OPERATING:
                operating_items.append(cash_flow_item)
            elif category == CashFlowCategory.INVESTING:
                investing_items.append(cash_flow_item)
            elif category == CashFlowCategory.FINANCING:
                financing_items.append(cash_flow_item)
        
        # Calculate totals
        operating_total = sum(item.amount for item in operating_items)
        investing_total = sum(item.amount for item in investing_items)
        financing_total = sum(item.amount for item in financing_items)
        net_cash_flow = operating_total + investing_total + financing_total
        
        # Calculate additional metrics
        free_cash_flow = self._calculate_free_cash_flow(operating_total, start_date, end_date)
        cash_conversion_cycle = self._calculate_cash_conversion_cycle(start_date, end_date)
        
        return {
            'period': f"{start_date} to {end_date}",
            'operating_activities': {
                'items': self._group_cash_flow_items(operating_items),
                'total': operating_total,
                'subcategory_totals': self._calculate_subcategory_totals(operating_items)
            },
            'investing_activities': {
                'items': self._group_cash_flow_items(investing_items),
                'total': investing_total,
                'subcategory_totals': self._calculate_subcategory_totals(investing_items)
            },
            'financing_activities': {
                'items': self._group_cash_flow_items(financing_items),
                'total': financing_total,
                'subcategory_totals': self._calculate_subcategory_totals(financing_items)
            },
            'net_cash_flow': net_cash_flow,
            'free_cash_flow': free_cash_flow,
            'cash_conversion_cycle': cash_conversion_cycle,
            'cash_flow_analysis': self._perform_cash_flow_analysis(
                operating_total, investing_total, financing_total, start_date, end_date
            )
        }
    
    def update_account_classification(self, account_code: str, category: CashFlowCategory,
                                    subcategory: str = None, effective_from: date = None) -> bool:
        """Update cash flow classification for an account."""
        if effective_from is None:
            effective_from = date.today()
        
        # End current classification
        end_current_sql = """
        UPDATE cash_flow_classifications 
        SET effective_to = %s
        WHERE account_code = %s AND effective_to IS NULL
        """
        
        # Insert new classification
        insert_new_sql = """
        INSERT INTO cash_flow_classifications 
        (account_code, cash_flow_category, subcategory, effective_from)
        VALUES (%s, %s, %s, %s)
        """
        
        try:
            with self.db_manager.get_db_cursor() as cursor:
                # End current classification
                cursor.execute(end_current_sql, (effective_from, account_code))
                
                # Insert new classification
                cursor.execute(insert_new_sql, (
                    account_code, category.value, subcategory, effective_from
                ))
            
            self.logger.info(f"Updated cash flow classification for {account_code} to {category.value}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update account classification: {e}")
            return False
    
    def get_cash_flow_trends(self, months: int = 12) -> Dict[str, Any]:
        """Get cash flow trends over specified months."""
        trends_data = []
        
        for i in range(months):
            period_end = date.today().replace(day=1) - timedelta(days=1)  # Last day of previous month
            period_start = period_end.replace(day=1)  # First day of month
            
            # Move back i months
            for _ in range(i):
                period_start = (period_start - timedelta(days=1)).replace(day=1)
                period_end = period_start.replace(
                    month=period_start.month + 1 if period_start.month < 12 else 1,
                    year=period_start.year if period_start.month < 12 else period_start.year + 1
                ) - timedelta(days=1)
            
            cash_flow_data = self.generate_enhanced_cash_flow_statement(period_start, period_end)
            
            trends_data.append({
                'period': f"{period_start.strftime('%Y-%m')}",
                'operating_cash_flow': cash_flow_data['operating_activities']['total'],
                'investing_cash_flow': cash_flow_data['investing_activities']['total'],
                'financing_cash_flow': cash_flow_data['financing_activities']['total'],
                'net_cash_flow': cash_flow_data['net_cash_flow'],
                'free_cash_flow': cash_flow_data['free_cash_flow']
            })
        
        # Calculate trend indicators
        operating_trend = self._calculate_trend(
            [period['operating_cash_flow'] for period in trends_data]
        )
        
        return {
            'trends_data': list(reversed(trends_data)),  # Most recent first
            'trend_analysis': {
                'operating_trend': operating_trend,
                'average_operating_cf': sum(p['operating_cash_flow'] for p in trends_data) / len(trends_data),
                'cash_flow_volatility': self._calculate_volatility(
                    [p['net_cash_flow'] for p in trends_data]
                )
            }
        }
    
    def _get_cash_transactions(self, start_date: date, end_date: date) -> List[Dict]:
        """Get all cash-affecting transactions for the period."""
        # This assumes we have enhanced journal entries structure
        # Fall back to basic structure if enhanced not available
        
        try:
            # Try enhanced structure first
            cash_sql = """
            SELECT 
                l.account_code,
                l.account_name,
                l.description,
                CASE 
                    WHEN l.debit_amount > 0 THEN l.debit_amount
                    ELSE -l.credit_amount 
                END as amount,
                h.entry_date as transaction_date
            FROM journal_entry_lines l
            JOIN journal_entry_headers h ON l.header_id = h.id
            JOIN cash_flow_classifications c ON l.account_code = c.account_code
            WHERE h.entry_date BETWEEN %s AND %s
            AND h.status = 'POSTED'
            AND c.is_cash_account = TRUE
            AND c.effective_from <= h.entry_date
            AND (c.effective_to IS NULL OR c.effective_to > h.entry_date)
            ORDER BY h.entry_date, l.line_number
            """
            
            with self.db_manager.get_db_cursor() as cursor:
                cursor.execute(cash_sql, (start_date, end_date))
                return cursor.fetchall()
                
        except Exception as e:
            self.logger.warning(f"Enhanced cash transactions query failed, falling back to basic: {e}")
            return self._get_basic_cash_transactions(start_date, end_date)
    
    def _get_basic_cash_transactions(self, start_date: date, end_date: date) -> List[Dict]:
        """Fallback method using basic journal entries structure."""
        cash_accounts = ['Cash', 'Cash in Hand', 'Cash at Bank', 'Petty Cash']
        transactions = []
        
        if self.accounting_system:
            try:
                # Get journal entries for cash accounts
                for cash_account in cash_accounts:
                    ledger_entries = self.accounting_system.get_ledger(
                        cash_account, 
                        start_date.strftime('%Y-%m-%d'), 
                        end_date.strftime('%Y-%m-%d')
                    )
                    
                    for entry in ledger_entries:
                        amount = 0
                        other_account = ""
                        
                        if entry[2] == cash_account:  # debit_account
                            amount = entry[4]  # Positive for cash inflow
                            other_account = entry[3]  # credit_account
                        elif entry[3] == cash_account:  # credit_account
                            amount = -entry[4]  # Negative for cash outflow
                            other_account = entry[2]  # debit_account
                        
                        transactions.append({
                            'account_code': cash_account[:4] if len(cash_account) > 4 else cash_account,
                            'account_name': other_account,
                            'description': entry[1],  # description
                            'amount': Decimal(str(amount)),
                            'transaction_date': entry[0]  # date
                        })
                        
            except Exception as e:
                self.logger.error(f"Failed to get basic cash transactions: {e}")
        
        return transactions
    
    def _get_account_classification(self, account_code: str) -> Optional[str]:
        """Get explicit cash flow classification for an account."""
        classification_sql = """
        SELECT cash_flow_category
        FROM cash_flow_classifications
        WHERE account_code = %s
        AND effective_from <= CURRENT_DATE
        AND (effective_to IS NULL OR effective_to > CURRENT_DATE)
        ORDER BY effective_from DESC
        LIMIT 1
        """
        
        try:
            with self.db_manager.get_db_cursor() as cursor:
                cursor.execute(classification_sql, (account_code,))
                result = cursor.fetchone()
                return result['cash_flow_category'] if result else None
        except Exception as e:
            self.logger.error(f"Failed to get account classification: {e}")
            return None
    
    def _determine_subcategory(self, transaction: Dict, category: CashFlowCategory) -> str:
        """Determine subcategory based on transaction details."""
        account_name = transaction['account_name'].lower()
        description = transaction.get('description', '').lower()
        
        if category == CashFlowCategory.OPERATING:
            if any(word in account_name or word in description 
                   for word in ['revenue', 'sales', 'income']):
                return 'Cash from customers'
            elif any(word in account_name or word in description 
                     for word in ['payable', 'supplier', 'vendor']):
                return 'Cash to suppliers'
            elif any(word in account_name or word in description 
                     for word in ['salary', 'wage', 'payroll']):
                return 'Cash to employees'
            else:
                return 'Other operating'
        
        elif category == CashFlowCategory.INVESTING:
            if any(word in account_name or word in description 
                   for word in ['equipment', 'machinery', 'building']):
                return 'Property, plant & equipment'
            elif any(word in account_name or word in description 
                     for word in ['investment', 'security', 'bond']):
                return 'Investments'
            else:
                return 'Other investing'
        
        elif category == CashFlowCategory.FINANCING:
            if any(word in account_name or word in description 
                   for word in ['loan', 'debt', 'borrowing']):
                return 'Debt financing'
            elif any(word in account_name or word in description 
                     for word in ['capital', 'equity', 'owner']):
                return 'Equity financing'
            else:
                return 'Other financing'
        
        return 'Other'
    
    def _group_cash_flow_items(self, items: List[CashFlowItem]) -> Dict[str, List[Dict]]:
        """Group cash flow items by subcategory."""
        grouped = {}
        for item in items:
            if item.subcategory not in grouped:
                grouped[item.subcategory] = []
            
            grouped[item.subcategory].append({
                'account_name': item.account_name,
                'amount': float(item.amount),
                'description': item.description,
                'date': item.transaction_date.isoformat()
            })
        
        return grouped
    
    def _calculate_subcategory_totals(self, items: List[CashFlowItem]) -> Dict[str, Decimal]:
        """Calculate totals by subcategory."""
        totals = {}
        for item in items:
            if item.subcategory not in totals:
                totals[item.subcategory] = Decimal('0')
            totals[item.subcategory] += item.amount
        
        return {k: float(v) for k, v in totals.items()}
    
    def _calculate_free_cash_flow(self, operating_cash_flow: Decimal, 
                                 start_date: date, end_date: date) -> Optional[Decimal]:
        """Calculate free cash flow (Operating CF - Capital Expenditures)."""
        try:
            # Get capital expenditures (investing activities that are asset purchases)
            capex_sql = """
            SELECT SUM(ABS(amount)) as capex
            FROM (
                SELECT amount FROM cash_flow_view
                WHERE transaction_date BETWEEN %s AND %s
                AND cash_flow_category = 'INVESTING'
                AND amount < 0  -- Cash outflows for asset purchases
            ) capex_data
            """
            
            with self.db_manager.get_db_cursor() as cursor:
                cursor.execute(capex_sql, (start_date, end_date))
                result = cursor.fetchone()
                capex = result['capex'] or Decimal('0')
                
                return operating_cash_flow - capex
                
        except Exception as e:
            self.logger.error(f"Failed to calculate free cash flow: {e}")
            return None
    
    def _calculate_cash_conversion_cycle(self, start_date: date, end_date: date) -> Optional[float]:
        """Calculate cash conversion cycle (Days Sales Outstanding + Days Inventory Outstanding - Days Payable Outstanding)."""
        try:
            if not self.accounting_system:
                return None
            
            # This would require more sophisticated calculation
            # For now, return None as placeholder
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to calculate cash conversion cycle: {e}")
            return None
    
    def _perform_cash_flow_analysis(self, operating_cf: Decimal, investing_cf: Decimal,
                                  financing_cf: Decimal, start_date: date, end_date: date) -> Dict[str, Any]:
        """Perform advanced cash flow analysis."""
        
        analysis = {
            'cash_flow_strength': 'Unknown',
            'concerns': [],
            'recommendations': [],
            'ratios': {}
        }
        
        # Analyze cash flow patterns
        if operating_cf > 0:
            if investing_cf < 0 and financing_cf <= 0:
                analysis['cash_flow_strength'] = 'Strong - Self-funding growth'
            elif investing_cf < 0 and financing_cf > 0:
                analysis['cash_flow_strength'] = 'Moderate - Funding growth with external capital'
            else:
                analysis['cash_flow_strength'] = 'Good - Positive operating cash flow'
        else:
            analysis['cash_flow_strength'] = 'Weak - Negative operating cash flow'
            analysis['concerns'].append('Negative operating cash flow indicates operational challenges')
        
        # Add specific recommendations
        if operating_cf < 0:
            analysis['recommendations'].append('Focus on improving operational efficiency and cash management')
        
        if investing_cf > operating_cf and operating_cf > 0:
            analysis['recommendations'].append('High investment relative to operating cash flow - monitor sustainability')
        
        if financing_cf > 0 and operating_cf < 0:
            analysis['recommendations'].append('Relying on external financing due to operational cash flow deficit')
        
        return analysis
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction from a list of values."""
        if len(values) < 2:
            return 'Insufficient data'
        
        # Simple linear trend calculation
        recent_avg = sum(values[:3]) / min(3, len(values))  # Most recent 3 periods
        older_avg = sum(values[-3:]) / min(3, len(values))  # Oldest 3 periods
        
        if recent_avg > older_avg * 1.1:
            return 'Improving'
        elif recent_avg < older_avg * 0.9:
            return 'Declining'
        else:
            return 'Stable'
    
    def _calculate_volatility(self, values: List[float]) -> float:
        """Calculate volatility (coefficient of variation) of cash flows."""
        if len(values) < 2:
            return 0.0
        
        mean_value = sum(values) / len(values)
        if mean_value == 0:
            return 0.0
        
        variance = sum((x - mean_value) ** 2 for x in values) / len(values)
        std_dev = variance ** 0.5
        
        return std_dev / abs(mean_value)  # Coefficient of variation
