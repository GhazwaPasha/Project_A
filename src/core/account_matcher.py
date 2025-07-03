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
    """Create a comprehensive dictionary of common account name variations and aliases."""
    return {
        # Cash and Banking
        'cash': ['cash', 'cash on hand', 'petty cash', 'cash account', 'money', 'till', 'register'],
        'bank': ['bank', 'checking', 'savings', 'bank account', 'checking account', 'chequing', 'current account'],
        'credit_card': ['credit card', 'visa', 'mastercard', 'amex', 'american express', 'cc', 'corporate card'],
        
        # Receivables
        'accounts_receivable': ['ar', 'a/r', 'accounts receivable', 'receivables', 'customer receivables', 'trade receivables', 'debtors'],
        'notes_receivable': ['notes receivable', 'promissory notes', 'loans receivable'],
        
        # Payables  
        'accounts_payable': ['ap', 'a/p', 'accounts payable', 'payables', 'vendor payables', 'trade payables', 'creditors'],
        'notes_payable': ['notes payable', 'loans payable', 'bank loan', 'term loan'],
        'accrued_expenses': ['accrued expenses', 'accruals', 'accrued liabilities', 'outstanding expenses'],
        
        # Inventory and Assets
        'inventory': ['inventory', 'stock', 'merchandise', 'goods', 'raw materials', 'finished goods', 'wip', 'work in progress'],
        'equipment': ['equipment', 'machinery', 'tools', 'furniture', 'fixtures', 'computer equipment', 'office equipment'],
        'buildings': ['building', 'buildings', 'real estate', 'property', 'land and buildings'],
        'vehicles': ['vehicle', 'vehicles', 'auto', 'automobile', 'truck', 'car', 'fleet'],
        'prepaid_expenses': ['prepaid', 'prepaid expenses', 'prepayments', 'deferred expenses'],
        
        # Revenue and Income (KEY ENHANCEMENT)
        'sales': ['sales', 'revenue', 'income', 'sales revenue', 'service revenue', 'gross sales', 'net sales', 'turnover'],
        'service_revenue': ['service revenue', 'services', 'consulting revenue', 'professional services', 'fees earned'],
        'interest_income': ['interest income', 'interest revenue', 'bank interest', 'investment income'],
        'other_income': ['other income', 'miscellaneous income', 'gain on sale', 'rental income'],
        
        # Cost of Goods Sold
        'cogs': ['cogs', 'cost of goods sold', 'cost of sales', 'direct costs', 'cost of revenue'],
        'materials': ['materials', 'raw materials', 'direct materials', 'supplies used'],
        'labor': ['labor', 'direct labor', 'wages', 'manufacturing wages'],
        
        # Operating Expenses
        'wages': ['wages', 'salary', 'salaries', 'payroll', 'compensation', 'employee costs', 'staff costs'],
        'benefits': ['benefits', 'employee benefits', 'health insurance', 'retirement', '401k', 'pension'],
        'rent': ['rent', 'rental', 'lease', 'rental expense', 'office rent'],
        'utilities': ['utilities', 'electric', 'electricity', 'gas', 'water', 'phone', 'internet', 'telephone', 'hydro'],
        'supplies': ['supplies', 'office supplies', 'materials', 'stationery', 'consumables'],
        'insurance': ['insurance', 'coverage', 'liability insurance', 'property insurance', 'general insurance'],
        'depreciation': ['depreciation', 'amortization', 'depletion', 'depreciation expense'],
        'repairs': ['repairs', 'maintenance', 'repairs and maintenance', 'upkeep', 'servicing'],
        
        # Professional Services
        'professional': ['professional', 'legal', 'consulting', 'accounting', 'audit', 'tax preparation', 'attorney'],
        'accounting': ['accounting', 'bookkeeping', 'cpa', 'tax prep', 'audit fees'],
        'legal': ['legal', 'attorney', 'lawyer', 'legal fees', 'litigation'],
        
        # Marketing and Sales
        'marketing': ['marketing', 'advertising', 'promotion', 'ads', 'promotional', 'marketing expense'],
        'advertising': ['advertising', 'ads', 'google ads', 'facebook ads', 'online advertising'],
        
        # Travel and Transportation
        'travel': ['travel', 'transportation', 'mileage', 'travel expense', 'airfare', 'hotels', 'meals'],
        'vehicle_expense': ['vehicle expense', 'auto expense', 'fuel', 'gas', 'gasoline', 'car expense'],
        
        # Financial
        'interest_expense': ['interest', 'interest expense', 'loan interest', 'mortgage interest', 'finance charges'],
        'bank_charges': ['bank charges', 'bank fees', 'service charges', 'transaction fees'],
        
        # Taxes
        'taxes': ['tax', 'taxes', 'income tax', 'sales tax', 'property tax', 'payroll tax', 'gst', 'hst', 'vat'],
        'payroll_tax': ['payroll tax', 'employment tax', 'social security', 'medicare', 'unemployment tax'],
        
        # Office and Administrative
        'office_expense': ['office expense', 'office', 'administrative', 'general expense'],
        'communications': ['communications', 'phone', 'internet', 'cell phone', 'mobile', 'telecommunications'],
        'software': ['software', 'subscriptions', 'saas', 'licenses', 'technology'],
        
        # Equity
        'equity': ['equity', 'owner equity', 'retained earnings', 'capital', 'shareholders equity'],
        'capital': ['capital', 'owner capital', 'paid in capital', 'share capital'],
        'drawings': ['drawings', 'withdrawals', 'owner withdrawals', 'distributions'],
        
        # Common Abbreviations and Variations
        'misc': ['misc', 'miscellaneous', 'other', 'sundry', 'general'],
        'admin': ['admin', 'administration', 'administrative', 'overhead']
    }


class EnhancedAccountMatcher(AccountMatcher):
    """Enhanced account matcher with semantic understanding and alias mapping."""
    
    def __init__(self, chart_of_accounts: List[str]):
        """Initialize with enhanced semantic matching capabilities."""
        super().__init__(chart_of_accounts)
        self.aliases = create_common_account_aliases()
        self._build_semantic_maps()
    
    def _build_semantic_maps(self):
        """Build semantic mapping for better account matching (optimized)."""
        self.semantic_map = {}  # Concept -> list of related accounts
        self.alias_to_concept = {}  # Alias -> concept

        # 1. Create a reverse map from alias to its semantic concept
        for concept, aliases in self.aliases.items():
            for alias in aliases:
                self.alias_to_concept[alias.lower()] = concept

        # 2. Create a map of concepts to related accounts in a single pass
        for account in self.chart_of_accounts:
            account_lower = account.lower()
            account_name = account_lower.split(" - ", 1)[-1]
            
            # Use a set to avoid duplicate concepts for a single account
            matched_concepts = set()

            # Check against all aliases to find matching concepts
            for alias, concept in self.alias_to_concept.items():
                if alias in account_name:
                    matched_concepts.add(concept)
            
            # Add account to all matched concepts
            for concept in matched_concepts:
                if concept not in self.semantic_map:
                    self.semantic_map[concept] = []
                self.semantic_map[concept].append(account)

    def match_account(self, input_text: str, confidence_threshold: float = 0.6) -> Tuple[Optional[str], float]:
        """Enhanced matching with semantic understanding."""
        if not input_text or not input_text.strip():
            return None, 0.0
        
        input_clean = input_text.strip().lower()
        
        # 1. Try parent class matching first (exact matches)
        matched_account, confidence = super().match_account(input_text, confidence_threshold)
        if matched_account and confidence >= 0.95:  # Trust very high confidence matches
            return matched_account, confidence
        
        # 2. Semantic/alias matching (now finds the best match)
        semantic_match, semantic_confidence = self._semantic_match(input_clean)
        
        # 3. Enhanced fuzzy matching for known concepts
        enhanced_match, enhanced_confidence = self._enhanced_fuzzy_match(input_clean)

        # Compare all potential matches and return the best one
        best_match = matched_account
        best_confidence = confidence

        if semantic_confidence > best_confidence:
            best_match = semantic_match
            best_confidence = semantic_confidence

        if enhanced_confidence > best_confidence:
            best_match = enhanced_match
            best_confidence = enhanced_confidence
            
        if best_confidence >= confidence_threshold:
            return best_match, best_confidence
        
        return None, 0.0

    def _semantic_match(self, input_text: str) -> Tuple[Optional[str], float]:
        """Match using semantic aliases, finding the best candidate."""
        input_words = set(self._extract_keywords(input_text))
        
        best_match = None
        best_score = 0.0
        
        # Find all candidate accounts from relevant semantic concepts
        candidate_accounts = set()
        for word in input_words:
            if word in self.alias_to_concept:
                concept = self.alias_to_concept[word]
                if concept in self.semantic_map:
                    candidate_accounts.update(self.semantic_map[concept])

        if not candidate_accounts:
            # Fallback for direct alias text match
            if input_text in self.alias_to_concept:
                concept = self.alias_to_concept[input_text]
                if concept in self.semantic_map:
                    candidate_accounts.update(self.semantic_map[concept])

        # Score each candidate to find the best one
        for account in candidate_accounts:
            # Use the base similarity calculator for a consistent score
            score = self._calculate_similarity(input_text, account)
            
            # Boost score for being a semantic match
            semantic_boost = 0.15
            final_score = min(0.9, score + semantic_boost)

            if final_score > best_score:
                best_score = final_score
                best_match = account
                
        return best_match, best_score
    
    def _enhanced_fuzzy_match(self, input_text: str) -> Tuple[Optional[str], float]:
        """Enhanced fuzzy matching for known accounting concepts."""
        # Look for key accounting terms and boost their matching
        accounting_term_boosts = {
            'sales': ['revenue', 'income'],
            'revenue': ['sales', 'income'], 
            'income': ['sales', 'revenue'],
            'expense': ['cost', 'expense'],
            'cost': ['expense'],
            'receivable': ['ar', 'debtor'],
            'payable': ['ap', 'creditor'],
            'cash': ['bank', 'money'],
            'bank': ['cash', 'checking'],
            'equipment': ['asset', 'machinery'],
            'depreciation': ['amortization'],
            'interest': ['finance'],
            'wage': ['salary', 'payroll'],
            'salary': ['wage', 'payroll'],
            'rent': ['lease'],
            'lease': ['rent'],
            'insurance': ['coverage'],
            'supply': ['material'],
            'material': ['supply']
        }
        
        best_match = None
        best_score = 0.0
        
        for account in self.chart_of_accounts:
            account_lower = account.lower()
            account_name = account_lower
            if " - " in account_lower:
                _, account_name = account_lower.split(" - ", 1)
            
            # Calculate base similarity
            base_score = self._calculate_similarity(input_text, account)
            
            # Apply boosts for related terms
            boost_score = 0.0
            input_words = input_text.split()
            account_words = account_name.split()
            
            for input_word in input_words:
                if input_word in accounting_term_boosts:
                    related_terms = accounting_term_boosts[input_word]
                    for account_word in account_words:
                        if any(term in account_word for term in related_terms):
                            boost_score = 0.2  # 20% boost for related terms
                            break
            
            final_score = min(0.9, base_score + boost_score)
            
            if final_score > best_score:
                best_score = final_score
                best_match = account
        
        return best_match, best_score
    
    def get_semantic_suggestions(self, input_text: str, max_suggestions: int = 5) -> List[Tuple[str, float, str]]:
        """Get suggestions with semantic reasoning explanations."""
        suggestions = []
        input_clean = input_text.strip().lower()
        
        # Get regular suggestions first
        regular_suggestions = self.get_suggestions(input_text, max_suggestions * 2)
        
        # Add semantic context
        for account, score in regular_suggestions:
            reason = "Similar name"
            
            # Check if this was a semantic match
            for alias, mapped_accounts in self.semantic_map.items():
                if account in mapped_accounts:
                    for alias_word in alias.split():
                        if alias_word in input_clean:
                            reason = f"Semantic match: '{input_text}' relates to '{alias}'"
                            score = min(1.0, score + 0.1)  # Small boost for semantic matches
                            break
            
            suggestions.append((account, score, reason))
        
        # Sort by score and return top suggestions
        suggestions.sort(key=lambda x: x[1], reverse=True)
        return suggestions[:max_suggestions]
