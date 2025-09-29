"""
Notification Manager - Core service for handling notifications in the AI Accountant application.
"""
import json
import sqlite3
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from PyQt6.QtCore import QObject, pyqtSignal
import logging


class NotificationManager(QObject):
    """Core notification management service."""
    
    # Signals
    notification_added = pyqtSignal(dict)  # Emitted when new notification is added
    notification_removed = pyqtSignal(str)  # Emitted when notification is removed
    notification_cleared = pyqtSignal()  # Emitted when all notifications are cleared
    badge_count_changed = pyqtSignal(int)  # Emitted when unread count changes
    
    def __init__(self, db_path: Optional[str] = None):
        super().__init__()
        self.logger = logging.getLogger(__name__)
          # Database setup - use cache directory
        if not db_path:
            cache_dir = os.path.join(os.path.expanduser('~'), '.ai_accountant_cache')
            os.makedirs(cache_dir, exist_ok=True)
            db_path = os.path.join(cache_dir, 'notifications.db')
        self.db_path = db_path
        self._init_database()
        
        # In-memory cache for active notifications
        self._notifications = []
        self._load_recent_notifications()
    
    def _init_database(self):
        """Initialize the notifications database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS notifications (
                        id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        message TEXT NOT NULL,
                        type TEXT DEFAULT 'info',
                        category TEXT DEFAULT 'general',
                        timestamp TEXT NOT NULL,
                        is_read BOOLEAN DEFAULT FALSE,
                        is_archived BOOLEAN DEFAULT FALSE,
                        metadata TEXT DEFAULT '{}'
                    )
                ''')
                conn.commit()
        except Exception as e:
            self.logger.error(f"Failed to initialize notifications database: {e}")
    
    def add_notification(self, title: str, message: str, notification_type: str = "info", 
                        category: str = "general", metadata: Optional[Dict] = None) -> str:
        """Add a new notification."""
        # Validate inputs to prevent empty notifications
        if not title or not title.strip():
            self.logger.warning("Attempted to add notification with empty title - skipping")
            return ""
        if not message or not message.strip():
            self.logger.warning("Attempted to add notification with empty message - skipping")
            return ""
            
        notification_id = f"notif_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        timestamp = datetime.now().isoformat()
        metadata = metadata or {}
        
        notification = {
            'id': notification_id,
            'title': title,
            'message': message,
            'type': notification_type,
            'category': category,
            'timestamp': timestamp,
            'is_read': False,
            'is_archived': False,
            'metadata': metadata
        }
        
        # Save to database
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO notifications 
                    (id, title, message, type, category, timestamp, is_read, is_archived, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    notification_id, title, message, notification_type, category,
                    timestamp, False, False, json.dumps(metadata)
                ))
                conn.commit()
        except Exception as e:
            self.logger.error(f"Failed to save notification to database: {e}")
            return ""
        
        # Add to in-memory cache
        self._notifications.insert(0, notification)  # Most recent first
        
        # Emit signals
        self.notification_added.emit(notification)
        self._update_badge_count()
        
        self.logger.info(f"Added notification: {title}")
        return notification_id
    
    def mark_as_read(self, notification_id: str) -> bool:
        """Mark a notification as read."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    'UPDATE notifications SET is_read = TRUE WHERE id = ?',
                    (notification_id,)
                )
                conn.commit()
                
                if cursor.rowcount > 0:
                    # Update in-memory cache
                    for notif in self._notifications:
                        if notif['id'] == notification_id:
                            notif['is_read'] = True
                            break
                    
                    self._update_badge_count()
                    return True
                    
        except Exception as e:
            self.logger.error(f"Failed to mark notification as read: {e}")
        
        return False
    
    def remove_notification(self, notification_id: str) -> bool:
        """Remove a notification."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    'UPDATE notifications SET is_archived = TRUE WHERE id = ?',
                    (notification_id,)
                )
                conn.commit()
                
                if cursor.rowcount > 0:
                    # Remove from in-memory cache
                    self._notifications = [n for n in self._notifications if n['id'] != notification_id]
                    
                    self.notification_removed.emit(notification_id)
                    self._update_badge_count()
                    return True
                    
        except Exception as e:
            self.logger.error(f"Failed to remove notification: {e}")
        
        return False
    
    def clear_all_notifications(self) -> bool:
        """Clear all notifications."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('UPDATE notifications SET is_archived = TRUE WHERE is_archived = FALSE')
                conn.commit()
            
            # Clear in-memory cache
            self._notifications.clear()
            
            self.notification_cleared.emit()
            self._update_badge_count()
            
            self.logger.info("Cleared all notifications")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to clear notifications: {e}")
            return False
    
    def get_notifications(self, limit: int = 50, include_read: bool = True) -> List[Dict]:
        """Get notifications from cache."""
        notifications = self._notifications[:limit]
        
        if not include_read:
            notifications = [n for n in notifications if not n['is_read']]
        
        return notifications
    
    def get_unread_count(self) -> int:
        """Get count of unread notifications."""
        return len([n for n in self._notifications if not n['is_read']])
    
    def _load_recent_notifications(self, days: int = 7):
        """Load recent notifications from database into memory."""
        try:
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    SELECT id, title, message, type, category, timestamp, is_read, is_archived, metadata
                    FROM notifications 
                    WHERE timestamp > ? AND is_archived = FALSE
                    ORDER BY timestamp DESC
                    LIMIT 100
                ''', (cutoff_date,))
                
                self._notifications = []
                for row in cursor.fetchall():
                    notification = {
                        'id': row[0],
                        'title': row[1],
                        'message': row[2],
                        'type': row[3],
                        'category': row[4],
                        'timestamp': row[5],
                        'is_read': bool(row[6]),
                        'is_archived': bool(row[7]),
                        'metadata': json.loads(row[8] or '{}')
                    }
                    self._notifications.append(notification)
                    
        except Exception as e:
            self.logger.error(f"Failed to load notifications from database: {e}")
            self._notifications = []
    
    def _update_badge_count(self):
        """Update and emit badge count."""
        count = self.get_unread_count()
        self.badge_count_changed.emit(count)
    
    def cleanup_old_notifications(self, days: int = 30):
        """Clean up old notifications from database."""
        try:
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    'DELETE FROM notifications WHERE timestamp < ? AND is_archived = TRUE',
                    (cutoff_date,)
                )
                conn.commit()
                
                self.logger.info(f"Cleaned up {cursor.rowcount} old notifications")
                
        except Exception as e:
            self.logger.error(f"Failed to cleanup old notifications: {e}")


# Notification type constants
class NotificationType:
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    SYNC = "sync"


# Notification category constants
class NotificationCategory:
    SYSTEM = "system"
    BUSINESS = "business"
    USER = "user"
    SYNC = "sync"
    SECURITY = "security"
