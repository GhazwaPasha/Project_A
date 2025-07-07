"""
Period Closing and Audit Trail Management System
"""

import uuid
from datetime import datetime, date, timedelta
from decimal import Decimal
import logging
import hashlib
import json
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass

@dataclass
class AuditLogEntry:
    """Audit log entry data structure."""
    table_name: str
    record_id: str
    operation: str
    old_values: Optional[Dict] = None
    new_values: Optional[Dict] = None
    changed_by: Optional[str] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

@dataclass
class AccountingPeriod:
    """Accounting period data structure."""
    period_name: str
    start_date: date
    end_date: date
    period_type: str = 'MONTHLY'
    status: str = 'OPEN'

class PeriodClosingManager:
    """Manages accounting period closing and audit trails."""
    
    def __init__(self, db_manager, organization_id=None, user_id=None):
        self.db_manager = db_manager
        self.organization_id = organization_id
        self.user_id = user_id
        self.logger = logging.getLogger(__name__)
    
    def create_accounting_period(self, period_name: str, start_date: date, end_date: date, 
                               period_type: str = 'MONTHLY') -> str:
        """Create a new accounting period."""
        period_id = str(uuid.uuid4())
        
        # Validate dates
        if start_date >= end_date:
            raise ValueError("Start date must be before end date")
        
        # Check for overlapping periods
        if self._check_period_overlap(start_date, end_date, period_type):
            raise ValueError("Period overlaps with existing period")
        
        insert_sql = """
        INSERT INTO accounting_periods 
        (id, period_name, start_date, end_date, period_type, status, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, NOW())
        """
        
        try:
            with self.db_manager.get_db_cursor() as cursor:
                cursor.execute(insert_sql, (
                    period_id, period_name, start_date, end_date, period_type, 'OPEN'
                ))
            
            self.logger.info(f"Created accounting period: {period_name} ({start_date} to {end_date})")
            return period_id
            
        except Exception as e:
            self.logger.error(f"Failed to create accounting period: {e}")
            raise
    
    def close_accounting_period(self, period_id: str, force_close: bool = False) -> bool:
        """Close an accounting period with validation checks."""
        try:
            # Get period details
            period = self._get_period_by_id(period_id)
            if not period:
                raise ValueError("Period not found")
            
            if period['status'] != 'OPEN':
                raise ValueError(f"Period is already {period['status']}")
            
            # Perform pre-closing validations
            validation_results = self._validate_period_for_closing(period_id)
            
            if not force_close and validation_results['errors']:
                raise ValueError(f"Period validation failed: {validation_results['errors']}")
            
            # Generate trial balance checksum
            trial_balance_checksum = self._generate_trial_balance_checksum(
                period['start_date'], period['end_date']
            )
            
            # Close the period
            update_sql = """
            UPDATE accounting_periods 
            SET status = 'CLOSED', 
                closed_by = %s, 
                closed_at = NOW(),
                trial_balance_checksum = %s
            WHERE id = %s
            """
            
            with self.db_manager.get_db_cursor() as cursor:
                cursor.execute(update_sql, (self.user_id, trial_balance_checksum, period_id))
            
            # Log the closing action
            self._log_audit_event(
                'accounting_periods', period_id, 'UPDATE',
                {'status': 'OPEN'}, {'status': 'CLOSED', 'closed_by': self.user_id}
            )
            
            self.logger.info(f"Closed accounting period: {period['period_name']}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to close accounting period: {e}")
            raise
    
    def reopen_accounting_period(self, period_id: str, reason: str) -> bool:
        """Reopen a closed accounting period with proper authorization."""
        try:
            period = self._get_period_by_id(period_id)
            if not period:
                raise ValueError("Period not found")
            
            if period['status'] not in ['CLOSED']:
                raise ValueError(f"Cannot reopen period with status: {period['status']}")
            
            # Check if subsequent periods are closed (they should be reopened first)
            subsequent_closed = self._check_subsequent_closed_periods(period['end_date'])
            if subsequent_closed:
                raise ValueError("Cannot reopen period with subsequent closed periods")
            
            update_sql = """
            UPDATE accounting_periods 
            SET status = 'OPEN', 
                closed_by = NULL, 
                closed_at = NULL,
                trial_balance_checksum = NULL
            WHERE id = %s
            """
            
            with self.db_manager.get_db_cursor() as cursor:
                cursor.execute(update_sql, (period_id,))
            
            # Log the reopening action
            self._log_audit_event(
                'accounting_periods', period_id, 'UPDATE',
                {'status': 'CLOSED'}, {'status': 'OPEN', 'reopened_by': self.user_id, 'reason': reason}
            )
            
            self.logger.info(f"Reopened accounting period: {period['period_name']}, reason: {reason}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to reopen accounting period: {e}")
            raise
    
    def get_period_status_summary(self) -> Dict[str, Any]:
        """Get summary of all accounting periods and their status."""
        query_sql = """
        SELECT 
            period_name,
            start_date,
            end_date,
            period_type,
            status,
            closed_at,
            trial_balance_checksum IS NOT NULL as has_checksum
        FROM accounting_periods 
        ORDER BY start_date DESC
        """
        
        try:
            with self.db_manager.get_db_cursor() as cursor:
                cursor.execute(query_sql)
                periods = cursor.fetchall()
            
            # Count by status
            status_counts = {'OPEN': 0, 'CLOSED': 0, 'LOCKED': 0}
            for period in periods:
                status_counts[period['status']] = status_counts.get(period['status'], 0) + 1
            
            return {
                'periods': periods,
                'status_summary': status_counts,
                'total_periods': len(periods)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get period status summary: {e}")
            raise
    
    def _validate_period_for_closing(self, period_id: str) -> Dict[str, Any]:
        """Validate period readiness for closing."""
        period = self._get_period_by_id(period_id)
        errors = []
        warnings = []
        
        try:
            with self.db_manager.get_db_cursor() as cursor:
                # Check for unbalanced journal entries
                balance_check_sql = """
                SELECT COUNT(*) as unbalanced_entries
                FROM (
                    SELECT 
                        h.id,
                        SUM(COALESCE(l.debit_amount, 0)) - SUM(COALESCE(l.credit_amount, 0)) as balance
                    FROM journal_entry_headers h
                    LEFT JOIN journal_entry_lines l ON h.id = l.header_id
                    WHERE h.entry_date BETWEEN %s AND %s
                    GROUP BY h.id
                    HAVING ABS(SUM(COALESCE(l.debit_amount, 0)) - SUM(COALESCE(l.credit_amount, 0))) > 0.01
                ) unbalanced
                """
                
                cursor.execute(balance_check_sql, (period['start_date'], period['end_date']))
                unbalanced = cursor.fetchone()['unbalanced_entries']
                
                if unbalanced > 0:
                    errors.append(f"{unbalanced} unbalanced journal entries found")
                
                # Check for draft entries
                draft_check_sql = """
                SELECT COUNT(*) as draft_entries
                FROM journal_entry_headers
                WHERE entry_date BETWEEN %s AND %s AND status = 'DRAFT'
                """
                
                cursor.execute(draft_check_sql, (period['start_date'], period['end_date']))
                draft_entries = cursor.fetchone()['draft_entries']
                
                if draft_entries > 0:
                    warnings.append(f"{draft_entries} draft journal entries found")
                
                # Check trial balance
                trial_balance_sql = """
                SELECT 
                    SUM(CASE WHEN debit_amount > 0 THEN debit_amount ELSE 0 END) as total_debits,
                    SUM(CASE WHEN credit_amount > 0 THEN credit_amount ELSE 0 END) as total_credits
                FROM journal_entry_lines l
                JOIN journal_entry_headers h ON l.header_id = h.id
                WHERE h.entry_date BETWEEN %s AND %s AND h.status = 'POSTED'
                """
                
                cursor.execute(trial_balance_sql, (period['start_date'], period['end_date']))
                trial_balance = cursor.fetchone()
                
                debit_credit_diff = abs(trial_balance['total_debits'] - trial_balance['total_credits'])
                if debit_credit_diff > 0.01:
                    errors.append(f"Trial balance difference: {debit_credit_diff}")
        
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")
        
        return {
            'errors': errors,
            'warnings': warnings,
            'can_close': len(errors) == 0
        }
    
    def _generate_trial_balance_checksum(self, start_date: date, end_date: date) -> str:
        """Generate checksum for trial balance integrity verification."""
        try:
            with self.db_manager.get_db_cursor() as cursor:
                checksum_sql = """
                SELECT 
                    l.account_code,
                    SUM(COALESCE(l.debit_amount, 0)) as total_debits,
                    SUM(COALESCE(l.credit_amount, 0)) as total_credits
                FROM journal_entry_lines l
                JOIN journal_entry_headers h ON l.header_id = h.id
                WHERE h.entry_date BETWEEN %s AND %s AND h.status = 'POSTED'
                GROUP BY l.account_code
                ORDER BY l.account_code
                """
                
                cursor.execute(checksum_sql, (start_date, end_date))
                trial_balance_data = cursor.fetchall()
                
                # Create deterministic string for hashing
                checksum_string = ""
                for row in trial_balance_data:
                    checksum_string += f"{row['account_code']}:{row['total_debits']}:{row['total_credits']}|"
                
                # Generate SHA-256 hash
                return hashlib.sha256(checksum_string.encode()).hexdigest()
                
        except Exception as e:
            self.logger.error(f"Failed to generate trial balance checksum: {e}")
            return ""
    
    def verify_period_integrity(self, period_id: str) -> Dict[str, Any]:
        """Verify the integrity of a closed period using checksums."""
        period = self._get_period_by_id(period_id)
        if not period:
            raise ValueError("Period not found")
        
        if period['status'] != 'CLOSED':
            return {'verified': False, 'reason': 'Period is not closed'}
        
        if not period['trial_balance_checksum']:
            return {'verified': False, 'reason': 'No checksum available'}
        
        current_checksum = self._generate_trial_balance_checksum(
            period['start_date'], period['end_date']
        )
        
        verified = current_checksum == period['trial_balance_checksum']
        
        return {
            'verified': verified,
            'reason': 'Verified' if verified else 'Checksum mismatch - data may have been modified',
            'original_checksum': period['trial_balance_checksum'],
            'current_checksum': current_checksum
        }
    
    def _check_period_overlap(self, start_date: date, end_date: date, period_type: str) -> bool:
        """Check if period overlaps with existing periods."""
        overlap_sql = """
        SELECT COUNT(*) as overlapping
        FROM accounting_periods
        WHERE period_type = %s
        AND (
            (start_date <= %s AND end_date >= %s) OR
            (start_date <= %s AND end_date >= %s) OR
            (start_date >= %s AND end_date <= %s)
        )
        """
        
        try:
            with self.db_manager.get_db_cursor() as cursor:
                cursor.execute(overlap_sql, (
                    period_type, start_date, start_date, end_date, end_date, start_date, end_date
                ))
                return cursor.fetchone()['overlapping'] > 0
        except Exception as e:
            self.logger.error(f"Failed to check period overlap: {e}")
            return True  # Err on the side of caution
    
    def _check_subsequent_closed_periods(self, period_end_date: date) -> bool:
        """Check if there are subsequent closed periods."""
        subsequent_sql = """
        SELECT COUNT(*) as subsequent_closed
        FROM accounting_periods
        WHERE start_date > %s AND status = 'CLOSED'
        """
        
        try:
            with self.db_manager.get_db_cursor() as cursor:
                cursor.execute(subsequent_sql, (period_end_date,))
                return cursor.fetchone()['subsequent_closed'] > 0
        except Exception as e:
            self.logger.error(f"Failed to check subsequent periods: {e}")
            return True
    
    def _get_period_by_id(self, period_id: str) -> Optional[Dict]:
        """Get period details by ID."""
        query_sql = """
        SELECT * FROM accounting_periods WHERE id = %s
        """
        
        try:
            with self.db_manager.get_db_cursor() as cursor:
                cursor.execute(query_sql, (period_id,))
                return cursor.fetchone()
        except Exception as e:
            self.logger.error(f"Failed to get period by ID: {e}")
            return None
    
    def _log_audit_event(self, table_name: str, record_id: str, operation: str, 
                        old_values: Optional[Dict] = None, new_values: Optional[Dict] = None):
        """Log an audit event."""
        audit_sql = """
        INSERT INTO audit_log 
        (table_name, record_id, operation, old_values, new_values, changed_by, changed_at)
        VALUES (%s, %s, %s, %s, %s, %s, NOW())
        """
        
        try:
            with self.db_manager.get_db_cursor() as cursor:
                cursor.execute(audit_sql, (
                    table_name, record_id, operation,
                    json.dumps(old_values) if old_values else None,
                    json.dumps(new_values) if new_values else None,
                    self.user_id
                ))
        except Exception as e:
            self.logger.error(f"Failed to log audit event: {e}")
    
class AuditTrailManager:
    """Manages audit trail queries and reporting."""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)
    
    def get_audit_trail(self, table_name: Optional[str] = None, record_id: Optional[str] = None,
                       start_date: Optional[date] = None, end_date: Optional[date] = None,
                       limit: int = 100) -> List[Dict]:
        """Get audit trail with optional filtering."""
        conditions = []
        params = []
        
        if table_name:
            conditions.append("table_name = %s")
            params.append(table_name)
        
        if record_id:
            conditions.append("record_id = %s")
            params.append(record_id)
        
        if start_date:
            conditions.append("changed_at >= %s")
            params.append(start_date)
        
        if end_date:
            conditions.append("changed_at <= %s")
            params.append(end_date)
        
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        
        query_sql = f"""
        SELECT 
            table_name,
            record_id,
            operation,
            old_values,
            new_values,
            changed_by,
            changed_at,
            session_id
        FROM audit_log
        {where_clause}
        ORDER BY changed_at DESC
        LIMIT %s
        """
        
        params.append(limit)
        
        try:
            with self.db_manager.get_db_cursor() as cursor:
                cursor.execute(query_sql, params)
                return cursor.fetchall()
        except Exception as e:
            self.logger.error(f"Failed to get audit trail: {e}")
            return []
    
    def get_user_activity_summary(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get summary of user activity over specified days."""
        start_date = datetime.now().date() - timedelta(days=days)
        
        activity_sql = """
        SELECT 
            table_name,
            operation,
            COUNT(*) as operation_count,
            MAX(changed_at) as last_activity
        FROM audit_log
        WHERE changed_by = %s AND changed_at >= %s
        GROUP BY table_name, operation
        ORDER BY operation_count DESC
        """
        
        try:
            with self.db_manager.get_db_cursor() as cursor:
                cursor.execute(activity_sql, (user_id, start_date))
                activities = cursor.fetchall()
            
            total_operations = sum(activity['operation_count'] for activity in activities)
            
            return {
                'user_id': user_id,
                'period_days': days,
                'total_operations': total_operations,
                'activities': activities,
                'most_active_table': activities[0]['table_name'] if activities else None
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get user activity summary: {e}")
            return {}
    
    def get_data_modification_report(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """Generate data modification report for a period."""
        modification_sql = """
        SELECT 
            table_name,
            operation,
            DATE(changed_at) as modification_date,
            COUNT(*) as modification_count
        FROM audit_log
        WHERE changed_at BETWEEN %s AND %s
        AND operation IN ('UPDATE', 'DELETE')
        GROUP BY table_name, operation, DATE(changed_at)
        ORDER BY modification_date DESC, modification_count DESC
        """
        
        try:
            with self.db_manager.get_db_cursor() as cursor:
                cursor.execute(modification_sql, (start_date, end_date))
                modifications = cursor.fetchall()
            
            # Group by table and operation
            summary = {}
            for mod in modifications:
                table = mod['table_name']
                if table not in summary:
                    summary[table] = {'UPDATE': 0, 'DELETE': 0}
                summary[table][mod['operation']] += mod['modification_count']
            
            return {
                'period': f"{start_date} to {end_date}",
                'detailed_modifications': modifications,
                'summary_by_table': summary
            }
            
        except Exception as e:
            self.logger.error(f"Failed to generate modification report: {e}")
            return {}
