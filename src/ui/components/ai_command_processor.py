"""
AI Command Processor - Natural language command processing for the status bar
"""
import requests
import json
import os
from datetime import datetime
from PyQt6.QtCore import QObject, pyqtSignal, QThread
import threading


class AICommandProcessor(QObject):
    """Process natural language commands using LLM API"""
    
    # Signals
    command_processed = pyqtSignal(str, dict)  # response_text, action_data
    processing_started = pyqtSignal()
    processing_finished = pyqtSignal()
    error_occurred = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.api_key = os.getenv('MISTRAL_API_KEY')
        self.api_url = "https://api.mistral.ai/v1/chat/completions"
        
    def process_command(self, user_input: str, context: dict = None):
        """Process user command asynchronously"""
        self.processing_started.emit()
        
        # Run in separate thread to avoid blocking UI
        thread = threading.Thread(target=self._process_command_thread, args=(user_input, context))
        thread.daemon = True
        thread.start()
        
    def _process_command_thread(self, user_input: str, context: dict):
        """Process command in background thread"""
        try:
            # Create system prompt for accounting assistant
            system_prompt = self._create_system_prompt(context)
            
            # Send to LLM API
            response = self._call_llm_api(system_prompt, user_input)
            
            # Parse response
            action_data = self._parse_llm_response(response)
            
            # Emit result
            self.command_processed.emit(response, action_data)
            
        except Exception as e:
            self.error_occurred.emit(f"AI processing error: {str(e)}")
        finally:
            self.processing_finished.emit()
    
    def _create_system_prompt(self, context: dict):
        """Create system prompt with accounting context"""
        current_page = context.get('page', 'dashboard') if context else 'dashboard'
        
        return f"""You are an AI assistant for an accounting application. The user is currently on the {current_page} page.

You can help with:
1. NAVIGATION: Navigate to different pages (dashboard, journal, ledger, trial balance, reports, accounts, settings)
2. DATA_QUERY: Answer questions about financial data
3. REMINDER: Set reminders and tasks
4. NOTIFICATION: Display information to user

Respond ONLY in this JSON format:
{{
    "intent": "NAVIGATION|DATA_QUERY|REMINDER|NOTIFICATION",
    "action": "specific action to take",
    "parameters": {{
        "page": "page name for navigation",
        "query": "data query details",
        "reminder_text": "reminder description",
        "reminder_time": "when to remind (ISO format)",
        "recurring": "daily|weekly|monthly|none"
    }},
    "response": "Natural language response to user"
}}

Examples:
- "go to dashboard" → {{"intent": "NAVIGATION", "action": "navigate", "parameters": {{"page": "dashboard"}}, "response": "Going to dashboard"}}
- "show cash balance" → {{"intent": "DATA_QUERY", "action": "query_balance", "parameters": {{"query": "cash_balance"}}, "response": "Checking cash balance..."}}
- "remind me tomorrow to reconcile" → {{"intent": "REMINDER", "action": "set_reminder", "parameters": {{"reminder_text": "Reconcile accounts", "reminder_time": "tomorrow", "recurring": "none"}}, "response": "Reminder set for tomorrow"}}

Current page: {current_page}
User input: """

    def _call_llm_api(self, system_prompt: str, user_input: str):
        """Call Mistral API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "mistral-small-latest",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ],
            "temperature": 0.1,
            "max_tokens": 500
        }
        
        response = requests.post(self.api_url, headers=headers, json=data, timeout=10)
        response.raise_for_status()
        
        result = response.json()
        return result['choices'][0]['message']['content']
    
    def _parse_llm_response(self, response: str):
        """Parse LLM JSON response"""
        try:
            # Clean response and parse JSON
            response = response.strip()
            if response.startswith('```json'):
                response = response[7:]
            if response.endswith('```'):
                response = response[:-3]
            
            action_data = json.loads(response)
            return action_data
            
        except json.JSONDecodeError:
            # Fallback parsing
            return {
                "intent": "NOTIFICATION",
                "action": "show_message", 
                "parameters": {},
                "response": response
            }
