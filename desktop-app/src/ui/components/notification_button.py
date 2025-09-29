"""
Notification Button - Window control style notification indicator with bell icon
Shows notification count badge and acts as notification center trigger
"""
from PyQt6.QtWidgets import QPushButton, QToolTip
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QRect, QSize
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QFontMetrics, QIcon
import logging
import os

class NotificationButton(QPushButton):
    """Compact notification button that shows notification count and triggers notification center"""
      # Signals
    notification_clicked = pyqtSignal()
    
    def __init__(self, parent=None, notification_manager=None):
        super().__init__(parent)
        self.setObjectName("NotificationButton")
        self.setFixedSize(40, 32)  # Same size as window control buttons
        self.setToolTip("Notifications")
        
        # Load the new notification icon
        self._load_notification_icon()
        
        # Notification state
        self.notification_count = 0
        self.has_unread = False
        self.notification_manager = notification_manager
        
        # Setup
        self._apply_styling()
        self.clicked.connect(self._on_notification_clicked)
        
        self.logger = logging.getLogger(__name__)        
        # Connect to notification manager
        if self.notification_manager:
            self.notification_manager.badge_count_changed.connect(self._update_badge_count)
    
    def _load_notification_icon(self):
        """Load the new notification SVG icon"""
        try:
            # Import resource manager
            from ...core.resource_manager import ResourceManager
            
            icon_path = ResourceManager.get_icon_path("notification_modern.svg")
            if icon_path and os.path.exists(icon_path):
                self.setIcon(QIcon(icon_path))
                self.setIconSize(QSize(16, 16))  # Match window control button size
            else:
                # Fallback to text if icon not found
                self.setText("🔔")
        except Exception as e:
            print(f"Failed to load notification icon: {e}")
            self.setText("🔔")
        
    def _apply_styling(self):
        """Apply window control button styling"""
        self.setStyleSheet("""
            QPushButton#NotificationButton {
                background: transparent;
                border: none;
                border-radius: 6px;
                color: rgba(255, 255, 255, 0.8);
                font-size: 16px;
                font-weight: normal;
                padding: 0px;
                margin: 0px;
            }            QPushButton#NotificationButton:hover {
                background: rgba(255, 255, 255, 0.1);
                color: white;
            }            QPushButton#NotificationButton:pressed {
                background: rgba(255, 255, 255, 0.05);
            }
        """)
        
    def paintEvent(self, event):
        """Custom paint to draw SVG icon and notification badge"""
        # First draw the base button (this will include the SVG icon)
        super().paintEvent(event)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Calculate center position for badge
        center_x = self.width() // 2
        center_y = self.height() // 2        # Draw notification count badge if there are notifications
        if self.notification_count > 0:
            # Badge text setup first to calculate proper size
            font = QFont("Segoe UI", 6, QFont.Weight.Bold)  # Smaller font size
            
            # Format count text
            if self.notification_count > 99:
                count_text = "99+"
            else:
                count_text = str(self.notification_count)
              # Calculate text dimensions
            fm = QFontMetrics(font)
            text_rect = fm.boundingRect(count_text)
            text_width = text_rect.width()
            text_height = text_rect.height()
            
            # Dynamic badge sizing based on content
            if self.notification_count <= 9:
                # Single digit - circular badge
                badge_radius = 7
                badge_x = center_x + 7
                badge_y = center_y - 7
            elif self.notification_count <= 99:
                # Double digit - slightly larger circular badge
                badge_radius = 9
                badge_x = center_x + 8
                badge_y = center_y - 8
            else:
                # 99+ - largest badge for text
                badge_radius = 10
                badge_x = center_x + 9
                badge_y = center_y - 9
            
            # FIRST: Draw badge background circle
            badge_color = QColor(220, 53, 69)  # Windows 11 red
            badge_border = QColor(255, 255, 255, 40)
            painter.setPen(QPen(badge_border, 0.5))
            painter.setBrush(QBrush(badge_color))
            painter.drawEllipse(badge_x - badge_radius, badge_y - badge_radius, 
                              badge_radius * 2, badge_radius * 2)
            
            # SECOND: Draw text ON TOP of the badge circle
            painter.setPen(QPen(QColor(255, 255, 255), 1))
            painter.setFont(font)
            
            # Perfect text centering within the badge circle
            text_x = badge_x - text_width // 2
            text_y = badge_y + fm.ascent() // 2 - 1  # Better vertical centering
            
            painter.drawText(text_x, text_y, count_text)
            
    def set_notification_count(self, count):
        """Update notification count and badge visibility"""
        self.notification_count = max(0, count)
        self.has_unread = self.notification_count > 0
        
        # Update tooltip
        if self.notification_count == 0:
            self.setToolTip("Notifications")
        elif self.notification_count == 1:
            self.setToolTip("1 new notification")
        else:
            self.setToolTip(f"{self.notification_count} new notifications")
            
        self.update()  # Trigger repaint
        
    def add_notification(self, notification_data=None):
        """Add a new notification (increments count)"""
        self.set_notification_count(self.notification_count + 1)
        self.logger.info(f"New notification added. Total: {self.notification_count}")
        
    def clear_notifications(self):
        """Clear all notifications"""
        self.set_notification_count(0)
        self.logger.info("All notifications cleared")
        
    def mark_as_read(self, count_to_remove=None):
        """Mark notifications as read (decrements count)"""
        if count_to_remove is None:
            # Mark all as read
            self.set_notification_count(0)
        else:
            # Mark specific count as read
            self.set_notification_count(self.notification_count - count_to_remove)
            
    def _on_notification_clicked(self):
        """Handle notification button click"""
        self.logger.info("Notification button clicked")
        self.notification_clicked.emit()
        
    def show_notification_preview(self, title, message, duration=3000):
        """Show a brief notification preview in tooltip"""
        original_tooltip = self.toolTip()
        preview_text = f"{title}\n{message}"
        self.setToolTip(preview_text)
        
        # Restore original tooltip after duration
        QTimer.singleShot(duration, lambda: self.setToolTip(original_tooltip))
        
    def _update_badge_count(self, count):
        """Update badge count from notification manager."""
        self.set_notification_count(count)
    
    # Convenience methods for common notification scenarios
    def add_system_notification(self, message):
        """Add a system notification"""
        self.add_notification({"type": "system", "message": message})
        
    def add_sync_notification(self, message):
        """Add a sync-related notification"""
        self.add_notification({"type": "sync", "message": message})
        
    def add_ai_notification(self, message):
        """Add an AI-related notification"""
        self.add_notification({"type": "ai", "message": message})
