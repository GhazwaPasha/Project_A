"""
Smart AI Command Processor for Accounting Application
Uses hybrid architecture: Command Registry + Plugin System + State Machine + API Fallback
Optimized for performance, maintainability, and extensibility.
"""

import json
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from abc import ABC, abstractmethod
from PyQt6.QtCore import QObject, QThread, pyqtSignal
import requests


# ============================================================================
# CORE AI RESPONSE CLASSES
# ============================================================================

class AIResponse:
    """Standardized AI response object"""
    def __init__(self, response_type: str, data: dict, message: str = ""):
        self.type = response_type
        self.data = data
        self.message = message
        self.timestamp = datetime.now()


# ============================================================================
# PLUGIN ARCHITECTURE
# ============================================================================

class AIPlugin(ABC):
    """Base class for AI plugins"""
    
    @abstractmethod
    def can_handle(self, user_input: str, context: dict) -> float:
        """Return confidence score 0.0-1.0 for handling this input"""
        pass
    
    @abstractmethod
    def execute(self, user_input: str, context: dict) -> AIResponse:
        """Execute the command and return response"""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Plugin name for debugging"""
        pass


class ReportsPlugin(AIPlugin):
    """Handles all report generation commands"""
    
    @property
    def name(self) -> str:
        return "ReportsPlugin"
    
    def can_handle(self, user_input: str, context: dict) -> float:
        input_lower = user_input.lower()
        
        # CRITICAL: If this is a reminder request, DON'T handle it
        reminder_indicators = ['remind', 'reminder', 'set reminder', 'create reminder', 'schedule', 'recurring', 'every month', 'every week', 'every day']
        if any(indicator in input_lower for indicator in reminder_indicators):
            print(f"🚫 ReportsPlugin: Detected reminder request, skipping (confidence: 0.0)")
            return 0.0
        
        # Check for action words + report keywords
        action_words = ['generate', 'create', 'show', 'run', 'produce', 'make']
        report_words = ['report', 'statement', 'balance', 'income', 'trial', 'cash flow', 'ledger']
        
        has_action = any(word in input_lower for word in action_words)
        has_report = any(word in input_lower for word in report_words)
        
        if has_action and has_report:
            return 0.9
        elif has_report:
            return 0.7
        return 0.0
    
    def execute(self, user_input: str, context: dict) -> AIResponse:
        input_lower = user_input.lower()
        
        # Clean input for better matching
        cleaned_input = input_lower.replace(' or ', ' for ').replace(' of ', ' for ')
        
        # Report patterns with typo tolerance
        report_patterns = {
            'income_statement': {
                'keywords': ['income statement', 'income statment', 'profit loss', 'p&l', 'pnl', 'profit and loss'],
                'message': 'Generating Income Statement...',
                'requires_dates': True
            },
            'balance_sheet': {
                'keywords': ['balance sheet', 'balance shet', 'financial position'],
                'message': 'Generating Balance Sheet...',
                'requires_dates': False
            },
            'cash_flow': {
                'keywords': ['cash flow', 'cashflow', 'cash flow statement'],
                'message': 'Generating Cash Flow Statement...',
                'requires_dates': True
            },
            'trial_balance': {
                'keywords': ['trial balance', 'trial bal', 'trial', 'trial balence'],
                'message': 'Generating Trial Balance...',
                'requires_dates': True
            },
            'general_ledger': {
                'keywords': ['general ledger', 'ledger', 'gl'],
                'message': 'Opening General Ledger...',
                'requires_dates': True
            }
        }
        
        # Find matching report type
        for report_id, config in report_patterns.items():
            if any(keyword in cleaned_input for keyword in config['keywords']):
                date_params = self._parse_dates(cleaned_input)
                
                return AIResponse(
                    response_type='report_generation',
                    data={
                        'report_type': report_id,
                        'date_params': date_params,
                        'original_prompt': cleaned_input,
                        'parameters': {'date_range': date_params}
                    },
                    message=config['message']
                )
        
        # Generic report request
        return AIResponse(
            response_type='help',
            data={},
            message="I can generate: income statement, balance sheet, cash flow, trial balance, or general ledger reports."
        )
    
    def _parse_dates(self, input_lower: str) -> dict:
        """Parse date information from command"""
        today = datetime.now()
        
        if 'last month' in input_lower:
            last_month = today.replace(day=1) - timedelta(days=1)
            start_of_last_month = last_month.replace(day=1)
            return {
                'start': start_of_last_month.strftime('%Y-%m-%d'),
                'end': last_month.strftime('%Y-%m-%d')
            }
        elif 'this month' in input_lower or 'current month' in input_lower:
            start_of_month = today.replace(day=1)
            return {
                'start': start_of_month.strftime('%Y-%m-%d'),
                'end': today.strftime('%Y-%m-%d')
            }
        elif 'last year' in input_lower:
            last_year = today.year - 1
            return {
                'start': f'{last_year}-01-01',
                'end': f'{last_year}-12-31'
            }
        elif 'this year' in input_lower or 'current year' in input_lower:
            return {
                'start': f'{today.year}-01-01',
                'end': today.strftime('%Y-%m-%d')
            }
        else:
            # Default to current month
            start_of_month = today.replace(day=1)
            return {
                'start': start_of_month.strftime('%Y-%m-%d'),
                'end': today.strftime('%Y-%m-%d')
            }


class NavigationPlugin(AIPlugin):
    """Handles navigation commands"""
    
    @property
    def name(self) -> str:
        return "NavigationPlugin"
    
    def can_handle(self, user_input: str, context: dict) -> float:
        input_lower = user_input.lower()
        
        nav_words = ['show', 'open', 'go to', 'navigate', 'take me to', 'switch to', 'display']
        page_words = ['dashboard', 'journal', 'accounts', 'ledger', 'reports', 'reminders', 'page']
        
        has_nav = any(word in input_lower for word in nav_words)
        has_page = any(word in input_lower for word in page_words)
        
        # Don't handle if it's a report (let ReportsPlugin handle it)
        report_words = ['statement', 'balance sheet', 'income', 'trial balance']
        has_report = any(word in input_lower for word in report_words)
        
        if has_nav and has_page and not has_report:
            return 0.9
        elif has_page and not has_report:
            return 0.6
        return 0.0
    
    def execute(self, user_input: str, context: dict) -> AIResponse:
        input_lower = user_input.lower()
        
        page_keywords = {
            'dashboard': ['dashboard', 'home', 'overview', 'main page'],
            'journal': ['journal', 'entries', 'transactions'],
            'accounts': ['accounts', 'chart of accounts', 'account list'],
            'trial_balance': ['trial balance page'],  # Only page navigation, not report
            'reports': ['reports page', 'financial reports page'],
            'ledger': ['ledger page'],  # Only page navigation, not report
            'reminders': ['reminders', 'tasks', 'notifications'],
            'period_closing': ['period closing', 'month end', 'year end']
        }
        
        for page, keywords in page_keywords.items():
            if any(keyword in input_lower for keyword in keywords):
                return AIResponse(
                    response_type='navigation',
                    data={'page': page, 'parameters': {}},
                    message=f"Navigating to {page.replace('_', ' ').title()}..."
                )
        
        return AIResponse(
            response_type='help',
            data={},
            message="Available pages: Dashboard, Journal, Accounts, Trial Balance, Reports, Ledger, Reminders, Period Closing"
        )


class RemindersPlugin(AIPlugin):
    """Handles reminder creation and management"""
    
    @property
    def name(self) -> str:
        return "RemindersPlugin"
    
    def can_handle(self, user_input: str, context: dict) -> float:
        input_lower = user_input.lower()
        
        # Primary reminder indicators - high priority
        reminder_words = ['remind', 'reminder', 'set reminder', 'create reminder', 'schedule', 'alert']
        recurring_words = ['recurring', 'repeat', 'every', 'daily', 'weekly', 'monthly', 'regularly']
        time_words = ['tomorrow', 'today', 'next week', 'pm', 'am', 'hour', 'minute', 'date', 'time']
        
        has_reminder = any(word in input_lower for word in reminder_words)
        has_recurring = any(word in input_lower for word in recurring_words)
        has_time = any(word in input_lower for word in time_words)
        
        # CRITICAL: If "reminder" is mentioned, this should be primary intent
        if has_reminder:
            if has_recurring:
                return 0.95  # Very high confidence for recurring reminders
            elif has_time:
                return 0.9   # High confidence for timed reminders
            else:
                return 0.8   # Still high confidence for any reminder
        
        # Secondary indicators without explicit "reminder"
        elif has_recurring and has_time:
            return 0.7  # Might be scheduling without saying "reminder"
        
        return 0.0
    
    def execute(self, user_input: str, context: dict) -> AIResponse:
        input_lower = user_input.lower()
        
        # Enhanced title extraction based on context
        title = self._extract_reminder_title(input_lower)
        
        # Parse recurring pattern
        recurring = self._parse_recurring(input_lower)
        
        # Parse date/time with recurring context
        due_datetime = self._parse_datetime(input_lower, recurring)
        
        # Enhanced priority detection
        priority = self._extract_priority(input_lower)
        
        reminder_data = {
            'id': f"reminder_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'title': title,
            'description': f"Reminder created from: {user_input}",
            'due_datetime': due_datetime,
            'recurring': recurring,
            'priority': priority,
            'created_datetime': datetime.now().isoformat(),
            'completed': False
        }
        
        return AIResponse(
            response_type='reminder_creation',
            data=reminder_data,
            message=f"✅ Recurring reminder created: {title} - {recurring} starting {due_datetime}"
        )
    
    def _extract_reminder_title(self, input_lower: str) -> str:
        """Extract meaningful title from user input"""
        if 'income statement' in input_lower:
            return "Monthly Income Statement Generation"
        elif 'balance sheet' in input_lower:
            return "Balance Sheet Report Generation"
        elif 'cash flow' in input_lower:
            return "Cash Flow Statement Generation"
        elif 'trial balance' in input_lower:
            return "Trial Balance Report Generation"
        elif 'report' in input_lower and 'monthly' in input_lower:
            return "Monthly Financial Reports"
        elif 'meeting' in input_lower:
            return "Meeting Reminder"
        elif 'deadline' in input_lower:
            return "Deadline Reminder"
        elif 'closing' in input_lower or 'month end' in input_lower:
            return "Month-End Closing Reminder"
        else:
            return "General Reminder"
    
    def _parse_recurring(self, input_lower: str) -> str:
        """Parse recurring pattern from natural language"""
        if any(word in input_lower for word in ['every month', 'monthly', 'each month']):
            return 'monthly'
        elif any(word in input_lower for word in ['every week', 'weekly', 'each week']):
            return 'weekly'
        elif any(word in input_lower for word in ['every day', 'daily', 'each day']):
            return 'daily'
        elif 'recurring' in input_lower or 'repeat' in input_lower:
            # Default to monthly for recurring without specific frequency
            return 'monthly'
        else:
            return 'none'
    
    def _extract_priority(self, input_lower: str) -> str:
        """Extract priority from context"""
        if any(word in input_lower for word in ['urgent', 'critical', 'important', 'asap']):
            return 'high'
        elif any(word in input_lower for word in ['low priority', 'when possible', 'optional']):
            return 'low'
        else:
            return 'medium'
    
    def _parse_datetime(self, input_lower: str, recurring: str = 'none') -> str:
        """Parse datetime from natural language with recurring context"""
        now = datetime.now()
        
        # Handle specific date patterns for recurring reminders
        if recurring == 'monthly':
            if '1st' in input_lower or 'first' in input_lower:
                # Next first of month
                if now.day == 1:
                    next_month = now  # Today is the 1st
                else:
                    # Get first day of next month
                    if now.month == 12:
                        next_month = now.replace(year=now.year + 1, month=1, day=1)
                    else:
                        next_month = now.replace(month=now.month + 1, day=1)
                
                # Parse time
                if any(time in input_lower for time in ['9am', '09:00', 'morning']):
                    return next_month.strftime('%Y-%m-%d 09:00')
                elif any(time in input_lower for time in ['5pm', '17:00', 'evening']):
                    return next_month.strftime('%Y-%m-%d 17:00')
                else:
                    return next_month.strftime('%Y-%m-%d 09:00')  # Default morning for monthly tasks
                    
            elif 'last day' in input_lower or 'end of month' in input_lower:
                # Last day of current month
                if now.month == 12:
                    last_day = now.replace(year=now.year + 1, month=1, day=1) - timedelta(days=1)
                else:
                    last_day = now.replace(month=now.month + 1, day=1) - timedelta(days=1)
                return last_day.strftime('%Y-%m-%d 17:00')
        
        # Handle regular time patterns
        if 'tomorrow' in input_lower:
            tomorrow = now + timedelta(days=1)
            if '4pm' in input_lower or '16:' in input_lower:
                return tomorrow.strftime('%Y-%m-%d 16:00')
            elif 'morning' in input_lower or '9am' in input_lower:
                return tomorrow.strftime('%Y-%m-%d 09:00')
            else:
                return tomorrow.strftime('%Y-%m-%d 16:00')  # Default 4pm
                
        elif 'today' in input_lower:
            if '5pm' in input_lower or '17:' in input_lower:
                return now.strftime('%Y-%m-%d 17:00')
            else:
                return now.strftime('%Y-%m-%d 17:00')  # Default 5pm today
                
        elif 'next week' in input_lower:
            next_week = now + timedelta(days=7)
            return next_week.strftime('%Y-%m-%d 09:00')  # Default Monday morning
            
        else:
            # Default based on recurring type
            if recurring == 'monthly':
                # Default to first of next month at 9am
                if now.month == 12:
                    next_month = now.replace(year=now.year + 1, month=1, day=1)
                else:
                    next_month = now.replace(month=now.month + 1, day=1)
                return next_month.strftime('%Y-%m-%d 09:00')
            else:
                # Default to tomorrow 4pm
                tomorrow = now + timedelta(days=1)
                return tomorrow.strftime('%Y-%m-%d 16:00')


class ExplanationPlugin(AIPlugin):
    """Handles explanation requests"""
    
    @property
    def name(self) -> str:
        return "ExplanationPlugin"
    
    def can_handle(self, user_input: str, context: dict) -> float:
        input_lower = user_input.lower()
        
        # Question words that indicate explanation requests
        explain_words = ['explain', 'what is', 'what are', 'how does', 'how do', 'tell me about', 'define', 'meaning of']
        
        # Expanded accounting concepts
        concept_words = [
            'debit', 'credit', 'ledger', 'journal', 'balance sheet', 'income statement', 
            'accounting', 'trial balance', 'cash flow', 'assets', 'liabilities', 'equity',
            'revenue', 'expenses', 'depreciation', 'accrual', 'accounts payable', 
            'accounts receivable', 'general ledger', 'chart of accounts'
        ]
        
        has_explain = any(word in input_lower for word in explain_words)
        has_concept = any(word in input_lower for word in concept_words)
        
        # High confidence for direct questions about accounting concepts
        if has_explain and has_concept:
            print(f"🔍 ExplanationPlugin: Detected explanation request (confidence: 0.95)")
            return 0.95  # Very high confidence for explanations
        elif has_explain:
            return 0.7   # Still high for any explanation request
        elif any(word in input_lower for word in ['what', 'how', 'why', 'define']) and has_concept:
            return 0.8   # High confidence for question words + concepts
        return 0.0
    
    def execute(self, user_input: str, context: dict) -> AIResponse:
        input_lower = user_input.lower()
        
        explanations = {
            'ledger': {
                'triggers': ['ledger', 'general ledger'],
                'content': """📚 General Ledger:
A general ledger is the master record of all financial transactions in your business. It contains all the accounts from your Chart of Accounts and shows the complete history of debits and credits for each account.

Key features:
• Complete transaction history for each account
• Running balance for every account
• Source of data for financial statements
• Essential for audit trails and compliance

Think of it as the "master book" where all your journal entries are permanently recorded and organized by account."""
            },
            'journal': {
                'triggers': ['journal', 'journal entry', 'journal entries'],
                'content': """📝 Journal & Journal Entries:
A journal is where business transactions are first recorded in chronological order. Each transaction is recorded as a journal entry with debits and credits.

Key components:
• Date of transaction
• Accounts affected (debit and credit)
• Description of the transaction
• Reference numbers for tracking

Example: When you pay rent of $1,000:
- Debit: Rent Expense $1,000
- Credit: Cash $1,000"""
            },
            'debit_credit': {
                'triggers': ['debit', 'credit', 'debits and credits'],
                'content': """⚖️ Debits and Credits:
The fundamental rule of double-entry bookkeeping. Every transaction affects at least two accounts.

Basic rules:
• Assets: Debit increases, Credit decreases
• Liabilities: Credit increases, Debit decreases  
• Equity: Credit increases, Debit decreases
• Revenue: Credit increases, Debit decreases
• Expenses: Debit increases, Credit decreases

Remember: Debits must always equal Credits in every transaction!"""
            },
            'balance_sheet': {
                'triggers': ['balance sheet', 'statement of financial position'],
                'content': """📊 Balance Sheet:
A snapshot of your company's financial position at a specific point in time. It shows what you own (assets), what you owe (liabilities), and what's left over (equity).

Structure:
Assets = Liabilities + Equity

• Assets: Cash, inventory, equipment, etc.
• Liabilities: Loans, accounts payable, etc.  
• Equity: Owner's investment + retained earnings

The balance sheet must always balance!"""
            },
            'income_statement': {
                'triggers': ['income statement', 'profit and loss', 'p&l', 'pnl'],
                'content': """💰 Income Statement (P&L):
Shows your company's profitability over a specific period (month, quarter, year).

Structure:
Revenue - Expenses = Net Income

• Revenue: Money earned from sales/services
• Cost of Goods Sold: Direct costs to produce products
• Gross Profit: Revenue - COGS
• Operating Expenses: Rent, salaries, utilities, etc.
• Net Income: What's left after all expenses

This tells you if your business is profitable!"""
            },
            'trial_balance': {
                'triggers': ['trial balance'],
                'content': """📋 Trial Balance:
A list of all accounts in your general ledger with their debit or credit balances at a specific point in time.

Purpose:
• Verify that total debits = total credits
• Check for mathematical errors in posting
• Basis for preparing financial statements
• Internal control and accuracy check

If the trial balance doesn't balance, there's an error that needs to be found and corrected."""
            },
            'cash_flow': {
                'triggers': ['cash flow', 'cash flow statement'],
                'content': """💸 Cash Flow Statement:
Shows how cash moved in and out of your business during a specific period.

Three categories:
• Operating Activities: Cash from day-to-day operations
• Investing Activities: Cash from buying/selling assets  
• Financing Activities: Cash from loans, investments, etc.

Important: A profitable company can still have cash flow problems! This statement shows actual cash movement, not just profits."""
            },
            'accounts_payable': {
                'triggers': ['accounts payable', 'payables'],
                'content': """📤 Accounts Payable:
Money your business owes to suppliers, vendors, or creditors for goods/services received but not yet paid for.

Examples:
• Unpaid supplier invoices
• Utility bills not yet paid
• Professional services invoices pending

This is a liability on your balance sheet. Managing A/P well helps with cash flow."""
            },
            'accounts_receivable': {
                'triggers': ['accounts receivable', 'receivables'],
                'content': """📥 Accounts Receivable:
Money owed to your business by customers for goods/services delivered but not yet paid for.

Examples:
• Customer invoices sent but unpaid
• Services completed, payment pending
• Sales made on credit terms

This is an asset on your balance sheet. Good A/R management is crucial for cash flow."""
            }
        }
        
        for concept, config in explanations.items():
            if any(trigger in input_lower for trigger in config['triggers']):
                return AIResponse(
                    response_type='explanation',
                    data={'concept': concept},
                    message=config['content']
                )
        
        return AIResponse(
            response_type='help',
            data={},
            message="I can explain accounting concepts like: ledger, journal entries, debits & credits, balance sheet, income statement, trial balance, cash flow, accounts payable/receivable, and more. What would you like to learn about?"
        )


# ============================================================================
# COMMAND REGISTRY
# ============================================================================

class AICommandRegistry:
    """Fast command registry for instant responses"""
    
    def __init__(self):
        self.quick_commands = {
            'help': "I can help with navigation, reports, reminders, and explanations. Try: 'show accounts', 'generate income statement', or 'explain debits'.",
            'what can you do': "I can navigate pages, generate reports, create reminders, and explain accounting concepts.",
            'commands': "Available commands: show [page], generate [report], create reminder, explain [concept]"
        }
    
    def try_handle(self, user_input: str) -> Optional[AIResponse]:
        """Try to handle with quick command registry"""
        input_lower = user_input.lower().strip()
        
        for command, response in self.quick_commands.items():
            if command in input_lower:
                return AIResponse(
                    response_type='quick_response',
                    data={'command': command},
                    message=response
                )
        
        return None


# ============================================================================
# STATE MACHINE
# ============================================================================

class AIStateMachine:
    """Handles multi-step conversations"""
    
    def __init__(self):
        self.state = 'idle'
        self.context = {}
    
    def has_active_state(self) -> bool:
        return self.state != 'idle'
    
    def process_input(self, user_input: str) -> AIResponse:
        """Process input based on current state"""
        if self.state == 'awaiting_date_range':
            return self._handle_date_input(user_input)
        elif self.state == 'awaiting_confirmation':
            return self._handle_confirmation(user_input)
        
        return AIResponse('error', {}, "Unknown state")
    
    def _handle_date_input(self, user_input: str) -> AIResponse:
        # Handle date range input
        self.state = 'idle'
        return AIResponse('info', {}, f"Date range processed: {user_input}")
    
    def _handle_confirmation(self, user_input: str) -> AIResponse:
        # Handle yes/no confirmation
        self.state = 'idle'
        return AIResponse('info', {}, f"Confirmation processed: {user_input}")


# ============================================================================
# PLUGIN MANAGER
# ============================================================================

class AIPluginManager:
    """Manages all AI plugins"""
    
    def __init__(self):
        self.plugins = [
            ReportsPlugin(),
            NavigationPlugin(),
            RemindersPlugin(),
            ExplanationPlugin()
        ]
    
    def try_handle(self, user_input: str, context: dict) -> Optional[AIResponse]:
        """Find best plugin and execute"""
        best_plugin = None
        best_confidence = 0.0
        
        for plugin in self.plugins:
            confidence = plugin.can_handle(user_input, context)
            if confidence > best_confidence:
                best_confidence = confidence
                best_plugin = plugin
        
        if best_plugin and best_confidence > 0.5:
            print(f"🔌 Using plugin: {best_plugin.name} (confidence: {best_confidence:.2f})")
            return best_plugin.execute(user_input, context)
        
        return None


# ============================================================================
# MAIN AI PROCESSOR
# ============================================================================

class ContextAwareAI(QObject):
    """Smart AI processor with hybrid architecture"""
    
    # Signals
    response_ready = pyqtSignal(str)
    navigation_requested = pyqtSignal(str, dict)
    report_requested = pyqtSignal(str, dict)
    reminder_created = pyqtSignal(dict)
    action_executed = pyqtSignal(str, dict)
    context_updated = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    processing_started = pyqtSignal()
    processing_finished = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.parent_window = parent
        
        # Context
        self.current_page = "dashboard"
        self.current_page_data = {}
        self.user_context = {}
        self.accounting_data = {}
        self.application_state = {}
        
        # Hybrid architecture components
        self.command_registry = AICommandRegistry()
        self.plugin_manager = AIPluginManager()
        self.state_machine = AIStateMachine()
        
        # API fallback
        self.api_key = os.getenv('MISTRAL_API_KEY') or os.getenv('OPENAI_API_KEY')
        self.processing_thread = None
        
        # Application mappings
        self.page_mapping = {
            'dashboard': {'index': 0, 'name': 'Dashboard'},
            'journal': {'index': 1, 'name': 'Journal Entries'},
            'ledger': {'index': 2, 'name': 'General Ledger'},
            'trial_balance': {'index': 3, 'name': 'Trial Balance'},
            'reports': {'index': 4, 'name': 'Reports'},
            'accounts': {'index': 5, 'name': 'Chart of Accounts'},
            'reminders': {'index': 6, 'name': 'Reminders & Tasks'},
            'period_closing': {'index': 7, 'name': 'Period Closing'},
            'settings': {'index': -1, 'name': 'Settings'}
        }
    
    def process_command(self, user_input: str):
        """Main command processing entry point"""
        print(f"🔍 AI Processor received: '{user_input}'")
        
        if not user_input.strip():
            self.error_occurred.emit("Please enter a command.")
            return
        
        try:
            # Step 1: Command registry (fastest)
            if response := self.command_registry.try_handle(user_input):
                print(f"⚡ Quick command: {response.message}")
                self.response_ready.emit(response.message)
                return
            
            # Step 2: State machine (for conversations)
            if self.state_machine.has_active_state():
                response = self.state_machine.process_input(user_input)
                self.response_ready.emit(response.message)
                return
            
            # Step 3: Plugin system (main processing)
            context = self._build_context()
            if response := self.plugin_manager.try_handle(user_input, context):
                print(f"🔧 Plugin response: {response.type}")
                self._execute_response(response)
                return
            
            # Step 4: API fallback (complex queries)
            if self.api_key:
                self._process_with_api(user_input)
            else:
                self.response_ready.emit("I didn't understand that command. Try 'help' for available commands.")
        
        except Exception as e:
            print(f"❌ Processing error: {e}")
            self.error_occurred.emit(f"Processing error: {str(e)}")
    
    def _execute_response(self, response: AIResponse):
        """Execute AI response and emit appropriate signals"""
        print(f"🚀 Executing {response.type}: {response.message}")
        
        if response.type == 'navigation':
            page = response.data['page']
            params = response.data.get('parameters', {})
            self.navigation_requested.emit(page, params)
            self.response_ready.emit(response.message)
        
        elif response.type == 'report_generation':
            report_type = response.data['report_type']
            params = response.data.get('parameters', {})
            self.report_requested.emit(report_type, params)
            self.response_ready.emit(response.message)
        
        elif response.type == 'reminder_creation':
            self.reminder_created.emit(response.data)
            self.response_ready.emit(response.message)
        
        else:
            self.response_ready.emit(response.message)
    
    def _build_context(self) -> dict:
        """Build context for plugins"""
        return {
            'current_page': self.current_page,
            'page_mapping': self.page_mapping,
            'accounting_data': self.accounting_data,
            'user_context': self.user_context
        }
    
    def _process_with_api(self, user_input: str):
        """Fallback API processing for complex queries"""
        if self.processing_thread and self.processing_thread.isRunning():
            self.error_occurred.emit("Please wait for current request to complete.")
            return
        
        print("🌐 Using API fallback...")
        self.processing_started.emit()
        
        self.processing_thread = APIFallbackThread(user_input, self.api_key)
        self.processing_thread.response_ready.connect(self.response_ready.emit)
        self.processing_thread.error_occurred.connect(self.error_occurred.emit)
        self.processing_thread.finished.connect(self.processing_finished.emit)
        self.processing_thread.start()
    
    def update_context(self, context_type: str, data: dict):
        """Update application context"""
        if context_type == "page":
            self.current_page = data.get('page', self.current_page)
            self.current_page_data = data.get('data', {})
        elif context_type == "accounting":
            self.accounting_data.update(data)
        
        self.context_updated.emit({context_type: data})
    
    def get_status(self) -> dict:
        """Get current AI status"""
        return {
            'api_available': bool(self.api_key),
            'processing': self.processing_thread is not None and self.processing_thread.isRunning(),
            'current_page': self.current_page,
            'state': self.state_machine.state
        }
    
    def stop_processing(self):
        """Stop any running processing"""
        if self.processing_thread and self.processing_thread.isRunning():
            self.processing_thread.quit()
            self.processing_thread.wait(3000)
            if self.processing_thread.isRunning():
                self.processing_thread.terminate()
                self.processing_thread.wait(1000)
            self.processing_thread = None


# ============================================================================
# API FALLBACK THREAD
# ============================================================================

class APIFallbackThread(QThread):
    """Lightweight API fallback for complex queries"""
    
    response_ready = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, user_input: str, api_key: str):
        super().__init__()
        self.user_input = user_input
        self.api_key = api_key
    
    def run(self):
        """Simple API call for general assistance"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "mistral-small-latest",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an AI assistant for an accounting application. Provide helpful, concise responses."
                    },
                    {
                        "role": "user",
                        "content": self.user_input
                    }
                ],
                "max_tokens": 500,
                "temperature": 0.1
            }
            
            response = requests.post(
                "https://api.mistral.ai/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=15
            )
            response.raise_for_status()
            
            result = response.json()['choices'][0]['message']['content'].strip()
            self.response_ready.emit(result)
            
        except Exception as e:
            self.error_occurred.emit(f"AI service error: {str(e)}")
