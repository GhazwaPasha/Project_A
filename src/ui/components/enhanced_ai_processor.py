"""
Enhanced AI Command Processor for Accounting Application
Provides context-aware, intelligent natural language processing with full application integration.
Uses Mistral API with rich context injection for accurate navigation, reporting, and task management.
"""

import json
import os
import re
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from PyQt6.QtCore import QObject, QThread, pyqtSignal, pyqtSlot
import requests


class ContextAwareAI(QObject):
    """
    Enhanced AI processor that understands application context and can perform
    complex navigation, reporting, and reminder management tasks.
    """
    
    # Enhanced signals for rich interactions
    response_ready = pyqtSignal(str)  # AI response text
    navigation_requested = pyqtSignal(str, dict)  # page, parameters
    report_requested = pyqtSignal(str, dict)  # report_type, parameters
    reminder_created = pyqtSignal(dict)  # reminder data
    action_executed = pyqtSignal(str, dict)  # action_type, results
    context_updated = pyqtSignal(dict)  # new context information
    error_occurred = pyqtSignal(str)  # error message
    processing_started = pyqtSignal()
    processing_finished = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        
        # Application context
        self.current_page = "dashboard"
        self.current_page_data = {}
        self.user_context = {}
        self.accounting_data = {}
        self.application_state = {}
        
        # Thread management
        self.processing_thread = None
        
        # Mistral API configuration
        self.api_key = os.getenv('MISTRAL_API_KEY')
        self.api_base_url = "https://api.mistral.ai/v1/chat/completions"
        self.model = "mistral-small-latest"
        
        # Application structure mapping
        self.page_mapping = {
            'dashboard': {'index': 0, 'name': 'Dashboard', 'key_data': ['summary', 'recent_transactions']},
            'journal': {'index': 1, 'name': 'Journal Entries', 'key_data': ['entries', 'filters']},
            'ledger': {'index': 2, 'name': 'General Ledger', 'key_data': ['accounts', 'balances']},
            'trial_balance': {'index': 3, 'name': 'Trial Balance', 'key_data': ['accounts', 'date_range']},
            'reports': {'index': 4, 'name': 'Reports', 'key_data': ['available_reports', 'parameters']},
            'accounts': {'index': 5, 'name': 'Chart of Accounts', 'key_data': ['hierarchy', 'balances']},
            'reminders': {'index': 6, 'name': 'Reminders & Tasks', 'key_data': ['reminders', 'tasks']},
            'period_closing': {'index': 7, 'name': 'Period Closing', 'key_data': ['status', 'checklist']},
            'settings': {'index': -1, 'name': 'Settings', 'key_data': ['preferences', 'system']}
        }
        
        self.report_types = {
            'trial_balance': {'title': 'Trial Balance', 'params': ['date_range']},
            'balance_sheet': {'title': 'Balance Sheet', 'params': ['date', 'comparison']},
            'income_statement': {'title': 'Income Statement', 'params': ['date_range', 'comparison']},
            'profit_loss': {'title': 'Profit & Loss', 'params': ['date_range', 'detail_level']},
            'cash_flow': {'title': 'Cash Flow Statement', 'params': ['date_range', 'method']},
            'financial_ratios': {'title': 'Financial Ratios', 'params': ['date_range']},
            'budget_variance': {'title': 'Budget Variance', 'params': ['period', 'budget_type']},
            'account_aging': {'title': 'Account Aging', 'params': ['as_of_date', 'account_type']}        }
        
    def update_context(self, context_type: str, data: dict):
        """Update application context for better AI understanding"""
        if context_type == "page":
            self.current_page = data.get('page', self.current_page)
            self.current_page_data = data.get('data', {})
        elif context_type == "user":
            self.user_context.update(data)
        elif context_type == "accounting":
            self.accounting_data.update(data)
        elif context_type == "application":
            self.application_state.update(data)
            
        self.context_updated.emit({context_type: data})
    
    def process_command(self, user_input: str):
        """Process user command with full context awareness"""
        print(f"🔍 AI Processor received command: '{user_input}'")  # Debug
        
        if not user_input.strip():
            print("❌ Empty input received")  # Debug
            self.error_occurred.emit("Please enter a command or question.")
            return
        
        # Check if API is available
        if not self.is_api_available():
            print("❌ Mistral API not available")  # Debug
            self.error_occurred.emit("AI service is not configured. Please check your API key.")
            return
            
        if self.processing_thread and self.processing_thread.isRunning():
            print("⚠️ Already processing a command")  # Debug
            self.error_occurred.emit("Please wait for the current request to complete.")
            return
            
        try:
            print("🚀 Starting AI processing...")  # Debug
            self.processing_started.emit()
            
            # Create processing thread
            self.processing_thread = AIProcessingThread(
                user_input=user_input,
                context=self._build_context(),
                ai_processor=self
            )
            
            # Connect signals
            self.processing_thread.response_ready.connect(self.response_ready.emit)
            self.processing_thread.navigation_requested.connect(self.navigation_requested.emit)
            self.processing_thread.report_requested.connect(self.report_requested.emit)
            self.processing_thread.reminder_created.connect(self.reminder_created.emit)
            self.processing_thread.action_executed.connect(self.action_executed.emit)
            self.processing_thread.error_occurred.connect(self.error_occurred.emit)
            self.processing_thread.finished.connect(self._on_processing_finished)
            
            print("🧵 Starting processing thread...")  # Debug
            self.processing_thread.start()
            
        except Exception as e:
            print(f"❌ Error starting AI processing: {e}")  # Debug
            self.processing_finished.emit()
            self.error_occurred.emit(f"Failed to start AI processing: {str(e)}")
    
    def _build_context(self) -> dict:
        """Build comprehensive context for AI processing"""
        return {
            'current_page': self.current_page,
            'current_page_data': self.current_page_data,
            'user_context': self.user_context,
            'accounting_data': self.accounting_data,
            'application_state': self.application_state,
            'page_mapping': self.page_mapping,
            'report_types': self.report_types,
            'current_datetime': datetime.now().isoformat(),
            'available_actions': self._get_available_actions()
        }
    
    def _get_available_actions(self) -> List[str]:
        """Get list of actions available from current page"""
        actions = ['navigate', 'generate_report', 'create_reminder', 'query_data']
        
        if self.current_page == 'reports':
            actions.extend(['set_date_range', 'export_report', 'save_report'])
        elif self.current_page == 'reminders':
            actions.extend(['edit_reminder', 'delete_reminder', 'mark_complete'])
        elif self.current_page in ['ledger', 'accounts']:
            actions.extend(['filter_accounts', 'view_account_detail', 'export_data'])
        elif self.current_page == 'journal':
            actions.extend(['create_entry', 'edit_entry', 'post_entries'])
            
        return actions
    
    def stop_processing(self):
        """Stop the current processing thread safely"""
        if self.processing_thread and self.processing_thread.isRunning():
            self.processing_thread.quit()
            self.processing_thread.wait(3000)  # Wait up to 3 seconds
            if self.processing_thread.isRunning():
                self.processing_thread.terminate()
                self.processing_thread.wait(1000)  # Wait up to 1 second for termination
            self.processing_thread = None
            print("🛑 AI processing thread stopped")
    
    def is_api_available(self) -> bool:
        """Check if Mistral API is available and configured"""
        if not self.api_key:
            return False
        
        # Don't call API just to check - assume it's available if key exists
        return len(self.api_key.strip()) > 10
    
    def get_status(self) -> dict:
        """Get current status of the AI processor"""
        return {
            'api_available': self.is_api_available(),
            'processing': self.processing_thread is not None and self.processing_thread.isRunning(),
            'current_page': self.current_page,
            'api_key_configured': bool(self.api_key)
        }
    
    def _on_processing_finished(self):
        """Handle processing thread completion"""
        print("✅ AI processing thread finished")  # Debug
        self.processing_finished.emit()
        
        # Clean up the thread reference
        if self.processing_thread:
            self.processing_thread.deleteLater()
            self.processing_thread = None


class AIProcessingThread(QThread):
    """Background thread for AI processing to keep UI responsive"""
    
    response_ready = pyqtSignal(str)
    navigation_requested = pyqtSignal(str, dict)
    report_requested = pyqtSignal(str, dict)
    reminder_created = pyqtSignal(dict)
    action_executed = pyqtSignal(str, dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, user_input: str, context: dict, ai_processor: ContextAwareAI):
        super().__init__()
        self.user_input = user_input
        self.context = context
        self.ai_processor = ai_processor
        self.api_key = ai_processor.api_key
        self.api_base_url = ai_processor.api_base_url
        self.model = ai_processor.model
    
    def run(self):
        """Main processing logic"""
        try:
            # Step 1: Classify intent with context
            intent = self._classify_intent()
            
            # Step 2: Process based on intent
            if intent == "NAVIGATION":
                self._process_navigation()
            elif intent == "REPORTING":
                self._process_reporting()
            elif intent == "REMINDER":
                self._process_reminder()
            elif intent == "DATA_QUERY":
                self._process_data_query()
            else:
                self._process_general()
                
        except Exception as e:
            self.error_occurred.emit(f"Processing error: {str(e)}")
    
    def _classify_intent(self) -> str:
        """Classify user intent with rich context"""
        system_prompt = f"""
You are an AI assistant for an accounting application. Analyze the user's request and classify it into one of these categories:

NAVIGATION: User wants to go to a specific page, view, or section
REPORTING: User wants to generate, view, or modify financial reports
REMINDER: User wants to create, edit, or manage reminders/tasks
DATA_QUERY: User wants to query specific accounting data (balances, transactions, etc.)
GENERAL: General questions, help requests, or other assistance

CURRENT CONTEXT:
- Current Page: {self.context['current_page']} ({self.context['page_mapping'][self.context['current_page']]['name']})
- Available Pages: {', '.join(self.context['page_mapping'].keys())}
- Available Reports: {', '.join(self.context['report_types'].keys())}
- Current Date/Time: {self.context['current_datetime']}

USER REQUEST: "{self.user_input}"

Respond with ONLY the category name (NAVIGATION, REPORTING, REMINDER, DATA_QUERY, or GENERAL).
"""
        
        try:
            response = self._call_mistral_api(system_prompt, "")
            return response.strip().upper()
        except Exception:
            return "GENERAL"
    
    def _process_navigation(self):
        """Process navigation requests with context awareness"""
        system_prompt = f"""
You are helping with navigation in an accounting application. Parse the user's request and determine:
1. The target page they want to navigate to
2. Any specific parameters or filters to apply
3. Provide a helpful response explaining what you're doing

CURRENT CONTEXT:
- Current Page: {self.context['current_page']} ({self.context['page_mapping'][self.context['current_page']]['name']})
- Available Pages: {json.dumps(self.context['page_mapping'], indent=2)}

USER REQUEST: "{self.user_input}"

Return a JSON object with:
{{
    "target_page": "page_identifier",
    "parameters": {{"param1": "value1", "param2": "value2"}},
    "response": "Natural language explanation of the navigation"
}}

If the user's request is unclear or the page doesn't exist, suggest alternatives.
"""
        
        try:
            response = self._call_mistral_api(system_prompt, "")
            data = json.loads(response)
            
            target_page = data.get('target_page', '')
            parameters = data.get('parameters', {})
            response_text = data.get('response', 'Navigating to requested page.')
            
            if target_page in self.context['page_mapping']:
                self.navigation_requested.emit(target_page, parameters)
                self.response_ready.emit(response_text)
            else:
                self.response_ready.emit(f"Page '{target_page}' not found. Available pages: {', '.join(self.context['page_mapping'].keys())}")
                
        except json.JSONDecodeError:
            self.error_occurred.emit("Failed to parse navigation response")
        except Exception as e:
            self.error_occurred.emit(f"Navigation processing error: {str(e)}")
    
    def _process_reporting(self):
        """Process report generation requests with intelligent parameter detection"""
        system_prompt = f"""
You are helping generate financial reports in an accounting application. Parse the user's request and determine:
1. The type of report they want
2. Date ranges or periods
3. Any specific parameters or filters
4. Provide a helpful response

CURRENT CONTEXT:
- Current Page: {self.context['current_page']}
- Available Reports: {json.dumps(self.context['report_types'], indent=2)}
- Current Date: {self.context['current_datetime']}

USER REQUEST: "{self.user_input}"

Return a JSON object with:
{{
    "report_type": "report_identifier",
    "parameters": {{
        "date_range": {{"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}},
        "other_params": "values"
    }},
    "response": "Natural language explanation of the report generation"
}}

If no specific dates are mentioned, suggest reasonable defaults (current month, quarter, etc.).
"""
        
        try:
            response = self._call_mistral_api(system_prompt, "")
            data = json.loads(response)
            
            report_type = data.get('report_type', '')
            parameters = data.get('parameters', {})
            response_text = data.get('response', 'Generating requested report.')
            
            if report_type in self.context['report_types']:
                self.report_requested.emit(report_type, parameters)
                self.response_ready.emit(response_text)
            else:
                self.response_ready.emit(f"Report type '{report_type}' not available. Available reports: {', '.join(self.context['report_types'].keys())}")
                
        except json.JSONDecodeError:
            self.error_occurred.emit("Failed to parse reporting response")
        except Exception as e:
            self.error_occurred.emit(f"Reporting processing error: {str(e)}")
    
    def _process_reminder(self):
        """Process reminder creation with smart date/time parsing"""
        system_prompt = f"""
You are helping create reminders in an accounting application. Parse the user's request and extract:
1. Title/description of the reminder
2. Due date and time
3. Whether it should recur
4. Priority level

CURRENT CONTEXT:
- Current Date/Time: {self.context['current_datetime']}

USER REQUEST: "{self.user_input}"

Return a JSON object with:
{{
    "title": "Brief title for the reminder",
    "description": "Detailed description if provided",
    "due_datetime": "YYYY-MM-DD HH:MM",
    "recurring": "none|daily|weekly|monthly|quarterly|yearly",
    "priority": "low|medium|high",
    "response": "Confirmation message for the user"
}}

Parse dates intelligently - "tomorrow", "next week", "end of month", etc.
For accounting reminders, suggest appropriate recurring patterns.
"""
        
        try:
            response = self._call_mistral_api(system_prompt, "")
            data = json.loads(response)
            
            # Add unique ID for the reminder
            data['id'] = f"reminder_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            data['created_datetime'] = datetime.now().isoformat()
            data['completed'] = False
            
            response_text = data.get('response', 'Reminder created successfully.')
            
            self.reminder_created.emit(data)
            self.response_ready.emit(response_text)
            
        except json.JSONDecodeError:
            self.error_occurred.emit("Failed to parse reminder response")
        except Exception as e:
            self.error_occurred.emit(f"Reminder processing error: {str(e)}")
    
    def _process_data_query(self):
        """Process data queries with context from current page"""
        system_prompt = f"""
You are answering questions about accounting data. Use the available context to provide accurate information.

CURRENT CONTEXT:
- Current Page: {self.context['current_page']} ({self.context['page_mapping'][self.context['current_page']]['name']})
- Page Data: {json.dumps(self.context['current_page_data'], indent=2)}
- Accounting Data: {json.dumps(self.context['accounting_data'], indent=2)}

USER QUERY: "{self.user_input}"

Provide a helpful, accurate response based on the available data. If you need more specific data that isn't available in the context, explain what information would be needed and suggest how the user can find it in the application.

Be specific and actionable in your response.
"""
        
        try:
            response = self._call_mistral_api(system_prompt, "")
            self.response_ready.emit(response)
            
        except Exception as e:
            self.error_occurred.emit(f"Data query processing error: {str(e)}")
    
    def _process_general(self):
        """Process general questions and help requests"""
        system_prompt = f"""
You are an AI assistant for an accounting application. Provide helpful, professional guidance.

CURRENT CONTEXT:
- User is currently on: {self.context['current_page']} page
- Available features: Navigation, Report Generation, Reminder Management, Data Queries

USER REQUEST: "{self.user_input}"

Provide a helpful response that:
1. Answers their question clearly
2. Suggests specific actions they can take in the application
3. References relevant features or pages when appropriate

Keep responses concise but informative.
"""
        try:
            response = self._call_mistral_api(system_prompt, "")
            self.response_ready.emit(response)
            
        except Exception as e:
            self.error_occurred.emit(f"General processing error: {str(e)}")
    
    def _call_mistral_api(self, system_prompt: str, user_message: str = "") -> str:
        """Make a call to the Mistral API with enhanced error handling"""
        if not self.api_key:
            raise Exception("Mistral API key not configured")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        messages = [{"role": "system", "content": system_prompt}]
        if user_message:
            messages.append({"role": "user", "content": user_message})
        
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": 1000,
            "temperature": 0.1
        }
        
        try:
            print(f"🌐 Making API call to Mistral...")  # Debug
            response = requests.post(
                self.api_base_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            result = data['choices'][0]['message']['content'].strip()
            print(f"✅ API call successful")  # Debug
            return result
            
        except requests.exceptions.Timeout:
            raise Exception("Request timed out. Please try again.")
        except requests.exceptions.ConnectionError:
            raise Exception("Unable to connect to AI service. Please check your internet connection.")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                raise Exception("Invalid API key. Please check your Mistral API configuration.")
            elif e.response.status_code == 429:
                raise Exception("API rate limit exceeded. Please wait a moment and try again.")
            else:
                raise Exception(f"API request failed: {e}")
        except KeyError as e:
            raise Exception(f"Unexpected API response format: {e}")
        except Exception as e:
            raise Exception(f"AI service error: {e}")
