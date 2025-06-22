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
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.is_expanded = False
        self.is_processing = False
        self.placeholder_text = "Ask AI anything..."
        
        # Setup UI
        self._setup_ui()
        self._setup_animations()
        self._apply_styling()
        
    def _setup_ui(self):
        """Setup the UI components"""
        # Set initial properties - start as a read-only status display
        self.setReadOnly(True)
        self.setText(self.placeholder_text)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setCursor(Qt.CursorShape.PointingHandCursor)        # Set initial size - compact for title bar
        self.setFixedHeight(30)  # Reduced height to 30px
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
        """Apply styling to match date range selector custom date fields"""
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
        if not hasattr(self.parent_window, '_process_ai_command'):
            self.setText("AI system not initialized")
            self.is_processing = False
            return
            
        try:
            self.parent_window._process_ai_command()
        except Exception as e:
            self.setText(f"Error: {str(e)}")
            self.is_processing = False
        
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
        
        # Reset fixed width after animation        QTimer.singleShot(300, lambda: self.setFixedWidth(250))
        
    def set_context(self, page_name, context_data=None):
        """Set the current page context for the AI status bar"""
        if not self.is_expanded and not self.is_processing:
            self.setText("🤖 AI Assistant")
            self.placeholder_text = "🤖 AI Assistant"
