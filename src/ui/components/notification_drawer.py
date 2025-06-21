"""
Windows 11-style Notification Drawer with Mica Effects
Slides in from the right as an overlay panel (like Windows 11 Action Center)
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                            QScrollArea, QFrame, QGraphicsDropShadowEffect, QApplication)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtSignal, QRect
from PyQt6.QtGui import QFont, QFontMetrics, QPainter, QColor, QBrush, QLinearGradient
from .mica_effect import MicaEffect
import datetime

class NotificationItem(QFrame):
    """Individual notification item"""
    
    def __init__(self, title, message, timestamp=None, notification_type="info", parent=None):
        super().__init__(parent)
        self.setObjectName("NotificationItem")
        self.setFixedHeight(80)
        
        # Notification data
        self.title = title
        self.message = message
        self.timestamp = timestamp or datetime.datetime.now()
        self.notification_type = notification_type
        self.is_read = False
        
        self._setup_ui()
        self._apply_styling()
        
    def _setup_ui(self):
        """Setup the notification item UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)
        
        # Type indicator (colored circle)
        self.type_indicator = QLabel()
        self.type_indicator.setFixedSize(8, 8)
        self.type_indicator.setStyleSheet(self._get_indicator_style())
        layout.addWidget(self.type_indicator, 0, Qt.AlignmentFlag.AlignTop)
        
        # Content area
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(4)
        
        # Title
        self.title_label = QLabel(self.title)
        self.title_label.setObjectName("NotificationTitle")
        self.title_label.setWordWrap(True)
        content_layout.addWidget(self.title_label)
        
        # Message
        self.message_label = QLabel(self.message)
        self.message_label.setObjectName("NotificationMessage")
        self.message_label.setWordWrap(True)
        content_layout.addWidget(self.message_label)
        
        layout.addLayout(content_layout, 1)
        
        # Timestamp
        time_str = self._format_timestamp()
        self.time_label = QLabel(time_str)
        self.time_label.setObjectName("NotificationTime")
        layout.addWidget(self.time_label, 0, Qt.AlignmentFlag.AlignTop)
        
    def _get_indicator_style(self):
        """Get color style for notification type indicator"""
        colors = {
            "info": "#3498db",      # Blue
            "success": "#2ecc71",   # Green
            "warning": "#f39c12",   # Orange
            "error": "#e74c3c",     # Red
            "sync": "#9b59b6"       # Purple
        }
        color = colors.get(self.notification_type, "#3498db")
        return f"""
            QLabel {{
                background-color: {color};
                border-radius: 4px;
            }}
        """
        
    def _format_timestamp(self):
        """Format timestamp for display"""
        now = datetime.datetime.now()
        diff = now - self.timestamp
        
        if diff.total_seconds() < 60:            return "Just now"
        elif diff.total_seconds() < 3600:
            minutes = int(diff.total_seconds() // 60)
            return f"{minutes}m ago"
        elif diff.total_seconds() < 86400:
            hours = int(diff.total_seconds() // 3600)
            return f"{hours}h ago"
        else:
            return self.timestamp.strftime("%m/%d")
            
    def _apply_styling(self):
        """Apply enhanced Windows 11-style styling to the notification item"""
        self.setStyleSheet("""
            QFrame#NotificationItem {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 255, 255, 0.06),
                    stop:1 rgba(255, 255, 255, 0.02));
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 10px;
                margin: 3px 0px;
            }
            QFrame#NotificationItem:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 255, 255, 0.12),
                    stop:1 rgba(255, 255, 255, 0.06));
                border: 1px solid rgba(255, 255, 255, 0.15);
            }
            QLabel#NotificationTitle {
                color: rgba(255, 255, 255, 0.98);
                font-size: 14px;
                font-weight: 600;
                font-family: 'Segoe UI Variable Display', 'Segoe UI', system-ui, sans-serif;
                letter-spacing: -0.3px;
            }
            QLabel#NotificationMessage {
                color: rgba(255, 255, 255, 0.78);
                font-size: 13px;
                font-weight: 400;
                font-family: 'Segoe UI', system-ui, sans-serif;
                line-height: 1.4;
            }
            QLabel#NotificationTime {
                color: rgba(255, 255, 255, 0.55);
                font-size: 11px;
                font-weight: 400;
                font-family: 'Segoe UI', system-ui, sans-serif;
            }
        """)

class NotificationDrawer(QWidget):
    """Windows 11-style notification drawer with Mica effects"""
    
    # Signals
    drawer_closed = pyqtSignal()
    notification_cleared = pyqtSignal(str)  # notification id
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("NotificationDrawer")
        self.parent_window = parent
        
        # Drawer state
        self.is_open = False
        self.notifications = []
        
        # Setup UI
        self._setup_ui()
        self._setup_animations()
        self._apply_mica_styling()
        
        # Apply Windows 11 Mica effect if available
        self._apply_mica_effect()
          # Initially hidden
        self.hide()
        
    def _setup_ui(self):
        """Setup the drawer UI"""
        # Calculate width as 20% of parent window (like Windows 11 Action Center)
        if self.parent_window:
            # Windows 11 Action Center is approximately 20% of screen width
            drawer_width = int(self.parent_window.width() * 0.20)
            # Minimum width for usability, maximum for large screens
            drawer_width = max(320, min(drawer_width, 480))
            self.setFixedWidth(drawer_width)
        else:
            self.setFixedWidth(380)  # Fallback
        
        # Position properly as overlay below title bar
        self._update_position_and_size()
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        header = self._create_header()
        layout.addWidget(header)
        
        # Scroll area for notifications
        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("NotificationScrollArea")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Notifications container
        self.notifications_widget = QWidget()
        self.notifications_layout = QVBoxLayout(self.notifications_widget)
        self.notifications_layout.setContentsMargins(16, 8, 16, 16)
        self.notifications_layout.setSpacing(8)
        self.notifications_layout.addStretch()  # Push notifications to top
        
        self.scroll_area.setWidget(self.notifications_widget)
        layout.addWidget(self.scroll_area, 1)
        
    def _update_position_and_size(self):
        """Update position and size for Windows 11 Action Center style overlay"""
        if self.parent_window:
            # IMPORTANT: The drawer is a direct child of QMainWindow (self.parent_window)
            # We need to ensure it's positioned correctly in the window's coordinate system
            
            # Get the main window's actual geometry
            window_width = self.parent_window.width()
            window_height = self.parent_window.height()
            
            # Calculate responsive width (20% of window width, constrained)
            drawer_width = int(window_width * 0.20)
            drawer_width = max(320, min(drawer_width, 480))  # Min 320px, max 480px
            self.setFixedWidth(drawer_width)
            
            # The drawer should cover from below the title bar (40px) to bottom
            title_bar_height = 40  # From the title bar creation
            drawer_height = window_height - title_bar_height
            self.setFixedHeight(drawer_height)
            
            # Position at right edge of window, initially off-screen
            x_pos = window_width  # Off-screen to the right
            y_pos = title_bar_height  # Below title bar
            self.move(x_pos, y_pos)
            
            print(f"📏 Window size: {window_width}x{window_height}")
            print(f"📏 Drawer size: {drawer_width}x{drawer_height} at ({x_pos}, {y_pos}) (below {title_bar_height}px title bar)")
        
    def _create_header(self):
        """Create the drawer header"""
        header = QFrame()
        header.setObjectName("NotificationHeader")
        header.setFixedHeight(60)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 16, 16, 16)
        layout.setSpacing(12)
        
        # Title
        title = QLabel("Notifications")
        title.setObjectName("NotificationDrawerTitle")
        layout.addWidget(title)
        
        layout.addStretch()
        
        # Clear all button
        clear_btn = QPushButton("Clear all")
        clear_btn.setObjectName("ClearAllButton")
        clear_btn.clicked.connect(self._clear_all_notifications)
        layout.addWidget(clear_btn)
        
        # Close button
        close_btn = QPushButton("×")
        close_btn.setObjectName("DrawerCloseButton")
        close_btn.setFixedSize(32, 32)
        close_btn.clicked.connect(self.close_drawer)
        layout.addWidget(close_btn)
        
        return header
        
    def _setup_animations(self):
        """Setup slide animations"""
        self.slide_animation = QPropertyAnimation(self, b"pos")
        self.slide_animation.setDuration(300)
        self.slide_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Animation debugging disabled for now
        # self.slide_animation.valueChanged.connect(self._on_animation_step)
        self.slide_animation.finished.connect(lambda: print("🎬 Animation FINISHED"))
        
    def _on_animation_step(self, value):
        """Debug function to track animation progress"""
        print(f"🎭 Animation step: drawer now at ({value.x()}, {value.y()})")
        
    def _apply_mica_styling(self):
        """Apply enhanced Windows 11 Mica-compatible styling"""
        self.setStyleSheet("""
            QWidget#NotificationDrawer {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 rgba(40, 40, 40, 0.98), 
                    stop:1 rgba(35, 35, 35, 0.95));
                border-left: 2px solid rgba(255, 255, 255, 0.15);
                border-top: 1px solid rgba(255, 255, 255, 0.10);
                border-bottom: 1px solid rgba(255, 255, 255, 0.08);
            }
            QFrame#NotificationHeader {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 255, 255, 0.08),
                    stop:1 rgba(255, 255, 255, 0.02));
                border-bottom: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 0px;
            }
            QLabel#NotificationDrawerTitle {
                color: rgba(255, 255, 255, 0.98);
                font-size: 18px;
                font-weight: 600;
                font-family: 'Segoe UI Variable Display', 'Segoe UI', system-ui, sans-serif;
                letter-spacing: -0.5px;
            }
            QPushButton#ClearAllButton {
                background: rgba(255, 255, 255, 0.06);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 8px;
                color: rgba(255, 255, 255, 0.85);
                font-size: 12px;
                font-weight: 500;
                font-family: 'Segoe UI', system-ui, sans-serif;
                padding: 8px 16px;
                min-width: 80px;
            }
            QPushButton#ClearAllButton:hover {
                background: rgba(255, 255, 255, 0.12);
                border: 1px solid rgba(255, 255, 255, 0.18);
                color: rgba(255, 255, 255, 0.98);
            }
            QPushButton#ClearAllButton:pressed {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.15);
            }
            QPushButton#DrawerCloseButton {
                background: transparent;
                border: none;
                border-radius: 8px;
                color: rgba(255, 255, 255, 0.75);
                font-size: 20px;
                font-weight: 300;
                font-family: 'Segoe UI Symbol', system-ui, sans-serif;
                min-width: 32px;
                max-width: 32px;
            }
            QPushButton#DrawerCloseButton:hover {
                background: rgba(255, 255, 255, 0.12);
                color: rgba(255, 255, 255, 0.98);
            }
            QPushButton#DrawerCloseButton:pressed {
                background: rgba(255, 255, 255, 0.08);
            }
            QScrollArea#NotificationScrollArea {
                background: transparent;
                border: none;
                border-radius: 0px;
            }
            QScrollBar:vertical {
                background: rgba(255, 255, 255, 0.03);
                width: 12px;
                border-radius: 6px;
                margin: 8px 4px 8px 0px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.25);
                border-radius: 6px;
                min-height: 30px;
                margin: 2px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(255, 255, 255, 0.35);
            }
            QScrollBar::handle:vertical:pressed {
                background: rgba(255, 255, 255, 0.45);
            }            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
                background: transparent;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: transparent;
            }
        """)
        
    def _apply_mica_effect(self):
        """Apply Windows 11 Mica effect to the notification drawer"""
        try:
            if MicaEffect.is_windows11():
                # Set window attributes for backdrop effect
                self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)                # Apply a subtle Mica backdrop effect
                MicaEffect.apply_mica(self, dark_mode=True, backdrop_type=1)  # DWMSBT_ACRYLIC for panels
        except Exception as e:
            print(f"Could not apply Mica effect to notification drawer: {e}")

    def showEvent(self, event):
        """Handle show event to ensure Mica effect"""
        super().showEvent(event)
        if self.isVisible():
            QTimer.singleShot(50, self._apply_mica_effect)
    
    def open_drawer(self):
        """Open the notification drawer with slide animation from the right"""
        if self.is_open:
            return
            
        self.is_open = True
        
        # Update position and size to be below title bar
        self._update_position_and_size()
        
        # Ensure drawer is above all other widgets
        self.raise_()
        
        # Install event filter on parent to detect outside clicks
        if self.parent_window:
            self.parent_window.installEventFilter(self)
        
        # 🎯 STATIC POSITIONING TEST - Skip animation for debugging
        drawer_width = self.width()
        window_width = self.parent_window.width()
        title_bar_height = 40
        
        # Place directly at final position (no animation)
        end_x = window_width - drawer_width
        end_y = title_bar_height
        self.move(end_x, end_y)
        self.show()
        self.raise_()
        
        print(f"🎯 STATIC TEST: Drawer placed at ({end_x}, {end_y}) - window size: {window_width}x{self.parent_window.height()}")
        print(f"🎯 Drawer actual position after move: ({self.pos().x()}, {self.pos().y()})")
        
        return  # Skip animation for now
        
        # Original animation code (temporarily disabled)
        # The drawer is now positioned below the title bar
        drawer_width = self.width()
        window_width = self.parent_window.width()
        title_bar_height = 40  # Match the title bar height
        
        # Start position: completely off-screen to the right of main window
        start_x = window_width  # Off-screen right
        start_y = title_bar_height  # Below title bar
        start_pos = (start_x, start_y)
        
        # End position: visible at the right edge of the main window
        end_x = window_width - drawer_width  # Right edge minus drawer width
        end_y = title_bar_height  # Below title bar
        end_pos = (end_x, end_y)
        
        print(f"🎭 Window Animation: {start_pos} → {end_pos} (window: {window_width}x{self.parent_window.height()})")
        
        # Set the initial position before showing
        self.move(start_x, start_y)
        self.show()
          # Setup and start animation
        self.slide_animation.setStartValue(start_pos)
        self.slide_animation.setEndValue(end_pos)
        self.slide_animation.start()
        
    def close_drawer(self):
        """Close the notification drawer - static hide for debugging"""
        if not self.is_open:
            return
            
        self.is_open = False
        
        # Remove event filter
        if self.parent_window:
            self.parent_window.removeEventFilter(self)
        
        # 🎯 STATIC CLOSE - Just hide directly, no animation
        print(f"🎯 STATIC CLOSE: Hiding drawer from position ({self.pos().x()}, {self.pos().y()})")
        self.hide()
        self.drawer_closed.emit()
        
        return  # Skip animation for now
        
        # Original animation code (temporarily disabled)
        # Animate slide out to right
        # The drawer is positioned below the title bar
        window_width = self.parent_window.width()
        title_bar_height = 40  # Match the title bar height
        start_pos = (window_width - self.width(), title_bar_height)  # Current position (right edge)
        end_pos = (window_width, title_bar_height)  # Off-screen right
        
        self.slide_animation.setStartValue(start_pos)
        self.slide_animation.setEndValue(end_pos)
        self.slide_animation.finished.connect(self._on_close_finished)
        self.slide_animation.start()
        
    def _on_close_finished(self):
        """Handle close animation finished"""
        self.hide()
        self.drawer_closed.emit()
        self.slide_animation.finished.disconnect()
        
    def add_notification(self, title, message, notification_type="info", notification_id=None):
        """Add a new notification to the drawer"""
        notification_item = NotificationItem(title, message, notification_type=notification_type)
        
        # Insert at the top (after the stretch)
        self.notifications_layout.insertWidget(0, notification_item)
        self.notifications.append({
            'id': notification_id or str(len(self.notifications)),
            'item': notification_item,
            'title': title,
            'message': message,
            'type': notification_type,
            'timestamp': datetime.datetime.now()
        })
          # Auto-scroll to top to show new notification
        QTimer.singleShot(50, lambda: self.scroll_area.verticalScrollBar().setValue(0))
        
    def get_notification_count(self):
        """Get total notification count"""
        return len(self.notifications)
        
    def _clear_all_notifications(self):
        """Clear all notifications"""
        for notification in self.notifications:
            self.notifications_layout.removeWidget(notification['item'])
            notification['item'].deleteLater()
            
        self.notifications.clear()
        
    def resizeEvent(self, event):
        """Handle parent window resize"""
        super().resizeEvent(event)
        if self.parent_window and self.is_open:
            # Update position and size when parent window resizes
            self._update_position_and_size()            # If drawer is open, make sure it stays in the correct position
            # The drawer is a direct child of QMainWindow
            correct_x = self.parent_window.width() - self.width()
            self.move(correct_x, 0)
            
    def mousePressEvent(self, event):
        """Handle mouse press to close drawer when clicking outside"""
        super().mousePressEvent(event)
        # This event will only fire for clicks on the drawer itself
        # The parent window will handle clicks outside the drawer
        
    def eventFilter(self, obj, event):
        """Event filter to detect clicks outside the drawer"""
        if event.type() == event.Type.MouseButtonPress:
            if self.is_open and self.parent_window:
                # Check if click is outside the drawer
                drawer_rect = self.geometry()
                click_pos = event.globalPosition().toPoint()
                
                if not drawer_rect.contains(self.parent_window.mapFromGlobal(click_pos)):
                    self.close_drawer()
                    return True
        return super().eventFilter(obj, event)
