"""
Notification Drawer - Main notification panel that slides in from the right side.
"""
from PyQt6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                            QScrollArea, QWidget, QApplication)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer, pyqtSignal, QEvent
from PyQt6.QtGui import QKeySequence, QShortcut

from .notification_item import NotificationItem
from .notification_manager import NotificationManager

# Simple responsive helper class for standalone use
class ResponsiveHelper:
    """Simple responsive helper for scaling UI elements."""
    
    @staticmethod
    def scale_size(small, medium, large):
        """Return medium size for simplicity."""
        return medium


class NotificationDrawer(QFrame):
    """Notification drawer that slides in from the right side."""
    
    # Signals
    closed = pyqtSignal()
    notification_clicked = pyqtSignal(str)  # notification_id
    
    def __init__(self, parent=None, notification_manager: NotificationManager = None):
        super().__init__(parent)
        self.notification_manager = notification_manager
        self.is_visible = False
        self.auto_hide_timer = QTimer()
        self.auto_hide_timer.timeout.connect(self._auto_hide)
        
        self._setup_ui()
        self._apply_styling()
        self._setup_animations()
        self._connect_signals()
        self._setup_shortcuts()
        
        # Initially hidden
        self.hide()
    
    def _setup_ui(self):
        """Setup the notification drawer UI."""
        self.setObjectName("NotificationDrawer")
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Header
        header = self._create_header()
        main_layout.addWidget(header)
        
        # Content area with scroll
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Scroll content widget
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(8, 8, 8, 8)
        self.content_layout.setSpacing(4)
        self.content_layout.addStretch()  # Push notifications to top
        
        self.scroll_area.setWidget(self.content_widget)
        main_layout.addWidget(self.scroll_area, 1)
        
        # Empty state label
        self.empty_label = QLabel("No notifications")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet(f"""
            QLabel {{
                color: rgba(255, 255, 255, 0.5);
                font-size: {ResponsiveHelper.scale_size(14, 13, 15)}px;
                background: transparent;
                padding: 40px 20px;
            }}
        """)
        self.content_layout.insertWidget(0, self.empty_label)
        
        # Load notifications
        self._load_notifications()
    
    def _create_header(self):
        """Create the notification drawer header."""
        header = QFrame()
        header.setObjectName("NotificationHeader")
        header.setFixedHeight(ResponsiveHelper.scale_size(48, 44, 52))
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(16, 8, 8, 8)
        layout.setSpacing(8)
        
        # Title
        title = QLabel("Notifications")
        title.setStyleSheet(f"""
            QLabel {{
                color: white;
                font-size: {ResponsiveHelper.scale_size(16, 15, 17)}px;
                font-weight: 600;
                background: transparent;
            }}
        """)
        layout.addWidget(title)
        
        layout.addStretch()        # Clear all button
        self.clear_all_btn = QPushButton("Clear")
        self.clear_all_btn.setFixedHeight(26)
        self.clear_all_btn.setMinimumWidth(50)
        self.clear_all_btn.setToolTip("Clear all notifications")
        self.clear_all_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 6px;
                color: rgba(255, 255, 255, 0.8);
                font-size: {ResponsiveHelper.scale_size(11, 10, 12)}px;
                font-weight: 500;
                padding: 4px 8px;
            }}
            QPushButton:hover {{
                background: rgba(255, 255, 255, 0.15);
                border-color: rgba(255, 255, 255, 0.25);
                color: white;
            }}
            QPushButton:pressed {{
                background: rgba(255, 255, 255, 0.1);
            }}
        """)
        self.clear_all_btn.clicked.connect(self._clear_all_notifications)
        layout.addWidget(self.clear_all_btn)
        
        # Header styling
        header.setStyleSheet(f"""
            QFrame#NotificationHeader {{
                background: rgba(255, 255, 255, 0.05);
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            }}
        """)
        
        return header
    
    def _apply_styling(self):
        """Apply styling to the notification drawer."""
        # Apply scrollbar styling
        scrollbar_style = """
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: rgba(255, 255, 255, 0.1);
                width: 8px;
                border-radius: 4px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.3);
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(255, 255, 255, 0.5);
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """
        
        self.setStyleSheet(f"""
            QFrame#NotificationDrawer {{
                background: rgba(20, 20, 20, 0.95);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px 0 0 12px;
                border-right: none;
            }}
            {scrollbar_style}
        """)
    
    def _setup_animations(self):
        """Setup slide animations."""
        self.slide_animation = QPropertyAnimation(self, b"geometry")
        self.slide_animation.setDuration(300)
        self.slide_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        self.opacity_animation = QPropertyAnimation(self, b"windowOpacity")
        self.opacity_animation.setDuration(300)
    
    def _setup_shortcuts(self):
        """Setup keyboard shortcuts."""
        # ESC key to close
        self.esc_shortcut = QShortcut(QKeySequence("Escape"), self)
        self.esc_shortcut.activated.connect(self.hide_drawer)
    
    def _connect_signals(self):
        """Connect notification manager signals."""
        if self.notification_manager:
            self.notification_manager.notification_added.connect(self._on_notification_added)
            self.notification_manager.notification_removed.connect(self._on_notification_removed)
            self.notification_manager.notification_cleared.connect(self._on_notifications_cleared)
    
    def show_drawer(self):
        """Show the notification drawer with animation."""
        if self.is_visible:
            return
        
        self.is_visible = True
        self.show()
        self.raise_()
          # Position drawer off-screen initially
        drawer_width = ResponsiveHelper.scale_size(320, 360, 400)
        parent_widget = self.parent()
        
        if parent_widget:
            # Calculate position based on parent widget dimensions
            drawer_width = ResponsiveHelper.scale_size(320, 360, 400)
            
            # Use parent widget geometry for positioning
            parent_rect = parent_widget.geometry()
            
            # Try to get title bar height from parent if available
            title_bar_height = 40  # Default height
            if hasattr(parent_widget, 'title_bar'):
                title_bar_height = parent_widget.title_bar.height()
            
            start_x = parent_widget.width()  # Off-screen right
            end_x = parent_widget.width() - drawer_width  # Final position (right side)
            y = title_bar_height
            height = parent_widget.height() - title_bar_height
            
            # Set initial position
            self.setGeometry(start_x, y, drawer_width, height)
            
            # Animate to final position
            self.slide_animation.setStartValue(self.geometry())
            self.slide_animation.setEndValue(self.geometry().adjusted(end_x - start_x, 0, end_x - start_x, 0))
            self.slide_animation.start()
        
        # Set focus to enable keyboard shortcuts
        self.setFocus()
        
        # Start auto-hide timer
        self._restart_auto_hide_timer()
    
    def hide_drawer(self):
        """Hide the notification drawer with animation."""
        if not self.is_visible:
            return
        
        self.is_visible = False
        self.auto_hide_timer.stop()
        
        # Animate off-screen
        current_rect = self.geometry()
        parent_widget = self.parent()
        
        if parent_widget:
            end_x = parent_widget.width()  # Off-screen right
            end_rect = current_rect.adjusted(end_x - current_rect.x(), 0, end_x - current_rect.x(), 0)
            
            self.slide_animation.setStartValue(current_rect)
            self.slide_animation.setEndValue(end_rect)
            self.slide_animation.finished.connect(self._on_hide_finished)
            self.slide_animation.start()
        else:
            self.hide()
        
        self.closed.emit()
    
    def _on_hide_finished(self):
        """Handle animation finished for hiding."""
        self.hide()
        self.slide_animation.finished.disconnect()
    
    def _load_notifications(self):
        """Load notifications from the manager."""
        if not self.notification_manager:
            return
        
        notifications = self.notification_manager.get_notifications(limit=50)
        self._update_notification_list(notifications)
    
    def _update_notification_list(self, notifications):
        """Update the notification list display."""
        # Clear existing notification items (keep empty label and stretch)
        for i in range(self.content_layout.count() - 2, 0, -1):  # Skip empty label and stretch
            item = self.content_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if isinstance(widget, NotificationItem):
                    widget.deleteLater()
                    self.content_layout.removeItem(item)
        
        # Show/hide empty state
        has_notifications = len(notifications) > 0
        self.empty_label.setVisible(not has_notifications)
        
        # Add notification items
        if has_notifications:
            for notification in notifications:
                item = NotificationItem(notification, self)
                item.marked_as_read.connect(self._on_item_marked_as_read)
                item.removed.connect(self._on_item_removed)
                
                # Insert before the stretch
                self.content_layout.insertWidget(self.content_layout.count() - 1, item)
    
    def _clear_all_notifications(self):
        """Clear all notifications."""
        if self.notification_manager:
            self.notification_manager.clear_all_notifications()
    
    def _on_notification_added(self, notification):
        """Handle new notification added."""
        self._load_notifications()
    
    def _on_notification_removed(self, notification_id):
        """Handle notification removed."""
        self._load_notifications()
    
    def _on_notifications_cleared(self):
        """Handle all notifications cleared."""
        self._load_notifications()
    
    def _on_item_marked_as_read(self, notification_id):
        """Handle notification item marked as read."""
        if self.notification_manager:
            self.notification_manager.mark_as_read(notification_id)
    
    def _on_item_removed(self, notification_id):
        """Handle notification item removed."""
        if self.notification_manager:
            self.notification_manager.remove_notification(notification_id)
    
    def _restart_auto_hide_timer(self):
        """Restart the auto-hide timer."""
        self.auto_hide_timer.stop()
        self.auto_hide_timer.start(5000)  # 5 seconds
    
    def _auto_hide(self):
        """Auto-hide the drawer after timeout."""
        self.hide_drawer()
    
    def mousePressEvent(self, event):
        """Handle mouse press to restart auto-hide timer."""
        self._restart_auto_hide_timer()
        super().mousePressEvent(event)
        # Accept event to prevent propagation
        event.accept()
    
    def enterEvent(self, event):
        """Handle mouse enter to stop auto-hide."""
        self.auto_hide_timer.stop()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Handle mouse leave to restart auto-hide."""
        if self.is_visible:
            self._restart_auto_hide_timer()
        super().leaveEvent(event)
    
    def focusOutEvent(self, event):
        """Handle focus loss to potentially auto-hide."""
        # Start a brief timer to check if focus went to a child or related widget
        QTimer.singleShot(100, self._check_focus_and_hide)
        super().focusOutEvent(event)
    
    def _check_focus_and_hide(self):
        """Check focus and hide if appropriate."""
        if not self.is_visible:
            return
        
        focused_widget = QApplication.focusWidget()
        parent_widget = self.parent()
        
        # Don't hide if focus went to our children or the notification button
        if (focused_widget and 
            (self.isAncestorOf(focused_widget) or 
             (parent_widget and hasattr(parent_widget, 'notification_button') and 
              focused_widget == parent_widget.notification_button))):
            return
        
        # Hide the drawer
        self.hide_drawer()
