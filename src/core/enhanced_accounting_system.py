"""
Enhanced Accounting System Integration
Integrates all advanced features: audit trails, period closing, advanced cash flow, financial ratios, and budgeting
"""

import logging
from datetime import datetime, date
from typing import Dict, List, Optional, Any

from .enhanced_database_schema import EnhancedDatabaseSchema
from .period_closing import PeriodClosingManager, AuditTrailManager
from .advanced_cash_flow import AdvancedCashFlowManager
from .financial_ratios import FinancialRatioCalculator
from .budget_manager import BudgetManager

class EnhancedAccountingSystem:
    """Enhanced accounting system with advanced features."""
    
    def __init__(self, db_manager, base_accounting_system, organization_id=None, user_id=None):
        self.db_manager = db_manager
        self.base_system = base_accounting_system
        self.organization_id = organization_id
        self.user_id = user_id
        self.logger = logging.getLogger(__name__)
        
        # Initialize enhanced components
        self.enhanced_schema = EnhancedDatabaseSchema(db_manager)
        self.period_manager = PeriodClosingManager(db_manager, organization_id, user_id)
        self.audit_manager = AuditTrailManager(db_manager)
        self.cash_flow_manager = AdvancedCashFlowManager(db_manager, base_accounting_system)
        self.ratio_calculator = FinancialRatioCalculator(db_manager, base_accounting_system)
        self.budget_manager = BudgetManager(db_manager, base_accounting_system, organization_id)
        
        self._initialized = False
    
    def initialize_enhanced_features(self, force_recreate: bool = False) -> Dict[str, bool]:
        """Initialize all enhanced features."""
        results = {}
        
        try:
            self.logger.info("Initializing enhanced accounting features...")
            
            # 1. Create enhanced database schema
            try:
                self.enhanced_schema.create_enhanced_tables()
                results['enhanced_tables'] = True
            except Exception as e:
                self.logger.error(f"Failed to create enhanced tables: {e}")
                results['enhanced_tables'] = False
            
            # 2. Create audit triggers
            try:
                self.enhanced_schema.create_audit_triggers()
                results['audit_triggers'] = True
            except Exception as e:
                self.logger.error(f"Failed to create audit triggers: {e}")
                results['audit_triggers'] = False
            
            # 3. Add foreign key constraints
            try:
                self.enhanced_schema.add_foreign_key_constraints()
                results['foreign_keys'] = True
            except Exception as e:
                self.logger.error(f"Failed to add foreign keys: {e}")
                results['foreign_keys'] = False
            
            # 4. Initialize cash flow classifications
            try:
                self.enhanced_schema.initialize_cash_flow_classifications()
                results['cash_flow_classifications'] = True
            except Exception as e:
                self.logger.error(f"Failed to initialize cash flow classifications: {e}")
                results['cash_flow_classifications'] = False
            
            # 5. Setup default financial ratios
            try:
                self.enhanced_schema.setup_default_financial_ratios()
                results['financial_ratios'] = True
            except Exception as e:
                self.logger.error(f"Failed to setup financial ratios: {e}")
                results['financial_ratios'] = False
            
            self._initialized = True
            self.logger.info("Enhanced accounting features initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize enhanced features: {e}")
            results['initialization_error'] = str(e)
        
        return results
    
    def get_comprehensive_financial_overview(self, as_of_date: date = None) -> Dict[str, Any]:
        """Get comprehensive financial overview with all enhanced features."""
        if as_of_date is None:
            as_of_date = date.today()
        
        overview = {
            'generated_at': datetime.now().isoformat(),
            'as_of_date': as_of_date.isoformat(),
            'organization_id': self.organization_id
        }
        
        try:
            # 1. Basic financial statements
            overview['financial_statements'] = self._get_basic_financial_statements(as_of_date)
            
            # 2. Advanced cash flow analysis
            overview['cash_flow_analysis'] = self._get_enhanced_cash_flow_analysis(as_of_date)
            
            # 3. Financial ratios and KPIs
            overview['financial_ratios'] = self._get_financial_ratios_analysis(as_of_date)
            
            # 4. Budget variance analysis (if budgets exist)
            overview['budget_analysis'] = self._get_budget_variance_analysis(as_of_date)
            
            # 5. Period closing status
            overview['period_status'] = self._get_period_closing_status()
            
            # 6. Audit trail summary
            overview['audit_summary'] = self._get_audit_trail_summary()
            
            # 7. Financial health score
            overview['financial_health'] = self._calculate_financial_health_score(overview)
            
        except Exception as e:
            self.logger.error(f"Failed to generate comprehensive overview: {e}")
            overview['error'] = str(e)
        
        return overview
    
    def perform_month_end_close(self, period_end_date: date, 
                              force_close: bool = False) -> Dict[str, Any]:
        """Perform comprehensive month-end closing process."""
        close_results = {
            'period_end_date': period_end_date.isoformat(),
            'started_at': datetime.now().isoformat(),
            'steps': {},
            'success': False
        }
        
        try:
            # 1. Create accounting period if not exists
            period_name = f"{period_end_date.strftime('%B %Y')}"
            period_start = period_end_date.replace(day=1)
            
            try:
                period_id = self.period_manager.create_accounting_period(
                    period_name, period_start, period_end_date
                )
                close_results['steps']['create_period'] = {'success': True, 'period_id': period_id}
            except Exception as e:
                # Period might already exist
                close_results['steps']['create_period'] = {'success': False, 'error': str(e)}
                period_id = None
            
            # 2. Generate and validate trial balance
            try:
                trial_balance = self.base_system.get_trial_balance(
                    period_start.strftime('%Y-%m-%d'),
                    period_end_date.strftime('%Y-%m-%d')
                )
                
                # Check if trial balance is balanced
                total_debits = sum(balance for balance in trial_balance.values() if balance > 0)
                total_credits = sum(abs(balance) for balance in trial_balance.values() if balance < 0)
                
                is_balanced = abs(total_debits - total_credits) < 0.01
                
                close_results['steps']['trial_balance'] = {
                    'success': is_balanced,
                    'total_debits': float(total_debits),
                    'total_credits': float(total_credits),
                    'difference': float(total_debits - total_credits)
                }
                
            except Exception as e:
                close_results['steps']['trial_balance'] = {'success': False, 'error': str(e)}
            
            # 3. Generate financial statements
            try:
                financial_statements = {
                    'income_statement': self.base_system.generate_income_statement_breakdown(
                        period_start.strftime('%Y-%m-%d'),
                        period_end_date.strftime('%Y-%m-%d')
                    ),
                    'balance_sheet': self.base_system.generate_balance_sheet_breakdown(
                        period_end_date.strftime('%Y-%m-%d')
                    ),
                    'cash_flow': self.cash_flow_manager.generate_enhanced_cash_flow_statement(
                        period_start, period_end_date
                    )
                }
                
                close_results['steps']['financial_statements'] = {'success': True}
                
            except Exception as e:
                close_results['steps']['financial_statements'] = {'success': False, 'error': str(e)}
            
            # 4. Calculate financial ratios
            try:
                ratios = self.ratio_calculator.calculate_all_ratios(period_end_date)
                close_results['steps']['financial_ratios'] = {'success': True, 'ratio_count': len(ratios.get('ratios', {}))}
                
            except Exception as e:
                close_results['steps']['financial_ratios'] = {'success': False, 'error': str(e)}
            
            # 5. Generate budget variance report (if applicable)
            try:
                budget_variance = self._generate_period_budget_variance(period_end_date)
                close_results['steps']['budget_variance'] = {'success': True}
                
            except Exception as e:
                close_results['steps']['budget_variance'] = {'success': False, 'error': str(e)}
            
            # 6. Close the period if validation passes
            if period_id and all(step.get('success', False) for step in [
                close_results['steps'].get('trial_balance', {}),
                close_results['steps'].get('financial_statements', {})
            ]):
                try:
                    self.period_manager.close_accounting_period(period_id, force_close)
                    close_results['steps']['period_closing'] = {'success': True}
                    close_results['success'] = True
                    
                except Exception as e:
                    close_results['steps']['period_closing'] = {'success': False, 'error': str(e)}
            
            close_results['completed_at'] = datetime.now().isoformat()
            
        except Exception as e:
            close_results['error'] = str(e)
            self.logger.error(f"Month-end close failed: {e}")
        
        return close_results
    
    def generate_management_dashboard(self) -> Dict[str, Any]:
        """Generate comprehensive management dashboard."""
        dashboard = {
            'generated_at': datetime.now().isoformat(),
            'organization_id': self.organization_id
        }
        
        try:
            current_date = date.today()
            
            # 1. Financial performance summary
            dashboard['performance_summary'] = self._get_performance_summary(current_date)
            
            # 2. Cash flow trends
            dashboard['cash_flow_trends'] = self.cash_flow_manager.get_cash_flow_trends(12)
            
            # 3. Financial ratio dashboard
            dashboard['ratio_dashboard'] = self.ratio_calculator.create_ratio_dashboard_data()
            
            # 4. Budget performance
            dashboard['budget_performance'] = self.budget_manager.generate_budget_performance_dashboard(
                current_date.year
            )
            
            # 5. Alerts and notifications
            dashboard['alerts'] = self._generate_management_alerts()
            
            # 6. Period status
            dashboard['period_status'] = self.period_manager.get_period_status_summary()
            
            # 7. Recent audit activity
            dashboard['recent_activity'] = self.audit_manager.get_audit_trail(limit=20)
            
        except Exception as e:
            dashboard['error'] = str(e)
            self.logger.error(f"Failed to generate management dashboard: {e}")
        
        return dashboard
    
    def _get_basic_financial_statements(self, as_of_date: date) -> Dict[str, Any]:
        """Get basic financial statements."""
        year_start = as_of_date.replace(month=1, day=1)
        
        return {
            'income_statement': self.base_system.generate_income_statement_breakdown(
                year_start.strftime('%Y-%m-%d'),
                as_of_date.strftime('%Y-%m-%d')
            ),
            'balance_sheet': self.base_system.generate_balance_sheet_breakdown(
                as_of_date.strftime('%Y-%m-%d')
            ),
            'statement_of_equity': self.base_system.generate_statement_of_equity(
                year_start.strftime('%Y-%m-%d'),
                as_of_date.strftime('%Y-%m-%d')
            )
        }
    
    def _get_enhanced_cash_flow_analysis(self, as_of_date: date) -> Dict[str, Any]:
        """Get enhanced cash flow analysis."""
        year_start = as_of_date.replace(month=1, day=1)
        
        return {
            'statement': self.cash_flow_manager.generate_enhanced_cash_flow_statement(
                year_start, as_of_date
            ),
            'trends': self.cash_flow_manager.get_cash_flow_trends(6)
        }
    
    def _get_financial_ratios_analysis(self, as_of_date: date) -> Dict[str, Any]:
        """Get financial ratios analysis."""
        return {
            'current_ratios': self.ratio_calculator.calculate_all_ratios(as_of_date),
            'trends': self.ratio_calculator.calculate_ratio_trends(6),
            'alerts': self.ratio_calculator.monitor_ratio_thresholds(as_of_date)
        }
    
    def _get_budget_variance_analysis(self, as_of_date: date) -> Dict[str, Any]:
        """Get budget variance analysis."""
        try:
            return self.budget_manager.generate_budget_performance_dashboard(as_of_date.year)
        except Exception as e:
            return {'error': f'Budget analysis not available: {str(e)}'}
    
    def _get_period_closing_status(self) -> Dict[str, Any]:
        """Get period closing status."""
        return self.period_manager.get_period_status_summary()
    
    def _get_audit_trail_summary(self) -> Dict[str, Any]:
        """Get audit trail summary."""
        if self.user_id:
            return self.audit_manager.get_user_activity_summary(self.user_id, 30)
        else:
            return {'error': 'User ID not available for audit summary'}
    
    def _calculate_financial_health_score(self, overview: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall financial health score."""
        score = 100  # Start with perfect score
        factors = []
        
        try:
            # Factor 1: Liquidity ratios
            ratios = overview.get('financial_ratios', {}).get('current_ratios', {}).get('ratios', {})
            liquidity = ratios.get('liquidity', {})
            
            current_ratio = liquidity.get('current_ratio', {}).get('value', 0)
            if current_ratio < 1.0:
                score -= 20
                factors.append('Low current ratio indicates liquidity concerns')
            elif current_ratio < 1.5:
                score -= 10
                factors.append('Current ratio below recommended level')
            
            # Factor 2: Profitability
            profitability = ratios.get('profitability', {})
            net_margin = profitability.get('net_profit_margin', {}).get('value', 0)
            
            if net_margin < 0:
                score -= 30
                factors.append('Negative profit margins')
            elif net_margin < 5:
                score -= 15
                factors.append('Low profit margins')
            
            # Factor 3: Cash flow
            cash_flow = overview.get('cash_flow_analysis', {}).get('statement', {})
            operating_cf = cash_flow.get('operating_activities', {}).get('total', 0)
            
            if operating_cf < 0:
                score -= 25
                factors.append('Negative operating cash flow')
            
            # Factor 4: Budget variance
            budget = overview.get('budget_analysis', {})
            if 'error' not in budget:
                # Add budget-related scoring here
                pass
            
            # Ensure score doesn't go below 0
            score = max(0, score)
            
            # Determine health category
            if score >= 80:
                health_category = 'Excellent'
            elif score >= 60:
                health_category = 'Good'
            elif score >= 40:
                health_category = 'Fair'
            else:
                health_category = 'Poor'
            
        except Exception as e:
            self.logger.error(f"Failed to calculate financial health score: {e}")
            return {'error': 'Unable to calculate financial health score'}
        
        return {
            'score': score,
            'category': health_category,
            'factors': factors,
            'last_calculated': datetime.now().isoformat()
        }
    
    def _generate_period_budget_variance(self, period_end_date: date) -> Dict[str, Any]:
        """Generate budget variance for period."""
        # Implementation depends on budget availability
        return {}
    
    def _get_performance_summary(self, current_date: date) -> Dict[str, Any]:
        """Get financial performance summary."""
        # Implementation for performance metrics
        return {}
    
    def _generate_management_alerts(self) -> List[Dict[str, Any]]:
        """Generate management alerts."""
        alerts = []
        
        try:
            # Get ratio alerts
            ratio_alerts = self.ratio_calculator.monitor_ratio_thresholds()
            for alert in ratio_alerts:
                alerts.append({
                    'type': 'FINANCIAL_RATIO',
                    'severity': alert.get('type', 'INFO'),
                    'message': alert.get('message', ''),
                    'category': alert.get('category', '')
                })
            
            # Get period closing alerts
            period_summary = self.period_manager.get_period_status_summary()
            open_periods = period_summary.get('status_summary', {}).get('OPEN', 0)
            
            if open_periods > 2:
                alerts.append({
                    'type': 'PERIOD_CLOSING',
                    'severity': 'WARNING',
                    'message': f'{open_periods} accounting periods are still open',
                    'category': 'period_management'
                })
            
        except Exception as e:
            self.logger.error(f"Failed to generate management alerts: {e}")
        
        return alerts

    # Delegation methods for backward compatibility
    def __getattr__(self, name):
        """Delegate missing method calls to the base accounting system."""
        if hasattr(self.base_system, name):
            return getattr(self.base_system, name)
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
    
    # Explicit delegation for commonly used methods
    def get_trial_balance(self, *args, **kwargs):
        """Get trial balance from base system."""
        return self.base_system.get_trial_balance(*args, **kwargs)
    
    def get_journal_entries(self, *args, **kwargs):
        """Get journal entries from base system."""
        return self.base_system.get_journal_entries(*args, **kwargs)
    
    def add_journal_entry(self, *args, **kwargs):
        """Add journal entry to base system."""
        return self.base_system.add_journal_entry(*args, **kwargs)
    
    def get_accounts(self, *args, **kwargs):
        """Get accounts from base system."""
        return self.base_system.get_accounts(*args, **kwargs)
    
    def get_account_balance(self, *args, **kwargs):
        """Get account balance from base system."""
        return self.base_system.get_account_balance(*args, **kwargs)
    
    def get_ledger_entries(self, *args, **kwargs):
        """Get ledger entries from base system."""
        return self.base_system.get_ledger_entries(*args, **kwargs)
    
    def get_income_statement(self, *args, **kwargs):
        """Get income statement from base system."""
        return self.base_system.get_income_statement(*args, **kwargs)
    
    def get_balance_sheet(self, *args, **kwargs):
        """Get balance sheet from base system."""
        return self.base_system.get_balance_sheet(*args, **kwargs)
    
    def get_cash_flow_statement(self, *args, **kwargs):
        """Get cash flow statement from base system."""
        return self.base_system.get_cash_flow_statement(*args, **kwargs)
    
    def add_account(self, *args, **kwargs):
        """Add account to base system."""
        return self.base_system.add_account(*args, **kwargs)
    
    def update_account(self, *args, **kwargs):
        """Update account in base system."""
        return self.base_system.update_account(*args, **kwargs)
    
    def delete_account(self, *args, **kwargs):
        """Delete account from base system."""
        return self.base_system.delete_account(*args, **kwargs)
    
    def get_chart_of_accounts(self, *args, **kwargs):
        """Get chart of accounts from base system."""
        return self.base_system.get_chart_of_accounts(*args, **kwargs)
    
    def close_books(self, *args, **kwargs):
        """Close books using base system."""
        return self.base_system.close_books(*args, **kwargs)
    
    def backup_data(self, *args, **kwargs):
        """Backup data using base system."""
        return self.base_system.backup_data(*args, **kwargs)
    
    def restore_data(self, *args, **kwargs):
        """Restore data using base system."""
        return self.base_system.restore_data(*args, **kwargs)
