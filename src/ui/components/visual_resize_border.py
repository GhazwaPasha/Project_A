"""
Visual Resize Border
Provides visual feedback for resize areas in frameless windows.
"""

from PyQt6.QtWidgets import QWidget, QFrame
from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QPainter, QPen, QColor

class VisualResizeBorder(QFrame):
    """
    Visual border overlay that shows resize areas when hovering.
    This provides better user feedback for resize functionality.
    """
    
    def __init__(self, parent=None, border_width=8):
        super().__init__(parent)
        self.border_width = border_width
        self.setFixedSize(parent.size() if parent else 100, parent.size() if parent else 100)
        
        # Make this widget transparent and click-through
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setStyleSheet("background: transparent;")
        
        # Track visibility
        self.border_visible = False
        
    def set_border_visible(self, visible):
        """Show or hide the resize border."""
        self.border_visible = visible
        self.update()
    
    def resizeEvent(self, event):
        """Resize the border overlay to match parent."""
        super().resizeEvent(event)
        if self.parent():
            self.setGeometry(0, 0, self.parent().width(), self.parent().height())
    
    def paintEvent(self, event):
        """Paint the resize border when visible."""
        if not self.border_visible:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Create a subtle border to indicate resize areas
        border_color = QColor(255, 255, 255, 40)  # Semi-transparent white
        pen = QPen(border_color, 2)
        painter.setPen(pen)
        
        rect = self.rect()
        
        # Draw border lines
        # Top
        painter.drawLine(0, 0, rect.width(), 0)
        # Bottom  
        painter.drawLine(0, rect.height()-1, rect.width(), rect.height()-1)
        # Left
        painter.drawLine(0, 0, 0, rect.height())
        # Right
        painter.drawLine(rect.width()-1, 0, rect.width()-1, rect.height())
        
        # Draw corner indicators
        corner_size = self.border_width
        corner_color = QColor(255, 255, 255, 60)
        painter.setPen(QPen(corner_color, 3))
        
        # Top-left corner
        painter.drawLine(0, 0, corner_size, 0)
        painter.drawLine(0, 0, 0, corner_size)
        
        # Top-right corner
        painter.drawLine(rect.width()-corner_size, 0, rect.width(), 0)
        painter.drawLine(rect.width()-1, 0, rect.width()-1, corner_size)
        
        # Bottom-left corner
        painter.drawLine(0, rect.height()-corner_size, 0, rect.height())
        painter.drawLine(0, rect.height()-1, corner_size, rect.height()-1)
        
        # Bottom-right corner
        painter.drawLine(rect.width()-corner_size, rect.height()-1, rect.width(), rect.height()-1)
        painter.drawLine(rect.width()-1, rect.height()-corner_size, rect.width()-1, rect.height())

class EnhancedFramelessBorder:
    """
    Enhanced border management for frameless windows with visual feedback.
    """
    
    def __init__(self, window):
        self.window = window
        self.visual_border = VisualResizeBorder(window)
        self.show_visual_feedback = True
        
        # Timer for auto-hiding border
        from PyQt6.QtCore import QTimer
        self.hide_timer = QTimer()
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self._hide_border)
        
    def set_visual_feedback(self, enabled):
        """Enable or disable visual feedback for resize areas."""
        self.show_visual_feedback = enabled
        if not enabled:
            self.visual_border.set_border_visible(False)
    
    def show_resize_hint(self):
        """Show visual hint that window can be resized."""
        if self.show_visual_feedback:
            self.visual_border.set_border_visible(True)
            # Auto-hide after 2 seconds
            self.hide_timer.start(2000)
    
    def hide_resize_hint(self):
        """Hide visual resize hint."""
        self.visual_border.set_border_visible(False)
        self.hide_timer.stop()
    
    def _hide_border(self):
        """Timer callback to hide border."""
        self.visual_border.set_border_visible(False)
    
    def update_geometry(self):
        """Update border geometry when window is resized."""
        if hasattr(self.visual_border, 'resizeEvent'):
            self.visual_border.setGeometry(0, 0, self.window.width(), self.window.height())
