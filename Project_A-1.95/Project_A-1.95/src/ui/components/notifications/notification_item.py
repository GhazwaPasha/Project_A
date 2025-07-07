"""
Notification Item - Individual notification component for the notification drawer.
"""
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from datetime import datetime
import json

# Local responsive helper implementation
class ResponsiveHelper:
    """Simple responsive helper for notification items."""
    
    @staticmethod
    def scale_size(small, medium, large):
        """Return medium size for simplicity."""
        return medium
    
    @staticmethod
    def get_base_font_size():
        """Get base font size for responsive design."""
        return 10  # Default font size
    
    @staticmethod
    def get_scale_factor():
        """Get scale factor for responsive design."""
        return 1.0  # Default scale


class NotificationItem(QFrame):
    """Individual notification item widget."""
    
    # Signals
    marked_as_read = pyqtSignal(str)  # notification_id
    removed = pyqtSignal(str)  # notification_id
    
    def __init__(self, notification_data: dict, parent=None):
        super().__init__(parent)
        self.notification_data = notification_data
        self.notification_id = notification_data['id']
        self._setup_ui()
        self._apply_styling()
    
    def _setup_ui(self):
        """Setup the notification item UI."""
        self.setObjectName("NotificationItem")
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 8, 12, 8)
        main_layout.setSpacing(6)
        
        # Header row with icon and title
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)
        
        # Notification type icon
        icon_label = QLabel(self._get_type_icon())
        icon_label.setFixedSize(20, 20)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet(f"""
            QLabel {{
                color: {self._get_type_color()};
                font-size: 16px;
                background: transparent;
            }}
        """)
        header_layout.addWidget(icon_label)
        
        # Title
        title_label = QLabel(self.notification_data['title'])
        title_label.setWordWrap(True)
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {'white' if not self.notification_data['is_read'] else 'rgba(255, 255, 255, 0.7)'};
                font-size: {ResponsiveHelper.scale_size(13, 12, 14)}px;
                font-weight: {'600' if not self.notification_data['is_read'] else '400'};
                background: transparent;
            }}
        """)
        header_layout.addWidget(title_label, 1)
        
        # Small remove button
        remove_btn = QPushButton("×")
        remove_btn.setFixedSize(16, 16)
        remove_btn.setToolTip("Remove notification")
        remove_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: rgba(255, 255, 255, 0.4);
                font-size: 12px;
                font-weight: bold;
                border-radius: 8px;
            }
            QPushButton:hover {
                background: rgba(255, 80, 80, 0.3);
                color: white;
            }
        """)
        remove_btn.clicked.connect(self._remove_notification)
        header_layout.addWidget(remove_btn)
        
        main_layout.addLayout(header_layout)
        
        # Message
        if self.notification_data['message']:
            message_label = QLabel(self.notification_data['message'])
            message_label.setWordWrap(True)
            message_label.setStyleSheet(f"""
                QLabel {{
                    color: rgba(255, 255, 255, 0.8);
                    font-size: {ResponsiveHelper.scale_size(12, 11, 13)}px;
                    background: transparent;
                    margin-left: 28px;
                }}
            """)
            main_layout.addWidget(message_label)
        
        # Timestamp
        timestamp_label = QLabel(self._format_timestamp())
        timestamp_label.setStyleSheet(f"""
            QLabel {{
                color: rgba(255, 255, 255, 0.5);
                font-size: {ResponsiveHelper.scale_size(10, 9, 11)}px;
                background: transparent;
                margin-left: 28px;
            }}
        """)
        main_layout.addWidget(timestamp_label)
        
        # Click handler for marking as read
        self.mousePressEvent = self._on_click
    
    def _apply_styling(self):
        """Apply styling to the notification item."""
        is_read = self.notification_data['is_read']
        
        self.setStyleSheet(f"""
            QFrame#NotificationItem {{
                background: {'rgba(255, 255, 255, 0.03)' if is_read else 'rgba(255, 255, 255, 0.08)'};
                border: {'1px solid rgba(255, 255, 255, 0.05)' if is_read else '1px solid rgba(255, 255, 255, 0.12)'};
                border-radius: 8px;
                margin: 2px 0;
            }}
            QFrame#NotificationItem:hover {{
                background: rgba(255, 255, 255, 0.12);
                border-color: rgba(255, 255, 255, 0.2);
            }}
        """)
    
    def _get_type_icon(self) -> str:
        """Get icon for notification type."""
        icons = {
            'info': 'ℹ️',
            'success': '✅',
            'warning': '⚠️',
            'error': '❌',
            'sync': '🔄',
            'system': '⚙️',
            'business': '📊',
            'user': '👤',
            'security': '🔒'
        }
        return icons.get(self.notification_data['type'], 'ℹ️')
    
    def _get_type_color(self) -> str:
        """Get color for notification type."""
        colors = {
            'info': '#64B5F6',
            'success': '#4CAF50',
            'warning': '#FF9800',
            'error': '#F44336',
            'sync': '#2196F3',
            'system': '#9E9E9E',
            'business': '#9C27B0',
            'user': '#00BCD4',
            'security': '#FF5722'
        }
        return colors.get(self.notification_data['type'], '#64B5F6')
    
    def _format_timestamp(self) -> str:
        """Format timestamp for display."""
        try:
            timestamp = datetime.fromisoformat(self.notification_data['timestamp'])
            now = datetime.now()
            diff = now - timestamp
            
            if diff.total_seconds() < 60:
                return "Just now"
            elif diff.total_seconds() < 3600:
                minutes = int(diff.total_seconds() / 60)
                return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
            elif diff.total_seconds() < 86400:
                hours = int(diff.total_seconds() / 3600)
                return f"{hours} hour{'s' if hours != 1 else ''} ago"
            elif diff.days < 7:
                return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
            else:
                return timestamp.strftime("%b %d, %Y")
        except:
            return "Unknown"
    
    def _on_click(self, event):
        """Handle click to mark as read."""
        if not self.notification_data['is_read']:
            self.notification_data['is_read'] = True
            self._apply_styling()
            self.marked_as_read.emit(self.notification_id)
        
        # Accept event to prevent propagation
        event.accept()
    
    def _remove_notification(self):
        """Handle remove button click."""
        self.removed.emit(self.notification_id)
    
    def update_read_status(self, is_read: bool):
        """Update the read status of the notification."""
        if self.notification_data['is_read'] != is_read:
            self.notification_data['is_read'] = is_read
            self._apply_styling()
            # Update title styling
            for child in self.findChildren(QLabel):
                if child.text() == self.notification_data['title']:
                    child.setStyleSheet(f"""
                        QLabel {{
                            color: {'white' if not is_read else 'rgba(255, 255, 255, 0.7)'};
                            font-size: {ResponsiveHelper.scale_size(13, 12, 14)}px;
                            font-weight: {'600' if not is_read else '400'};
                            background: transparent;
                        }}
                    """)
                    break
