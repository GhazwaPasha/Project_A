"""
Notification Button - Window control style notification indicator with bell icon
Shows notification count badge and acts as notification center trigger
"""
from PyQt6.QtWidgets import QPushButton, QToolTip
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QRect
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QFontMetrics
import logging

class NotificationButton(QPushButton):
    """Compact notification button that shows notification count and triggers notification center"""
    
    # Signals
    notification_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("NotificationButton")
        self.setFixedSize(40, 32)  # Same size as window control buttons
        self.setToolTip("Notifications")
        
        # Notification state
        self.notification_count = 0
        self.has_unread = False
        
        # Setup
        self._apply_styling()
        self.clicked.connect(self._on_notification_clicked)
        
        self.logger = logging.getLogger(__name__)
        
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
            }
            QPushButton#NotificationButton:pressed {
                background: rgba(255, 255, 255, 0.05);
            }
        """)
        
    def paintEvent(self, event):
        """Custom paint to draw enhanced bell icon and notification badge"""
        super().paintEvent(event)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Calculate center and icon size
        center_x = self.width() // 2
        center_y = self.height() // 2
        
        # Enhanced bell icon with better proportions
        bell_color = QColor(255, 255, 255, 210) if not self.has_unread else QColor(255, 255, 255, 255)
        painter.setPen(QPen(bell_color, 1.5))
        painter.setBrush(QBrush(Qt.BrushStyle.NoBrush))
        
        # Bell dimensions
        bell_width = 14
        bell_height = 12
        bell_top_y = center_y - 6
        bell_bottom_y = center_y + 4
        
        # Draw bell body (more realistic bell shape)
        # Main bell body outline
        bell_path = QPainter(self)
        bell_path.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Bell dome (top arc)
        painter.drawArc(center_x - bell_width//2, bell_top_y - 1, bell_width, 10, 0, 180 * 16)
        
        # Bell sides (curved outward)
        painter.drawLine(center_x - bell_width//2, bell_top_y + 3, center_x - 3, bell_bottom_y)
        painter.drawLine(center_x + bell_width//2, bell_top_y + 3, center_x + 3, bell_bottom_y)
        
        # Bell bottom rim
        painter.setPen(QPen(bell_color, 2))
        painter.drawLine(center_x - 3, bell_bottom_y, center_x + 3, bell_bottom_y)
        
        # Bell handle (attachment point)
        painter.setPen(QPen(bell_color, 1.5))
        painter.setBrush(QBrush(bell_color))
        painter.drawEllipse(center_x - 1, bell_top_y - 4, 2, 3)
        painter.setBrush(QBrush(Qt.BrushStyle.NoBrush))
        
        # Bell clapper (more subtle)
        clapper_color = QColor(255, 255, 255, 130)
        painter.setPen(QPen(clapper_color, 1))
        painter.drawEllipse(center_x - 1, bell_bottom_y - 2, 2, 2)
        
        # Sound lines (if has unread notifications)
        if self.has_unread:
            sound_color = QColor(255, 255, 255, 100)
            painter.setPen(QPen(sound_color, 1))
            # Right side sound lines
            painter.drawArc(center_x + 8, center_y - 4, 6, 8, 180 * 16, 90 * 16)
            painter.drawArc(center_x + 10, center_y - 6, 8, 12, 180 * 16, 90 * 16)
            # Left side sound lines
            painter.drawArc(center_x - 14, center_y - 4, 6, 8, 270 * 16, 90 * 16)
            painter.drawArc(center_x - 18, center_y - 6, 8, 12, 270 * 16, 90 * 16)
        
        # Draw notification count badge if there are notifications
        if self.notification_count > 0:
            # Enhanced badge with gradient
            badge_color = QColor(220, 53, 69)  # Windows 11 red
            badge_border = QColor(255, 255, 255, 40)
            
            # Badge position (top-right of bell)
            badge_x = center_x + 7
            badge_y = center_y - 7
            badge_radius = 8
            
            # Adjust badge size based on count
            if self.notification_count > 99:
                badge_radius = 11
                badge_x = center_x + 8
            elif self.notification_count > 9:
                badge_radius = 9
                badge_x = center_x + 7
                
            # Draw badge background with subtle border
            painter.setPen(QPen(badge_border, 0.5))
            painter.setBrush(QBrush(badge_color))
            painter.drawEllipse(badge_x - badge_radius//2, badge_y - badge_radius//2, 
                              badge_radius, badge_radius)
            
            # Badge text with better typography
            painter.setPen(QPen(QColor(255, 255, 255), 1))
            font = QFont("Segoe UI", 7, QFont.Weight.Bold)
            painter.setFont(font)
            
            # Format count text
            if self.notification_count > 99:
                count_text = "99+"
            else:
                count_text = str(self.notification_count)
                
            # Center text in badge with better positioning
            fm = QFontMetrics(font)
            text_rect = fm.boundingRect(count_text)
            text_x = badge_x - text_rect.width() // 2
            text_y = badge_y + text_rect.height() // 2 - 1
            
            painter.drawText(text_x, text_y, count_text)
            badge_y = center_y - 6
            badge_radius = 8
            
            # Adjust badge size based on count
            if self.notification_count > 99:
                badge_radius = 10
            elif self.notification_count > 9:
                badge_radius = 9
                
            painter.drawEllipse(badge_x - badge_radius//2, badge_y - badge_radius//2, 
                              badge_radius, badge_radius)
            
            # Badge text
            painter.setPen(QPen(QColor(255, 255, 255), 1))
            font = QFont("Segoe UI", 7, QFont.Weight.Bold)
            painter.setFont(font)
            
            # Format count text
            if self.notification_count > 99:
                count_text = "99+"
            else:
                count_text = str(self.notification_count)
                
            # Center text in badge
            fm = QFontMetrics(font)
            text_rect = fm.boundingRect(count_text)
            text_x = badge_x - text_rect.width() // 2
            text_y = badge_y + text_rect.height() // 2 - 1
            
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
