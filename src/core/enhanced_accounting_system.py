"""
Enhanced Accounting System - Now a wrapper around UnifiedAccountingSystem
All advanced features are now integrated into the main system
"""

import logging
from datetime import datetime, date
from typing import Dict, List, Optional, Any

from .unified_accounting_system import UnifiedAccountingSystem

class EnhancedAccountingSystem:
    """
    Enhanced accounting system - now just a wrapper around UnifiedAccountingSystem
    for backward compatibility. All features are now integrated into the main system.
    """
    
    def __init__(self, base_accounting_system, organization_id=None, user_id=None):
        # The base_accounting_system is now the UnifiedAccountingSystem
        self.base_system = base_accounting_system
        self.organization_id = organization_id
        self.user_id = user_id
        self.logger = logging.getLogger(__name__)
        
        # Set organization context if provided
        if organization_id and hasattr(self.base_system, 'set_organization'):
            self.base_system.set_organization(organization_id)
        
        self.logger.info("Enhanced features are now integrated into UnifiedAccountingSystem")
    
    def initialize_enhanced_features(self, force_recreate: bool = False) -> Dict[str, bool]:
        """Enhanced features are now built-in to the unified system"""
        return {
            'unified_system': True,
            'offline_support': True,
            'financial_calculations': True,
            'advanced_reporting': True,
            'note': 'All features are now integrated into UnifiedAccountingSystem'
        }
    
    def get_comprehensive_financial_overview(self, as_of_date: date = None) -> Dict[str, Any]:
        """Get comprehensive financial overview"""
        if as_of_date is None:
            as_of_date = date.today()
        
        overview = {
            'generated_at': datetime.now().isoformat(),
            'as_of_date': as_of_date.isoformat(),
            'organization_id': self.organization_id
        }
        
        try:
            # Use unified system's methods
            as_of_str = as_of_date.strftime('%Y-%m-%d')
            year_start = as_of_date.replace(month=1, day=1).strftime('%Y-%m-%d')
            
            overview['financial_statements'] = {
                'income_statement': self.base_system.generate_income_statement_breakdown(year_start, as_of_str),
                'balance_sheet': self.base_system.generate_balance_sheet_breakdown(as_of_str),
                'statement_of_equity': self.base_system.generate_statement_of_equity(year_start, as_of_str)
            }
            
            overview['financial_health'] = self.base_system.get_financial_health_score(as_of_date)
            overview['sync_status'] = self.base_system.get_sync_status()
            
        except Exception as e:
            self.logger.error(f"Failed to generate comprehensive overview: {e}")
            overview['error'] = str(e)
        
        return overview
    
    # Delegation methods - pass everything to the unified system
    def __getattr__(self, name):
        """Delegate all method calls to the unified system"""
        if hasattr(self.base_system, name):
            return getattr(self.base_system, name)
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
    
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
        """Get accounts (alias for get_all_accounts with enhanced formatting)."""
        return self.get_all_accounts(*args, **kwargs)
    
    def get_account_balance(self, account_name, as_of_date=None):
        """Calculate account balance as of a specific date."""
        if as_of_date:
            trial_balance = self.base_system.get_trial_balance(None, as_of_date)
        else:
            trial_balance = self.base_system.get_trial_balance()
        
        # Try to find the account in trial balance
        for acc_name, balance in trial_balance.items():
            if acc_name.lower() == account_name.lower():
                return balance
        
        return 0.0
    
    def get_ledger_entries(self, account_name, from_date=None, to_date=None):
        """Get ledger entries (alias for get_ledger)."""
        return self.base_system.get_ledger(account_name, from_date, to_date)
    
    def update_account(self, *args, **kwargs):
        """Update account (alias for edit_account)."""
        return self.base_system.edit_account(*args, **kwargs)
    
    def get_chart_of_accounts(self, active_only: bool = True):
        """Get chart of accounts with hierarchy."""
        try:
            return self.base_system.get_chart_of_accounts(active_only=active_only)
        except (AttributeError, TypeError):
            # Fallback - get accounts directly from db manager
            if hasattr(self.base_system, 'db_manager'):
                return self.base_system.db_manager.get_accounts()
            elif hasattr(self.base_system, 'get_chart_of_accounts'):
                # Try without parameters if the method doesn't support them
                return self.base_system.get_chart_of_accounts()
            return []
    
    # Critical missing methods from original system
    def clear_journal_entries(self):
        """Clear all journal entries from base system."""
        return self.base_system.clear_journal_entries()
    
    def add_journal_entries_batch(self, entries):
        """Add journal entries in batch using base system."""
        return self.base_system.add_journal_entries_batch(entries)
    
    def add_journal_entries_with_progress(self, entries, progress_callback=None):
        """Add journal entries with progress tracking using base system."""
        return self.base_system.add_journal_entries_with_progress(entries, progress_callback)

    def get_journal_entries_by_date_range(self, start_date, end_date):
        """Get journal entries by date range - alias for get_journal_entries with dates"""
        return self.base_system.get_journal_entries(start_date, end_date)
    
    def seed_hierarchical_accounts(self):
        """Seed chart of accounts using base system."""
        return self.base_system.seed_hierarchical_accounts()
    
    def force_reseed_hierarchical_accounts(self):
        """Force reseed accounts using base system."""
        return self.base_system.force_reseed_hierarchical_accounts()
    
    def refresh_connection(self):
        """Refresh database connection using base system."""
        return self.base_system.refresh_connection()
    
    def get_recent_journal_entries(self, limit=20):
        """Get recent journal entries using base system."""
        return self.base_system.get_recent_journal_entries(limit)
    
    def get_accounts_by_level(self, level=1):
        """Get accounts by hierarchy level using base system."""
        return self.base_system.get_accounts_by_level(level)
    
    def get_postable_accounts(self):
        """Get postable accounts using base system."""
        return self.base_system.get_postable_accounts()
    
    def is_account_postable(self, account_name_or_code):
        """Check if account is postable using base system."""
        return self.base_system.is_account_postable(account_name_or_code)
    
    def resolve_account(self, account_input):
        """Resolve account using base system."""
        return self.base_system.resolve_account(account_input)
    
    def begin_transaction(self):
        """Begin transaction using base system."""
        return self.base_system.begin_transaction()
    
    def commit_transaction(self):
        """Commit transaction using base system."""
        return self.base_system.commit_transaction()
    
    # Enhanced functionality that builds on base system
    def close_books(self, period_end_date, force_close=False):
        """Enhanced book closing using period management."""
        return self.perform_month_end_close(period_end_date, force_close)
    
    def backup_data(self):
        """Enhanced backup functionality."""
        # Implementation would depend on database type and enhanced features
        backup_info = {
            'timestamp': datetime.now().isoformat(),
            'organization_id': self.organization_id,
            'base_system_backup': 'Not implemented in base system',
            'enhanced_features': {
                'period_status': self.period_manager.get_period_status_summary(),
                'audit_trail_count': len(self.audit_manager.get_audit_trail(limit=1000)),
                'financial_ratios': len(self.ratio_calculator.calculate_all_ratios().get('ratios', {})),
            }
        }
        self.logger.warning("Enhanced backup functionality not fully implemented")
        return backup_info
    
    # Enhanced fuzzy search methods (ported from original system)
    def fuzzy_match_account(self, search_term):
        """
        Enhanced fuzzy match for account name or code.
        Returns (matched_name, matched_type, matched_code) or (None, None, None) if no match
        """
        try:
            return self.base_system._fuzzy_match_account(search_term)
        except AttributeError:
            # Fallback implementation if base system doesn't have this method
            return self._enhanced_fuzzy_match_account(search_term)
    
    def find_matching_account(self, search_term):
        """Enhanced account matching with improved scoring."""
        try:
            return self.base_system._find_matching_account(search_term)
        except AttributeError:
            # Fallback implementation if base system doesn't have this method
            return self._enhanced_find_matching_account(search_term)
    
    def _enhanced_fuzzy_match_account(self, search_term):
        """Enhanced implementation of fuzzy account matching."""
        if not search_term:
            return None, None, None
            
        search_term = search_term.strip().lower()
        all_accounts = self.get_postable_accounts()
        
        # Try exact matches first
        for name, acc_type, code, parent_code, level, is_postable, description in all_accounts:
            if name.lower() == search_term or (code and code.lower() == search_term):
                return name, acc_type, code
        
        # Try partial matches with scoring
        matches = []
        for name, acc_type, code, parent_code, level, is_postable, description in all_accounts:
            score = 0
            name_lower = name.lower()
            
            # Scoring algorithm
            if name_lower.startswith(search_term):
                score += 10
            elif f" {search_term}" in name_lower:
                score += 8
            elif search_term in name_lower:
                score += 5
            elif name_lower.endswith(search_term):
                score += 3
                
            # Bonus for shorter names (more specific match)
            if score > 0:
                score += max(0, 20 - len(name))
                matches.append((score, name, acc_type, code))
        
        # Return best match
        if matches:
            matches.sort(reverse=True, key=lambda x: x[0])
            return matches[0][1], matches[0][2], matches[0][3]
            
        return None, None, None
    
    def _enhanced_find_matching_account(self, search_term):
        """Enhanced implementation of account finding with multiple strategies."""
        if not search_term:
            return None
            
        search_term = search_term.strip().lower()
        all_accounts = self.get_all_accounts()
        
        # Strategy 1: Exact matches
        for name, acc_type, code, parent_code, level, is_postable, description in all_accounts:
            if name.lower() == search_term or (code and code.lower() == search_term):
                return (name, acc_type, code)
        
        # Strategy 2: Code-name format (e.g., "1101 - Cash")
        if " - " in search_term:
            parts = search_term.split(" - ", 1)
            if len(parts) == 2:
                code_part = parts[0].strip()
                name_part = parts[1].strip()
                
                for name, acc_type, code, parent_code, level, is_postable, description in all_accounts:
                    if (code and code.lower() == code_part) or name.lower() == name_part:
                        return (name, acc_type, code)
        
        # Strategy 3: Partial word matching with advanced scoring
        words = search_term.split()
        if words:
            matches = []
            
            for name, acc_type, code, parent_code, level, is_postable, description in all_accounts:
                score = 0
                name_lower = name.lower()
                
                for word in words:
                    if name_lower.startswith(word):
                        score += 10
                    elif f" {word} " in name_lower:
                        score += 8
                    elif f" {word}" in name_lower:
                        score += 6
                    elif word in name_lower:
                        score += 4
                
                if score > 0:
                    # Boost score for postable accounts
                    if is_postable:
                        score += 2
                    # Penalty for very long names
                    score -= max(0, len(name) - 30) * 0.1
                    matches.append((score, name, acc_type, code))
            
            if matches:
                matches.sort(reverse=True, key=lambda x: x[0])
                return (matches[0][1], matches[0][2], matches[0][3])
        
        return None
    
    def search_accounts(self, query, limit=10, include_non_postable=False):
        """Enhanced account search with multiple results."""
        if not query:
            return []
            
        query = query.strip().lower()
        all_accounts = self.get_all_accounts()
        results = []
        
        for name, acc_type, code, parent_code, level, is_postable, description in all_accounts:
            if not include_non_postable and not is_postable:
                continue
                
            score = 0
            name_lower = name.lower()
            
            # Exact match gets highest score
            if name_lower == query or (code and code.lower() == query):
                score = 100
            # Starts with query
            elif name_lower.startswith(query):
                score = 80
            # Contains query as whole word
            elif f" {query} " in name_lower:
                score = 60
            # Contains query
            elif query in name_lower:
                score = 40
            # Description contains query
            elif description and query in description.lower():
                score = 20
            
            if score > 0:
                results.append({
                    'score': score,
                    'name': name,
                    'type': acc_type,
                    'code': code,
                    'level': level,
                    'is_postable': is_postable,
                    'description': description,
                    'display_name': f"{code} - {name}" if code else name
                })
        
        # Sort by score and return top results
        results.sort(reverse=True, key=lambda x: (x['score'], -len(x['name'])))
        return results[:limit]
      # Enhanced versions of base system methods that provide better UI compatibility
    def get_all_accounts(self):
        """Get all accounts in tuple format for UI compatibility."""
        # Delegate to the unified base system's get_all_accounts which returns tuples
        return self.base_system.get_all_accounts()
    
    def get_postable_accounts(self):
        """Get postable accounts with enhanced formatting."""
        raw_accounts = self.base_system.get_postable_accounts()
        
        accounts = []
        for account in raw_accounts:
            try:
                if isinstance(account, dict):
                    accounts.append(account)
                elif isinstance(account, (tuple, list)) and len(account) >= 7:
                    name, acc_type, code, parent_code, level, is_postable, description = account[:7]
                    accounts.append({
                        'name': name,
                        'type': acc_type,
                        'code': code, 
                        'parent_code': parent_code,
                        'level': level,
                        'is_postable': bool(is_postable),
                        'description': description or ""
                    })
                else:
                    self.logger.warning(f"Unexpected postable account format: {account}")
            except Exception as e:
                self.logger.error(f"Error processing postable account: {account}, error: {e}")
                
        return accounts
    
    def get_accounts_by_level(self, level=1):
        """Get accounts by level with enhanced formatting."""
        raw_accounts = self.base_system.get_accounts_by_level(level)
        
        accounts = []
        for account in raw_accounts:
            if len(account) >= 7:
                name, acc_type, code, parent_code, acc_level, is_postable, description = account
                accounts.append({
                    'name': name,
                    'type': acc_type,
                    'code': code,
                    'parent_code': parent_code, 
                    'level': acc_level,
                    'is_postable': bool(is_postable),
                    'description': description or ""
                })
                
        return accounts
    
    def get_recent_journal_entries(self, limit=20):
        """Get recent journal entries with enhanced formatting."""
        # The base system already returns this in dictionary format
        return self.base_system.get_recent_journal_entries(limit)
