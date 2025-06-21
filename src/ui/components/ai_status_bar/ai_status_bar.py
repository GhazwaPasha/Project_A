"""
AI Status Bar - Main interactive component with personality and productivity features
"""
import json
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit, 
                            QPushButton, QFrame, QTextEdit, QScrollArea, QProgressBar)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtSignal, QThread, pyqtSlot
from PyQt6.QtGui import QFont, QColor, QPalette, QPixmap, QPainter, QLinearGradient
from ..styles import ModernStyles, GlassmorphismHelper
from ..mica_effect import MicaEffect
from .personality_engine import PersonalityEngine
from .reminder_manager import ReminderManager
from .context_analyzer import ContextAnalyzer
from .mistral_connector import MistralConnector


class AIStatusBar(QWidget):
    """Interactive AI status bar with personality, reminders, and accounting intelligence"""
    
    # Signals
    command_executed = pyqtSignal(str, dict)  # Command and result
    mood_changed = pyqtSignal(str)  # Mood state changed
    
    def __init__(self, accounting_system, session_manager=None, parent=None):
        super().__init__(parent)
        self.accounting_system = accounting_system
        self.session_manager = session_manager
        
        # Core components
        self.personality = PersonalityEngine()
        self.reminders = ReminderManager()
        self.context = ContextAnalyzer(accounting_system)
        self.mistral = MistralConnector()
        
        # State management
        self.current_mood = "happy"
        self.is_expanded = False
        self.is_processing = False
        self.current_context = "dashboard"
        
        # Animation states
        self.pulse_animation = None
        self.expand_animation = None
        
        # Setup UI
        self._setup_ui()
        self._setup_animations()
        self._setup_timers()
        self._apply_styling()
        
        # Load user data
        self._load_user_state()
        
        # Start with greeting
        self._show_greeting()
    
    def _setup_ui(self):
        """Setup the main UI structure"""
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)
        
        # Compact bar (always visible)
        self.compact_bar = self._create_compact_bar()
        layout.addWidget(self.compact_bar)
        
        # Expanded panel (hidden by default)
        self.expanded_panel = self._create_expanded_panel()
        self.expanded_panel.hide()
        layout.addWidget(self.expanded_panel)
        
        # Set fixed height for compact mode
        self.setFixedHeight(60)
    
    def _create_compact_bar(self):
        """Create the compact status bar"""
        bar = QFrame()
        bar.setObjectName("AICompactBar")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)
        
        # AI Avatar/Icon with mood indicator
        self.avatar = QLabel("🤖")
        self.avatar.setStyleSheet("""
            QLabel {
                font-size: 24px;
                padding: 4px;
                border-radius: 20px;
                background: rgba(74, 144, 226, 0.2);
                border: 2px solid rgba(74, 144, 226, 0.5);
            }
        """)
        self.avatar.setFixedSize(40, 40)
        self.avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.avatar)
        
        # Status message area
        self.status_label = QLabel("Hi! I'm your AI accounting assistant. What can I help you with today? 😊")
        self.status_label.setObjectName("AIStatusMessage")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label, 1)
        
        # Quick action buttons
        self.quick_actions = self._create_quick_actions()
        layout.addLayout(self.quick_actions)
        
        # Expand/collapse button
        self.expand_btn = QPushButton("💬")
        self.expand_btn.setObjectName("AIExpandButton")
        self.expand_btn.setFixedSize(32, 32)
        self.expand_btn.setToolTip("Expand AI Assistant")
        self.expand_btn.clicked.connect(self.toggle_expanded)
        layout.addWidget(self.expand_btn)
        
        # Make the bar clickable for quick expansion
        bar.mousePressEvent = lambda e: self.toggle_expanded() if e.button() == Qt.MouseButton.LeftButton else None
        bar.setCursor(Qt.CursorShape.PointingHandCursor)
        
        return bar
    
    def _create_quick_actions(self):
        """Create quick action buttons"""
        layout = QHBoxLayout()
        layout.setSpacing(8)
        
        # Reminder indicator
        self.reminder_btn = QPushButton("📋")
        self.reminder_btn.setObjectName("AIQuickAction")
        self.reminder_btn.setFixedSize(28, 28)
        self.reminder_btn.setToolTip("View Reminders")
        self.reminder_btn.clicked.connect(self._show_reminders)
        layout.addWidget(self.reminder_btn)
        
        # Mood indicator
        self.mood_btn = QPushButton("😊")
        self.mood_btn.setObjectName("AIQuickAction")
        self.mood_btn.setFixedSize(28, 28)
        self.mood_btn.setToolTip("Mood & Wellness")
        self.mood_btn.clicked.connect(self._toggle_mood_panel)
        layout.addWidget(self.mood_btn)
        
        # Voice input (future feature)
        self.voice_btn = QPushButton("🎤")
        self.voice_btn.setObjectName("AIQuickAction")
        self.voice_btn.setFixedSize(28, 28)
        self.voice_btn.setToolTip("Voice Input (Coming Soon)")
        self.voice_btn.setEnabled(False)
        layout.addWidget(self.voice_btn)
        
        return layout
    
    def _create_expanded_panel(self):
        """Create the expanded interaction panel"""
        panel = QFrame()
        panel.setObjectName("AIExpandedPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 12, 16, 16)
        layout.setSpacing(12)
        
        # Input area
        input_layout = QHBoxLayout()
        
        self.input_field = QLineEdit()
        self.input_field.setObjectName("AIInputField")
        self.input_field.setPlaceholderText("Ask me anything about your finances, or set reminders...")
        self.input_field.returnPressed.connect(self._process_input)
        input_layout.addWidget(self.input_field, 1)
        
        self.send_btn = QPushButton("Send")
        self.send_btn.setObjectName("AISendButton")
        self.send_btn.clicked.connect(self._process_input)
        input_layout.addWidget(self.send_btn)
        
        layout.addLayout(input_layout)
        
        # Response area
        self.response_area = QTextEdit()
        self.response_area.setObjectName("AIResponseArea")
        self.response_area.setMaximumHeight(120)
        self.response_area.setReadOnly(True)
        self.response_area.setPlaceholderText("AI responses will appear here...")
        layout.addWidget(self.response_area)
        
        # Quick suggestions
        self.suggestions = self._create_suggestions()
        layout.addWidget(self.suggestions)
        
        return panel
    
    def _create_suggestions(self):
        """Create quick suggestion buttons"""
        frame = QFrame()
        frame.setObjectName("AISuggestions")
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(0, 8, 0, 0)
        layout.setSpacing(8)
        
        suggestions = [
            ("What's my cash position?", "💰"),
            ("Show trial balance", "⚖️"),
            ("Set reminder", "⏰"),
            ("Monthly summary", "📊"),
            ("Take a break", "☕")
        ]
        
        for text, icon in suggestions:
            btn = QPushButton(f"{icon} {text}")
            btn.setObjectName("AISuggestionButton")
            btn.clicked.connect(lambda checked, t=text: self._execute_suggestion(t))
            layout.addWidget(btn)
        
        layout.addStretch()
        return frame
    
    def _setup_animations(self):
        """Setup smooth animations"""
        # Pulse animation for mood indication
        self.pulse_animation = QPropertyAnimation(self.avatar, b"styleSheet")
        self.pulse_animation.setDuration(1500)
        self.pulse_animation.setLoopCount(-1)  # Infinite loop
        
        # Expand/collapse animation
        self.expand_animation = QPropertyAnimation(self, b"maximumHeight")
        self.expand_animation.setDuration(300)
        self.expand_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
    
    def _setup_timers(self):
        """Setup periodic timers for proactive features"""
        # Wellness check timer (every 30 minutes)
        self.wellness_timer = QTimer()
        self.wellness_timer.timeout.connect(self._wellness_check)
        self.wellness_timer.start(30 * 60 * 1000)  # 30 minutes
        
        # Reminder check timer (every minute)
        self.reminder_timer = QTimer()
        self.reminder_timer.timeout.connect(self._check_reminders)
        self.reminder_timer.start(60 * 1000)  # 1 minute
        
        # Context update timer (every 5 seconds)
        self.context_timer = QTimer()
        self.context_timer.timeout.connect(self._update_context)
        self.context_timer.start(5 * 1000)  # 5 seconds
    
    def _apply_styling(self):
        """Apply glassmorphism styling matching the app theme"""
        GlassmorphismHelper.apply_main_container_effect(self)
        
        self.setStyleSheet(f"""
            QWidget#AICompactBar {{
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 12px;
                backdrop-filter: blur(20px);
            }}
            
            QWidget#AIExpandedPanel {{
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                margin-top: 4px;
            }}
            
            QLabel#AIStatusMessage {{
                color: white;
                font-size: 14px;
                font-weight: 500;
                background: transparent;
                border: none;
            }}
            
            QPushButton#AIExpandButton, QPushButton#AIQuickAction {{
                background: rgba(74, 144, 226, 0.2);
                border: 1px solid rgba(74, 144, 226, 0.4);
                border-radius: 16px;
                color: white;
                font-size: 16px;
            }}
            
            QPushButton#AIExpandButton:hover, QPushButton#AIQuickAction:hover {{
                background: rgba(74, 144, 226, 0.3);
                border-color: rgba(74, 144, 226, 0.6);
            }}
            
            QLineEdit#AIInputField {{
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                padding: 8px 12px;
                color: white;
                font-size: 14px;
            }}
            
            QLineEdit#AIInputField:focus {{
                border-color: rgba(74, 144, 226, 0.6);
                background: rgba(255, 255, 255, 0.15);
            }}
            
            QPushButton#AISendButton {{
                background: rgba(74, 144, 226, 0.8);
                border: none;
                border-radius: 6px;
                color: white;
                font-weight: 600;
                padding: 8px 16px;
            }}
            
            QPushButton#AISendButton:hover {{
                background: rgba(74, 144, 226, 1.0);
            }}
            
            QTextEdit#AIResponseArea {{
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                color: white;
                font-size: 13px;
                padding: 8px;
            }}
            
            QPushButton#AISuggestionButton {{
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 6px;
                color: white;
                padding: 6px 12px;
                font-size: 12px;
            }}
            
            QPushButton#AISuggestionButton:hover {{
                background: rgba(255, 255, 255, 0.12);
                border-color: rgba(74, 144, 226, 0.4);
            }}
        """)
    
    def _show_greeting(self):
        """Show initial greeting based on time of day"""
        now = datetime.now()
        hour = now.hour
        
        if hour < 12:
            greeting = "Good morning! ☀️"
        elif hour < 17:
            greeting = "Good afternoon! 🌤️"
        else:
            greeting = "Good evening! 🌙"
            
        user_name = self.session_manager.get_current_user_name() if self.session_manager else "there"
        message = f"{greeting} Ready to make today's numbers count, {user_name}?"
        
        self._update_status(message, mood="happy")
    
    def _update_status(self, message: str, mood: str = None, animate: bool = True):
        """Update the status message and mood"""
        self.status_label.setText(message)
        
        if mood and mood != self.current_mood:
            self.current_mood = mood
            self._update_mood_visuals(mood)
            self.mood_changed.emit(mood)
        
        if animate:
            self._pulse_avatar()
    
    def _update_mood_visuals(self, mood: str):
        """Update visual elements based on mood"""
        mood_config = {
            "happy": {"emoji": "😊", "color": "rgba(76, 175, 80, 0.3)", "border": "rgba(76, 175, 80, 0.6)"},
            "focused": {"emoji": "🤔", "color": "rgba(74, 144, 226, 0.3)", "border": "rgba(74, 144, 226, 0.6)"},
            "celebrating": {"emoji": "🎉", "color": "rgba(255, 193, 7, 0.3)", "border": "rgba(255, 193, 7, 0.6)"},
            "concerned": {"emoji": "😐", "color": "rgba(255, 152, 0, 0.3)", "border": "rgba(255, 152, 0, 0.6)"},
            "relaxed": {"emoji": "😌", "color": "rgba(156, 39, 176, 0.3)", "border": "rgba(156, 39, 176, 0.6)"}
        }
        
        config = mood_config.get(mood, mood_config["happy"])
        
        # Update avatar
        self.avatar.setText(config["emoji"])
        self.mood_btn.setText(config["emoji"])
        
        # Update avatar background
        self.avatar.setStyleSheet(f"""
            QLabel {{
                font-size: 24px;
                padding: 4px;
                border-radius: 20px;
                background: {config["color"]};
                border: 2px solid {config["border"]};
            }}
        """)
    
    def _pulse_avatar(self):
        """Create a gentle pulse animation on the avatar"""
        if self.pulse_animation.state() == QPropertyAnimation.State.Running:
            self.pulse_animation.stop()
        
        original_style = self.avatar.styleSheet()
        pulse_style = original_style.replace("0.3)", "0.5)")
        
        self.pulse_animation.setStartValue(original_style)
        self.pulse_animation.setEndValue(pulse_style)
        self.pulse_animation.start()
    
    def toggle_expanded(self):
        """Toggle between compact and expanded view"""
        if self.is_expanded:
            self._collapse()
        else:
            self._expand()
    
    def _expand(self):
        """Expand to show full interaction panel"""
        self.is_expanded = True
        self.expanded_panel.show()
        
        # Animate height change
        self.expand_animation.setStartValue(60)
        self.expand_animation.setEndValue(280)
        self.expand_animation.finished.connect(lambda: self.setMaximumHeight(16777215))  # Remove height limit
        self.expand_animation.start()
        
        # Update button
        self.expand_btn.setText("▼")
        self.expand_btn.setToolTip("Collapse AI Assistant")
        
        # Focus input field
        self.input_field.setFocus()
    
    def _collapse(self):
        """Collapse to compact view"""
        self.is_expanded = False
        
        # Animate height change
        self.expand_animation.setStartValue(self.height())
        self.expand_animation.setEndValue(60)
        self.expand_animation.finished.connect(lambda: self.expanded_panel.hide())
        self.expand_animation.start()
        
        # Update button
        self.expand_btn.setText("💬")
        self.expand_btn.setToolTip("Expand AI Assistant")
    
    def _process_input(self):
        """Process user input and generate AI response"""
        user_input = self.input_field.text().strip()
        if not user_input:
            return
        
        # Clear input
        self.input_field.clear()
        
        # Show processing state
        self._show_processing()
        
        # Process in background thread
        self._process_command_async(user_input)
    
    def _show_processing(self):
        """Show processing state"""
        self.is_processing = True
        self._update_status("I'm thinking... 🤔", mood="focused", animate=True)
        self.send_btn.setEnabled(False)
        self.input_field.setEnabled(False)
    
    def _hide_processing(self):
        """Hide processing state"""
        self.is_processing = False
        self.send_btn.setEnabled(True)
        self.input_field.setEnabled(True)
    
    def _process_command_async(self, command: str):
        """Process command asynchronously"""
        # This would typically run in a separate thread
        # For now, we'll simulate with a timer
        QTimer.singleShot(1000, lambda: self._handle_command_result(command, "Processing complete!"))
    
    def _handle_command_result(self, command: str, result: str):
        """Handle the result of command processing"""
        self._hide_processing()
        
        # Update response area
        self.response_area.append(f"<b>You:</b> {command}")
        self.response_area.append(f"<b>AI:</b> {result}")
        
        # Update status
        self._update_status("How else can I help you today? 😊", mood="happy")
        
        # Emit signal
        self.command_executed.emit(command, {"result": result})
    
    def _execute_suggestion(self, suggestion: str):
        """Execute a quick suggestion"""
        self.input_field.setText(suggestion)
        if not self.is_expanded:
            self._expand()
        self._process_input()
    
    def _show_reminders(self):
        """Show current reminders"""
        reminders = self.reminders.get_active_reminders()
        if reminders:
            count = len(reminders)
            self._update_status(f"You have {count} active reminder{'s' if count != 1 else ''}. Click to expand for details.", mood="focused")
        else:
            self._update_status("No active reminders. Want to set one? 📋", mood="happy")
        
        if not self.is_expanded:
            self._expand()
    
    def _toggle_mood_panel(self):
        """Toggle mood and wellness panel"""
        wellness_message = self.personality.get_wellness_tip()
        self._update_status(wellness_message, mood="relaxed")
        
        if not self.is_expanded:
            self._expand()
    
    def _wellness_check(self):
        """Periodic wellness check"""
        # This would analyze work patterns and suggest breaks
        message = self.personality.get_wellness_reminder()
        if message:
            self._update_status(message, mood="relaxed")
    
    def _check_reminders(self):
        """Check for due reminders"""
        due_reminders = self.reminders.get_due_reminders()
        if due_reminders:
            count = len(due_reminders)
            self._update_status(f"⏰ {count} reminder{'s' if count != 1 else ''} due!", mood="concerned")
            
            # Update reminder button with badge
            self.reminder_btn.setText(f"📋{count}")
    
    def _update_context(self):
        """Update current context for better AI responses"""
        # This would analyze the current page/state
        new_context = self.context.get_current_context()
        if new_context != self.current_context:
            self.current_context = new_context
            # Could trigger context-specific suggestions
    
    def _load_user_state(self):
        """Load user preferences and state"""
        # This would load from persistent storage
        pass
    
    def _save_user_state(self):
        """Save current user state"""
        # This would save to persistent storage
        pass
    
    def set_context(self, context: str, data: Dict[str, Any] = None):
        """Set the current application context"""
        self.current_context = context
        self.context.update_context(context, data)
        
        # Update suggestions based on context
        self._update_context_suggestions(context)
    
    def _update_context_suggestions(self, context: str):
        """Update suggestion buttons based on current context"""
        # This would dynamically update the suggestion buttons
        # based on what page the user is currently viewing
        pass
    
    def celebrate_achievement(self, achievement: str):
        """Trigger celebration for user achievements"""
        celebration_message = self.personality.get_celebration_message(achievement)
        self._update_status(celebration_message, mood="celebrating")
        
        # Could trigger special animations or effects
        self._trigger_celebration_animation()
    
    def _trigger_celebration_animation(self):
        """Trigger celebration visual effects"""
        # This would create sparkle animations or other celebratory effects
        pass
