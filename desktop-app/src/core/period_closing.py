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
    """Manages accounting period closing and audit trails using SupabaseManager."""
    
    def __init__(self, db_manager, organization_id=None, user_id=None):
        self.db_manager = db_manager  # This is a SupabaseManager instance
        self.organization_id = organization_id
        self.user_id = user_id
        self.logger = logging.getLogger(__name__)
    
    def create_accounting_period(self, period_name: str, start_date: date, end_date: date, period_type: str = 'MONTHLY') -> str:
        """Create a new accounting period using Supabase."""
        if start_date >= end_date:
            raise ValueError("Start date must be before end date")
        if self._check_period_overlap(start_date, end_date, period_type):
            raise ValueError("Period overlaps with existing period")
        closing_data = {
            "organization_id": self.organization_id,
            "period_name": period_name,
            "start_date": start_date.isoformat() if hasattr(start_date, 'isoformat') else start_date,
            "end_date": end_date.isoformat() if hasattr(end_date, 'isoformat') else end_date,
            "is_closed": False,
            "notes": f"Period type: {period_type}"
        }
        result = self.db_manager.create_period_closing(closing_data)
        if not result:
            raise Exception("Failed to create period closing (Supabase error)")
        return result['id']
    
    def close_accounting_period(self, period_id: str, force_close: bool = False) -> bool:
        """Close an accounting period using Supabase."""
        period = self._get_period_by_id(period_id)
        if not period:
            raise ValueError("Period not found")
        if period.get('is_closed'):
            raise ValueError("Period is already closed")
        validation_results = self._validate_period_for_closing(period_id)
        if not force_close and validation_results['errors']:
            raise ValueError(f"Period validation failed: {validation_results['errors']}")
        start_date = period.get('start_date')
        end_date = period.get('end_date')
        if not start_date or not end_date:
            raise ValueError("Period start_date or end_date is missing")
        trial_balance_checksum = self._generate_trial_balance_checksum(start_date, end_date)
        notes = (period.get('notes') or '') + f" | Trial balance checksum: {trial_balance_checksum}"
        update_result = self.db_manager.supabase.table('period_closing').update({
            "is_closed": True,
            "closed_by": self.user_id,
            "closed_at": datetime.now().isoformat(),
            "notes": notes
        }).eq("id", period_id).execute()
        if not update_result.data:
            raise Exception("Failed to close period (Supabase error)")
        self._log_audit_event('period_closing', period_id, 'UPDATE', {'is_closed': False}, {'is_closed': True, 'closed_by': self.user_id})
        self.logger.info(f"Closed accounting period: {period.get('period_name')}")
        return True
    
    def reopen_accounting_period(self, period_id: str, reason: str) -> bool:
        """Reopen a closed accounting period using Supabase."""
        period = self._get_period_by_id(period_id)
        if not period:
            raise ValueError("Period not found")
        if not period.get('is_closed'):
            raise ValueError("Period is not closed")
        end_date = period.get('end_date')
        if not end_date:
            raise ValueError("Period end_date is missing")
        subsequent_closed = self._check_subsequent_closed_periods(end_date)
        if subsequent_closed:
            raise ValueError("Cannot reopen period with subsequent closed periods")
        notes = (period.get('notes') or '') + f" | Reopened: {reason}"
        update_result = self.db_manager.supabase.table('period_closing').update({
            "is_closed": False,
            "closed_by": None,
            "closed_at": None,
            "notes": notes
        }).eq("id", period_id).execute()
        if not update_result.data:
            raise Exception("Failed to reopen period (Supabase error)")
        self._log_audit_event('period_closing', period_id, 'UPDATE', {'is_closed': True}, {'is_closed': False, 'reopened_by': self.user_id, 'reason': reason})
        self.logger.info(f"Reopened accounting period: {period.get('period_name')}, reason: {reason}")
        return True
    
    def get_period_status_summary(self) -> Dict[str, Any]:
        """Get summary of all accounting periods and their status using Supabase."""
        periods = self.db_manager.get_period_closings(self.organization_id)
        formatted_periods = []
        for period in periods:
            if period:
                formatted_periods.append({
                    'id': period.get('id'),
                    'period_name': period.get('period_name'),
                    'start_date': period.get('start_date'),
                    'end_date': period.get('end_date'),
                    'status': 'CLOSED' if period.get('is_closed') else 'OPEN',
                    'closed_at': period.get('closed_at'),
                    'closed_by': period.get('closed_by'),
                    'notes': period.get('notes')
                })
        status_counts = {'OPEN': 0, 'CLOSED': 0}
        for period in formatted_periods:
            status_counts[period['status']] = status_counts.get(period['status'], 0) + 1
        return {
            'periods': formatted_periods,
            'status_summary': status_counts,
            'total_periods': len(formatted_periods)
        }
    
    def _validate_period_for_closing(self, period_id: str) -> Dict[str, Any]:
        """Validate period readiness for closing."""
        period = self._get_period_by_id(period_id)
        errors = []
        warnings = []
        
        if not period:
            errors.append("Period not found")
            return {
                'errors': errors,
                'warnings': warnings,
                'is_valid': False
            }
        
        try:
            with self.db_manager.get_db_cursor() as cursor:
                # Check for unbalanced journal entries
                balance_check_sql = """
                SELECT COUNT(*) as unbalanced_entries
                FROM (
                    SELECT 
                        je.id,
                        SUM(COALESCE(jel.debit_amount, 0)) - SUM(COALESCE(jel.credit_amount, 0)) as balance
                    FROM journal_entries je
                    LEFT JOIN journal_entry_lines jel ON je.id = jel.journal_entry_id
                    WHERE je.entry_date BETWEEN %s AND %s
                    GROUP BY je.id
                    HAVING ABS(SUM(COALESCE(jel.debit_amount, 0)) - SUM(COALESCE(jel.credit_amount, 0))) > 0.01
                ) unbalanced
                """
                
                cursor.execute(balance_check_sql, (period.get('start_date'), period.get('end_date')))
                result = cursor.fetchone()
                if result:
                    unbalanced = result.get('unbalanced_entries', 0)
                    if unbalanced > 0:
                        errors.append(f"{unbalanced} unbalanced journal entries found")
                
                # Check for draft entries (assuming there's a status field)
                draft_check_sql = """
                SELECT COUNT(*) as draft_entries
                FROM journal_entries
                WHERE entry_date BETWEEN %s AND %s AND status = 'DRAFT'
                """
                
                cursor.execute(draft_check_sql, (period.get('start_date'), period.get('end_date')))
                result = cursor.fetchone()
                if result:
                    draft_entries = result.get('draft_entries', 0)
                
                if draft_entries > 0:
                    warnings.append(f"{draft_entries} draft journal entries found")
                
                # Check trial balance
                trial_balance_sql = """
                SELECT 
                    SUM(CASE WHEN jel.debit_amount > 0 THEN jel.debit_amount ELSE 0 END) as total_debits,
                    SUM(CASE WHEN jel.credit_amount > 0 THEN jel.credit_amount ELSE 0 END) as total_credits
                FROM journal_entry_lines jel
                JOIN journal_entries je ON jel.journal_entry_id = je.id
                WHERE je.entry_date BETWEEN %s AND %s
                """
                
                cursor.execute(trial_balance_sql, (period.get('start_date'), period.get('end_date')))
                result = cursor.fetchone()
                
                if result:
                    total_debits = result.get('total_debits', 0) or 0
                    total_credits = result.get('total_credits', 0) or 0
                    
                    if abs(total_debits - total_credits) > 0.01:
                        errors.append(f"Trial balance out of balance: Debits {total_debits}, Credits {total_credits}")
                    else:
                        warnings.append(f"Trial balance balanced: Debits {total_debits}, Credits {total_credits}")
                
        except Exception as e:
            self.logger.error(f"Validation error: {e}")
            errors.append(f"Validation failed: {str(e)}")
        
        return {
            'errors': errors,
            'warnings': warnings,
            'is_valid': len(errors) == 0
        }
    
    def _generate_trial_balance_checksum(self, start_date: date, end_date: date) -> str:
        """Generate a checksum for trial balance validation."""
        try:
            with self.db_manager.get_db_cursor() as cursor:
                # Get trial balance data
                sql = """
                SELECT 
                    a.code,
                    a.name,
                    SUM(COALESCE(jel.debit_amount, 0)) as total_debits,
                    SUM(COALESCE(jel.credit_amount, 0)) as total_credits
                FROM accounts a
                LEFT JOIN journal_entry_lines jel ON a.id = jel.account_id
                LEFT JOIN journal_entries je ON jel.journal_entry_id = je.id
                WHERE je.entry_date BETWEEN %s AND %s
                GROUP BY a.id, a.code, a.name
                ORDER BY a.code
                """
                
                cursor.execute(sql, (start_date, end_date))
                trial_balance = cursor.fetchall()
                
                # Create checksum string
                checksum_data = []
                for row in trial_balance:
                    checksum_data.append(f"{row['code']}:{row['total_debits']}:{row['total_credits']}")
                
                checksum_string = "|".join(checksum_data)
                return hashlib.sha256(checksum_string.encode()).hexdigest()[:16]
                
        except Exception as e:
            self.logger.error(f"Failed to generate trial balance checksum: {e}")
            return "ERROR"
    
    def verify_period_integrity(self, period_id: str) -> Dict[str, Any]:
        """Verify the integrity of a closed period."""
        period = self._get_period_by_id(period_id)
        if not period:
            return {'valid': False, 'error': 'Period not found'}
        
        try:
            # Get dates with proper validation
            start_date = period.get('start_date')
            end_date = period.get('end_date')
            
            if not start_date or not end_date:
                return {'valid': False, 'error': 'Invalid period dates'}
            
            # Recalculate checksum
            current_checksum = self._generate_trial_balance_checksum(start_date, end_date)
            
            # Extract stored checksum from notes
            stored_checksum = None
            if period.get('notes'):
                for line in period.get('notes', '').split('|'):
                    if 'Trial balance checksum:' in line:
                        stored_checksum = line.split(':')[-1].strip()
                        break
            
            return {
                'valid': stored_checksum == current_checksum,
                'stored_checksum': stored_checksum,
                'current_checksum': current_checksum,
                'period_name': period.get('period_name', 'Unknown')
            }
            
        except Exception as e:
            return {'valid': False, 'error': str(e)}
    
    def _check_period_overlap(self, start_date: date, end_date: date, period_type: str) -> bool:
        """Check if a new period would overlap with existing periods using Supabase."""
        # Ensure dates are ISO strings for Supabase filter
        start_date_str = start_date.isoformat() if hasattr(start_date, 'isoformat') else str(start_date)
        end_date_str = end_date.isoformat() if hasattr(end_date, 'isoformat') else str(end_date)
        or_filter = (
            f"and(start_date.lte.{start_date_str},end_date.gte.{start_date_str}),"
            f"and(start_date.lte.{end_date_str},end_date.gte.{end_date_str}),"
            f"and(start_date.gte.{start_date_str},end_date.lte.{end_date_str})"
        )
        result = self.db_manager.supabase.table('period_closing') \
            .select('id') \
            .eq('organization_id', self.organization_id) \
            .or_(or_filter) \
            .execute()
        return bool(result.data)
    
    def _check_subsequent_closed_periods(self, period_end_date: date) -> bool:
        """Check if there are closed periods after the given date using Supabase."""
        result = self.db_manager.supabase.table('period_closing') \
            .select('id') \
            .eq('organization_id', self.organization_id) \
            .gt('start_date', period_end_date) \
            .eq('is_closed', True) \
            .execute()
        return bool(result.data)
    
    def _get_period_by_id(self, period_id: str) -> Optional[Dict]:
        """Get period details by ID using Supabase."""
        periods = self.db_manager.supabase.table('period_closing').select('*').eq('id', period_id).eq('organization_id', self.organization_id).execute()
        if periods.data and len(periods.data) > 0:
            return periods.data[0]
        return None
    
    def _log_audit_event(self, table_name: str, record_id: str, operation: str, 
                        old_values: Optional[Dict] = None, new_values: Optional[Dict] = None):
        """Log an audit event (placeholder for audit trail)."""
        # This would typically write to an audit log table
        self.logger.info(f"Audit: {operation} on {table_name} record {record_id}")
        if old_values:
            self.logger.debug(f"Old values: {old_values}")
        if new_values:
            self.logger.debug(f"New values: {new_values}")

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
