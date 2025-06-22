"""
Enhanced AI Status Bar - Intelligent, context-aware AI assistant
Handles navigation, analysis, reminders, and provides motivational support
"""
from PyQt6.QtWidgets import QLineEdit, QApplication
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtSignal, QThread, pyqtSlot
from PyQt6.QtGui import QFont, QFontMetrics, QPainter, QPalette
import threading
import time
import json
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

class MotivationalMessageManager:
    """Manages motivational and wellness messages for the AI status bar"""
    
    def __init__(self):
        self.last_message_time = None
        self.last_message_type = None
        self.user_preferences = {
            'motivation_enabled': True,
            'wellness_enabled': True,
            'break_reminders': True,
            'break_interval': 3600,  # 1 hour in seconds
            'achievement_level': 'standard'  # minimal, standard, enthusiastic
        }
        
        self.messages = {
            'morning_motivation': [
                "Great job starting your day with financial management! 📊",
                "Ready to make today's numbers count? Let's go! 💪",
                "Fresh start, fresh books - you've got this! ✨",
                "Morning focus = evening satisfaction. Start strong! 🌅"
            ],
            'work_motivation': [
                "Every transaction recorded is a step toward better financial control 💪",
                "Your attention to detail makes all the difference in accounting ✨",
                "Consistent bookkeeping today = stress-free reporting tomorrow 🎯",
                "Mastering these accounting skills builds your expertise 📚"
            ],
            'wellness_reminders': [
                "Remember to take a short break and stretch your eyes 👀",
                "You've been working hard - time for a 5-minute breather? ☕",
                "Stay hydrated while crunching those numbers! 💧",
                "Good posture = better focus. Adjust your seat and carry on! 🪑"
            ],
            'achievements': [
                "Great progress on your financial records today! 🏆",
                "Your books are looking organized and professional 📈",
                "Excellent attention to detail in those entries! 🎉",
                "Your systematic approach to bookkeeping is paying off 💼"
            ],
            'break_reminders': [
                "It's been 2 hours - consider taking a short walk 🚶‍♀️",
                "Time for a quick break to recharge your focus 🔋",
                "Deep breath in, numbers out - you've got this! 🧘‍♀️",
                "A brief pause now = better productivity ahead ⏰"
            ],
            'evening_wrap': [
                "End of day approaching - great work today! 🌅",
                "Take time to appreciate how much you've accomplished 🙏",
                "Tomorrow's fresh start begins with today's good work 🌟",
                "Well done wrapping up another productive day! 👏"
            ]
        }
    
    def get_appropriate_message(self, context: Dict[str, Any]) -> Optional[str]:
        """Get an appropriate message based on context and timing"""
        if not self.user_preferences['motivation_enabled']:
            return None
            
        current_time = datetime.now()
        hour = current_time.hour
        
        # Don't show messages too frequently
        if (self.last_message_time and 
            (current_time - self.last_message_time).seconds < 1800):  # 30 minutes
            return None
        
        # Determine message type based on time and context
        message_type = self._determine_message_type(hour, context)
        if not message_type:
            return None
            
        # Select random message from appropriate category
        messages = self.messages.get(message_type, [])
        if not messages:
            return None
            
        message = random.choice(messages)
        self.last_message_time = current_time
        self.last_message_type = message_type
        
        return message
    
    def _determine_message_type(self, hour: int, context: Dict[str, Any]) -> Optional[str]:
        """Determine appropriate message type based on time and context"""
        # Morning messages (6-10 AM)
        if 6 <= hour <= 10 and self.last_message_type != 'morning_motivation':
            return 'morning_motivation'
        
        # Break reminders based on activity
        if (context.get('work_duration', 0) > self.user_preferences['break_interval'] and
            self.user_preferences['break_reminders']):
            return 'break_reminders'
        
        # Achievement messages after completing tasks
        if context.get('recent_achievement'):
            return 'achievements'
        
        # Evening wrap-up (17-20 PM)
        if 17 <= hour <= 20 and self.last_message_type != 'evening_wrap':
            return 'evening_wrap'
        
        # Wellness reminders during long work sessions
        if (context.get('continuous_work_time', 0) > 7200 and  # 2 hours
            self.user_preferences['wellness_enabled']):
            return 'wellness_reminders'
        
        # Default work motivation
        if random.random() < 0.3:  # 30% chance for general motivation
            return 'work_motivation'
        
        return None

class StatusDisplayManager:
    """Manages different display states and messages for the AI status bar"""
    
    def __init__(self, status_bar):
        self.status_bar = status_bar
        self.current_state = 'idle'
        self.background_processes = []
        self.notification_count = 0
        self.motivational_manager = MotivationalMessageManager()
        
        # Timers for different states
        self.idle_timer = QTimer()
        self.idle_timer.timeout.connect(self._update_idle_display)
        self.idle_timer.start(10000)  # Update every 10 seconds
        
        self.process_timer = QTimer()
        self.process_timer.timeout.connect(self._update_process_display)
    
    def set_state(self, state: str, data: Dict[str, Any] = None):
        """Set the current display state"""
        self.current_state = state
        
        if state == 'idle':
            self.process_timer.stop()
            self.idle_timer.start(10000)
            self._update_idle_display()
        elif state == 'processing':
            self.idle_timer.stop()
            self.process_timer.start(2000)  # Update every 2 seconds
            self._update_process_display(data)
        elif state == 'notification':
            self._show_notification(data)
    
    def _update_idle_display(self):
        """Update display for idle state"""
        if self.status_bar.is_expanded or self.status_bar.is_processing:
            return
            
        # Priority order: Notifications > Background Processes > Motivational Messages > Default
        
        # Check for unread notifications
        if self.notification_count > 0:
            self.status_bar.setText(f"📢 {self.notification_count} unread notifications - Click to review")
            return
        
        # Check for background processes
        if self.background_processes:
            process_text = self._get_background_process_text()
            if process_text:
                self.status_bar.setText(process_text)
                return
        
        # Show motivational message occasionally
        context = self._get_current_context()
        motivational_msg = self.motivational_manager.get_appropriate_message(context)
        if motivational_msg:
            self.status_bar.setText(motivational_msg)
            return
        
        # Default state
        self.status_bar.setText("🤖 AI Assistant - Ask me anything!")
    
    def _update_process_display(self, data: Dict[str, Any] = None):
        """Update display for processing state"""
        if not data:
            return
            
        process_type = data.get('type', 'general')
        progress = data.get('progress', 0)
        
        messages = {
            'command_analysis': [
                "Understanding your request...",
                "Analyzing command context...",
                "Processing natural language input..."
            ],
            'data_retrieval': [
                "Gathering financial data...",
                f"Retrieving records... {progress}%",
                "Accessing database information..."
            ],
            'report_generation': [
                f"Creating custom report... {progress}%",
                "Generating financial analysis...",
                "Compiling report data..."
            ],
            'ai_processing': [
                "Consulting AI assistant...",
                "Analyzing with artificial intelligence...",
                "Generating intelligent insights..."
            ]
        }
        
        msg_list = messages.get(process_type, ["Processing your request..."])
        message = random.choice(msg_list)
        self.status_bar.setText(message)
    
    def _show_notification(self, data: Dict[str, Any]):
        """Show notification message"""
        notification_text = data.get('text', 'New notification received')
        self.status_bar.setText(f"🔔 {notification_text}")
        
        # Auto-return to idle after 5 seconds
        QTimer.singleShot(5000, lambda: self.set_state('idle'))
    
    def _get_background_process_text(self) -> str:
        """Get text for current background processes"""
        if not self.background_processes:
            return ""
            
        process = self.background_processes[0]  # Show first process
        process_type = process.get('type', 'unknown')
        progress = process.get('progress', 0)
        
        process_messages = {
            'sync': f"🔄 Syncing with cloud database... {progress}%",
            'backup': f"💾 Creating automatic backup... {progress}%",
            'reconciliation': f"🔍 Processing bank reconciliation... {progress}%",
            'report': f"📊 Generating report in background... {progress}%"
        }
        
        return process_messages.get(process_type, f"⚙️ Background process running... {progress}%")
    
    def _get_current_context(self) -> Dict[str, Any]:
        """Get current context for motivational messages"""
        # This would integrate with the main application to get real context
        return {
            'work_duration': 3600,  # Placeholder
            'continuous_work_time': 1800,  # Placeholder
            'recent_achievement': False  # Placeholder
        }
    
    def add_background_process(self, process_type: str, description: str):
        """Add a background process to monitor"""
        self.background_processes.append({
            'type': process_type,
            'description': description,
            'progress': 0,
            'start_time': datetime.now()
        })
    
    def update_background_process(self, process_type: str, progress: int):
        """Update progress of a background process"""
        for process in self.background_processes:
            if process['type'] == process_type:
                process['progress'] = progress
                if progress >= 100:
                    self.background_processes.remove(process)
                break
    
    def set_notification_count(self, count: int):
        """Set the number of unread notifications"""
        self.notification_count = count

class AICommandProcessor(QThread):
    """Processes AI commands in a separate thread"""
    
    command_processed = pyqtSignal(dict)
    processing_started = pyqtSignal(dict)
    processing_finished = pyqtSignal()
    error_occurred = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.command_queue = []
        self.current_command = None
        
    def process_command(self, command: str, context: Dict[str, Any] = None):
        """Add command to processing queue"""
        self.command_queue.append({
            'command': command,
            'context': context or {},
            'timestamp': datetime.now()
        })
        
        if not self.isRunning():
            self.start()
    
    def run(self):
        """Process commands from queue"""
        while self.command_queue:
            self.current_command = self.command_queue.pop(0)
            self._process_single_command(self.current_command)
    
    def _process_single_command(self, command_data: Dict[str, Any]):
        """Process a single command"""
        try:
            command = command_data['command']
            context = command_data['context']
            
            # Emit processing started
            self.processing_started.emit({
                'type': 'command_analysis',
                'command': command
            })
            
            # Simulate AI processing (replace with actual Mistral API call)
            time.sleep(1)
            
            # Parse command type and generate response
            response = self._generate_ai_response(command, context)
            
            # Emit completion
            self.command_processed.emit(response)
            self.processing_finished.emit()
            
        except Exception as e:
            self.error_occurred.emit(str(e))
    
    def _generate_ai_response(self, command: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AI response (placeholder for Mistral API integration)"""
        # This is where we'll integrate with Mistral API
        # For now, return a simple response
        
        command_lower = command.lower()
        
        if any(word in command_lower for word in ['report', 'show', 'generate']):
            return {
                'type': 'report',
                'action': 'generate_report',
                'response': f"I'll generate that report for you. Analyzing your request: '{command}'",
                'data': {'report_type': 'custom', 'parameters': {}}
            }
        elif any(word in command_lower for word in ['remind', 'reminder']):
            return {
                'type': 'reminder',
                'action': 'create_reminder',
                'response': f"I'll set up that reminder for you: '{command}'",
                'data': {'reminder_text': command}
            }
        elif any(word in command_lower for word in ['go', 'navigate', 'open']):
            return {
                'type': 'navigation',
                'action': 'navigate',
                'response': f"Navigating as requested: '{command}'",
                'data': {'target_page': 'dashboard'}
            }
        else:
            return {
                'type': 'general',
                'action': 'general_response',
                'response': f"I understand you want to: '{command}'. Let me help you with that.",
                'data': {}
            }

class EnhancedAIStatusBar(QLineEdit):
    """Enhanced AI Status Bar with comprehensive functionality"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.is_expanded = False
        self.is_processing = False
        self.placeholder_text = "🤖 AI Assistant - Ask me anything!"
        
        # Initialize components
        self.display_manager = StatusDisplayManager(self)
        self.ai_processor = AICommandProcessor()
        
        # Setup UI and connections
        self._setup_ui()
        self._setup_animations()
        self._apply_styling()
        self._setup_ai_connections()
        
    def _setup_ui(self):
        """Setup the UI components"""
        self.setReadOnly(True)
        self.setText(self.placeholder_text)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(30)
        self.setFixedWidth(300)  # Slightly wider for longer messages
        
        self.returnPressed.connect(self._process_input)
        
    def _setup_animations(self):
        """Setup smooth animations"""
        self.width_animation = QPropertyAnimation(self, b"maximumWidth")
        self.width_animation.setDuration(300)
        self.width_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        self.min_width_animation = QPropertyAnimation(self, b"minimumWidth")
        self.min_width_animation.setDuration(300)
        self.min_width_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
    def _apply_styling(self):
        """Apply modern styling"""
        self.setStyleSheet("""
            QLineEdit {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(0, 0, 0, 0.3);
                border-radius: 8px;
                color: white;
                font-size: 12px;
                font-family: 'Segoe UI', system-ui, sans-serif;
                font-weight: 500;
                padding: 4px 12px;
                selection-background-color: rgba(100, 181, 246, 0.3);
                outline: none;
                text-align: center;
            }
            
            QLineEdit:hover {
                background: rgba(255, 255, 255, 0.12);
                border: 1px solid rgba(100, 181, 246, 0.3);
                outline: none;
            }
            
            QLineEdit:focus {
                background: rgba(255, 255, 255, 0.12);
                border: 1px solid rgba(100, 181, 246, 0.5);
                color: white;
                outline: none;
                text-align: left;
            }
            
            QLineEdit[readOnly="true"] {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(0, 0, 0, 0.3);
                color: white;
                outline: none;
                text-align: center;
            }
            
            QLineEdit[readOnly="true"]:hover {
                background: rgba(255, 255, 255, 0.12);
                border: 1px solid rgba(100, 181, 246, 0.3);
                outline: none;
                text-align: center;
            }
        """)
    
    def _setup_ai_connections(self):
        """Setup AI processor signal connections"""
        self.ai_processor.command_processed.connect(self._handle_ai_response)
        self.ai_processor.processing_started.connect(self._on_processing_started)
        self.ai_processor.processing_finished.connect(self._on_processing_finished)
        self.ai_processor.error_occurred.connect(self._on_ai_error)
    
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
        
        self.setReadOnly(False)
        self.clear()
        self.setPlaceholderText("Type your question or command...")
        self.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.setCursor(Qt.CursorShape.IBeamCursor)
        self.setFocus()
        
        # Animate expansion
        self.width_animation.setStartValue(300)
        self.width_animation.setEndValue(500)
        self.min_width_animation.setStartValue(300)
        self.min_width_animation.setEndValue(500)
        
        self.width_animation.start()
        self.min_width_animation.start()
        
        QTimer.singleShot(300, lambda: self.setFixedWidth(500))
    
    def _process_input(self):
        """Process user input"""
        user_input = self.text().strip()
        if not user_input or self.is_processing:
            return
        
        self.is_processing = True
        
        # Transform back to status display
        self.setReadOnly(True)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setCursor(Qt.CursorShape.ArrowCursor)
        
        # Get current context
        context = self._get_current_context()
        
        # Process with AI
        self.ai_processor.process_command(user_input, context)
    
    def _get_current_context(self) -> Dict[str, Any]:
        """Get current application context"""
        context = {
            'current_page': 'dashboard',  # This should come from parent window
            'user_role': 'accountant',    # This should come from session manager
            'organization_id': 'default', # This should come from session manager
            'timestamp': datetime.now().isoformat()
        }
        
        # Add parent window context if available
        if hasattr(self.parent_window, 'get_current_context'):
            parent_context = self.parent_window.get_current_context()
            context.update(parent_context)
        
        return context
    
    @pyqtSlot(dict)
    def _handle_ai_response(self, response: Dict[str, Any]):
        """Handle AI response"""
        response_text = response.get('response', 'Command processed')
        self.setText(response_text)
        
        # Perform action if needed
        action = response.get('action')
        if action and hasattr(self.parent_window, 'handle_ai_action'):
            self.parent_window.handle_ai_action(action, response.get('data', {}))
    
    @pyqtSlot(dict)
    def _on_processing_started(self, data: Dict[str, Any]):
        """Handle processing started"""
        self.display_manager.set_state('processing', data)
    
    @pyqtSlot()
    def _on_processing_finished(self):
        """Handle processing finished"""
        self.is_processing = False
        
        # Auto-collapse after a delay
        QTimer.singleShot(3000, self._collapse_to_normal)
    
    @pyqtSlot(str)
    def _on_ai_error(self, error_message: str):
        """Handle AI processing error"""
        self.setText(f"Error: {error_message}")
        self.is_processing = False
        QTimer.singleShot(5000, self._collapse_to_normal)
    
    def _collapse_to_normal(self):
        """Collapse back to normal state"""
        if self.is_processing:
            return
            
        self.is_expanded = False
        
        self.setReadOnly(True)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setPlaceholderText("")
        
        # Animate contraction
        self.width_animation.setStartValue(500)
        self.width_animation.setEndValue(300)
        self.min_width_animation.setStartValue(500)
        self.min_width_animation.setEndValue(300)
        
        self.width_animation.start()
        self.min_width_animation.start()
        
        QTimer.singleShot(300, lambda: self.setFixedWidth(300))
        
        # Return to idle state
        self.display_manager.set_state('idle')
    
    def set_context(self, page_name: str, context_data: Dict[str, Any] = None):
        """Set current page context for the AI status bar"""
        if hasattr(self.display_manager, 'current_context'):
            self.display_manager.current_context = {
                'page': page_name,
                'data': context_data or {}
            }
    
    def show_notification(self, notification_text: str):
        """Show a notification in the status bar"""
        self.display_manager.set_state('notification', {'text': notification_text})
    
    def add_background_process(self, process_type: str, description: str):
        """Add a background process to display"""
        self.display_manager.add_background_process(process_type, description)
    
    def update_background_process(self, process_type: str, progress: int):
        """Update background process progress"""
        self.display_manager.update_background_process(process_type, progress)
    
    def set_notification_count(self, count: int):
        """Set unread notification count"""
        self.display_manager.set_notification_count(count)
