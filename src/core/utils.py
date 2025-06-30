"""
utils.py - Shared utilities for AI Accountant
"""
import os
import requests
import logging
from datetime import datetime

# --- Logging Setup ---
logging.basicConfig(
    filename='accounting_app.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)

def get_current_currency_symbol():
    """Get the current currency symbol from the main window."""
    try:
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        if app:
            for widget in app.topLevelWidgets():
                if hasattr(widget, 'get_currency_symbol'):
                    return widget.get_currency_symbol()
    except Exception:
        pass
    return '$'  # fallback

def format_currency(amount, symbol=None):
    """Format currency amount with proper formatting."""
    if symbol is None:
        symbol = get_current_currency_symbol()
        
    if amount == 0:
        return f"{symbol}0.00" if symbol not in ["Rs", "₹", "ر.س", "د.إ", "د.ك", "ر.ق"] else f"{symbol} 0.00"
    
    # Handle different currency symbol positions
    if symbol in ["Rs", "₹", "ر.س", "د.إ", "د.ك", "ر.ق"]:
        # These currencies typically go before the amount with a space
        return f"{symbol} {amount:,.2f}"
    else:
        # Standard currencies like $, €, £, ¥, etc.
        return f"{symbol}{amount:,.2f}"

def get_mistral_api_key():
    key = os.environ.get('MISTRAL_API_KEY')
    if not key:
        logging.error('MISTRAL_API_KEY not set in environment.')
        raise EnvironmentError('MISTRAL_API_KEY not set in environment.')
    return key

MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"

def get_smart_account_suggestions(system, nl_input):
    """
    Get intelligent account suggestions based on hierarchical structure and context.
    Returns only leaf accounts (accounts with no children) - the actual usable accounts for journal entries.
    Excludes parent accounts and intermediate accounts like 'Cash & Cash Equivalents'.
    """
    all_accounts = system.get_all_accounts()
    
    # Find all account codes that are parents (have children)
    parent_codes = set()
    for name, acc_type, code, parent_code, level, is_postable, description in all_accounts:
        if parent_code:
            parent_codes.add(parent_code)
      # Only use leaf accounts (accounts that are not parents to other accounts)
    leaf_accounts = []
    
    for name, acc_type, code, parent_code, level, is_postable, description in all_accounts:
        # Include only accounts that don't have children (leaf accounts)
        if code not in parent_codes:
            leaf_accounts.append((name, acc_type, code, parent_code, level, is_postable, description))
    
    # Keywords that suggest specific leaf accounts (updated for our chart of accounts)
    specific_keywords = {
        'bank': ['bank', 'check', 'cheque', 'online banking', 'wire transfer', 'eft', 'transfer'],
        'hand': ['hand', 'cash in hand', 'petty cash', 'cash on hand', 'cash'],
        'pos': ['pos', 'point of sale', 'credit card', 'card payment', 'card'],
        'food': ['food', 'meal', 'restaurant', 'kitchen'],
        'beverage': ['beverage', 'drink', 'coffee', 'tea', 'soda', 'juice'],
        'meat': ['meat', 'beef', 'chicken', 'pork', 'lamb'],
        'dairy': ['dairy', 'milk', 'cheese', 'yogurt', 'butter'],
        'vegetables': ['vegetable', 'veggie', 'carrot', 'lettuce', 'tomato'],
        'dry goods': ['dry goods', 'rice', 'flour', 'pasta', 'cereal'],
        'loan': ['loan', 'bank loan', 'mortgage', 'credit']
    }
    
    nl_lower = nl_input.lower()
    suggested_accounts = []
    
    # Always include the most commonly used leaf accounts
    priority_leaf_accounts = ['Cash in Hand', 'Cash at Bank', 'Cash at POS', 'Sales', 'Rent', 'Utilities', 'Equipment', 'Insurance']
    
    # Check for specific sub-account keywords and prioritize matching accounts
    specific_match_found = False
    for category, keywords in specific_keywords.items():
        for keyword in keywords:
            if keyword in nl_lower:
                # Look for matching leaf accounts and prioritize them
                for name, acc_type, code, parent_code, level, is_postable, description in leaf_accounts:
                    if any(k in name.lower() for k in keywords):
                        if name not in suggested_accounts:
                            suggested_accounts.append(name)
                        specific_match_found = True
    
    # Add priority leaf accounts
    for name in priority_leaf_accounts:
        if name not in suggested_accounts:
            # Check if this account exists in our chart
            for acc_name, acc_type, acc_code, parent_code, level, is_postable, description in leaf_accounts:
                if acc_name == name:
                    suggested_accounts.append(name)
                    break
    
    # Add expense leaf accounts for common business operations
    expense_keywords = ['paid', 'purchase', 'bought', 'expense', 'cost']
    if any(keyword in nl_lower for keyword in expense_keywords):
        expense_leaf_accounts = [name for name, acc_type, code, parent_code, level, is_postable, description in leaf_accounts if acc_type == 'Expense']
        for acc_name in expense_leaf_accounts[:10]:  # Limit to top 10 expense leaf accounts
            if acc_name not in suggested_accounts:
                suggested_accounts.append(acc_name)
    
    # Add revenue leaf accounts for income operations
    income_keywords = ['received', 'income', 'revenue', 'sales', 'earned']
    if any(keyword in nl_lower for keyword in income_keywords):
        revenue_leaf_accounts = [name for name, acc_type, code, parent_code, level, is_postable, description in leaf_accounts if acc_type == 'Revenue']
        for acc_name in revenue_leaf_accounts[:5]:  # Limit to top 5 revenue leaf accounts
            if acc_name not in suggested_accounts:
                suggested_accounts.append(acc_name)
    
    # Add asset leaf accounts for asset-related operations
    asset_keywords = ['bought', 'purchase', 'acquire', 'asset', 'equipment', 'inventory']
    if any(keyword in nl_lower for keyword in asset_keywords):
        asset_leaf_accounts = [name for name, acc_type, code, parent_code, level, is_postable, description in leaf_accounts if acc_type == 'Asset']
        for acc_name in asset_leaf_accounts[:8]:  # Limit to top 8 asset leaf accounts
            if acc_name not in suggested_accounts:
                suggested_accounts.append(acc_name)
    
    # If we haven't found many accounts yet, add more common leaf accounts as fallback
    if len(suggested_accounts) < 15:
        # Add remaining commonly used leaf accounts
        common_leafs = ['Accounts Receivable', 'Accounts Payable', 'Salaries & Wages', 'Marketing', 'Depreciation']
        for name in common_leafs:
            if name not in suggested_accounts:
                for acc_name, acc_type, acc_code, parent_code, level, is_postable, description in leaf_accounts:
                    if acc_name == name:
                        suggested_accounts.append(name)
                        break
        
        # Add any remaining leaf accounts if still needed
        for name, acc_type, code, parent_code, level, is_postable, description in leaf_accounts:
            if name not in suggested_accounts and len(suggested_accounts) < 20:
                suggested_accounts.append(name)
    
    # Limit to reasonable number of suggestions (typically 15-25 leaf accounts)
    return suggested_accounts[:25]


def parse_transaction(nl_input, valid_accounts=None, system=None):
    """
    Uses Mistral AI API to parse a natural language transaction into structured data.
    Relies purely on the LLM's accounting knowledge and reasoning capabilities.
    """
    prompt = f"""
You are an expert accountant. Create a proper double-entry journal entry following STRICT accounting rules.

Transaction Description: "{nl_input}"

Available Accounts: {valid_accounts if valid_accounts else 'Use standard accounting account names'}

🚨 CRITICAL ACCOUNTING RULES (NEVER VIOLATE THESE):

| Account Type    | Normal Balance | To INCREASE | To DECREASE |
| --------------- | -------------- | ----------- | ----------- |
| **Assets**      | DEBIT          | DEBIT       | CREDIT      |
| **Liabilities** | CREDIT         | CREDIT      | DEBIT       |
| **Equity**      | CREDIT         | CREDIT      | DEBIT       |
| **Revenue**     | CREDIT         | CREDIT      | DEBIT       |
| **Expenses**    | DEBIT          | DEBIT       | CREDIT      |

🔥 TRANSACTION PATTERNS (MANDATORY RULES - NO EXCEPTIONS):

1. **EXPENSE PAYMENTS** (rent, utilities, salaries, supplies, etc.):
   ✅ CORRECT: DEBIT Expense Account + CREDIT Cash/Bank Account
   ❌ NEVER: CREDIT an expense account when paying for it
   Example: "Paid rent $1000" → DEBIT: Rent Expense, CREDIT: Cash at Bank

2. **REVENUE RECEIPTS** (sales, service income, interest earned):
   ✅ CORRECT: DEBIT Cash/Bank Account + CREDIT Revenue Account
   ❌ NEVER: DEBIT a revenue account when receiving money
   Example: "Received sales $500" → DEBIT: Cash in Hand, CREDIT: Sales Revenue

3. **ASSET PURCHASES** (equipment, inventory, supplies):
   ✅ CORRECT: DEBIT New Asset + CREDIT Cash/Bank
   Example: "Bought equipment $2000" → DEBIT: Equipment, CREDIT: Cash at Bank

4. **DEBT PAYMENTS** (loan payments, paying creditors):
   ✅ CORRECT: DEBIT Liability Account + CREDIT Cash/Bank
   Example: "Paid loan $1000" → DEBIT: Bank Loans, CREDIT: Cash at Bank

5. **CASH RECEIPTS FROM CUSTOMERS**:
   ✅ CORRECT: DEBIT Cash/Bank + CREDIT Revenue or Accounts Receivable
   
6. **CASH PAYMENTS TO SUPPLIERS**:
   ✅ CORRECT: DEBIT Expense or Asset + CREDIT Cash/Bank

⚠️ VALIDATION CHECKS:
- Expense accounts (Rent, Utilities, Salaries, etc.) = ALWAYS DEBIT when incurring the expense
- Revenue accounts (Sales, Service Revenue, etc.) = ALWAYS CREDIT when earning income
- Cash/Bank accounts = DEBIT when receiving money, CREDIT when paying money

STEP-BY-STEP PROCESS:
1. Identify: What type of transaction is this? (expense payment, revenue receipt, asset purchase, etc.)
2. Find the pattern: Match to one of the mandatory patterns above
3. Apply the rule: Use the exact DEBIT/CREDIT combination from the pattern
4. Verify: Check that expenses are debited and revenues are credited

JSON RESPONSE FORMAT:
{{
    "date": "YYYY-MM-DD" (ONLY if a specific date is mentioned in the input, otherwise leave empty or null),
    "description": "Clear description of the transaction",
    "debit_account": "Account to be debited",
    "credit_account": "Account to be credited", 
    "amount": number (without currency symbols)
}}

⛔ CRITICAL: If this is an expense payment, the expense account MUST be debited, never credited.
⛔ CRITICAL: If this is revenue receipt, the revenue account MUST be credited, never debited.

Respond with ONLY the JSON object, no explanations.
"""
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {get_mistral_api_key()}"
    }
    data = {
        "model": "mistral-tiny",
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    
    try:
        response = requests.post(MISTRAL_API_URL, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        
        import json as pyjson
        content = result['choices'][0]['message']['content']
        
        # Extract JSON from response
        start = content.find('{')
        end = content.rfind('}') + 1
        if start == -1 or end == 0:
            raise ValueError("No JSON found in AI response")
        
        json_str = content[start:end]
        
        # Clean up common JSON formatting issues
        json_str = json_str.replace("'", '"')
        import re
        json_str = re.sub(r',\s*}', '}', json_str)
        json_str = re.sub(r',\s*]', ']', json_str)
        
        try:
            parsed = pyjson.loads(json_str)
        except Exception as e:
            raise ValueError(f"Invalid JSON from AI: {e}")
        
        # Ensure required fields exist (date is optional)
        required_fields = ['description', 'debit_account', 'credit_account', 'amount']
        for field in required_fields:
            if field not in parsed:
                raise ValueError(f"Missing required field: {field}")
        
        # Don't auto-set date - let UI preserve existing date if not specified
        # Only set empty string if date field is missing entirely
        if 'date' not in parsed:
            parsed['date'] = ''
          # Ensure amount is a number
        try:
            parsed['amount'] = float(str(parsed['amount']).replace(',', '').replace('$', '').strip())
        except:
            raise ValueError(f"Invalid amount: {parsed['amount']}")
        
        # CRITICAL: Enforce textbook accounting logic
        if system:
            parsed = enforce_accounting_logic(parsed, system)
        
        return parsed
        
    except Exception as e:
        logging.error(f"Error parsing transaction: {e}")
        raise ValueError(f"AI could not parse the transaction: {e}")

def enforce_accounting_logic(parsed, system):
    """
    Enforce fundamental double-entry accounting principles with comprehensive validation.
    
    TEXTBOOK ACCOUNTING RULES (MUST BE FOLLOWED):
    | Account Type    | Normal Balance | When to DEBIT     | When to CREDIT    |
    | --------------- | -------------- | ----------------- | ----------------- |
    | **Assets**      | DEBIT          | Acquire/Increase  | Use/Decrease      |
    | **Liabilities** | CREDIT         | Pay off/Decrease  | Incur/Increase    |
    | **Equity**      | CREDIT         | Decrease          | Increase          |
    | **Revenue**     | CREDIT         | Reverse/Decrease  | Earn/Increase     |
    | **Expenses**    | DEBIT          | Incur/Increase    | Reverse/Decrease  |
    """
    try:
        # Get account types from the system
        all_accounts = system.get_all_accounts()
        account_types = {}
        for name, acc_type, code, parent_code, level, is_postable, description in all_accounts:
            account_types[name.lower().strip()] = acc_type
        
        debit_account = parsed['debit_account'].lower().strip()
        credit_account = parsed['credit_account'].lower().strip()
        
        debit_type = account_types.get(debit_account)
        credit_type = account_types.get(credit_account)
        
        if not debit_type or not credit_type:
            # If we can't find account types, return as-is (LLM decision)
            logging.warning(f"Could not find account types for: {debit_account} ({debit_type}), {credit_account} ({credit_type})")
            return parsed
        
        # Analyze the transaction to understand what's happening
        description = parsed['description'].lower()
        amount = parsed['amount']
        
        # Comprehensive validation rules
        validation_errors = []
        validation_passed = []
        
        # 1. EXPENSE PAYMENT VALIDATION
        # Common expense keywords
        expense_keywords = ['paid', 'purchase', 'bought', 'rent', 'utility', 'utilities', 'salary', 'salaries', 
                           'wage', 'wages', 'supply', 'supplies', 'maintenance', 'repair', 'insurance',
                           'telephone', 'internet', 'electricity', 'gas', 'water', 'fuel', 'office', 'travel']
        
        if any(keyword in description for keyword in expense_keywords):
            if debit_type == 'Expense' and credit_type in ['Asset']:
                validation_passed.append(f"✅ Correct expense payment: DEBIT {parsed['debit_account']} (Expense), CREDIT {parsed['credit_account']} (Asset)")
            elif debit_type in ['Asset'] and credit_type == 'Expense':
                validation_errors.append(f"❌ CRITICAL ERROR: Expense payment should DEBIT the expense account, not credit it!")
                validation_errors.append(f"   Should be: DEBIT {parsed['credit_account']} (Expense), CREDIT {parsed['debit_account']} (Asset)")
            elif credit_type == 'Expense':
                validation_errors.append(f"❌ CRITICAL ERROR: Never credit an expense account when paying for it!")
                validation_errors.append(f"   Rule: Expense payments = DEBIT Expense + CREDIT Cash/Bank")
        
        # 2. REVENUE RECEIPT VALIDATION
        revenue_keywords = ['received', 'income', 'revenue', 'sales', 'earned', 'service', 'fee', 'commission']
        
        if any(keyword in description for keyword in revenue_keywords):
            if debit_type in ['Asset'] and credit_type == 'Revenue':
                validation_passed.append(f"✅ Correct revenue receipt: DEBIT {parsed['debit_account']} (Asset), CREDIT {parsed['credit_account']} (Revenue)")
            elif debit_type == 'Revenue' and credit_type in ['Asset']:
                validation_errors.append(f"❌ CRITICAL ERROR: Revenue receipt should CREDIT the revenue account, not debit it!")
                validation_errors.append(f"   Should be: DEBIT {parsed['credit_account']} (Asset), CREDIT {parsed['debit_account']} (Revenue)")
            elif debit_type == 'Revenue':
                validation_errors.append(f"❌ CRITICAL ERROR: Never debit a revenue account when earning money!")
                validation_errors.append(f"   Rule: Revenue receipts = DEBIT Cash/Bank + CREDIT Revenue")
        
        # 3. ASSET PURCHASE VALIDATION
        asset_keywords = ['bought', 'purchased', 'acquired', 'equipment', 'inventory', 'vehicle', 'computer', 'furniture']
        
        if any(keyword in description for keyword in asset_keywords):
            if debit_type in ['Asset'] and credit_type in ['Asset']:
                validation_passed.append(f"✅ Correct asset purchase: DEBIT {parsed['debit_account']} (Asset), CREDIT {parsed['credit_account']} (Asset)")
        
        # 4. DEBT/LIABILITY PAYMENT VALIDATION
        debt_keywords = ['loan', 'debt', 'payable', 'mortgage', 'credit card', 'borrowing']
        
        if any(keyword in description for keyword in debt_keywords) and any(pay_word in description for pay_word in ['paid', 'payment', 'settle']):
            if debit_type in ['Liability'] and credit_type in ['Asset']:
                validation_passed.append(f"✅ Correct debt payment: DEBIT {parsed['debit_account']} (Liability), CREDIT {parsed['credit_account']} (Asset)")
            elif debit_type in ['Asset'] and credit_type in ['Liability']:
                validation_errors.append(f"❌ CRITICAL ERROR: Debt payment should DEBIT the liability, not credit it!")
                validation_errors.append(f"   Should be: DEBIT {parsed['credit_account']} (Liability), CREDIT {parsed['debit_account']} (Asset)")
        
        # 5. GENERAL ACCOUNT TYPE VALIDATION
        # Ensure expenses are never credited in normal operations
        if credit_type == 'Expense' and 'refund' not in description and 'return' not in description:
            validation_errors.append(f"❌ GENERAL ERROR: Expense accounts should rarely be credited in normal business operations")
            validation_errors.append(f"   Check if this should be: DEBIT {parsed['credit_account']} (Expense) instead")
        
        # Ensure revenues are never debited in normal operations  
        if debit_type == 'Revenue' and 'refund' not in description and 'return' not in description:
            validation_errors.append(f"❌ GENERAL ERROR: Revenue accounts should rarely be debited in normal business operations")
            validation_errors.append(f"   Check if this should be: CREDIT {parsed['debit_account']} (Revenue) instead")
        
        # Log all validation results
        for success in validation_passed:
            logging.info(success)
            
        for error in validation_errors:
            logging.error(error)
            
        if validation_errors:
            logging.error(f"TRANSACTION FAILED VALIDATION: {parsed}")
            logging.error("=" * 80)
        else:
            logging.info(f"Transaction passed all validations: {parsed}")
        
        # Always return the parsed transaction - validation is for logging only
        return parsed
        
    except Exception as e:
        logging.error(f"Error in accounting logic enforcement: {e}")
        # If validation fails, return original parsing
        return parsed

def log_action(action, details=None):
    msg = f"ACTION: {action}"
    if details:
        msg += f" | DETAILS: {details}"
    logging.info(msg)

def log_error(error, details=None):
    msg = f"ERROR: {error}"
    if details:
        msg += f" | DETAILS: {details}"
    logging.error(msg)

def analyze_accounts_with_llm(system, nl_input):
    """
    Use LLM to intelligently analyze the chart of accounts and suggest the most relevant accounts
    for the given transaction description. This adds a smart layer of account matching.
    """
    all_accounts = system.get_all_accounts()
    
    # Get only leaf accounts (usable accounts)
    all_parent_codes = set([parent_code for name, acc_type, code, parent_code, level, is_postable, description in all_accounts if parent_code])
    leaf_accounts = []
    for name, acc_type, code, parent_code, level, is_postable, description in all_accounts:
        if parent_code and code not in all_parent_codes:
            leaf_accounts.append((name, acc_type, code, parent_code, level, is_postable, description))
    
    # Create a structured account list for LLM analysis
    account_info = []
    for name, acc_type, code, parent_code, level, is_postable, description in leaf_accounts:
        account_info.append(f"- {name} (Type: {acc_type}, Code: {code})")
    
    account_list = "\n".join(account_info)
    
    prompt = f"""
You are an expert accountant analyzing a transaction to suggest the most relevant accounts.

TRANSACTION DESCRIPTION: "{nl_input}"

AVAILABLE ACCOUNTS:
{account_list}

TASK: Analyze the transaction description and identify the most relevant accounts that would likely be used. Consider:

1. Transaction Type Analysis:
   - Is this a payment, receipt, purchase, sale, or other transaction?
   - What business activity is described?

2. Account Relevance:
   - Which accounts directly relate to the transaction?
   - Consider account names, types, and typical business usage
   - Think about both the source and destination of value

3. Context Clues:
   - Keywords in the description (cash, bank, rent, sales, etc.)
   - Business context and common accounting practices
   - Payment methods mentioned

PROVIDE: A focused list of 8-12 most relevant accounts from the available accounts list, ordered by relevance (most relevant first).

EXAMPLE FORMAT:
For "paid office rent 500 by bank transfer":
1. Rent
2. Cash at Bank
3. Utilities
4. Operating Expenses
...

Respond with ONLY the numbered list of account names, no explanations.
"""

    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {get_mistral_api_key()}"
        }
        data = {
            "model": "mistral-tiny",
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
        
        response = requests.post(MISTRAL_API_URL, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        
        content = result['choices'][0]['message']['content']
        
        # Parse the numbered list response
        lines = content.strip().split('\n')
        suggested_accounts = []
        
        for line in lines:
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-')):
                # Extract account name from "1. Account Name" or "- Account Name" format
                if '. ' in line:
                    account_name = line.split('. ', 1)[1].strip()
                elif '- ' in line:
                    account_name = line.split('- ', 1)[1].strip()
                else:
                    continue
                
                # Verify the account exists in our chart
                for name, acc_type, code, parent_code, level, is_postable, description in leaf_accounts:
                    if name.lower().strip() == account_name.lower().strip():
                        if name not in suggested_accounts:
                            suggested_accounts.append(name)
                        break
        
        # If LLM analysis fails or returns too few accounts, fall back to context-based suggestions
        if len(suggested_accounts) < 8:
            fallback_accounts = get_smart_account_suggestions(system, nl_input)
            for account in fallback_accounts:
                if account not in suggested_accounts and len(suggested_accounts) < 12:
                    suggested_accounts.append(account)
        
        return suggested_accounts[:12]  # Limit to 12 most relevant accounts
        
    except Exception as e:
        logging.error(f"LLM account analysis failed: {e}")
        # Fall back to the existing smart account suggestions
        return get_smart_account_suggestions(system, nl_input)
