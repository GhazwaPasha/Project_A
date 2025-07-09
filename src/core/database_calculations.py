"""
Database Calculations Adapter
Calls SQL functions for financial calculations instead of Python calculations.
"""

from typing import Dict, List, Any, Optional
from datetime import date, datetime
import json


class DatabaseCalculations:
    """Adapter for calling database financial calculation functions."""
    
    def __init__(self, supabase_client):
        self.supabase = supabase_client
    
    def calculate_current_ratio(self, org_id: str, as_of_date: Optional[date] = None) -> float:
        """Calculate current ratio using database function."""
        try:
            if not as_of_date:
                as_of_date = date.today()
            
            result = self.supabase.rpc(
                'calculate_current_ratio',
                {
                    'p_org_id': org_id,
                    'p_as_of_date': as_of_date.isoformat()
                }
            ).execute()
            
            if result.data:
                return float(result.data[0] if isinstance(result.data, list) else result.data)
            return 0.0
            
        except Exception as e:
            print(f"Error calculating current ratio: {e}")
            return 0.0
    
    def calculate_quick_ratio(self, org_id: str, as_of_date: Optional[date] = None) -> float:
        """Calculate quick ratio using database function."""
        try:
            if not as_of_date:
                as_of_date = date.today()
            
            result = self.supabase.rpc(
                'calculate_quick_ratio',
                {
                    'p_org_id': org_id,
                    'p_as_of_date': as_of_date.isoformat()
                }
            ).execute()
            
            if result.data:
                return float(result.data[0] if isinstance(result.data, list) else result.data)
            return 0.0
            
        except Exception as e:
            print(f"Error calculating quick ratio: {e}")
            return 0.0
    
    def calculate_gross_profit_margin(self, org_id: str, from_date: date, to_date: date) -> float:
        """Calculate gross profit margin using database function."""
        try:
            result = self.supabase.rpc(
                'calculate_gross_profit_margin',
                {
                    'p_org_id': org_id,
                    'p_from_date': from_date.isoformat(),
                    'p_to_date': to_date.isoformat()
                }
            ).execute()
            
            if result.data:
                return float(result.data[0] if isinstance(result.data, list) else result.data)
            return 0.0
            
        except Exception as e:
            print(f"Error calculating gross profit margin: {e}")
            return 0.0
    
    def calculate_net_profit_margin(self, org_id: str, from_date: date, to_date: date) -> float:
        """Calculate net profit margin using database function."""
        try:
            result = self.supabase.rpc(
                'calculate_net_profit_margin',
                {
                    'p_org_id': org_id,
                    'p_from_date': from_date.isoformat(),
                    'p_to_date': to_date.isoformat()
                }
            ).execute()
            
            if result.data:
                return float(result.data[0] if isinstance(result.data, list) else result.data)
            return 0.0
            
        except Exception as e:
            print(f"Error calculating net profit margin: {e}")
            return 0.0
    
    def calculate_roa(self, org_id: str, from_date: date, to_date: date) -> float:
        """Calculate ROA using database function."""
        try:
            result = self.supabase.rpc(
                'calculate_roa',
                {
                    'p_org_id': org_id,
                    'p_from_date': from_date.isoformat(),
                    'p_to_date': to_date.isoformat()
                }
            ).execute()
            
            if result.data:
                return float(result.data[0] if isinstance(result.data, list) else result.data)
            return 0.0
            
        except Exception as e:
            print(f"Error calculating ROA: {e}")
            return 0.0
    
    def calculate_working_capital(self, org_id: str, as_of_date: Optional[date] = None) -> float:
        """Calculate working capital using database function."""
        try:
            if not as_of_date:
                as_of_date = date.today()
            
            result = self.supabase.rpc(
                'calculate_working_capital',
                {
                    'p_org_id': org_id,
                    'p_as_of_date': as_of_date.isoformat()
                }
            ).execute()
            
            if result.data:
                return float(result.data[0] if isinstance(result.data, list) else result.data)
            return 0.0
            
        except Exception as e:
            print(f"Error calculating working capital: {e}")
            return 0.0
    
    def generate_balance_sheet(self, org_id: str, as_of_date: Optional[date] = None) -> List[Dict[str, Any]]:
        """Generate balance sheet using database function."""
        try:
            if not as_of_date:
                as_of_date = date.today()
            
            print(f"🔍 Calling generate_balance_sheet for org {org_id} as of {as_of_date}")
            
            result = self.supabase.rpc(
                'generate_balance_sheet',
                {
                    'p_org_id': org_id,
                    'p_as_of_date': as_of_date.isoformat()
                }
            ).execute()
            
            print(f"📊 Balance sheet result: {result.data}")
            print(f"📊 Result type: {type(result.data)}")
            print(f"📊 Result length: {len(result.data) if result.data else 0}")
            
            if result.data:
                return result.data
            return []
            
        except Exception as e:
            print(f"Error generating balance sheet: {e}")
            return []
    
    def generate_income_statement(self, org_id: str, from_date: date, to_date: date) -> List[Dict[str, Any]]:
        """Generate income statement using database function."""
        try:
            print(f"🔍 Calling generate_income_statement for org {org_id} from {from_date} to {to_date}")
            
            result = self.supabase.rpc(
                'generate_income_statement',
                {
                    'p_org_id': org_id,
                    'p_from_date': from_date.isoformat(),
                    'p_to_date': to_date.isoformat()
                }
            ).execute()
            
            print(f"📊 Database result: {result.data}")
            print(f"📊 Result type: {type(result.data)}")
            print(f"📊 Result length: {len(result.data) if result.data else 0}")
            
            if result.data:
                return result.data
            return []
            
        except Exception as e:
            print(f"Error generating income statement: {e}")
            return []
    
    def get_trial_balance(self, org_id: str, as_of_date: Optional[date] = None) -> List[Dict[str, Any]]:
        """Get trial balance using database function."""
        try:
            if not as_of_date:
                as_of_date = date.today()
            
            print(f"🔍 Calling get_trial_balance for org {org_id} as of {as_of_date}")
            
            result = self.supabase.rpc(
                'get_trial_balance',
                {
                    'p_org_id': org_id,
                    'p_as_of_date': as_of_date.isoformat()
                }
            ).execute()
            
            print(f"📊 Trial balance result: {result.data}")
            print(f"📊 Result type: {type(result.data)}")
            print(f"📊 Result length: {len(result.data) if result.data else 0}")
            
            if result.data:
                return result.data
            return []
            
        except Exception as e:
            print(f"Error getting trial balance: {e}")
            return []
    
    def calculate_all_ratios(self, org_id: str, from_date: date, to_date: date, 
                           as_of_date: Optional[date] = None) -> Dict[str, Any]:
        """Calculate all financial ratios using optimized database function."""
        try:
            if not as_of_date:
                as_of_date = date.today()
            
            result = self.supabase.rpc(
                'calculate_all_ratios',
                {
                    'p_org_id': org_id,
                    'p_from_date': from_date.isoformat(),
                    'p_to_date': to_date.isoformat(),
                    'p_as_of_date': as_of_date.isoformat()
                }
            ).execute()
            
            if result.data:
                # Handle different return types from database function
                if isinstance(result.data, dict):
                    # Database function returned a dict directly
                    return result.data
                elif isinstance(result.data, str):
                    # Database function returned a JSON string
                    return json.loads(result.data)
                elif isinstance(result.data, list) and len(result.data) > 0:
                    # Database function returned a list with JSON string as first element
                    if isinstance(result.data[0], str):
                        return json.loads(result.data[0])
                    elif isinstance(result.data[0], dict):
                        return result.data[0]
                    else:
                        return result.data[0]
                else:
                    # Fallback to raw data
                    return result.data
            return {}
            
        except Exception as e:
            print(f"Error calculating all ratios: {e}")
            return {}
    
    def get_net_income(self, org_id: str, from_date: date, to_date: date) -> float:
        """Get net income using database function."""
        try:
            result = self.supabase.rpc(
                'calculate_net_income',
                {
                    'p_org_id': org_id,
                    'p_from_date': from_date.isoformat(),
                    'p_to_date': to_date.isoformat()
                }
            ).execute()
            
            if result.data:
                return float(result.data[0] if isinstance(result.data, list) else result.data)
            return 0.0
            
        except Exception as e:
            print(f"Error calculating net income: {e}")
            return 0.0 