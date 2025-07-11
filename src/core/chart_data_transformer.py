"""
Chart Data Transformer
Transforms existing financial data for chart visualization without duplicating calculations.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import calendar


class ChartDataTransformer:
    """Transforms existing financial data for chart display without duplicating calculations."""
    
    def __init__(self, accounting_system):
        self.accounting_system = accounting_system
    
    def transform_income_statement_to_expense_chart(self, income_statement: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Transform income statement data to expense donut chart format.
        Uses existing income statement instead of duplicating expense calculations.
        """
        try:
            # Validate input
            if not income_statement:
                print("Warning: No income statement data provided")
                return []
            
            # Define colors for each expense group
            group_colors = {
                'cogs': '#f44336',  # Red for COGS
                'operating_expense': '#ff9800',  # Orange for Operating
                'administrative_expense': '#9c27b0',  # Purple for Admin
                'selling_expense': '#2196f3',  # Blue for Selling
                'financial_expense': '#ff5722',  # Deep Orange for Financial
                'other_expense': '#607d8b'  # Blue Grey for Other
            }
            
            expense_breakdown = []
            
            # Extract expense data from income statement
            expenses = income_statement.get('expenses', [])
            
            if not expenses:
                print("Warning: No expenses found in income statement")
                return []
            
            # Group expenses by type (simplified grouping)
            expense_groups = {}
            for expense_item in expenses:
                # Handle different expense data formats
                if isinstance(expense_item, (list, tuple)) and len(expense_item) >= 2:
                    expense_name, amount = expense_item[0], expense_item[1]
                elif isinstance(expense_item, dict):
                    expense_name = expense_item.get('name', 'Unknown')
                    amount = expense_item.get('amount', 0)
                else:
                    print(f"Warning: Skipping invalid expense item: {expense_item}")
                    continue
                
                # Simple grouping logic - in practice, you'd use account classifications
                if 'cost' in expense_name.lower() or 'cogs' in expense_name.lower():
                    group_key = 'cogs'
                    group_name = 'Cost of Goods Sold'
                elif 'admin' in expense_name.lower():
                    group_key = 'administrative_expense'
                    group_name = 'Administrative Expenses'
                elif 'selling' in expense_name.lower() or 'marketing' in expense_name.lower():
                    group_key = 'selling_expense'
                    group_name = 'Selling Expenses'
                elif 'financial' in expense_name.lower() or 'interest' in expense_name.lower():
                    group_key = 'financial_expense'
                    group_name = 'Financial Expenses'
                else:
                    group_key = 'operating_expense'
                    group_name = 'Operating Expenses'
                
                if group_key not in expense_groups:
                    expense_groups[group_key] = {'name': group_name, 'amount': 0}
                expense_groups[group_key]['amount'] += amount
            
            # Convert to chart format
            for group_key, group_data in expense_groups.items():
                if group_data['amount'] > 0:
                    expense_breakdown.append({
                        'group': group_key,
                        'name': group_data['name'],
                        'amount': group_data['amount'],
                        'color': group_colors.get(group_key, '#607d8b')
                    })
            
            # Sort by amount (largest first)
            expense_breakdown.sort(key=lambda x: x['amount'], reverse=True)
            
            return expense_breakdown
            
        except Exception as e:
            print(f"Error transforming income statement to expense chart: {e}")
            return []
    
    def transform_ledger_to_balance_chart(self, ledger_data: List[tuple], 
                                        account_name: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """
        Transform ledger data to balance chart format.
        Uses existing ledger data instead of duplicating balance calculations.
        """
        try:
            # Generate periods for the date range
            periods = self._generate_periods(start_date, end_date)
            
            # For each period, calculate running balance from ledger entries
            historical_balances = []
            
            for period in periods:
                # Calculate balance as of this period end
                period_date = datetime.strptime(period['date'], "%Y-%m-%d")
                
                # Sum all ledger entries up to this date
                running_balance = 0
                for entry in ledger_data:
                    entry_date = datetime.strptime(entry[0], "%Y-%m-%d")  # Assuming date is first element
                    if entry_date <= period_date:
                        # Add or subtract based on entry type
                        # This is simplified - actual implementation would depend on ledger format
                        amount = entry[2] if len(entry) > 2 else 0  # Assuming amount is third element
                        running_balance += amount
                
                historical_balances.append({
                    'period': period['label'],
                    'date': period['date'],
                    'balance': running_balance
                })
            
            return historical_balances
            
        except Exception as e:
            print(f"Error transforming ledger to balance chart: {e}")
            return []
    
    def transform_trial_balance_to_comparison_chart(self, trial_balance: List[Dict[str, Any]], 
                                                  account1_name: str, account2_name: str) -> Dict[str, Any]:
        """
        Transform trial balance data to account comparison chart format.
        Uses existing trial balance instead of duplicating balance calculations.
        """
        try:
            # Find the two accounts in trial balance
            account1_data = None
            account2_data = None
            
            for entry in trial_balance:
                if entry['name'] == account1_name:
                    account1_data = entry
                elif entry['name'] == account2_name:
                    account2_data = entry
            
            # Extract balance data
            account1_balance = account1_data.get('net_balance', 0) if account1_data else 0
            account2_balance = account2_data.get('net_balance', 0) if account2_data else 0
            
            return {
                'month_labels': ['Current'],  # Simplified - would be historical periods
                'account1': {
                    'name': account1_name,
                    'balances': [account1_balance]
                },
                'account2': {
                    'name': account2_name,
                    'balances': [account2_balance]
                },
                'months': 1
            }
            
        except Exception as e:
            print(f"Error transforming trial balance to comparison chart: {e}")
            return {
                'month_labels': [],
                'account1': {'name': account1_name, 'balances': []},
                'account2': {'name': account2_name, 'balances': []},
                'months': 0
            }
    
    def _generate_periods(self, start_date: str, end_date: str) -> List[Dict[str, str]]:
        """Generate monthly periods between start and end dates."""
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
            
            periods = []
            current = start.replace(day=1)
            
            while current <= end:
                # Get last day of this month
                last_day = calendar.monthrange(current.year, current.month)[1]
                month_end = current.replace(day=last_day)
                
                # Only include if within range
                if month_end >= start and month_end <= end:
                    periods.append({
                        'label': current.strftime('%b'),
                        'date': month_end.strftime('%Y-%m-%d')
                    })
                
                # Move to next month
                if current.month == 12:
                    current = current.replace(year=current.year + 1, month=1)
                else:
                    current = current.replace(month=current.month + 1)
            
            return periods
            
        except Exception as e:
            print(f"Error generating periods: {e}")
            return [] 