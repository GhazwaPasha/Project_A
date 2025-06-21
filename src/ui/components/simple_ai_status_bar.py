"""
Simple AI Status Bar - Clean, expandable AI interface
The status bar itself becomes the input field when expanded
"""
from PyQt6.QtWidgets import QLineEdit, QApplication
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtSignal
from PyQt6.QtGui import QFont, QFontMetrics, QPainter, QPalette
import threading
import time

class SimpleAIStatusBar(QLineEdit):
    """Simple, clean AI status bar that transforms into an input field when clicked"""
    
    # Signals
    ai_response_ready = pyqtSignal(str, str)  # input, response
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.is_expanded = False
        self.is_processing = False
        self.placeholder_text = "Ask AI anything..."
        self.response_text = ""
        
        # Setup UI
        self._setup_ui()
        self._setup_animations()
        self._apply_styling()
        
        # Connect signals
        self.ai_response_ready.connect(self._handle_ai_response)
        
    def _setup_ui(self):
        """Setup the UI components"""
        # Set initial properties - start as a read-only status display
        self.setReadOnly(True)
        self.setText(self.placeholder_text)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Set initial size - compact for title bar
        self.setFixedHeight(28)
        self.setFixedWidth(250)
        
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
        """Apply clean, minimal styling"""
        self.setStyleSheet("""
            QLineEdit {
                background: #3c3c3c;
                border: 1px solid #5a5a5a;
                border-radius: 6px;
                color: #cccccc;
                font-size: 13px;
                font-family: 'Segoe UI', system-ui, sans-serif;
                font-weight: 400;
                padding: 6px 12px;
                selection-background-color: #007acc;
                outline: none;
            }
            
            QLineEdit:hover {
                border: 1px solid #007acc;
                outline: none;
            }
            
            QLineEdit:focus {
                background: #3c3c3c;
                border: 1px solid #007acc;
                color: #ffffff;
                outline: none;
            }
            
            QLineEdit[readOnly="true"] {
                background: #3c3c3c;
                border: 1px solid #5a5a5a;
                color: #cccccc;
                outline: none;
            }
            
            QLineEdit[readOnly="true"]:hover {
                border: 1px solid #007acc;
                outline: none;
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
        self.width_animation.setStartValue(250)
        self.width_animation.setEndValue(400)
        self.min_width_animation.setStartValue(250)
        self.min_width_animation.setEndValue(400)
        
        # Start both animations simultaneously for center expansion
        self.width_animation.start()
        self.min_width_animation.start()
        
        # Update fixed width after animation
        QTimer.singleShot(300, lambda: self.setFixedWidth(400))
        
    def _process_input(self):
        """Process user input"""
        user_input = self.text().strip()
        if not user_input or self.is_processing:
            return
            
        self.is_processing = True
        
        # Transform back to status display showing processing
        self.setReadOnly(True)
        self.setText("Processing...")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setCursor(Qt.CursorShape.ArrowCursor)
        
        # Process in background thread
        self._process_ai_request(user_input)
        
    def _process_ai_request(self, user_input):
        """Process AI request in background"""
        def process():
            # Simulate AI processing (replace with actual AI call)
            time.sleep(1.5)
            
            # Simple response generation (replace with real AI)
            response = self._generate_simple_response(user_input)
            
            # Emit signal to update UI
            self.ai_response_ready.emit(user_input, response)
            
        thread = threading.Thread(target=process, daemon=True)
        thread.start()
        
    def _generate_simple_response(self, user_input):
        """Generate a simple response (replace with actual AI integration)"""
        input_lower = user_input.lower()
        
        if "balance" in input_lower or "money" in input_lower:
            return "Your current account balances are available in the ledger section."
        elif "report" in input_lower:
            return "You can generate reports from the Reports section in the navigation."
        elif "help" in input_lower:
            return "I can help you navigate the accounting system, check balances, and generate reports."
        elif "journal" in input_lower:
            return "The journal entry section allows you to record transactions."
        else:
            return f"I understand you're asking about: '{user_input}'. Let me help you find what you need."
            
    def _handle_ai_response(self, user_input, response):
        """Handle AI response in main thread - show inline"""
        self.is_processing = False
        
        # Show response in the status bar (truncated if too long)
        max_length = 60  # Max characters to show
        if len(response) > max_length:
            display_response = response[:max_length] + "..."
        else:
            display_response = response
            
        self.setText(display_response)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Auto-collapse after 4 seconds
        QTimer.singleShot(4000, self._collapse_to_normal)
        
    def _collapse_to_normal(self):
        """Collapse back to normal state with center contraction"""
        self.is_expanded = False
        
        # Transform back to status display
        self.setReadOnly(True)
        self.setText(self.placeholder_text)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setPlaceholderText("")
        
        # Animate width contraction to center
        self.width_animation.setStartValue(400)
        self.width_animation.setEndValue(250)
        self.min_width_animation.setStartValue(400)
        self.min_width_animation.setEndValue(250)
        
        # Start both animations simultaneously
        self.width_animation.start()
        self.min_width_animation.start()
        
        # Reset fixed width after animation
        QTimer.singleShot(300, lambda: self.setFixedWidth(250))
