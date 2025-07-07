"""
AI Account Resolver Service
Provides fuzzy matching and context-aware account name resolution for AI navigation.
Specifically designed for the AI status bar to understand user queries like "show me cash in hand ledger".
"""

import re
from typing import List, Tuple, Optional, Dict
from difflib import SequenceMatcher


class AccountMatch:
    """Represents a matched account with confidence score"""
    
    def __init__(self, account_id: str, account_name: str, account_code: str, 
                 confidence: float, match_type: str):
        self.account_id = account_id
        self.account_name = account_name
        self.account_code = account_code
        self.confidence = confidence
        self.match_type = match_type  # 'exact', 'fuzzy', 'partial', 'contextual'
    
    def __repr__(self):
        return f"AccountMatch({self.account_name}, {self.confidence:.2f}, {self.match_type})"


class AIAccountResolver:
    """Smart account matching for AI navigation with fuzzy search and context awareness"""
    
    def __init__(self, accounting_system=None):
        self.accounting_system = accounting_system
        self._account_cache = {}
        self._pattern_cache = {}
        
        # Common account type patterns for context matching
        self.account_patterns = {
            'cash': {
                'keywords': ['cash', 'petty cash', 'till', 'drawer'],
                'account_types': ['Cash', 'Current Assets'],
                'codes': ['1001', '1010', '1100']
            },
            'bank': {
                'keywords': ['bank', 'checking', 'savings', 'deposit'],
                'account_types': ['Bank', 'Current Assets'], 
                'codes': ['1002', '1020', '1200']
            },
            'sales': {
                'keywords': ['sales', 'revenue', 'income'],
                'account_types': ['Revenue', 'Income'],
                'codes': ['4001', '4000', '4100']
            },
            'expense': {
                'keywords': ['expense', 'cost', 'payment'],
                'account_types': ['Expense', 'Operating Expenses'],
                'codes': ['5', '6', '7']  # Account codes starting with these
            }
        }
    
    def find_matches(self, query: str, min_confidence: float = 0.4) -> List[AccountMatch]:
        """Find account matches for a query string - now using REAL data instead of mock data"""
        if not query or len(query.strip()) < 2:
            return []
        
        query = query.strip().lower()
        accounts = self._get_accounts()
        
        if not accounts:
            return []
        
        matches = []
        
        # 1. Exact name matches (highest priority)
        for account in accounts:
            if account['name'].lower() == query:
                matches.append(AccountMatch(
                    account['id'], account['name'], account['code'],
                    1.0, 'exact'
                ))
        
        # 2. Exact code matches
        for account in accounts:
            if account['code'].lower() == query:
                matches.append(AccountMatch(
                    account['id'], account['name'], account['code'],
                    0.95, 'exact'
                ))
        
        # 3. Fuzzy name matches
        for account in accounts:
            similarity = self._calculate_similarity(query, account['name'].lower())
            if similarity >= min_confidence:
                matches.append(AccountMatch(
                    account['id'], account['name'], account['code'],
                    similarity, 'fuzzy'
                ))
        
        # 4. Partial matches
        for account in accounts:
            if self._is_partial_match(query, account['name'].lower()):
                confidence = min(0.8, len(query) / len(account['name'].lower()))
                matches.append(AccountMatch(
                    account['id'], account['name'], account['code'],
                    confidence, 'partial'
                ))
        
        # 5. Contextual matches (based on account type patterns)
        contextual_matches = self._find_contextual_matches(query, accounts)
        matches.extend(contextual_matches)
        
        # Remove duplicates and sort by confidence (BEST match first)
        unique_matches = {}
        for match in matches:
            key = match.account_id
            if key not in unique_matches or match.confidence > unique_matches[key].confidence:
                unique_matches[key] = match
        
        sorted_matches = sorted(unique_matches.values(), 
                              key=lambda x: x.confidence, reverse=True)
        
        # Debug output for transparency
        if sorted_matches:
            print(f"🔍 Account matching results for '{query}' (using REAL accounts):")
            for i, match in enumerate(sorted_matches[:5]):  # Show top 5
                print(f"  {i+1}. {match.account_name} (confidence: {match.confidence:.3f}, type: {match.match_type})")
        
        return sorted_matches[:10]  # Top 10 matches
    
    def find_best_match(self, query: str, min_confidence: float = 0.6) -> Optional[AccountMatch]:
        """Find the single best match for a query"""
        matches = self.find_matches(query, min_confidence)
        if matches and matches[0].confidence >= min_confidence:
            return matches[0]
        return None
    
    def _get_accounts(self) -> List[Dict]:
        """Get all accounts from the accounting system using the same method as CSV import"""
        if not self.accounting_system:
            print("⚠️ No accounting system provided to AIAccountResolver, using mock data")
            return self._get_mock_accounts()
        
        try:
            # Use the same logic as load_accounts_from_system for consistency
            if hasattr(self.accounting_system, 'get_chart_of_accounts'):
                accounts_data = self.accounting_system.get_chart_of_accounts(active_only=True)
                formatted_accounts = []
                
                if accounts_data and len(accounts_data) > 0:
                    for account in accounts_data:
                        if isinstance(account, dict):
                            # Dict format - convert to our format
                            formatted_accounts.append({
                                'id': str(account.get('id', '')),
                                'name': account.get('name', ''),
                                'code': account.get('code', ''),
                                'type': account.get('account_type', account.get('type', '')),
                                'parent_id': str(account.get('parent_id', ''))
                            })
                        elif isinstance(account, tuple) and len(account) >= 3:
                            # Tuple format: (name, type, code, parent_code, level, is_postable, description)
                            name, acc_type, code = account[0], account[1], account[2]
                            formatted_accounts.append({
                                'id': code or str(len(formatted_accounts)),  # Use code as ID or fallback
                                'name': name,
                                'code': code,
                                'type': acc_type,
                                'parent_id': account[3] if len(account) > 3 else ''
                            })
                
                if formatted_accounts:
                    print(f"✅ AIAccountResolver loaded {len(formatted_accounts)} real accounts from system")
                    return formatted_accounts
                    
            print("⚠️ No accounts found in system, using mock data")
            return self._get_mock_accounts()
            
        except Exception as e:
            print(f"❌ Error getting real accounts from system: {e}")
            print("   Falling back to mock data")
            return self._get_mock_accounts()
    
    def _get_mock_accounts(self) -> List[Dict]:
        """Mock accounts for testing when no accounting system is available"""
        return [
            {'id': '1001', 'name': 'Cash in Hand', 'code': '1001', 'type': 'Current Assets'},
            {'id': '1002', 'name': 'Cash at Bank - Checking', 'code': '1002', 'type': 'Current Assets'},
            {'id': '1003', 'name': 'Cash at Bank - Savings', 'code': '1003', 'type': 'Current Assets'},
            {'id': '1201', 'name': 'Accounts Receivable', 'code': '1201', 'type': 'Current Assets'},
            {'id': '2001', 'name': 'Accounts Payable', 'code': '2001', 'type': 'Current Liabilities'},
            {'id': '4001', 'name': 'Sales Revenue', 'code': '4001', 'type': 'Revenue'},
            {'id': '4002', 'name': 'Sales - Cash', 'code': '4002', 'type': 'Revenue'},
            {'id': '4003', 'name': 'Sales - Credit', 'code': '4003', 'type': 'Revenue'},
            {'id': '5001', 'name': 'Office Supplies Expense', 'code': '5001', 'type': 'Operating Expenses'},
            {'id': '5002', 'name': 'Rent Expense', 'code': '5002', 'type': 'Operating Expenses'},
        ]
    
    def _calculate_similarity(self, query: str, account_name: str) -> float:
        """Calculate similarity between query and account name"""
        # Use SequenceMatcher for basic similarity
        similarity = SequenceMatcher(None, query, account_name).ratio()
        
        # Boost similarity for word matches
        query_words = set(query.split())
        account_words = set(account_name.split())
        
        # Check for word overlaps
        common_words = query_words.intersection(account_words)
        if common_words:
            word_boost = len(common_words) / max(len(query_words), len(account_words))
            similarity = min(1.0, similarity + word_boost * 0.3)
        
        return similarity
    
    def _is_partial_match(self, query: str, account_name: str) -> bool:
        """Check if query is a partial match within account name"""
        # Check if query is contained in account name
        if query in account_name:
            return True
        
        # Check if all words in query appear in account name
        query_words = query.split()
        account_words = account_name.lower().split()
        
        for word in query_words:
            if not any(word in account_word for account_word in account_words):
                return False
        
        return len(query_words) > 0
    
    def _find_contextual_matches(self, query: str, accounts: List[Dict]) -> List[AccountMatch]:
        """Find matches based on context patterns"""
        matches = []
        
        for pattern_name, pattern_info in self.account_patterns.items():
            if any(keyword in query for keyword in pattern_info['keywords']):
                # Find accounts matching this pattern
                for account in accounts:
                    confidence = 0.0
                    
                    # Check account type match
                    if account['type'] in pattern_info['account_types']:
                        confidence += 0.4
                    
                    # Check code pattern match
                    account_code = account['code']
                    for code_pattern in pattern_info['codes']:
                        if account_code.startswith(code_pattern):
                            confidence += 0.3
                            break
                    
                    # Check name keyword match
                    account_name_lower = account['name'].lower()
                    for keyword in pattern_info['keywords']:
                        if keyword in account_name_lower:
                            confidence += 0.2
                            break
                    
                    if confidence >= 0.4:
                        matches.append(AccountMatch(
                            account['id'], account['name'], account['code'],
                            confidence, 'contextual'
                        ))
        
        return matches
    
    def suggest_accounts(self, partial_query: str, limit: int = 5) -> List[AccountMatch]:
        """Suggest accounts as user types (for autocomplete)"""
        if len(partial_query) < 2:
            return []
        
        matches = self.find_matches(partial_query, min_confidence=0.3)
        return matches[:limit]
    
    def get_account_by_id(self, account_id: str) -> Optional[Dict]:
        """Get account details by ID"""
        accounts = self._get_accounts()
        for account in accounts:
            if account['id'] == account_id:
                return account
        return None
    
    def get_account_by_name(self, account_name: str) -> Optional[Dict]:
        """Get account details by exact name match"""
        accounts = self._get_accounts()
        for account in accounts:
            if account['name'].lower() == account_name.lower():
                return account
        return None 