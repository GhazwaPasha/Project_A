"""
Frameless Window Mixin
Easy-to-use mixin class that adds complete frameless window functionality
to any QMainWindow or QWidget.
"""

from PyQt6.QtCore import Qt, QEvent
from PyQt6.QtGui import QMouseEvent
from .frameless_window_manager import FramelessWindowManager

class FramelessWindowMixin:
    """
    Mixin class that provides complete frameless window functionality.
      Usage:
        class MyWindow(QMainWindow, FramelessWindowMixin):
            def __init__(self):
                super().__init__()
                self.setup_frameless_window()
    """
    
    def setup_frameless_window(self):
        """Initialize frameless window functionality."""
        self.frameless_manager = FramelessWindowManager(self)
        
        # Enable mouse tracking for cursor updates
        self.setMouseTracking(True)
        
        # Store original event handlers (but don't override closeEvent to avoid recursion)
        self._original_mouse_move_event = self.mouseMoveEvent
        self._original_mouse_press_event = self.mousePressEvent
        self._original_mouse_release_event = self.mouseReleaseEvent
        self._original_mouse_double_click_event = self.mouseDoubleClickEvent
        
        # Replace with frameless-aware handlers
        self.mouseMoveEvent = self._frameless_mouse_move_event
        self.mousePressEvent = self._frameless_mouse_press_event
        self.mouseReleaseEvent = self._frameless_mouse_release_event
        self.mouseDoubleClickEvent = self._frameless_mouse_double_click_event
    
    def _frameless_mouse_move_event(self, event):
        """Enhanced mouse move event with resize functionality."""
        # Handle frameless window functionality first
        self.frameless_manager.handle_mouse_move(event)
        
        # Call original handler if it exists
        if hasattr(self, '_original_mouse_move_event'):
            self._original_mouse_move_event(event)
    
    def _frameless_mouse_press_event(self, event):
        """Enhanced mouse press event with resize functionality."""
        # Handle frameless window functionality first
        handled = self.frameless_manager.handle_mouse_press(event)
        
        # If not handled by frameless manager, call original handler
        if not handled and hasattr(self, '_original_mouse_press_event'):
            self._original_mouse_press_event(event)
    
    def _frameless_mouse_release_event(self, event):
        """Enhanced mouse release event with resize functionality."""
        # Handle frameless window functionality first
        handled = self.frameless_manager.handle_mouse_release(event)
        
        # If not handled by frameless manager, call original handler
        if not handled and hasattr(self, '_original_mouse_release_event'):
            self._original_mouse_release_event(event)
    
    def _frameless_mouse_double_click_event(self, event):
        """Enhanced double-click event with maximize/restore functionality."""
        # Handle frameless window functionality first
        handled = self.frameless_manager.handle_double_click(event)
        
        # If not handled by frameless manager, call original handler
        if not handled and hasattr(self, '_original_mouse_double_click_event'):
            self._original_mouse_double_click_event(event)    
    def cleanup_frameless_window(self):
        """Cleanup frameless window resources. Call this from your closeEvent."""
        if hasattr(self, 'frameless_manager'):
            self.frameless_manager.cleanup()
    
    def set_resize_border_width(self, width):
        """Set the width of resize borders."""
        if hasattr(self, 'frameless_manager'):
            self.frameless_manager.resize_border_width = width
    
    def set_title_bar_height(self, height):
        """Set the height of the title bar for dragging."""
        if hasattr(self, 'frameless_manager'):
            self.frameless_manager.title_bar_height = height
    
    def is_in_resize_area(self, pos):
        """Check if position is in a resize area."""
        if hasattr(self, 'frameless_manager'):
            from .frameless_window_manager import ResizeDirection
            direction = self.frameless_manager.get_resize_direction(pos)
            return direction != ResizeDirection.NONE
        return False
