"""
Simple AI Status Bar - Enhanced with dynamic status display and AI integration
The status bar itself becomes the input field when expanded
"""
from PyQt6.QtWidgets import QLineEdit, QApplication
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtSignal
from PyQt6.QtGui import QFont, QFontMetrics, QPainter, QPalette
import threading
import time
import random
import json
import os
from datetime import datetime, timedelta

class SimpleAIStatusBar(QLineEdit):
    """Enhanced AI status bar with dynamic status display, notifications, and motivational messages"""
    ai_command_submitted = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.is_expanded = False
        self.is_processing = False
        self.placeholder_text = "🤖 AI Assistant - Ask me anything!"
        
        # Initialize enhanced AI processor directly
        from .enhanced_ai_processor import ContextAwareAI
        self.ai_processor = ContextAwareAI(parent)
        self._setup_ai_connections()
        
        # Dynamic status management
        self.current_state = "idle"  # idle, processing, notification, background_task
        self.last_activity_time = datetime.now()
        self.last_interaction_time = datetime.now() - timedelta(hours=1)
        self.current_page_context = None
        self.unread_notifications_count = 0
        self.background_processes = []
        
        # Enhanced features
        self.smart_suggestions_enabled = True
        self.contextual_help_enabled = True
        self.last_suggestion_time = datetime.now() - timedelta(hours=1)
        
        # Conversation memory
        self.recent_commands = []
        self.user_preferences = {
            'helpful_tips': True,
            'quick_actions': True,
            'contextual_suggestions': True
        }
        
        # Setup UI
        self._setup_ui()
        self._setup_animations()
        self._apply_styling()
        self._setup_dynamic_status()
    
    def _setup_ai_connections(self):
        """Setup AI processor signal connections"""
        self.ai_processor.response_ready.connect(self.handle_ai_response)
        self.ai_processor.navigation_requested.connect(self._handle_navigation)
        self.ai_processor.report_requested.connect(self._handle_report_request)
        self.ai_processor.reminder_created.connect(self._handle_reminder_created)
        self.ai_processor.processing_started.connect(self.handle_processing_started)
        self.ai_processor.processing_finished.connect(self.handle_processing_finished)
        self.ai_processor.error_occurred.connect(self.handle_ai_error)
    
    def _handle_navigation(self, page: str, params: dict):
        """Handle navigation requests"""
        self.setText(f"📍 Navigating to {page.replace('_', ' ').title()}...")
        
        # Forward to parent window
        if hasattr(self.parent_window, 'navigate_to_page'):
            self.parent_window.navigate_to_page(page, params)
        elif hasattr(self.parent_window, '_handle_ai_navigation'):
            self.parent_window._handle_ai_navigation(page, params)
    
    def _handle_report_request(self, report_type: str, params: dict):
        """Handle report generation requests"""
        self.setText(f"📊 Generating {report_type.replace('_', ' ').title()}...")
        
        # Forward to parent window
        if hasattr(self.parent_window, 'generate_report'):
            self.parent_window.generate_report(report_type, params)
        elif hasattr(self.parent_window, '_handle_ai_report_request'):
            self.parent_window._handle_ai_report_request(report_type, params)
    
    def _handle_reminder_created(self, reminder_data: dict):
        """Handle reminder creation"""
        title = reminder_data.get('title', 'Reminder')
        self.setText(f"✅ Created: {title}")
        
        # Forward to parent window
        if hasattr(self.parent_window, 'add_reminder'):
            self.parent_window.add_reminder(reminder_data)
        elif hasattr(self.parent_window, '_handle_ai_reminder_creation'):
            self.parent_window._handle_ai_reminder_creation(reminder_data)
        
    def _setup_dynamic_status(self):
        """Setup timers and monitoring for dynamic status display"""
        # Main status update timer - more frequent for better responsiveness
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._update_dynamic_status)
        self.status_timer.start(60000)  # 1 minute for responsive updates
        
        # Notification checker - checks every 15 seconds for timely notifications
        self.notification_timer = QTimer()
        self.notification_timer.timeout.connect(self._check_notifications)
        self.notification_timer.start(15000)  # 15 seconds for responsive notifications
        
        # Smart suggestions timer - provides contextual help
        self.suggestion_timer = QTimer()
        self.suggestion_timer.timeout.connect(self._show_smart_suggestion)
        self.suggestion_timer.start(300000)  # 5 minutes for helpful suggestions
        
        # Initial status set
        self._update_dynamic_status()
        
    def _setup_ui(self):
        """Setup the UI components"""
        # Set initial properties - start as a read-only status display
        self.setReadOnly(True)
        self.setText(self.placeholder_text)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setCursor(Qt.CursorShape.PointingHandCursor)        # Set initial size - compact for title bar
        self.setFixedHeight(30)  # Reduced height to 30px
        self.setFixedWidth(350)
        
        # Connect events
        self.returnPressed.connect(self._process_input)
        
    def _setup_animations(self):
        """Setup smooth animations"""
        # Width animation for smooth expansion
        self.width_animation = QPropertyAnimation(self, b"maximumWidth")
        self.width_animation.setDuration(300)
        self.width_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Width animation for minimum width to ensure proper center expansion
        self.min_width_animation = QPropertyAnimation(self, b"minimumWidth")
        self.min_width_animation.setDuration(300)
        self.min_width_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
    def _apply_styling(self):
        """Apply styling to match date range selector custom date fields"""
        self.setStyleSheet("""
            QLineEdit {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(0, 0, 0, 0.3);
                border-radius: 8px;
                color: white;
                font-size: 12px;
                font-family: 'Segoe UI', system-ui, sans-serif;
                font-weight: 600;
                padding: 4px 12px;
                selection-background-color: rgba(100, 181, 246, 0.3);
                outline: none;
                text-align: center;
                /* Spotlight effect */
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 rgba(255, 255, 255, 0.12),
                    stop: 0.3 rgba(255, 255, 255, 0.08),
                    stop: 0.7 rgba(255, 255, 255, 0.08),
                    stop: 1 rgba(255, 255, 255, 0.04));
                box-shadow: 
                    inset 0 1px 0 rgba(255, 255, 255, 0.2),
                    0 0 20px rgba(100, 181, 246, 0.15),
                    0 2px 8px rgba(0, 0, 0, 0.1);
            }
            
            QLineEdit:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 rgba(255, 255, 255, 0.16),
                    stop: 0.3 rgba(255, 255, 255, 0.12),
                    stop: 0.7 rgba(255, 255, 255, 0.12),
                    stop: 1 rgba(255, 255, 255, 0.08));
                border: 1px solid rgba(100, 181, 246, 0.3);
                outline: none;
                box-shadow: 
                    inset 0 1px 0 rgba(255, 255, 255, 0.3),
                    0 0 25px rgba(100, 181, 246, 0.25),
                    0 2px 12px rgba(0, 0, 0, 0.15);
            }
            
            QLineEdit:focus {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 rgba(255, 255, 255, 0.16),
                    stop: 0.3 rgba(255, 255, 255, 0.12),
                    stop: 0.7 rgba(255, 255, 255, 0.12),
                    stop: 1 rgba(255, 255, 255, 0.08));
                border: 1px solid rgba(100, 181, 246, 0.5);
                color: white;
                outline: none;
                text-align: left;
                box-shadow: 
                    inset 0 1px 0 rgba(255, 255, 255, 0.3),
                    0 0 30px rgba(100, 181, 246, 0.35),
                    0 2px 16px rgba(0, 0, 0, 0.2);
            }
            
            QLineEdit[readOnly="true"] {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 rgba(255, 255, 255, 0.12),
                    stop: 0.3 rgba(255, 255, 255, 0.08),
                    stop: 0.7 rgba(255, 255, 255, 0.08),
                    stop: 1 rgba(255, 255, 255, 0.04));
                border: 1px solid rgba(0, 0, 0, 0.3);
                color: white;
                outline: none;
                text-align: center;
                box-shadow: 
                    inset 0 1px 0 rgba(255, 255, 255, 0.2),
                    0 0 20px rgba(100, 181, 246, 0.15),
                    0 2px 8px rgba(0, 0, 0, 0.1);
            }
            
            QLineEdit[readOnly="true"]:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 rgba(255, 255, 255, 0.16),
                    stop: 0.3 rgba(255, 255, 255, 0.12),
                    stop: 0.7 rgba(255, 255, 255, 0.12),
                    stop: 1 rgba(255, 255, 255, 0.08));
                border: 1px solid rgba(100, 181, 246, 0.3);
                outline: none;
                text-align: center;
                box-shadow: 
                    inset 0 1px 0 rgba(255, 255, 255, 0.3),
                    0 0 25px rgba(100, 181, 246, 0.25),
                    0 2px 12px rgba(0, 0, 0, 0.15);
            }
        """)
        
    def mousePressEvent(self, event):
        """Handle mouse click to expand"""
        if not self.is_expanded and not self.is_processing and self.isReadOnly():
            self._expand_for_input()
        else:
            super().mousePressEvent(event)
            
    def focusOutEvent(self, event):
        """Handle losing focus - collapse if not processing"""
        super().focusOutEvent(event)
        if self.is_expanded and not self.text().strip() and not self.is_processing:
            QTimer.singleShot(50, self._collapse_to_normal)
            
    def _expand_for_input(self):
        """Expand the status bar to become an input field"""
        self.is_expanded = True
        
        # Transform into input field
        self.setReadOnly(False)
        self.clear()
        self.setPlaceholderText("Type your question...")
        self.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.setCursor(Qt.CursorShape.IBeamCursor)
        self.setFocus()
        
        # Animate width expansion from center
        self.width_animation.setStartValue(350)
        self.width_animation.setEndValue(500)
        self.min_width_animation.setStartValue(350)
        self.min_width_animation.setEndValue(500)
        
        # Start both animations simultaneously for center expansion
        self.width_animation.start()
        self.min_width_animation.start()
        
        # Update fixed width after animation
        QTimer.singleShot(300, lambda: self.setFixedWidth(500))        
    def _process_input(self):
        """Process user input using enhanced AI processor directly."""
        user_input = self.text().strip()
        if not user_input or self.is_processing:
            return
        
        # Store command in recent history
        self.recent_commands.append({
            'command': user_input,
            'timestamp': datetime.now(),
            'page_context': self.current_page_context
        })
        
        # Keep only last 10 commands
        if len(self.recent_commands) > 10:
            self.recent_commands.pop(0)
        
        # Update interaction time
        self.last_interaction_time = datetime.now()
        
        # Set processing state
        self.is_processing = True
        self.setText("🤖 AI is thinking...")
        self.setReadOnly(True)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setCursor(Qt.CursorShape.ArrowCursor)
        
        # Get current context and process with enhanced AI
        context = self._get_current_context()
        self.ai_processor.update_context("application", context)
        self.ai_processor.process_command(user_input)
        
        # Also emit signal for backward compatibility
        self.ai_command_submitted.emit(user_input)
    
    def _get_current_context(self) -> dict:
        """Get current application context for AI processing"""
        context = {
            'current_page': self.current_page_context or 'dashboard',
            'user_role': 'accountant',  # Default role
            'timestamp': datetime.now().isoformat(),
            'recent_commands': self.recent_commands[-5:] if self.recent_commands else []
        }
        
        # Add parent window context if available
        if hasattr(self.parent_window, 'get_current_context'):
            parent_context = self.parent_window.get_current_context()
            context.update(parent_context)
        elif hasattr(self.parent_window, '_get_current_context'):
            parent_context = self.parent_window._get_current_context()
            context.update(parent_context)
        
        return context

    def show_processing_indicator(self):
        """Display a processing message."""
        self.is_processing = True
        self.setReadOnly(True)
        self.setText("Processing...")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setCursor(Qt.CursorShape.ArrowCursor)

    def hide_processing_indicator(self):
        """Hide the processing message and collapse the bar."""
        self.is_processing = False
        self._collapse_to_normal()

    def set_ai_response(self, response: str):
        """Display the AI's final response message."""
        self.is_processing = False
        self.setText(response)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        # Collapse after a delay to allow user to read the response
        QTimer.singleShot(4000, self._collapse_to_normal)

    def set_error_message(self, error_message: str):
        """Display an error message."""
        self.is_processing = False
        self.setText(f"Error: {error_message}")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        # Collapse after a delay
        QTimer.singleShot(5000, self._collapse_to_normal)

    def _collapse_to_normal(self):
        """Collapse the input field back to a status display"""
        self.is_expanded = False
        self.is_processing = False
        
        # Restore read-only status display
        self.setReadOnly(True)
        self.setPlaceholderText("") # Clear placeholder
        self.setText("Ask AI anything...") # Reset to default
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clearFocus()
        
        # Animate width collapse
        self.width_animation.setStartValue(self.width())
        self.width_animation.setEndValue(350)
        self.min_width_animation.setStartValue(self.width())
        self.min_width_animation.setEndValue(350)
        
        self.width_animation.start()
        self.min_width_animation.start()
          # Reset fixed width after animation
        QTimer.singleShot(300, lambda: self.setFixedWidth(350))
    
    def set_context(self, page_name, context_data=None):
        """Set the current page context for the AI status bar"""
        self.current_page_context = page_name.lower() if page_name else None
        if not self.is_expanded and not self.is_processing:
            self._update_dynamic_status()
    
    def set_processing_status(self, status_message):
        """Set a custom processing status message"""
        if self.is_processing:
            self.setText(status_message)
    
    def update_activity(self):
        """Update last activity time - call this when user interacts with the app"""
        self.last_activity_time = datetime.now()
    
    def _get_intelligent_status_messages(self):
        """Get intelligent status messages that provide real value"""
        return {
            "productivity_tips": [
                "💡 Pro tip: Use keyboard shortcuts - Ctrl+N for new entries",
                "⚡ Speed up work: Try voice commands like 'create expense entry'",
                "🔍 Quick search: Press Ctrl+F to find any transaction instantly",
                "📊 Save time: Ask me to 'generate standard reports' automatically"
            ],
            "accounting_insights": [
                "📚 Did you know? I can explain any accounting principle instantly",
                "⚖️ Remember: Assets = Liabilities + Equity (fundamental equation)",
                "💡 Tip: Regular reconciliation prevents month-end surprises",
                "📈 Insight: Trend analysis reveals business patterns over time"
            ],
            "feature_highlights": [
                "🆕 Try the new AI features: 'explain this transaction'",
                "🔧 Power user tip: Ask me to 'automate recurring entries'",
                "📋 Organization tip: I can help categorize and clean up accounts",
                "🔄 Sync tip: I can monitor and explain sync status issues"
            ]
        }
    
    def _get_context_messages(self):
        """Get intelligent, actionable context-aware messages based on current page"""
        return {
            "dashboard": [
                "🤖 I can explain these metrics or help you navigate anywhere",
                "💡 Ask me: 'What do these numbers mean?' or 'Show trial balance'",
                "📊 Try: 'Generate this month's report' or 'Explain cash flow'",
                "⚡ Quick navigation: 'Open accounts' or 'Show journal'"
            ],
            "journal": [
                "📝 I can help create entries, explain rules, or find transactions",
                "💡 Try: 'How to reverse this entry?' or 'Create expense entry'",
                "⚖️ Ask: 'Why don't debits equal credits?' or 'Explain posting'",
                "🔍 Search: 'Find entry for [vendor]' or 'Show last week entries'"
            ],
            "accounts": [
                "🗂️ I can explain account types, help organize, or check balances",
                "💡 Try: 'What type of account is this?' or 'Show account history'",
                "🔍 Ask: 'How to reconcile accounts?' or 'Find duplicate accounts'",
                "⚡ Quick: 'Create new account' or 'Merge similar accounts'"
            ],
            "trial_balance": [
                "⚖️ I can troubleshoot balance issues or explain discrepancies",
                "💡 Try: 'Why doesn't this balance?' or 'Explain trial balance'",
                "🔍 Ask: 'Find the error' or 'Show largest differences'",
                "📊 Quick: 'Export data' or 'Compare to last month'"
            ],
            "reports": [
                "📈 I can help generate reports, explain ratios, or customize formats",
                "💡 Try: 'Create P&L report' or 'Explain gross profit margin'",
                "🔍 Ask: 'Compare years' or 'Show trends'",
                "⚡ Quick: 'Email report' or 'Save as PDF'"
            ],
            "ledger": [
                "📚 I can help navigate entries, explain postings, or find transactions",
                "💡 Try: 'Explain this posting' or 'Show account activity'",
                "🔍 Ask: 'Find transaction by amount' or 'Show adjustments'",
                "⚡ Quick: 'Filter by date' or 'Sort by amount'"
            ],
            "reminders": [
                "🔔 I can help manage tasks, set deadlines, or explain priorities",
                "💡 Try: 'Create month-end reminder' or 'Show overdue tasks'",
                "🔍 Ask: 'What's due this week?' or 'Explain task types'",
                "⚡ Quick: 'Mark complete' or 'Snooze reminder'"
            ],
            "period_closing": [
                "📅 I can guide through closing steps or troubleshoot issues",
                "💡 Try: 'Help me close the month' or 'Check closing requirements'",
                "🔍 Ask: 'What's blocking closure?' or 'Show closing checklist'",
                "⚡ Quick: 'Run close reports' or 'Verify all entries'"
            ]
        }
    
    def _update_dynamic_status(self):
        """Update the status bar with intelligent, context-aware content"""
        try:
            if self.is_expanded or self.is_processing:
                return
                
            current_time = datetime.now()
            
            # Priority 1: Background processes
            if self.background_processes:
                self._show_background_process_status()
                return
                
            # Priority 2: Unread notifications
            if self.unread_notifications_count > 0:
                self._show_notification_reminder()
                return
            
            # Priority 3: Context-based suggestions (smart help)
            context_suggestion = self._get_recent_context_suggestions()
            if context_suggestion:
                self.setText(context_suggestion)
                self.placeholder_text = context_suggestion
                return
            
            # Priority 4: Time-based helpful tips
            time_since_interaction = current_time - self.last_interaction_time
            if time_since_interaction.total_seconds() > 1800:  # 30 minutes since last interaction
                helpful_tip = self._get_helpful_tip()
                if helpful_tip:
                    self.setText(helpful_tip)
                    self.placeholder_text = helpful_tip
                    return
            
            # Default: Context-aware status
            self._show_context_message()
                
        except Exception as e:
            # Silent fail - don't disrupt the UI, but log for debugging
            print(f"AI Status Bar update error: {e}")
            self.setText("🤖 AI Assistant - Ask me anything!")
            self.placeholder_text = "🤖 AI Assistant - Ask me anything!"

    def _get_helpful_tip(self) -> str:
        """Get helpful tips based on time and context"""
        tips = {
            'general': [
                "💡 Tip: Try asking 'help me with journal entries'",
                "🔍 Did you know? I can explain any accounting concept",
                "⚡ Quick tip: Say 'show accounts' to navigate instantly",
                "📊 Pro tip: Ask 'how do I...' for step-by-step guidance"
            ],
            'dashboard': [
                "💡 From here, try: 'show me key metrics'",
                "📈 Ask me: 'how to read these charts?'",
                "🔍 Try: 'explain cash flow trends'"
            ],
            'journal': [
                "💡 Need help? Try: 'how to create journal entry'",
                "⚖️ Ask: 'explain debit and credit rules'",
                "🔍 Try: 'find entry from last month'"
            ],
            'reports': [
                "💡 Try: 'generate profit and loss report'",
                "📊 Ask: 'explain this financial ratio'",
                "🔍 Try: 'compare periods'"
            ]
        }
        
        # Get context-specific tips if available
        context_tips = tips.get(self.current_page_context or 'general', tips['general'])
        return random.choice(context_tips)
    
    def _show_intelligent_insight(self):
        """Display intelligent insights based on context and usage patterns"""
        if not self.smart_suggestions_enabled:
            return
            
        insights = self._get_intelligent_status_messages()
        current_hour = datetime.now().hour
        
        # Choose insight category based on time and context
        if self.current_page_context in ['journal', 'accounts']:
            category = random.choice(["accounting_insights", "productivity_tips"])
        elif 9 <= current_hour < 12:  # Morning
            category = "productivity_tips"
        elif 12 <= current_hour < 17:  # Afternoon
            category = random.choice(["feature_highlights", "accounting_insights"])
        else:  # Evening
            category = "accounting_insights"
        
        if category in insights:
            message = random.choice(insights[category])
            self.setText(message)
            self.placeholder_text = message
            self.last_suggestion_time = datetime.now()
            
            # Reset to normal after 15 seconds (longer for educational content)
            QTimer.singleShot(15000, self._reset_to_default_message)
    
    def _show_feature_highlight(self):
        """Show helpful feature highlights and tips"""
        if not self.contextual_help_enabled:
            return
            
        feature_highlights = [
            "💡 New: Ask me 'explain this account type' for instant definitions",
            "⚡ Tip: Try 'compare this month to last month' for quick analysis",
            "🔍 Feature: Say 'find transactions over $1000' for smart filtering",
            "📊 Pro tip: I can generate and email reports with 'send P&L to [email]'",
            "🤖 Advanced: Ask complex questions like 'why is my gross margin low?'"
        ]
        
        message = random.choice(feature_highlights)
        self.setText(message)
        self.placeholder_text = message
        
        # Reset to normal after 12 seconds
        QTimer.singleShot(12000, self._reset_to_default_message)
    
    def _show_notification_reminder(self):
        """Show intelligent notification reminder with context"""
        if self.unread_notifications_count == 1:
            message = f"🔔 1 unread notification - I can help you review it"
        elif self.unread_notifications_count <= 5:
            message = f"🔔 {self.unread_notifications_count} notifications waiting - ask me to 'show notifications'"
        else:
            message = f"🔔 {self.unread_notifications_count} notifications - try 'prioritize my notifications'"
            
        self.setText(message)
        self.placeholder_text = message
    
    def _show_background_process_status(self):
        """Show intelligent background process status with helpful context"""
        if not self.background_processes:
            return
            
        # Show the most important/recent process
        process = self.background_processes[-1]
        process_message = process.get('message', 'Background process running')
        progress = process.get('progress', '')
        
        # Add helpful context based on process type
        if 'sync' in process_message.lower():
            message = f"🔄 {process_message} {progress} - Ask me about sync issues"
        elif 'backup' in process_message.lower():
            message = f"💾 {process_message} {progress} - Your data is being protected"
        elif 'report' in process_message.lower():
            message = f"📊 {process_message} {progress} - I can explain the results"
        else:
            message = f"⚙️ {process_message} {progress} - Ask me for details"
        
        self.setText(message)
        self.placeholder_text = message
    
    def _show_context_message(self):
        """Show intelligent context-aware message based on current page"""
        messages = self._get_context_messages()
        
        if self.current_page_context and self.current_page_context in messages:
            message = random.choice(messages[self.current_page_context])
        else:
            # Enhanced default messages with actionable suggestions
            default_messages = [
                "🤖 AI Assistant ready! Try: 'help me with...' or 'show me...'",
                "💡 I understand accounting - ask about debits, credits, or reports",
                "⚡ Quick navigation: 'open journal', 'show accounts', 'run trial balance'",
                "🔍 Need help? Try: 'explain [concept]' or 'how do I [task]?'",
                "📊 I can generate reports, explain metrics, or guide you through tasks"
            ]
            message = random.choice(default_messages)
            
        self.setText(message)
        self.placeholder_text = message
    
    def _reset_to_default_message(self):
        """Reset to default dynamic message"""
        if not self.is_expanded and not self.is_processing:
            self._update_dynamic_status()
    
    def _check_notifications(self):
        """Check for new notifications and update count"""
        try:
            # Check if reminders_data.json exists and get unread count
            reminders_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'reminders_data.json')
            if os.path.exists(reminders_file):
                with open(reminders_file, 'r') as f:
                    reminders_data = json.load(f)
                    
                # Count unread notifications (assuming there's an 'unread' field)
                unread_count = 0
                for reminder in reminders_data.get('reminders', []):
                    if reminder.get('status') == 'active' and not reminder.get('acknowledged', False):
                        unread_count += 1
                        
                if unread_count != self.unread_notifications_count:
                    old_count = self.unread_notifications_count
                    self.unread_notifications_count = unread_count
                    
                    # Show new notification alert if count increased
                    if unread_count > old_count and not self.is_expanded:
                        self._show_new_notification_alert()
                        
        except Exception as e:
            # Silent fail - don't disrupt the UI
            pass
    
    def _show_new_notification_alert(self):
        """Show intelligent alert for new notification with actionable suggestions"""
        alert_messages = [
            "🔔 New notification! Ask me to 'read notifications' or 'show important ones'",
            "✨ Something new arrived! Try 'what's the notification about?' for details",
            "🔔 Fresh update! I can help you 'prioritize notifications' or 'mark as read'"
        ]
        
        alert_message = random.choice(alert_messages)
        self.setText(alert_message)
        self.placeholder_text = alert_message
        
        # Enhanced visual feedback with more professional highlighting
        original_style = self.styleSheet()
        highlight_style = original_style.replace(
            "border: 1px solid rgba(0, 0, 0, 0.3)",
            "border: 2px solid rgba(100, 181, 246, 0.8); background: rgba(100, 181, 246, 0.1)"
        )
        self.setStyleSheet(highlight_style)
        
        # Reset style and message after 4 seconds (longer to read the helpful text)
        QTimer.singleShot(4000, lambda: [
            self.setStyleSheet(original_style),
            self._reset_to_default_message()
        ])
    
    # Background process management methods
    def add_background_process(self, process_id, message, progress=""):
        """Add a background process to track"""
        process = {
            'id': process_id,
            'message': message,
            'progress': progress,
            'start_time': datetime.now()
        }
        self.background_processes.append(process)
        
        if not self.is_expanded and not self.is_processing:
            self._show_background_process_status()
    
    def update_background_process(self, process_id, message=None, progress=None):
        """Update a background process"""
        for process in self.background_processes:
            if process['id'] == process_id:
                if message:
                    process['message'] = message
                if progress:
                    process['progress'] = progress
                    
                if not self.is_expanded and not self.is_processing:
                    self._show_background_process_status()
                break
    
    def remove_background_process(self, process_id):
        """Remove a completed background process"""
        self.background_processes = [p for p in self.background_processes if p['id'] != process_id]
        
        # Update display if this was the last process
        if not self.background_processes and not self.is_expanded and not self.is_processing:
            self._update_dynamic_status()
    
    def handle_ai_response(self, response_text: str):
        """Handle response from AI command processor"""
        self.setText(response_text)
        self.is_processing = False
        
        # Auto-collapse after showing response for 5 seconds
        QTimer.singleShot(5000, self._collapse_to_normal)
    
    def handle_ai_error(self, error_message: str):
        """Handle AI processing errors"""
        self.setText(f"AI Error: {error_message}")
        self.is_processing = False
        QTimer.singleShot(3000, self._reset_to_default_message)
    
    def handle_processing_started(self):
        """Handle AI processing started signal"""
        self.set_processing_status("AI is thinking...")
    
    def handle_processing_finished(self):
        """Handle AI processing finished signal"""
        # Processing status will be updated by other handlers
        pass
    
    def _show_smart_suggestion(self):
        """Show intelligent suggestions based on context and user behavior"""
        if not self.smart_suggestions_enabled or self.is_expanded or self.is_processing:
            return
        
        current_time = datetime.now()
        time_since_last_suggestion = current_time - self.last_suggestion_time
        
        # Don't show suggestions too frequently
        if time_since_last_suggestion.total_seconds() < 1800:  # 30 minutes
            return
        
        suggestion = self._get_contextual_suggestion()
        if suggestion:
            self.setText(suggestion)
            self.placeholder_text = suggestion
            self.last_suggestion_time = current_time
            
            # Reset after 12 seconds
            QTimer.singleShot(12000, self._reset_to_default_message)

    def _get_contextual_suggestion(self) -> str:
        """Get intelligent suggestion based on current context"""
        page_suggestions = {
            'dashboard': [
                "💡 Try: 'show me this month's summary'",
                "🔍 Ask: 'how is my cash flow looking?'",
                "📊 Try: 'generate income statement'",
                "⚡ Quick: 'open trial balance'"
            ],
            'journal': [
                "💡 Try: 'help me create a journal entry'",
                "🔍 Ask: 'explain debit and credit rules'",
                "📝 Try: 'show recent transactions'",
                "⚡ Quick: 'how to reverse an entry?'"
            ],
            'accounts': [
                "💡 Try: 'explain this account type'",
                "🔍 Ask: 'show account balance history'",
                "📋 Try: 'help me organize accounts'",
                "⚡ Quick: 'create new account'"
            ],
            'trial_balance': [
                "💡 Try: 'why doesn't my trial balance balance?'",
                "🔍 Ask: 'explain trial balance purpose'",
                "📊 Try: 'show me the largest variances'",
                "⚡ Quick: 'export to Excel'"
            ],
            'reports': [
                "💡 Try: 'generate custom report'",
                "🔍 Ask: 'explain financial ratios'",
                "📈 Try: 'compare this year vs last year'",
                "⚡ Quick: 'email this report'"
            ],
            'ledger': [
                "💡 Try: 'explain general ledger entries'",
                "🔍 Ask: 'find specific transaction'",
                "📚 Try: 'show account activity'",
                "⚡ Quick: 'filter by date range'"
            ]
        }
        
        # Context-based suggestions
        if self.current_page_context in page_suggestions:
            suggestions = page_suggestions[self.current_page_context]
            return random.choice(suggestions)
        
        # Time-based suggestions
        current_hour = datetime.now().hour
        if 9 <= current_hour < 12:  # Morning
            return random.choice([
                "🌅 Good morning! Try: 'show yesterday's entries'",
                "☀️ Start your day: 'open dashboard overview'",
                "📊 Morning check: 'run trial balance'"
            ])
        elif 12 <= current_hour < 17:  # Afternoon
            return random.choice([
                "⚡ Need help? Try: 'explain account reconciliation'",
                "📈 Afternoon task: 'generate P&L statement'",
                "🔍 Quick check: 'show overdue items'"
            ])
        else:  # Evening
            return random.choice([
                "🌙 End of day: 'review today's transactions'",
                "📋 Wrap up: 'show pending approvals'",
                "✅ Daily close: 'run cash position report'"
            ])

    def _get_recent_context_suggestions(self) -> str | None:
        """Get suggestions based on recent user commands"""
        if not self.recent_commands:
            return None
        
        recent_command = self.recent_commands[-1]['command'].lower()
        
        # Suggest follow-up actions based on recent commands
        follow_ups = {
            'journal': "Try: 'show journal entry templates'",
            'balance': "Try: 'explain why accounts don't balance'",
            'report': "Try: 'customize report format'",
            'account': "Try: 'show account reconciliation'",
            'transaction': "Try: 'find duplicate transactions'"
        }
        
        for keyword, suggestion in follow_ups.items():
            if keyword in recent_command:
                return f"💭 Based on your last query: {suggestion}"
        
        return None
