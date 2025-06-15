"""
Account matching utility for intelligent CSV import functionality.
This module provides smart matching of imported account names to the chart of accounts.
"""

import re
from difflib import SequenceMatcher
from typing import List, Tuple, Optional, Dict


class AccountMatcher:
    """Smart account matching for CSV imports."""
    
    def __init__(self, chart_of_accounts: List[str]):
        """
        Initialize with the chart of accounts.
        
        Args:
            chart_of_accounts: List of account strings in format "Code - Name"
        """
        self.chart_of_accounts = chart_of_accounts
        self._build_matching_maps()
    
    def _build_matching_maps(self):
        """Build various maps for efficient matching."""
        self.account_map = {}  # Full account string -> account
        self.code_map = {}     # Account code -> account  
        self.name_map = {}     # Account name -> account
        self.keyword_map = {}  # Keywords -> account
        
        for account in self.chart_of_accounts:
            # Parse account format "Code - Name"
            if " - " in account:
                code, name = account.split(" - ", 1)
                self.account_map[account.lower()] = account
                self.code_map[code.lower()] = account
                self.name_map[name.lower()] = account
                
                # Build keyword map for fuzzy matching
                keywords = self._extract_keywords(name)
                for keyword in keywords:
                    if keyword not in self.keyword_map:
                        self.keyword_map[keyword] = []
                    self.keyword_map[keyword].append(account)
            else:
                # Handle accounts without standard format
                self.account_map[account.lower()] = account
                keywords = self._extract_keywords(account)
                for keyword in keywords:
                    if keyword not in self.keyword_map:
                        self.keyword_map[keyword] = []
                    self.keyword_map[keyword].append(account)
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract meaningful keywords from account names."""
        # Clean and split text
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        words = text.split()
        
        # Filter out common words and short words
        stop_words = {'and', 'or', 'the', 'a', 'an', 'of', 'for', 'in', 'on', 'at', 'to', 'from'}
        keywords = [word for word in words if len(word) > 2 and word not in stop_words]
        
        return keywords
    
    def match_account(self, input_text: str, confidence_threshold: float = 0.6) -> Tuple[Optional[str], float]:
        """
        Match input text to the best account in chart of accounts.
        
        Args:
            input_text: The account name/description to match
            confidence_threshold: Minimum confidence score to accept a match
            
        Returns:
            Tuple of (matched_account, confidence_score) or (None, 0) if no good match
        """
        if not input_text or not input_text.strip():
            return None, 0.0
        
        input_clean = input_text.strip().lower()
        
        # 1. Exact match (highest priority)
        if input_clean in self.account_map:
            return self.account_map[input_clean], 1.0
        
        # 2. Code match
        if input_clean in self.code_map:
            return self.code_map[input_clean], 1.0
        
        # 3. Name match  
        if input_clean in self.name_map:
            return self.name_map[input_clean], 1.0
        
        # 4. Partial/fuzzy matching
        best_match = None
        best_score = 0.0
        
        # Check all accounts for similarity
        for account in self.chart_of_accounts:
            score = self._calculate_similarity(input_clean, account)
            if score > best_score and score >= confidence_threshold:
                best_score = score
                best_match = account
        
        return best_match, best_score
    
    def _calculate_similarity(self, input_text: str, account: str) -> float:
        """Calculate similarity score between input and account."""
        account_lower = account.lower()
        
        # Extract account name from "Code - Name" format
        account_name = account_lower
        if " - " in account_lower:
            _, account_name = account_lower.split(" - ", 1)
        
        # 1. Direct substring match
        if input_text in account_lower or input_text in account_name:
            return 0.8
        if account_name in input_text:
            return 0.75
        
        # 2. Keyword matching
        input_keywords = set(self._extract_keywords(input_text))
        account_keywords = set(self._extract_keywords(account_name))
        
        if input_keywords and account_keywords:
            keyword_overlap = len(input_keywords & account_keywords)
            keyword_score = keyword_overlap / max(len(input_keywords), len(account_keywords))
            if keyword_score > 0:
                return min(0.7, keyword_score + 0.2)
        
        # 3. Sequence similarity
        seq_score = SequenceMatcher(None, input_text, account_name).ratio()
        if seq_score > 0.6:
            return min(0.6, seq_score)
        
        return 0.0
    
    def get_suggestions(self, input_text: str, max_suggestions: int = 5) -> List[Tuple[str, float]]:
        """
        Get multiple account suggestions for input text.
        
        Args:
            input_text: The account name/description to match
            max_suggestions: Maximum number of suggestions to return
            
        Returns:
            List of (account, confidence_score) tuples, sorted by confidence
        """
        if not input_text or not input_text.strip():
            return []
        
        suggestions = []
        input_clean = input_text.strip().lower()
        
        # Get similarity scores for all accounts
        for account in self.chart_of_accounts:
            score = self._calculate_similarity(input_clean, account)
            if score > 0.3:  # Lower threshold for suggestions
                suggestions.append((account, score))
        
        # Sort by score (descending) and return top suggestions
        suggestions.sort(key=lambda x: x[1], reverse=True)
        return suggestions[:max_suggestions]
    
    def create_mapping_report(self, imported_accounts: List[str]) -> Dict[str, Dict]:
        """
        Create a detailed mapping report for imported accounts.
        
        Args:
            imported_accounts: List of account names from imported data
            
        Returns:
            Dictionary with mapping results and statistics
        """
        report = {
            'mappings': {},
            'unmapped': [],
            'statistics': {
                'total_accounts': len(imported_accounts),
                'mapped_accounts': 0,
                'unmapped_accounts': 0,
                'high_confidence': 0,  # > 0.8
                'medium_confidence': 0,  # 0.6-0.8
                'low_confidence': 0    # < 0.6
            }
        }
        
        for imported_account in set(imported_accounts):  # Remove duplicates
            if not imported_account.strip():
                continue
                
            matched_account, confidence = self.match_account(imported_account)
            
            if matched_account:
                report['mappings'][imported_account] = {
                    'matched_account': matched_account,
                    'confidence': confidence,
                    'suggestions': self.get_suggestions(imported_account, 3)
                }
                report['statistics']['mapped_accounts'] += 1
                
                if confidence > 0.8:
                    report['statistics']['high_confidence'] += 1
                elif confidence >= 0.6:
                    report['statistics']['medium_confidence'] += 1
                else:
                    report['statistics']['low_confidence'] += 1
            else:
                report['unmapped'].append(imported_account)
                report['statistics']['unmapped_accounts'] += 1
        
        return report


def create_common_account_aliases() -> Dict[str, List[str]]:
    """Create a dictionary of common account name variations and aliases."""
    return {
        'cash': ['cash', 'cash on hand', 'petty cash', 'cash account', 'money'],
        'bank': ['bank', 'checking', 'savings', 'bank account', 'checking account'],
        'accounts_receivable': ['ar', 'a/r', 'accounts receivable', 'receivables', 'customer receivables'],
        'accounts_payable': ['ap', 'a/p', 'accounts payable', 'payables', 'vendor payables'],
        'inventory': ['inventory', 'stock', 'merchandise', 'goods'],
        'equipment': ['equipment', 'machinery', 'tools', 'furniture', 'fixtures'],
        'sales': ['sales', 'revenue', 'income', 'sales revenue', 'service revenue'],
        'expenses': ['expense', 'expenses', 'cost', 'costs'],
        'rent': ['rent', 'rental', 'lease'],
        'utilities': ['utilities', 'electric', 'electricity', 'gas', 'water', 'phone', 'internet'],
        'supplies': ['supplies', 'office supplies', 'materials'],
        'insurance': ['insurance', 'coverage'],
        'depreciation': ['depreciation', 'amortization'],
        'interest': ['interest', 'interest expense', 'interest income'],
        'taxes': ['tax', 'taxes', 'income tax', 'sales tax'],
        'wages': ['wages', 'salary', 'payroll', 'compensation'],
        'marketing': ['marketing', 'advertising', 'promotion'],
        'travel': ['travel', 'transportation', 'mileage'],
        'professional': ['professional', 'legal', 'consulting', 'accounting']
    }
