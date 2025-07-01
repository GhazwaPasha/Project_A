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
import re


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


# ReportsPlugin removed - functionality merged into UnifiedNavigationPlugin


# NavigationPlugin removed - functionality merged into UnifiedNavigationPlugin


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


# ExplanationPlugin removed - no help functionality needed


# ============================================================================
# COMMAND REGISTRY
# ============================================================================

# AICommandRegistry removed - no help commands needed


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
            UnifiedNavigationPlugin(),
            RemindersPlugin()
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
            # Step 1: State machine (for conversations)
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
        
        # report_generation handling removed - merged into navigation
        
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
        
        if not self.api_key:
            self.error_occurred.emit("API key not configured for advanced processing.")
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


class UnifiedNavigationPlugin(AIPlugin):
    """Unified plugin for all navigation - pages, reports, and account-specific views"""
    
    @property
    def name(self) -> str:
        return "UnifiedNavigationPlugin"
    
    def can_handle(self, user_input: str, context: dict) -> float:
        input_lower = user_input.lower()
        
        # Skip if it's a reminder request
        reminder_indicators = ['remind', 'reminder', 'set reminder', 'create reminder', 'schedule', 'recurring']
        if any(indicator in input_lower for indicator in reminder_indicators):
            return 0.0
        
        # Navigation indicators
        nav_words = ['show', 'open', 'go to', 'navigate', 'take me to', 'switch to', 'display', 'generate', 'create', 'run', 'produce']
        target_words = ['dashboard', 'journal', 'accounts', 'ledger', 'reports', 'reminders', 'page', 'statement', 'balance', 'trial', 'account', 'cash flow']
        
        has_nav = any(word in input_lower for word in nav_words)
        has_target = any(word in input_lower for word in target_words)
        
        # High confidence for specific account requests
        account_indicators = ['account', 'ledger for', 'show me', 'cash', 'bank', 'sales']
        has_account = any(indicator in input_lower for indicator in account_indicators)
        
        if has_nav and has_target:
            return 0.95
        elif has_account:
            return 0.9
        elif has_target:
            return 0.8
        return 0.0
    
    def execute(self, user_input: str, context: dict) -> AIResponse:
        input_lower = user_input.lower()
        
        # Extract navigation target and parameters
        target_page = self._extract_target_page(input_lower)
        parameters = self._extract_parameters(input_lower, target_page)
        
        return AIResponse(
            response_type='navigation',
            data={
                'page': target_page,
                'parameters': parameters
            },
            message=f"Opening {target_page.replace('_', ' ').title()}..."
        )
    
    def _extract_target_page(self, input_lower: str) -> str:
        """Extract the target page from user input"""
        
        # Page patterns with priority
        page_patterns = {
            # Reports (specific report types)
            'reports': [
                'income statement', 'profit loss', 'p&l', 'pnl',
                'balance sheet', 'financial position',
                'cash flow', 'cashflow',
                'trial balance', 'trial',
                'report', 'statement'
            ],
            
            # Account-specific navigation
            'ledger': [
                'ledger', 'account ledger', 'show account', 'open account',
                'cash', 'bank', 'sales', 'expense', 'revenue'
            ],
            
            # Direct page navigation
            'dashboard': ['dashboard', 'home', 'overview', 'main'],
            'journal': ['journal', 'entries', 'transactions'],
            'accounts': ['chart of accounts', 'accounts', 'account list'],
            'trial_balance': ['trial balance page'],
            'reminders': ['reminders', 'tasks', 'notifications'],
            'period_closing': ['period closing', 'month end', 'year end'],
            'settings': ['settings', 'preferences', 'config']
        }
        
        # Find best match
        for page, keywords in page_patterns.items():
            if any(keyword in input_lower for keyword in keywords):
                return page
        
        return 'dashboard'  # Default fallback
    
    def _extract_parameters(self, input_lower: str, target_page: str) -> dict:
        """Extract parameters based on target page and user input"""
        params = {}
        
        # Extract account name for ledger navigation
        if target_page == 'ledger':
            account_name = self._extract_account_name(input_lower)
            if account_name:
                params['account_name'] = account_name
                params['specific_account'] = True
        
        # Extract report type for reports page
        if target_page == 'reports':
            report_type = self._extract_report_type(input_lower)
            if report_type:
                params['report_type'] = report_type
        
        # Extract date range for applicable pages
        if target_page in ['reports', 'ledger', 'trial_balance']:
            date_params = self._extract_dates(input_lower)
            if date_params:
                params.update(date_params)
        
        return params
    
    def _extract_account_name(self, input_lower: str) -> str:
        """Extract account name using smart matching patterns and AccountMatcher"""
        patterns = [
            # Direct account references
            r'show (?:me )?(.+?)(?:\s+account|\s+ledger|$)',
            r'open (?:the )?(.+?)(?:\s+account|\s+ledger|$)', 
            r'(?:account|ledger) (?:for )?(.+?)(?:\s|$)',
            r'(.+?)(?:\s+account|\s+ledger)(?:\s|$)',
            
            # Specific account types
            r'(cash (?:in hand|in bank|at bank|on hand))',
            r'(accounts (?:receivable|payable))',
            r'(bank (?:account|checking|savings))',
            r'(sales (?:account|revenue))'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, input_lower)
            if match:
                raw_account_name = match.group(1).strip()
                # Clean up common words
                raw_account_name = re.sub(r'\b(the|a|an|show|open|me)\b', '', raw_account_name)
                raw_account_name = raw_account_name.strip()
                
                if raw_account_name and len(raw_account_name) > 1:
                    # Use AccountMatcher to find the best match
                    account_match = self._find_best_account_match(raw_account_name)
                    if account_match:
                        print(f"🎯 Smart account match: '{raw_account_name}' → '{account_match.account_name}' (confidence: {account_match.confidence:.2f})")
                        return account_match.account_name
                    else:
                        # Fallback to original extraction
                        return raw_account_name.title()
        
        return ""
    
    def _find_best_account_match(self, query: str):
        """Find best account match using AIAccountResolver"""
        try:
            from src.core.ai_account_resolver import AIAccountResolver
            resolver = AIAccountResolver()  # Use without accounting system for now (mock data)
            return resolver.find_best_match(query, min_confidence=0.6)
        except Exception as e:
            print(f"⚠️ AIAccountResolver error: {e}")
            return None
    
    def _extract_report_type(self, input_lower: str) -> str:
        """Extract report type from user input"""
        report_mapping = {
            'income_statement': ['income statement', 'profit loss', 'p&l', 'pnl'],
            'balance_sheet': ['balance sheet', 'financial position'],
            'cash_flow': ['cash flow', 'cashflow'],
            'trial_balance': ['trial balance', 'trial'],
            'general_ledger': ['general ledger', 'gl']
        }
        
        for report_id, keywords in report_mapping.items():
            if any(keyword in input_lower for keyword in keywords):
                return report_id
        
        return 'income_statement'  # Default
    
    def _extract_dates(self, input_lower: str) -> dict:
        """Extract date parameters from user input"""
        from datetime import datetime, timedelta
        
        today = datetime.now()
        
        if 'last month' in input_lower:
            last_month = today.replace(day=1) - timedelta(days=1)
            start_of_last_month = last_month.replace(day=1)
            return {
                'start_date': start_of_last_month.strftime('%Y-%m-%d'),
                'end_date': last_month.strftime('%Y-%m-%d')
            }
        elif 'this month' in input_lower or 'current month' in input_lower:
            start_of_month = today.replace(day=1)
            return {
                'start_date': start_of_month.strftime('%Y-%m-%d'),
                'end_date': today.strftime('%Y-%m-%d')
            }
        elif 'last year' in input_lower:
            last_year = today.year - 1
            return {
                'start_date': f'{last_year}-01-01',
                'end_date': f'{last_year}-12-31'
            }
        elif 'this year' in input_lower or 'current year' in input_lower:
            return {
                'start_date': f'{today.year}-01-01',
                'end_date': today.strftime('%Y-%m-%d')
            }
        
        return {}
