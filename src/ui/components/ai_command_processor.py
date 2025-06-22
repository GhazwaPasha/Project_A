"""
Modern AI Command Processor for Accounting Application
Provides intelligent natural language processing for navigation, reporting, and reminders
using the Mistral API for all natural language understanding.
"""

import json
import os
import re
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from PyQt6.QtCore import QObject, QThread, pyqtSignal, pyqtSlot
import requests


class AICommandProcessor(QObject):
    """
    Modern AI command processor that uses Mistral API for intelligent 
    natural language understanding and command execution.
    """
    
    # Signals for communication with UI
    response_ready = pyqtSignal(str)  # AI response text
    navigation_requested = pyqtSignal(str, dict)  # page, parameters
    report_requested = pyqtSignal(str, dict)  # report_type, parameters
    reminder_created = pyqtSignal(dict)  # reminder data
    error_occurred = pyqtSignal(str)  # error message
    processing_started = pyqtSignal()  # processing indicator
    processing_finished = pyqtSignal()  # processing complete
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        
        # Thread management
        self.processing_thread = None
        self.system_prompt = ""

        # Get Mistral API configuration from environment
        self.api_key = os.getenv('MISTRAL_API_KEY')
        self.api_base_url = "https://api.mistral.ai/v1/chat/completions"
        self.model = "mistral-small-latest"
        
        # Available pages and reports in the application
        self.available_pages = {
            'dashboard': 'Dashboard',
            'accounts': 'Chart of Accounts',
            'journal': 'Journal Entries',
            'ledger': 'General Ledger',
            'reports': 'Reports',
            'trial_balance': 'Trial Balance',
            'balance_sheet': 'Balance Sheet',
            'income_statement': 'Income Statement',
            'cash_flow': 'Cash Flow Statement',
            'budget': 'Budget Management',
            'settings': 'Settings'
        }
        
        self.available_reports = {
            'trial_balance': 'Trial Balance',
            'balance_sheet': 'Balance Sheet',
            'income_statement': 'Income Statement',
            'profit_loss': 'Profit & Loss Statement',
            'cash_flow': 'Cash Flow Statement',
            'financial_ratios': 'Financial Ratios',
            'budget_variance': 'Budget Variance Report',
            'account_aging': 'Account Aging Report'
        }
        
        # System prompts for different command types
        self.system_prompts = {
            'classify': self._get_classification_prompt(),
            'navigate': self._get_navigation_prompt(),
            'report': self._get_reporting_prompt(),
            'reminder': self._get_reminder_prompt()
        }
        
    def _get_classification_prompt(self) -> str:
        """Get the system prompt for command classification."""
        return """You are an AI assistant for an accounting application. Classify user commands into one of these categories:

NAVIGATION: User wants to go to a specific page or section
REPORTING: User wants to generate or view a financial report
REMINDER: User wants to create a reminder or task
GENERAL: General questions or help requests

Available pages: dashboard, accounts, journal, ledger, reports, trial_balance, balance_sheet, income_statement, cash_flow, budget, settings

Available reports: trial_balance, balance_sheet, income_statement, profit_loss, cash_flow, financial_ratios, budget_variance, account_aging

Respond with ONLY the category name (NAVIGATION, REPORTING, REMINDER, or GENERAL)."""

    def _get_navigation_prompt(self) -> str:
        """Get the system prompt for navigation commands."""
        return f"""You are helping with navigation in an accounting application. Parse the user's request and return a JSON object with:
- "page": the target page identifier
- "parameters": any additional parameters (like date ranges, filters)

Available pages: {', '.join(self.available_pages.keys())}

Example responses:
{{"page": "dashboard", "parameters": {{}}}}
{{"page": "journal", "parameters": {{"date_from": "2024-01-01", "date_to": "2024-01-31"}}}}
{{"page": "accounts", "parameters": {{"account_type": "assets"}}}}

If the request is unclear, use the most likely page and empty parameters.
Respond with ONLY valid JSON."""

    def _get_reporting_prompt(self) -> str:
        """Get the system prompt for reporting commands."""
        return f"""You are helping generate financial reports. Parse the user's request and return a JSON object with:
- "report_type": the type of report requested
- "parameters": report parameters (date ranges, filters, etc.)

Available reports: {', '.join(self.available_reports.keys())}

Example responses:
{{"report_type": "trial_balance", "parameters": {{"date": "2024-01-31"}}}}
{{"report_type": "income_statement", "parameters": {{"date_from": "2024-01-01", "date_to": "2024-12-31"}}}}
{{"report_type": "cash_flow", "parameters": {{"period": "quarterly", "year": 2024}}}}

If dates aren't specified, use current period. Respond with ONLY valid JSON."""

    def _get_reminder_prompt(self) -> str:
        """Get the system prompt for reminder creation."""
        return """You are helping create reminders for an accounting application. Parse the user's request and return a JSON object with:
- "title": brief reminder title
- "description": detailed description
- "due_date": due date in YYYY-MM-DD format
- "priority": "high", "medium", or "low"
- "category": "tax", "reporting", "reconciliation", "payment", or "general"

Examples:
{"title": "File quarterly taxes", "description": "Submit Q1 tax returns", "due_date": "2024-04-15", "priority": "high", "category": "tax"}
{"title": "Bank reconciliation", "description": "Reconcile January bank statements", "due_date": "2024-02-05", "priority": "medium", "category": "reconciliation"}

If no date is specified, assume it's due within a week. Respond with ONLY valid JSON."""

    def update_available_options(self, pages: list[str], reports: list[str]):
        """
        Update the available pages and reports, and regenerate system prompts.
        """
        self.available_pages = pages
        self.available_reports = reports
        self._generate_system_prompt()

    def _generate_system_prompt(self):
        """
        Regenerate the system prompts based on available pages and reports.
        """
        self.system_prompts['classify'] = self._get_classification_prompt()
        self.system_prompts['navigate'] = self._get_navigation_prompt()
        self.system_prompts['report'] = self._get_reporting_prompt()
        self.system_prompts['reminder'] = self._get_reminder_prompt()

    def process_command(self, command: str):
        """
        Processes a user command by starting a new AIProcessingThread.
        If a thread is already running, it emits an error and returns.
        If no API key is available, it uses a fallback mechanism.
        """
        if self.processing_thread and self.processing_thread.isRunning():
            logging.warning("AI command processing is already in progress.")
            self.error_occurred.emit("A command is already being processed. Please wait.")
            return

        self.processing_started.emit()

        if not self.api_key:
            self._process_command_no_api(command)
            self.processing_finished.emit()  # Fallback is synchronous
            return

        self.processing_thread = AIProcessingThread(
            command, 
            self.system_prompts, 
            self.api_key, 
            self.api_base_url, 
            self.model
        )
        
        # Connect signals from the new thread to handlers in this class
        self.processing_thread.classification_complete.connect(self._handle_classification)
        self.processing_thread.navigation_complete.connect(self._handle_navigation)
        self.processing_thread.reporting_complete.connect(self._handle_reporting)
        self.processing_thread.reminder_complete.connect(self._handle_reminder)
        self.processing_thread.general_response.connect(self._handle_general)
        self.processing_thread.error_occurred.connect(self._handle_error)
        self.processing_thread.finished.connect(self._on_processing_finished)
        
        self.processing_thread.start()

    @pyqtSlot()
    def _on_processing_finished(self):
        """
        Slot called when the AI processing thread has finished.
        Cleans up the thread object.
        """
        sender_thread = self.sender()
        logging.debug(f"Thread finished: {sender_thread}")
        
        self.processing_finished.emit()
        
        if sender_thread:
            sender_thread.deleteLater()

        if self.processing_thread is sender_thread:
            self.processing_thread = None

    def stop_processing(self):
        """Stops the processing thread if it's running."""
        if self.processing_thread and self.processing_thread.isRunning():
            self.logger.info("Stopping AI processing thread...")
            self.processing_thread.quit()
            # Wait for the thread to finish. The finished signal will trigger deleteLater.
            if not self.processing_thread.wait(2000):  # Wait up to 2 seconds
                self.logger.warning("AI thread did not quit gracefully, terminating.")
                self.processing_thread.terminate()
                self.processing_thread.wait() # Wait for termination
            self.logger.info("AI processing thread stopped.")

    def _process_command_no_api(self, command: str) -> None:
        """Handle commands when API key is not available using basic pattern matching."""
        self.logger.warning("No Mistral API key available, using basic pattern matching")
        
        command_lower = command.lower()
        
        # Basic navigation patterns
        if any(word in command_lower for word in ['go to', 'show', 'open', 'navigate']):
            for page_key, page_name in self.available_pages.items():
                if page_key.replace('_', ' ') in command_lower or page_name.lower() in command_lower:
                    self._handle_navigation(page_key, {})
                    return
            self.response_ready.emit("Please specify which page you'd like to navigate to.")
                
        # Basic reporting patterns
        elif any(word in command_lower for word in ['report', 'generate', 'show me']):
            for report_key, report_name in self.available_reports.items():
                if report_key.replace('_', ' ') in command_lower or report_name.lower() in command_lower:
                    self._handle_reporting(report_key, {})
                    return
            self.response_ready.emit("Please specify which report you'd like to generate.")
                
        # Basic reminder patterns
        elif any(word in command_lower for word in ['remind', 'reminder', 'task']):
            reminder_data = {
                'title': 'Manual Reminder',
                'description': command,
                'due_date': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'),
                'priority': 'medium',
                'category': 'general'
            }
            self._handle_reminder(reminder_data)
            
        else:
            self._handle_general("I'm here to help with navigation, reports, and reminders. Try 'go to dashboard' or 'generate trial balance'.")
    
    def _handle_classification(self, command: str, category: str) -> None:
        """Handle the result of command classification."""
        self.logger.info(f"Command classified as: {category}")
        # Classification complete, specific processing will follow
        
    def _handle_navigation(self, page: str, parameters: dict) -> None:
        """Handle navigation command results."""
        if page in self.available_pages:
            page_name = self.available_pages[page]
            self.navigation_requested.emit(page, parameters)
            
            param_info = ""
            if parameters:
                param_info = f" with parameters: {parameters}"
            
            self.response_ready.emit(f"Opening {page_name}...{param_info}")
        else:
            self.response_ready.emit(f"Unknown page: {page}. Available pages: {', '.join(self.available_pages.values())}")
    
    def _handle_reporting(self, report_type: str, parameters: dict) -> None:
        """Handle reporting command results."""
        if report_type in self.available_reports:
            report_name = self.available_reports[report_type]
            self.report_requested.emit(report_type, parameters)
            
            param_info = ""
            if parameters:
                param_info = f" with parameters: {parameters}"
                
            self.response_ready.emit(f"Generating {report_name}...{param_info}")
        else:
            self.response_ready.emit(f"Unknown report: {report_type}. Available reports: {', '.join(self.available_reports.values())}")
    
    def _handle_reminder(self, reminder_data: dict) -> None:
        """Handle reminder creation results."""
        try:
            # Validate reminder data
            required_fields = ['title', 'description', 'due_date', 'priority', 'category']
            if all(field in reminder_data for field in required_fields):
                self.reminder_created.emit(reminder_data)
                due_date = reminder_data['due_date']
                title = reminder_data['title']
                self.response_ready.emit(f"Reminder '{title}' created for {due_date}")
            else:
                self.response_ready.emit("Could not create reminder. Missing required information.")
        except Exception as e:
            self.logger.error(f"Error creating reminder: {e}")
            self.response_ready.emit("Error creating reminder. Please try again.")
    
    def _handle_general(self, response: str) -> None:
        """Handle general AI responses."""
        self.response_ready.emit(response)
    
    def _handle_error(self, error_message: str) -> None:
        """Handle processing errors."""
        self.logger.error(f"AI processing error: {error_message}")
        self.error_occurred.emit(error_message)
        self.response_ready.emit("Sorry, I encountered an error processing your request. Please try again.")
    
    def _processing_finished(self) -> None:
        """Handle processing completion."""
        self.processing_finished.emit()


class AIProcessingThread(QThread):
    """
    Separate thread for AI processing to avoid blocking the UI.
    """

    classification_complete = pyqtSignal(str, str)  # command, category
    navigation_complete = pyqtSignal(str, dict)  # page, parameters
    reporting_complete = pyqtSignal(str, dict)  # report_type, parameters
    reminder_complete = pyqtSignal(dict)  # reminder_data
    general_response = pyqtSignal(str)  # response text
    error_occurred = pyqtSignal(str)  # error message
    
    def __init__(self, command: str, system_prompts: dict, api_key: str, api_base_url: str, model: str):
        super().__init__()
        self.command = command
        self.system_prompts = system_prompts
        self.api_key = api_key
        self.api_base_url = api_base_url
        self.model = model
        self.logger = logging.getLogger(__name__)
    
    def run(self):
        """Main processing logic."""
        try:
            # Step 1: Classify the command
            category = self._classify_command(self.command)
            self.classification_complete.emit(self.command, category)
            
            # Step 2: Process based on category
            if category == "NAVIGATION":
                self._process_navigation()
            elif category == "REPORTING":
                self._process_reporting()
            elif category == "REMINDER":
                self._process_reminder()
            elif category == "GENERAL":
                self._process_general()
            else:
                self.error_occurred.emit(f"Unknown category: {category}")
                
        except Exception as e:
            self.logger.error(f"Processing thread error: {e}")
            self.error_occurred.emit(str(e))
    
    def _classify_command(self, command: str) -> str:
        """Classify the command using Mistral API."""
        response = self._call_mistral_api(self.system_prompts['classify'], command)
        return response.strip().upper()
    
    def _process_navigation(self):
        """Process navigation commands."""
        response = self._call_mistral_api(self.system_prompts['navigate'], self.command)
        try:
            data = json.loads(response)
            page = data.get('page', '')
            parameters = data.get('parameters', {})
            self.navigation_complete.emit(page, parameters)
        except json.JSONDecodeError:
            self.error_occurred.emit("Failed to parse navigation response")
    
    def _process_reporting(self):
        """Process reporting commands."""
        response = self._call_mistral_api(self.system_prompts['report'], self.command)
        try:
            data = json.loads(response)
            report_type = data.get('report_type', '')
            parameters = data.get('parameters', {})
            self.reporting_complete.emit(report_type, parameters)
        except json.JSONDecodeError:
            self.error_occurred.emit("Failed to parse reporting response")
    
    def _process_reminder(self):
        """Process reminder commands."""
        response = self._call_mistral_api(self.system_prompts['reminder'], self.command)
        try:
            data = json.loads(response)
            self.reminder_complete.emit(data)
        except json.JSONDecodeError:
            self.error_occurred.emit("Failed to parse reminder response")
    
    def _process_general(self):
        """Process general commands."""
        general_prompt = """You are an AI assistant for an accounting application. 
        Provide helpful, concise answers about accounting, the application features, or general assistance.
        Keep responses brief and professional."""
        
        response = self._call_mistral_api(general_prompt, self.command)
        self.general_response.emit(response)
    
    def _call_mistral_api(self, system_prompt: str, user_message: str) -> str:
        """Make a call to the Mistral API."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            "max_tokens": 500,
            "temperature": 0.1
        }
        
        try:
            response = requests.post(
                self.api_base_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            return data['choices'][0]['message']['content'].strip()
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {e}")
        except KeyError as e:
            raise Exception(f"Unexpected API response format: {e}")
        except Exception as e:
            raise Exception(f"API call error: {e}")