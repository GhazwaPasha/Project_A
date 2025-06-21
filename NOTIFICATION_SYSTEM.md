# Notification System Documentation

## Overview
The notification system is a modular, persistent, and visually appealing notification solution for the PyQt6 desktop application. It features a slide-in drawer from the right side, badge counts, and glassmorphism styling.

## Components

### 1. NotificationManager (`src/ui/components/notifications/notification_manager.py`)
- **Purpose**: Core notification service with SQLite persistence and signal management
- **Features**:
  - Persistent storage of notifications
  - Signal-based communication (`notification_added`, `badge_count_changed`)
  - CRUD operations for notifications
  - Badge count management

### 2. NotificationButton (`src/ui/components/notification_button.py`)
- **Purpose**: Window control style notification indicator with bell icon
- **Features**:
  - Custom bell icon with sound lines animation
  - Badge count display (supports 99+ format)
  - Hover effects and styling
  - Integrates with NotificationManager for real-time updates

### 3. NotificationDrawer (`src/ui/components/notifications/notification_drawer.py`)
- **Purpose**: Main notification panel that slides in from the right
- **Features**:
  - Sliding animation with smooth easing
  - Auto-hide functionality (configurable timeout)
  - Scrollable content area
  - "Clear All" functionality
  - Glassmorphism styling
  - Focus management

### 4. NotificationItem (`src/ui/components/notifications/notification_item.py`)
- **Purpose**: Individual notification widget
- **Features**:
  - Type-based styling (info, success, warning, error)
  - Timestamp display
  - Mark as read/Remove actions
  - Responsive design

## Usage

### Basic Usage
```python
# In your main window initialization
from ui.components.notifications.notification_manager import NotificationManager
from ui.components.notifications.notification_drawer import NotificationDrawer
from ui.components.notification_button import NotificationButton

# Initialize notification manager
self.notification_manager = NotificationManager()

# Create notification button (usually in title bar)
self.notification_button = NotificationButton(self, self.notification_manager)
self.notification_button.clicked.connect(self._show_notifications)

# Create notification drawer (overlay)
self.notification_drawer = NotificationDrawer(self, self.notification_manager)
self.notification_drawer.hide()

# Install event filter for click-outside-to-close
self.installEventFilter(self)
```

### Adding Notifications
```python
# Add a notification
self.notification_manager.add_notification(
    title="Sync Complete",
    message="Your data has been synchronized successfully.",
    notification_type="success"
)

# Or use the convenience method
self.add_notification("Task Complete", "Your task has finished successfully.", "info")
```

### Event Filter Implementation
```python
def eventFilter(self, obj, event):
    """Filter events to handle click-outside-to-close for notification drawer."""
    from PyQt6.QtCore import QEvent
    from PyQt6.QtGui import QMouseEvent
    
    if event.type() == QEvent.Type.MouseButtonPress:
        if isinstance(event, QMouseEvent):
            if hasattr(self, 'notification_drawer') and self.notification_drawer.isVisible():
                global_pos = event.globalPosition().toPoint()
                drawer_pos = self.notification_drawer.mapFromGlobal(global_pos)
                
                if not self.notification_drawer.rect().contains(drawer_pos):
                    if hasattr(self, 'notification_button'):
                        btn_pos = self.notification_button.mapFromGlobal(global_pos)
                        if not self.notification_button.rect().contains(btn_pos):
                            self.notification_drawer.hide()
                            return True
    
    return super().eventFilter(obj, event)
```

### Positioning the Drawer
```python
def _position_notification_drawer(self):
    """Position the notification drawer on the right side"""
    if not hasattr(self, 'notification_drawer'):
        return
        
    drawer_width = 320  # Or use ResponsiveHelper.scale_size(320, 360, 400)
    
    # Calculate position relative to content area
    content_rect = self.content_widget.geometry()
    title_bar_height = self.title_bar.height() if hasattr(self, 'title_bar') else 40
    
    # Position overlaying the right side of content
    x = content_rect.right() - drawer_width
    y = title_bar_height
    height = content_rect.height()
    
    self.notification_drawer.setGeometry(x, y, drawer_width, height)
```

## Database Schema
The notification system uses SQLite with the following schema:
```sql
CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    message TEXT,
    type TEXT DEFAULT 'info',
    is_read BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

## Notification Types
- **info**: General information (blue accent)
- **success**: Success messages (green accent)
- **warning**: Warning messages (orange accent)
- **error**: Error messages (red accent)

## Auto-hide Behavior
- The drawer auto-hides after 30 seconds of inactivity (configurable)
- Auto-hide is disabled when the mouse is over the drawer
- Clicking outside the drawer also closes it
- The escape key can close the drawer

## Styling
The notification system follows the app's glassmorphism/Mica design:
- Translucent backgrounds with blur effects
- Modern gradients and subtle borders
- Smooth animations and transitions
- Consistent typography and spacing

## Testing
Run the standalone test:
```bash
python test_notification_system.py
```

This creates a minimal test window to verify all components work independently.

## Integration Status
✅ **Completed:**
- NotificationManager with SQLite persistence
- NotificationButton with badge count and animations
- NotificationDrawer with slide-in animation and auto-hide
- NotificationItem with type-based styling
- MainWindow integration with event filtering
- Click-outside-to-close functionality
- Window resize handling for drawer repositioning
- Standalone test application

✅ **Ready for use** in the main accounting application.
