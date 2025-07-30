"""
Animated Stack Widget - Provides smooth swipe transitions between pages
"""
from PyQt6.QtWidgets import QStackedWidget, QWidget, QVBoxLayout, QHBoxLayout
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer, pyqtSignal, QRect
from PyQt6.QtGui import QPainter, QColor, QPixmap
import math

class AnimatedStackWidget(QStackedWidget):
    """Stack widget with smooth swipe transitions"""
    
    # Signal emitted when transition is complete
    transition_completed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_animation = None
        self.transition_duration = 300  # milliseconds
        self.transition_type = "slide"  # "slide", "fade", "zoom"
        self.direction = "right"  # "left", "right", "up", "down"
        
        # Store previous widget for transition
        self.previous_widget = None
        self.is_transitioning = False
        
        # Setup animation properties
        self._setup_animations()
    
    def _setup_animations(self):
        """Setup animation properties and easing curves"""
        self.slide_easing = QEasingCurve.Type.OutCubic
        self.fade_easing = QEasingCurve.Type.InOutQuad
        self.zoom_easing = QEasingCurve.Type.OutBack
    
    def setTransitionType(self, transition_type):
        """Set the transition type"""
        self.transition_type = transition_type
    
    def setTransitionDuration(self, duration):
        """Set the transition duration in milliseconds"""
        self.transition_duration = duration
    
    def setDirection(self, direction):
        """Set the transition direction"""
        self.direction = direction
    
    def slideTransition(self, from_index, to_index):
        """Perform slide transition between pages"""
        if self.is_transitioning:
            return
        
        self.is_transitioning = True
        
        # Get the widgets
        from_widget = self.widget(from_index)
        to_widget = self.widget(to_index)
        
        if not from_widget or not to_widget:
            self._complete_transition(to_index)
            return
        
        # Store previous widget
        self.previous_widget = from_widget
        
        # Calculate slide direction and distance
        slide_distance = self.width()
        
        if self.direction == "left":
            from_start_x = 0
            from_end_x = -slide_distance
            to_start_x = slide_distance
            to_end_x = 0
        elif self.direction == "right":
            from_start_x = 0
            from_end_x = slide_distance
            to_start_x = -slide_distance
            to_end_x = 0
        elif self.direction == "up":
            from_start_x = 0
            from_end_x = 0
            to_start_x = 0
            to_end_x = 0
            slide_distance = self.height()
            from_start_y = 0
            from_end_y = -slide_distance
            to_start_y = slide_distance
            to_end_y = 0
        else:  # down
            from_start_x = 0
            from_end_x = 0
            to_start_x = 0
            to_end_x = 0
            slide_distance = self.height()
            from_start_y = 0
            from_end_y = slide_distance
            to_start_y = -slide_distance
            to_end_y = 0
        
        # Position widgets for animation
        if self.direction in ["left", "right"]:
            from_widget.setGeometry(from_start_x, 0, self.width(), self.height())
            to_widget.setGeometry(to_start_x, 0, self.width(), self.height())
        else:
            from_widget.setGeometry(0, from_start_y, self.width(), self.height())
            to_widget.setGeometry(0, to_start_y, self.width(), self.height())
        
        # Hide the background widget and show the sliding widget
        from_widget.hide()  # Hide background widget
        to_widget.show()    # Show only the sliding widget
        
        # Create animations
        from_animation = QPropertyAnimation(from_widget, b"geometry")
        from_animation.setDuration(self.transition_duration)
        from_animation.setEasingCurve(self.slide_easing)
        
        to_animation = QPropertyAnimation(to_widget, b"geometry")
        to_animation.setDuration(self.transition_duration)
        to_animation.setEasingCurve(self.slide_easing)
        
        # Set start and end geometries
        if self.direction in ["left", "right"]:
            from_animation.setStartValue(QRect(from_start_x, 0, self.width(), self.height()))
            from_animation.setEndValue(QRect(from_end_x, 0, self.width(), self.height()))
            to_animation.setStartValue(QRect(to_start_x, 0, self.width(), self.height()))
            to_animation.setEndValue(QRect(to_end_x, 0, self.width(), self.height()))
        else:
            from_animation.setStartValue(QRect(0, from_start_y, self.width(), self.height()))
            from_animation.setEndValue(QRect(0, from_end_y, self.width(), self.height()))
            to_animation.setStartValue(QRect(0, to_start_y, self.width(), self.height()))
            to_animation.setEndValue(QRect(0, to_end_y, self.width(), self.height()))
        
        # Start animations
        from_animation.start()
        to_animation.start()
        
        # Store current animation
        self.current_animation = to_animation
        
        # Connect animation finished signal
        to_animation.finished.connect(lambda: self._complete_transition(to_index))
    
    def fadeTransition(self, from_index, to_index):
        """Perform fade transition between pages"""
        if self.is_transitioning:
            return
        
        self.is_transitioning = True
        
        # Get the widgets
        from_widget = self.widget(from_index)
        to_widget = self.widget(to_index)
        
        if not from_widget or not to_widget:
            self._complete_transition(to_index)
            return
        
        # Store previous widget
        self.previous_widget = from_widget
        
        # Position widgets
        from_widget.setGeometry(0, 0, self.width(), self.height())
        to_widget.setGeometry(0, 0, self.width(), self.height())
        
        # For fade transition, we need both widgets visible but with opacity control
        from_widget.show()
        to_widget.show()
        
        # Create fade animations
        from_animation = QPropertyAnimation(from_widget, b"windowOpacity")
        from_animation.setDuration(self.transition_duration)
        from_animation.setEasingCurve(self.fade_easing)
        from_animation.setStartValue(1.0)
        from_animation.setEndValue(0.0)
        
        to_animation = QPropertyAnimation(to_widget, b"windowOpacity")
        to_animation.setDuration(self.transition_duration)
        to_animation.setEasingCurve(self.fade_easing)
        to_animation.setStartValue(0.0)
        to_animation.setEndValue(1.0)
        
        # Start animations
        from_animation.start()
        to_animation.start()
        
        # Store current animation
        self.current_animation = to_animation
        
        # Connect animation finished signal
        to_animation.finished.connect(lambda: self._complete_transition(to_index))
    
    def zoomTransition(self, from_index, to_index):
        """Perform zoom transition between pages"""
        if self.is_transitioning:
            return
        
        self.is_transitioning = True
        
        # Get the widgets
        from_widget = self.widget(from_index)
        to_widget = self.widget(to_index)
        
        if not from_widget or not to_widget:
            self._complete_transition(to_index)
            return
        
        # Store previous widget
        self.previous_widget = from_widget
        
        # Position widgets
        from_widget.setGeometry(0, 0, self.width(), self.height())
        to_widget.setGeometry(0, 0, self.width(), self.height())
        
        # For zoom transition, hide background and show only the zooming widget
        from_widget.hide()  # Hide background widget
        to_widget.show()    # Show only the zooming widget
        
        # Create zoom animations
        from_animation = QPropertyAnimation(from_widget, b"geometry")
        from_animation.setDuration(self.transition_duration)
        from_animation.setEasingCurve(self.zoom_easing)
        
        to_animation = QPropertyAnimation(to_widget, b"geometry")
        to_animation.setDuration(self.transition_duration)
        to_animation.setEasingCurve(self.zoom_easing)
        
        # Calculate zoom effect
        center_x = self.width() // 2
        center_y = self.height() // 2
        zoom_factor = 0.8
        
        # Set start and end geometries
        from_animation.setStartValue(QRect(0, 0, self.width(), self.height()))
        from_animation.setEndValue(QRect(
            center_x - (self.width() * zoom_factor) // 2,
            center_y - (self.height() * zoom_factor) // 2,
            self.width() * zoom_factor,
            self.height() * zoom_factor
        ))
        
        to_animation.setStartValue(QRect(
            center_x - (self.width() * zoom_factor) // 2,
            center_y - (self.height() * zoom_factor) // 2,
            self.width() * zoom_factor,
            self.height() * zoom_factor
        ))
        to_animation.setEndValue(QRect(0, 0, self.width(), self.height()))
        
        # Start animations
        from_animation.start()
        to_animation.start()
        
        # Store current animation
        self.current_animation = to_animation
        
        # Connect animation finished signal
        to_animation.finished.connect(lambda: self._complete_transition(to_index))
    
    def _complete_transition(self, to_index):
        """Complete the transition and cleanup"""
        # Ensure proper widget visibility
        if self.previous_widget:
            self.previous_widget.hide()
            self.previous_widget = None
        
        # Ensure current widget is visible and properly positioned
        current_widget = self.widget(to_index)
        if current_widget:
            current_widget.setGeometry(0, 0, self.width(), self.height())
            current_widget.show()
        
        # Set current index
        super().setCurrentIndex(to_index)
        
        # Reset transition state
        self.is_transitioning = False
        self.current_animation = None
        
        # Emit completion signal
        self.transition_completed.emit()
    
    def setCurrentIndex(self, index):
        """Override to add transition animation"""
        current_index = self.currentIndex()
        
        # If no transition is set or same index, use normal behavior
        if (self.transition_type == "none" or 
            current_index == index or 
            self.is_transitioning or
            current_index == -1):  # First time setup
            super().setCurrentIndex(index)
            return
        
        # Determine direction based on index change
        if index > current_index:
            self.direction = "right"
        else:
            self.direction = "left"
        
        # Perform transition based on type
        if self.transition_type == "slide":
            self.slideTransition(current_index, index)
        elif self.transition_type == "fade":
            self.fadeTransition(current_index, index)
        elif self.transition_type == "zoom":
            self.zoomTransition(current_index, index)
        else:
            # Fallback to normal behavior
            super().setCurrentIndex(index)
    
    def setCurrentWidget(self, widget):
        """Override to add transition animation"""
        index = self.indexOf(widget)
        if index >= 0:
            self.setCurrentIndex(index)
    
    def stopCurrentAnimation(self):
        """Stop the current animation if running"""
        if self.current_animation and self.current_animation.state() == QPropertyAnimation.State.Running:
            self.current_animation.stop()
            self.is_transitioning = False
            self.current_animation = None 