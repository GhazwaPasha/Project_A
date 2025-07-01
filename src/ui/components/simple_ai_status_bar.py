"""
Simple AI Status Bar - Clean and focused AI input interface
The status bar becomes the input field when expanded
"""
from PyQt6.QtWidgets import QLineEdit, QApplication
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtSignal
from PyQt6.QtGui import QFont, QFontMetrics, QPainter, QPalette
import threading
import time
import json
import os
from datetime import datetime, timedelta

class SimpleAIStatusBar(QLineEdit):
    """Clean AI status bar with essential functionality only"""
    ai_command_submitted = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.is_expanded = False
        self.is_processing = False
        self.placeholder_text = "Your AI Sidekick - Ready"
        
        # Initialize AI processor
        from .enhanced_ai_processor import ContextAwareAI
        self.ai_processor = ContextAwareAI(parent)
        self._setup_ai_connections()
        
        # Basic state management
        self.current_page_context = None
        self.unread_notifications_count = 0
        self.background_processes = []
        
        # Setup UI
        self._setup_ui()
        self._setup_animations()
        self._apply_styling()
        self._setup_status_timers()
    
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
        
    def _setup_status_timers(self):
        """Setup essential timers for status updates"""
        # Status update timer
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._update_status)
        self.status_timer.start(60000)  # 1 minute
        
        # Notification checker
        self.notification_timer = QTimer()
        self.notification_timer.timeout.connect(self._check_notifications)
        self.notification_timer.start(15000)  # 15 seconds
        
        # Initial status
        self._update_status()
        
    def _setup_ui(self):
        """Setup the UI components"""
        self.setReadOnly(True)
        self.setText(self.placeholder_text)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(36)
        self.setFixedWidth(380)
        
        # Connect events
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
        """Apply modern styling with spotlight effect"""
        self.setStyleSheet("""
            QLineEdit {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 rgba(255, 255, 255, 0.12),
                    stop: 0.3 rgba(255, 255, 255, 0.08),
                    stop: 0.7 rgba(255, 255, 255, 0.08),
                    stop: 1 rgba(255, 255, 255, 0.04));
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
                box-shadow: 
                    inset 0 1px 0 rgba(255, 255, 255, 0.2),
                    0 0 20px rgba(255, 255, 255, 0.1),
                    0 2px 8px rgba(0, 0, 0, 0.1);
            }
            
            QLineEdit:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 rgba(255, 255, 255, 0.16),
                    stop: 0.3 rgba(255, 255, 255, 0.12),
                    stop: 0.7 rgba(255, 255, 255, 0.12),
                    stop: 1 rgba(255, 255, 255, 0.08));
                border: 1px solid rgba(0, 0, 0, 0.3);
                outline: none;
                box-shadow: 
                    inset 0 1px 0 rgba(255, 255, 255, 0.2),
                    0 2px 8px rgba(0, 0, 0, 0.1);
            }
            
            QLineEdit:focus {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 rgba(255, 255, 255, 0.16),
                    stop: 0.3 rgba(255, 255, 255, 0.12),
                    stop: 0.7 rgba(255, 255, 255, 0.12),
                    stop: 1 rgba(255, 255, 255, 0.08));
                border: 1px solid rgba(0, 0, 0, 0.3);
                color: white;
                outline: none;
                text-align: left;
                box-shadow: 
                    inset 0 1px 0 rgba(255, 255, 255, 0.2),
                    0 2px 8px rgba(0, 0, 0, 0.1);
            }
            
            QLineEdit::placeholder {
                color: rgba(255, 255, 255, 0.7);
                font-weight: 500;
            }
        """)
    
    def mousePressEvent(self, event):
        """Handle mouse press to expand for input"""
        if not self.is_expanded and not self.is_processing:
            self._expand_for_input()
        super().mousePressEvent(event)
    
    def focusOutEvent(self, event):
        """Handle focus out to collapse"""
        if self.is_expanded and not self.text().strip():
            self._collapse_to_normal()
        super().focusOutEvent(event)
    
    def _expand_for_input(self):
        """Expand the status bar for AI input"""
        self.is_expanded = True
        self.setReadOnly(False)
        self.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.setCursor(Qt.CursorShape.IBeamCursor)
        self.setText("")
        self.setPlaceholderText("You Say, I do - Search, Reports and Reminders")
        
        # Animate width expansion
        self.width_animation.setStartValue(380)
        self.width_animation.setEndValue(560)
        self.width_animation.start()
        
        self.min_width_animation.setStartValue(380)
        self.min_width_animation.setEndValue(560)
        self.min_width_animation.start()
        
        # Focus for immediate input
        self.setFocus()
    
    def _process_input(self):
        """Process AI input command"""
        command = self.text().strip()
        if not command:
            self._collapse_to_normal()
            return
        
        # Show processing state
        self.is_processing = True
        self.setReadOnly(True)
        self.setText("🤖 Processing...")
        
        # Submit to AI processor
        self.ai_command_submitted.emit(command)
        
        # Process with AI
        self.ai_processor.process_command(command)
    
    def _get_current_context(self) -> dict:
        """Get current context for AI processing"""
        context = {
            'page': self.current_page_context,
            'notifications': self.unread_notifications_count,
            'background_processes': len(self.background_processes)
        }
        
        # Get additional context from parent if available
        if hasattr(self.parent_window, 'get_current_context'):
            try:
                parent_context = self.parent_window.get_current_context()
                context.update(parent_context)
            except:
                pass
        
        return context
    
    def show_processing_indicator(self):
        """Show processing indicator"""
        self.is_processing = True
        self.setText("🤖 AI is thinking...")
        self.setReadOnly(True)
    
    def hide_processing_indicator(self):
        """Hide processing indicator"""
        self.is_processing = False
        self.setReadOnly(False)
        self._update_status()
    
    def set_ai_response(self, response: str):
        """Set AI response text"""
        self.setText(response)
        self.is_processing = False
        
        # Auto-collapse after 5 seconds
        QTimer.singleShot(5000, self._collapse_to_normal)
    
    def set_error_message(self, error_message: str):
        """Set error message"""
        self.setText(f"❌ {error_message}")
        self.is_processing = False
        QTimer.singleShot(3000, self._reset_to_default)
    
    def _collapse_to_normal(self):
        """Collapse back to normal status bar"""
        self.is_expanded = False
        self.setReadOnly(True)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clear()
        
        # Animate width collapse
        self.width_animation.setStartValue(560)
        self.width_animation.setEndValue(380)
        self.width_animation.start()
        
        self.min_width_animation.setStartValue(560)
        self.min_width_animation.setEndValue(380)
        self.min_width_animation.start()
        
        # Reset to default status
        self._update_status()
    
    def set_context(self, page_name, context_data=None):
        """Set current page context"""
        self.current_page_context = page_name
    
    def set_processing_status(self, status_message):
        """Set processing status message"""
        if not self.is_expanded:
            self.setText(status_message)
    
    def update_activity(self):
        """Update activity timestamp"""
        pass  # Simplified - no longer needed
    
    def _update_status(self):
        """Update status display"""
        if self.is_expanded or self.is_processing:
            return
            
        # Show background processes
        if self.background_processes:
            self._show_background_process_status()
            return
            
        # Show notifications
        if self.unread_notifications_count > 0:
            self._show_notification_status()
            return
            
        # Default status
        self.setText(self.placeholder_text)
    
    def _show_background_process_status(self):
        """Show background process status"""
        if not self.background_processes:
            return
            
        process = self.background_processes[-1]
        process_message = process.get('message', 'Background process running')
        progress = process.get('progress', '')
        
        if 'sync' in process_message.lower():
            message = f"🔄 {process_message} {progress}"
        elif 'backup' in process_message.lower():
            message = f"💾 {process_message} {progress}"
        elif 'report' in process_message.lower():
            message = f"📊 {process_message} {progress}"
        else:
            message = f"⚙️ {process_message} {progress}"
        
        self.setText(message)
    
    def _show_notification_status(self):
        """Show notification status"""
        if self.unread_notifications_count == 1:
            message = f"🔔 1 unread notification"
        else:
            message = f"🔔 {self.unread_notifications_count} notifications"
        
        self.setText(message)
    
    def _reset_to_default(self):
        """Reset to default status"""
        if not self.is_expanded and not self.is_processing:
            self._update_status()
    
    def _check_notifications(self):
        """Check for new notifications"""
        try:
            reminders_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'reminders_data.json')
            if os.path.exists(reminders_file):
                with open(reminders_file, 'r') as f:
                    reminders_data = json.load(f)
                    
                unread_count = 0
                for reminder in reminders_data.get('reminders', []):
                    if reminder.get('status') == 'active' and not reminder.get('acknowledged', False):
                        unread_count += 1
                        
                if unread_count != self.unread_notifications_count:
                    self.unread_notifications_count = unread_count
                    if not self.is_expanded and not self.is_processing:
                        self._update_status()
                        
        except Exception:
            pass  # Silent fail
    
    def add_background_process(self, process_id, message, progress=""):
        """Add background process"""
        process = {
            'id': process_id,
            'message': message,
            'progress': progress,
            'start_time': datetime.now()
        }
        self.background_processes.append(process)
        
        if not self.is_expanded and not self.is_processing:
            self._update_status()
    
    def update_background_process(self, process_id, message=None, progress=None):
        """Update background process"""
        for process in self.background_processes:
            if process['id'] == process_id:
                if message:
                    process['message'] = message
                if progress:
                    process['progress'] = progress
                    
                if not self.is_expanded and not self.is_processing:
                    self._update_status()
                break
    
    def remove_background_process(self, process_id):
        """Remove background process"""
        self.background_processes = [p for p in self.background_processes if p['id'] != process_id]
        
        if not self.background_processes and not self.is_expanded and not self.is_processing:
            self._update_status()
    
    def handle_ai_response(self, response_text: str):
        """Handle AI response"""
        self.setText(response_text)
        self.is_processing = False
        QTimer.singleShot(5000, self._collapse_to_normal)
    
    def handle_ai_error(self, error_message: str):
        """Handle AI error"""
        self.setText(f"❌ {error_message}")
        self.is_processing = False
        QTimer.singleShot(3000, self._reset_to_default)
    
    def handle_processing_started(self):
        """Handle processing started"""
        self.set_processing_status("AI is thinking...")
    
    def handle_processing_finished(self):
        """Handle processing finished"""
        pass  # Handled by other methods
