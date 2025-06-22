"""
Comprehensive Budget Management System with Variance Analysis
"""

import uuid
from datetime import datetime, date, timedelta
from decimal import Decimal
import logging
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

class BudgetStatus(Enum):
    DRAFT = "DRAFT"
    APPROVED = "APPROVED"
    ACTIVE = "ACTIVE"
    LOCKED = "LOCKED"

class VarianceType(Enum):
    FAVORABLE = "FAVORABLE"
    UNFAVORABLE = "UNFAVORABLE"

@dataclass
class BudgetLine:
    """Budget line item data structure."""
    account_code: str
    account_name: str
    period_month: int
    budgeted_amount: Decimal
    actual_amount: Optional[Decimal] = None
    variance_amount: Optional[Decimal] = None
    variance_percent: Optional[float] = None

@dataclass
class VarianceAnalysis:
    """Variance analysis results."""
    total_budget: Decimal
    total_actual: Decimal
    total_variance: Decimal
    variance_percent: float
    favorable_variances: List[BudgetLine]
    unfavorable_variances: List[BudgetLine]

class BudgetManager:
    """Comprehensive budget management with variance analysis."""
    
    def __init__(self, db_manager, accounting_system=None, organization_id=None):
        self.db_manager = db_manager
        self.accounting_system = accounting_system
        self.organization_id = organization_id
        self.logger = logging.getLogger(__name__)
    
    def create_budget(self, budget_name: str, fiscal_year: int, 
                     start_date: date, end_date: date, created_by: str) -> str:
        """Create a new budget."""
        budget_id = str(uuid.uuid4())
        
        # Validate dates
        if start_date >= end_date:
            raise ValueError("Start date must be before end date")
        
        if start_date.year != fiscal_year or end_date.year != fiscal_year:
            self.logger.warning(f"Budget dates span beyond fiscal year {fiscal_year}")
        
        insert_sql = """
        INSERT INTO budgets 
        (id, budget_name, fiscal_year, start_date, end_date, status, created_by, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
        """
        
        try:
            with self.db_manager.get_db_cursor() as cursor:
                cursor.execute(insert_sql, (
                    budget_id, budget_name, fiscal_year, start_date, end_date, 
                    BudgetStatus.DRAFT.value, created_by
                ))
            
            self.logger.info(f"Created budget: {budget_name} for fiscal year {fiscal_year}")
            return budget_id
            
        except Exception as e:
            self.logger.error(f"Failed to create budget: {e}")
            raise
    
    def add_budget_line(self, budget_id: str, account_code: str, account_name: str,
                       period_month: int, budgeted_amount: Decimal, notes: str = None) -> str:
        """Add a line item to a budget."""
        line_id = str(uuid.uuid4())
        
        # Validate month
        if not 1 <= period_month <= 12:
            raise ValueError("Period month must be between 1 and 12")
        
        # Check if budget exists and is editable
        budget_status = self._get_budget_status(budget_id)
        if budget_status in [BudgetStatus.LOCKED.value]:
            raise ValueError("Cannot modify locked budget")
        
        insert_sql = """
        INSERT INTO budget_lines 
        (id, budget_id, account_code, account_name, period_month, budgeted_amount, notes, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
        ON CONFLICT (budget_id, account_code, period_month) 
        DO UPDATE SET 
            budgeted_amount = EXCLUDED.budgeted_amount,
            notes = EXCLUDED.notes
        """
        
        try:
            with self.db_manager.get_db_cursor() as cursor:
                cursor.execute(insert_sql, (
                    line_id, budget_id, account_code, account_name, 
                    period_month, budgeted_amount, notes
                ))
            
            self.logger.info(f"Added budget line for {account_code} - {account_name}: {budgeted_amount}")
            return line_id
            
        except Exception as e:
            self.logger.error(f"Failed to add budget line: {e}")
            raise
    
    def bulk_create_budget_from_previous_year(self, budget_id: str, previous_budget_id: str,
                                            adjustment_factor: float = 1.0) -> bool:
        """Create budget lines based on previous year with optional adjustment."""
        try:
            # Get previous year budget lines
            previous_lines_sql = """
            SELECT account_code, account_name, period_month, budgeted_amount
            FROM budget_lines
            WHERE budget_id = %s
            ORDER BY account_code, period_month
            """
            
            with self.db_manager.get_db_cursor() as cursor:
                cursor.execute(previous_lines_sql, (previous_budget_id,))
                previous_lines = cursor.fetchall()
            
            # Create new budget lines with adjustment
            for line in previous_lines:
                adjusted_amount = Decimal(str(line['budgeted_amount'])) * Decimal(str(adjustment_factor))
                
                self.add_budget_line(
                    budget_id=budget_id,
                    account_code=line['account_code'],
                    account_name=line['account_name'],
                    period_month=line['period_month'],
                    budgeted_amount=adjusted_amount,
                    notes=f"Based on previous year with {adjustment_factor:.1%} adjustment"
                )
            
            self.logger.info(f"Created {len(previous_lines)} budget lines from previous year")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create budget from previous year: {e}")
            return False
    
    def approve_budget(self, budget_id: str, approved_by: str) -> bool:
        """Approve a budget for use."""
        try:
            # Validate budget completeness
            validation_result = self._validate_budget_completeness(budget_id)
            if not validation_result['is_complete']:
                raise ValueError(f"Budget validation failed: {validation_result['issues']}")
            
            update_sql = """
            UPDATE budgets 
            SET status = %s, approved_by = %s, updated_at = NOW()
            WHERE id = %s AND status = %s
            """
            
            with self.db_manager.get_db_cursor() as cursor:
                cursor.execute(update_sql, (
                    BudgetStatus.APPROVED.value, approved_by, budget_id, BudgetStatus.DRAFT.value
                ))
                
                if cursor.rowcount == 0:
                    raise ValueError("Budget not found or not in draft status")
            
            self.logger.info(f"Budget {budget_id} approved by {approved_by}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to approve budget: {e}")
            raise
    
    def activate_budget(self, budget_id: str) -> bool:
        """Activate an approved budget."""
        try:
            # Deactivate any currently active budgets for the same fiscal year
            budget_info = self._get_budget_info(budget_id)
            if not budget_info:
                raise ValueError("Budget not found")
            
            deactivate_sql = """
            UPDATE budgets 
            SET status = %s 
            WHERE fiscal_year = %s AND status = %s
            """
            
            activate_sql = """
            UPDATE budgets 
            SET status = %s, updated_at = NOW()
            WHERE id = %s AND status = %s
            """
            
            with self.db_manager.get_db_cursor() as cursor:
                # Deactivate other budgets
                cursor.execute(deactivate_sql, (
                    BudgetStatus.APPROVED.value, budget_info['fiscal_year'], BudgetStatus.ACTIVE.value
                ))
                
                # Activate this budget
                cursor.execute(activate_sql, (
                    BudgetStatus.ACTIVE.value, budget_id, BudgetStatus.APPROVED.value
                ))
                
                if cursor.rowcount == 0:
                    raise ValueError("Budget not found or not approved")
            
            self.logger.info(f"Budget {budget_id} activated for fiscal year {budget_info['fiscal_year']}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to activate budget: {e}")
            raise
    
    def generate_variance_report(self, budget_id: str, report_month: int) -> Dict[str, Any]:
        """Generate detailed variance analysis report."""
        try:
            budget_info = self._get_budget_info(budget_id)
            if not budget_info:
                raise ValueError("Budget not found")
            
            # Get budget lines for the month
            budget_lines = self._get_budget_lines(budget_id, report_month)
            
            # Get actual amounts for the same period
            actual_amounts = self._get_actual_amounts(budget_info, report_month)
            
            # Calculate variances
            variance_lines = []
            total_budget = Decimal('0')
            total_actual = Decimal('0')
            favorable_variances = []
            unfavorable_variances = []
            
            for line in budget_lines:
                account_code = line['account_code']
                budgeted = Decimal(str(line['budgeted_amount']))
                actual = actual_amounts.get(account_code, Decimal('0'))
                
                variance = actual - budgeted
                variance_percent = float((variance / budgeted) * 100) if budgeted != 0 else 0
                
                variance_line = BudgetLine(
                    account_code=account_code,
                    account_name=line['account_name'],
                    period_month=report_month,
                    budgeted_amount=budgeted,
                    actual_amount=actual,
                    variance_amount=variance,
                    variance_percent=variance_percent
                )
                
                variance_lines.append(variance_line)
                total_budget += budgeted
                total_actual += actual
                
                # Classify variance (account type dependent)
                account_type = self._get_account_type(account_code)
                is_favorable = self._is_variance_favorable(variance, account_type)
                
                if is_favorable:
                    favorable_variances.append(variance_line)
                else:
                    unfavorable_variances.append(variance_line)
            
            total_variance = total_actual - total_budget
            total_variance_percent = float((total_variance / total_budget) * 100) if total_budget != 0 else 0
            
            # Generate variance analysis
            analysis = VarianceAnalysis(
                total_budget=total_budget,
                total_actual=total_actual,
                total_variance=total_variance,
                variance_percent=total_variance_percent,
                favorable_variances=favorable_variances,
                unfavorable_variances=unfavorable_variances
            )
            
            # Calculate summary statistics
            summary_stats = self._calculate_variance_summary_stats(variance_lines)
            
            return {
                'budget_info': budget_info,
                'report_period': f"{budget_info['fiscal_year']}-{report_month:02d}",
                'variance_lines': [self._serialize_budget_line(line) for line in variance_lines],
                'analysis': {
                    'total_budget': float(analysis.total_budget),
                    'total_actual': float(analysis.total_actual),
                    'total_variance': float(analysis.total_variance),
                    'variance_percent': analysis.variance_percent,
                    'favorable_count': len(analysis.favorable_variances),
                    'unfavorable_count': len(analysis.unfavorable_variances)
                },
                'summary_stats': summary_stats,
                'recommendations': self._generate_variance_recommendations(analysis)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to generate variance report: {e}")
            raise
    
    def generate_budget_performance_dashboard(self, fiscal_year: int) -> Dict[str, Any]:
        """Generate comprehensive budget performance dashboard."""
        try:
            # Get active budget for fiscal year
            active_budget = self._get_active_budget(fiscal_year)
            if not active_budget:
                return {'error': f'No active budget found for fiscal year {fiscal_year}'}
            
            budget_id = active_budget['id']
            current_month = date.today().month
            
            # Generate year-to-date variance
            ytd_variance = self._calculate_ytd_variance(budget_id, current_month)
            
            # Get monthly performance trends
            monthly_trends = self._get_monthly_budget_trends(budget_id, current_month)
            
            # Calculate key performance indicators
            kpis = self._calculate_budget_kpis(budget_id, current_month)
            
            # Get top variances (positive and negative)
            top_variances = self._get_top_variances(budget_id, current_month)
            
            # Forecast remaining year performance
            forecast = self._forecast_year_end_performance(budget_id, current_month)
            
            return {
                'budget_info': active_budget,
                'current_period': f"{fiscal_year}-{current_month:02d}",
                'ytd_performance': ytd_variance,
                'monthly_trends': monthly_trends,
                'kpis': kpis,
                'top_variances': top_variances,
                'year_end_forecast': forecast,
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to generate budget dashboard: {e}")
            return {'error': str(e)}
    
    def _get_budget_status(self, budget_id: str) -> Optional[str]:
        """Get budget status."""
        query_sql = "SELECT status FROM budgets WHERE id = %s"
        
        try:
            with self.db_manager.get_db_cursor() as cursor:
                cursor.execute(query_sql, (budget_id,))
                result = cursor.fetchone()
                return result['status'] if result else None
        except Exception as e:
            self.logger.error(f"Failed to get budget status: {e}")
            return None
    
    def _get_budget_info(self, budget_id: str) -> Optional[Dict]:
        """Get budget information."""
        query_sql = """
        SELECT id, budget_name, fiscal_year, start_date, end_date, status, created_by, approved_by
        FROM budgets WHERE id = %s
        """
        
        try:
            with self.db_manager.get_db_cursor() as cursor:
                cursor.execute(query_sql, (budget_id,))
                return cursor.fetchone()
        except Exception as e:
            self.logger.error(f"Failed to get budget info: {e}")
            return None
    
    def _get_budget_lines(self, budget_id: str, period_month: int) -> List[Dict]:
        """Get budget lines for specific month."""
        query_sql = """
        SELECT account_code, account_name, period_month, budgeted_amount, notes
        FROM budget_lines 
        WHERE budget_id = %s AND period_month = %s
        ORDER BY account_code
        """
        
        try:
            with self.db_manager.get_db_cursor() as cursor:
                cursor.execute(query_sql, (budget_id, period_month))
                return cursor.fetchall()
        except Exception as e:
            self.logger.error(f"Failed to get budget lines: {e}")
            return []
    
    def _get_actual_amounts(self, budget_info: Dict, report_month: int) -> Dict[str, Decimal]:
        """Get actual amounts for budget comparison."""
        if not self.accounting_system:
            return {}
        
        try:
            # Calculate period dates
            start_date = date(budget_info['fiscal_year'], report_month, 1)
            if report_month == 12:
                end_date = date(budget_info['fiscal_year'] + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = date(budget_info['fiscal_year'], report_month + 1, 1) - timedelta(days=1)
            
            # Get trial balance for the period
            trial_balance = self.accounting_system.get_trial_balance(
                start_date.strftime('%Y-%m-%d'),
                end_date.strftime('%Y-%m-%d')
            )
            
            # Convert to account codes (simplified mapping)
            actual_amounts = {}
            for account_name, balance in trial_balance.items():
                # Try to get account code
                account_code = self._get_account_code_by_name(account_name)
                if account_code:
                    actual_amounts[account_code] = Decimal(str(balance))
            
            return actual_amounts
            
        except Exception as e:
            self.logger.error(f"Failed to get actual amounts: {e}")
            return {}
    
    def _get_account_code_by_name(self, account_name: str) -> Optional[str]:
        """Get account code by account name."""
        if not self.accounting_system:
            return None
        
        try:
            # Get all accounts and find matching name
            accounts = self.accounting_system.get_all_accounts()
            for account in accounts:
                if account[0] == account_name:  # name is first element
                    return account[2]  # code is third element
            return None
        except Exception as e:
            self.logger.error(f"Failed to get account code: {e}")
            return None
    
    def _get_account_type(self, account_code: str) -> str:
        """Get account type by code."""
        if not self.accounting_system:
            return 'Unknown'
        
        try:
            accounts = self.accounting_system.get_all_accounts()
            for account in accounts:
                if account[2] == account_code:  # code is third element
                    return account[1]  # type is second element
            return 'Unknown'
        except Exception as e:
            self.logger.error(f"Failed to get account type: {e}")
            return 'Unknown'
    
    def _is_variance_favorable(self, variance: Decimal, account_type: str) -> bool:
        """Determine if variance is favorable based on account type."""
        # For Revenue accounts: Higher actual is favorable (positive variance)
        # For Expense accounts: Lower actual is favorable (negative variance)
        # For Asset accounts: Higher actual is generally favorable
        # For Liability accounts: Lower actual is generally favorable
        
        if account_type in ['Revenue', 'Income']:
            return variance > 0
        elif account_type in ['Expense']:
            return variance < 0
        elif account_type in ['Asset']:
            return variance > 0
        elif account_type in ['Liability']:
            return variance < 0
        else:
            return variance > 0  # Default assumption
    
    def _validate_budget_completeness(self, budget_id: str) -> Dict[str, Any]:
        """Validate budget completeness before approval."""
        issues = []
        
        try:
            # Check if all months have budget lines
            month_coverage_sql = """
            SELECT DISTINCT period_month 
            FROM budget_lines 
            WHERE budget_id = %s 
            ORDER BY period_month
            """
            
            with self.db_manager.get_db_cursor() as cursor:
                cursor.execute(month_coverage_sql, (budget_id,))
                covered_months = [row['period_month'] for row in cursor.fetchall()]
            
            missing_months = [month for month in range(1, 13) if month not in covered_months]
            if missing_months:
                issues.append(f"Missing budget lines for months: {missing_months}")
            
            # Check for negative budget amounts
            negative_amounts_sql = """
            SELECT COUNT(*) as negative_count
            FROM budget_lines 
            WHERE budget_id = %s AND budgeted_amount < 0
            """
            
            with self.db_manager.get_db_cursor() as cursor:
                cursor.execute(negative_amounts_sql, (budget_id,))
                negative_count = cursor.fetchone()['negative_count']
            
            if negative_count > 0:
                issues.append(f"{negative_count} budget lines have negative amounts")
            
            # Check for zero budget amounts in revenue/expense accounts
            zero_amounts_sql = """
            SELECT account_code, account_name 
            FROM budget_lines 
            WHERE budget_id = %s AND budgeted_amount = 0
            LIMIT 5
            """
            
            with self.db_manager.get_db_cursor() as cursor:
                cursor.execute(zero_amounts_sql, (budget_id,))
                zero_accounts = cursor.fetchall()
            
            if zero_accounts:
                account_list = [f"{acc['account_code']}" for acc in zero_accounts]
                issues.append(f"Zero budget amounts for accounts: {', '.join(account_list)}")
            
        except Exception as e:
            issues.append(f"Validation error: {str(e)}")
        
        return {
            'is_complete': len(issues) == 0,
            'issues': issues
        }
    
    def _serialize_budget_line(self, budget_line: BudgetLine) -> Dict[str, Any]:
        """Serialize budget line for JSON response."""
        return {
            'account_code': budget_line.account_code,
            'account_name': budget_line.account_name,
            'period_month': budget_line.period_month,
            'budgeted_amount': float(budget_line.budgeted_amount),
            'actual_amount': float(budget_line.actual_amount) if budget_line.actual_amount else None,
            'variance_amount': float(budget_line.variance_amount) if budget_line.variance_amount else None,
            'variance_percent': budget_line.variance_percent
        }
    
    def _calculate_variance_summary_stats(self, variance_lines: List[BudgetLine]) -> Dict[str, Any]:
        """Calculate summary statistics for variance analysis."""
        if not variance_lines:
            return {}
        
        variances = [line.variance_percent for line in variance_lines if line.variance_percent is not None]
        
        if not variances:
            return {}
        
        return {
            'average_variance_percent': sum(variances) / len(variances),
            'max_positive_variance': max(variances),
            'max_negative_variance': min(variances),
            'accounts_over_budget': len([v for v in variances if v > 0]),
            'accounts_under_budget': len([v for v in variances if v < 0]),
            'accounts_on_budget': len([v for v in variances if abs(v) < 5])  # Within 5%
        }
    
    def _generate_variance_recommendations(self, analysis: VarianceAnalysis) -> List[str]:
        """Generate recommendations based on variance analysis."""
        recommendations = []
        
        # High-level recommendations based on total variance
        if analysis.variance_percent > 10:
            recommendations.append("Overall spending is significantly over budget. Review expense controls.")
        elif analysis.variance_percent < -10:
            recommendations.append("Actual results are significantly under budget. Consider revising forecasts.")
        
        # Specific recommendations for large variances
        large_unfavorable = [v for v in analysis.unfavorable_variances 
                           if abs(v.variance_percent or 0) > 20]
        
        if large_unfavorable:
            recommendations.append(f"{len(large_unfavorable)} accounts have significant unfavorable variances. Immediate attention required.")
        
        return recommendations
    
    def _get_active_budget(self, fiscal_year: int) -> Optional[Dict]:
        """Get active budget for fiscal year."""
        query_sql = """
        SELECT * FROM budgets 
        WHERE fiscal_year = %s AND status = %s
        """
        
        try:
            with self.db_manager.get_db_cursor() as cursor:
                cursor.execute(query_sql, (fiscal_year, BudgetStatus.ACTIVE.value))
                return cursor.fetchone()
        except Exception as e:
            self.logger.error(f"Failed to get active budget: {e}")
            return None
    
    def _calculate_ytd_variance(self, budget_id: str, current_month: int) -> Dict[str, Any]:
        """Calculate year-to-date variance."""
        # Implementation placeholder
        return {
            'ytd_budget': 0,
            'ytd_actual': 0,
            'ytd_variance': 0,
            'ytd_variance_percent': 0
        }
    
    def _get_monthly_budget_trends(self, budget_id: str, current_month: int) -> List[Dict]:
        """Get monthly budget performance trends."""
        # Implementation placeholder
        return []
    
    def _calculate_budget_kpis(self, budget_id: str, current_month: int) -> Dict[str, Any]:
        """Calculate budget KPIs."""
        # Implementation placeholder
        return {
            'budget_accuracy': 0,
            'forecast_reliability': 0,
            'variance_trend': 'stable'
        }
    
    def _get_top_variances(self, budget_id: str, current_month: int) -> Dict[str, List]:
        """Get top positive and negative variances."""
        # Implementation placeholder
        return {
            'top_favorable': [],
            'top_unfavorable': []
        }
    
    def _forecast_year_end_performance(self, budget_id: str, current_month: int) -> Dict[str, Any]:
        """Forecast year-end budget performance."""
        # Implementation placeholder
        return {
            'forecasted_total': 0,
            'budgeted_total': 0,
            'projected_variance': 0
        }
