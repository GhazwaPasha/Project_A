"""
Compact Sync Button - Window control style sync indicator and manual sync button
Shows connection status with split circle icon and acts as manual sync trigger
"""
from PyQt6.QtWidgets import QPushButton, QToolTip
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush
import logging

class CompactSyncButton(QPushButton):
    """Compact sync button that shows connection status and triggers manual sync"""
    
    # Signals
    sync_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("CompactSyncButton")
        self.setFixedSize(40, 32)  # Same size as window control buttons
        self.setToolTip("Connection Status - Click to sync")
        
        # Connection status
        self.local_connected = False
        self.remote_connected = False
        self.is_syncing = False
        
        # Setup
        self._apply_styling()
        self.clicked.connect(self._on_sync_clicked)
        
        # Animation timer for syncing state
        self.sync_animation_timer = QTimer()
        self.sync_animation_timer.timeout.connect(self._animate_sync)
        self.sync_animation_phase = 0
        
        self.logger = logging.getLogger(__name__)
        
    def _apply_styling(self):
        """Apply window control button styling"""
        self.setStyleSheet("""
            QPushButton#CompactSyncButton {
                background: transparent;
                border: none;
                border-radius: 6px;
                color: rgba(255, 255, 255, 0.8);
                font-size: 16px;
                font-weight: normal;
                padding: 0px;
                margin: 0px;
            }
            QPushButton#CompactSyncButton:hover {
                background: rgba(255, 255, 255, 0.1);
                color: white;
            }
            QPushButton#CompactSyncButton:pressed {
                background: rgba(255, 255, 255, 0.05);
            }
        """)
        
    def paintEvent(self, event):
        """Custom paint to draw split circle connection indicator"""
        super().paintEvent(event)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Calculate center and size
        center_x = self.width() // 2
        center_y = self.height() // 2
        radius = 6
        
        if self.is_syncing:
            # Animated sync state - pulsing full circle
            alpha = int(128 + 127 * abs(1 - (self.sync_animation_phase % 2)))
            color = QColor(0, 122, 204, alpha)  # Blue pulse
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(color, 1))
            painter.drawEllipse(center_x - radius, center_y - radius, radius * 2, radius * 2)
        else:
            # Split circle showing connection status
            # Left half - Local DB
            if self.local_connected:
                color = QColor(46, 204, 113)  # Green for connected
            else:
                color = QColor(231, 76, 60)   # Red for disconnected
                
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(color, 1))
            
            # Draw left semicircle
            painter.drawChord(
                center_x - radius, center_y - radius, 
                radius * 2, radius * 2, 
                90 * 16, 180 * 16  # 90 to 270 degrees (left half)
            )
            
            # Right half - Remote DB
            if self.remote_connected:
                color = QColor(52, 152, 219)  # Blue for connected
            else:
                color = QColor(149, 165, 166) # Gray for disconnected
                
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(color, 1))
            
            # Draw right semicircle
            painter.drawChord(
                center_x - radius, center_y - radius,
                radius * 2, radius * 2,
                270 * 16, 180 * 16  # 270 to 90 degrees (right half)
            )
            
            # Draw center divider line
            painter.setPen(QPen(QColor(255, 255, 255, 100), 1))
            painter.drawLine(center_x, center_y - radius, center_x, center_y + radius)
        
    def update_connection_status(self, status):
        """Update connection status from database manager"""
        try:
            self.local_connected = status.get('local_available', False)
            self.remote_connected = status.get('remote_available', False)
            
            sync_status = status.get('sync_status', {})
            was_syncing = self.is_syncing
            self.is_syncing = sync_status.get('is_syncing', False)
            
            # Update tooltip with detailed status
            self._update_tooltip(status)
            
            # Handle sync animation
            if self.is_syncing and not was_syncing:
                self.sync_animation_timer.start(100)  # 100ms intervals
            elif not self.is_syncing and was_syncing:
                self.sync_animation_timer.stop()
                self.sync_animation_phase = 0
            
            self.update()  # Trigger repaint
            
        except Exception as e:
            self.logger.error(f"Error updating sync button status: {e}")
            
    def _update_tooltip(self, status):
        """Update tooltip with connection details"""
        try:
            local_status = "Connected" if self.local_connected else "Disconnected"
            remote_status = "Connected" if self.remote_connected else "Disconnected"
            
            sync_status = status.get('sync_status', {})
            last_sync = sync_status.get('last_sync', 'Never')
            pending_ops = sync_status.get('pending_operations', 0)
            
            if self.is_syncing:
                tooltip = f"🔄 Syncing...\nLocal: {local_status}\nRemote: {remote_status}"
            else:
                tooltip = f"Local DB: {local_status}\nRemote DB: {remote_status}"
                if last_sync != 'Never':
                    tooltip += f"\nLast sync: {last_sync}"
                if pending_ops > 0:
                    tooltip += f"\nPending: {pending_ops} operations"
                tooltip += "\n\nClick to sync manually"
            
            self.setToolTip(tooltip)
            
        except Exception as e:
            self.setToolTip("Connection Status - Click to sync")
            
    def _animate_sync(self):
        """Animate syncing state"""
        self.sync_animation_phase += 0.1
        self.update()
        
    def _on_sync_clicked(self):
        """Handle sync button click"""
        if not self.is_syncing:
            self.logger.info("Manual sync requested from compact button")
            self.sync_requested.emit()
        
    def show_success(self, message):
        """Show success feedback (brief tooltip update)"""
        original_tooltip = self.toolTip()
        self.setToolTip(f"✅ {message}")
        # Restore original tooltip after 3 seconds
        QTimer.singleShot(3000, lambda: self.setToolTip(original_tooltip))
        
    def show_error(self, message):
        """Show error feedback (brief tooltip update)"""
        original_tooltip = self.toolTip()
        self.setToolTip(f"❌ {message}")
        # Restore original tooltip after 5 seconds
        QTimer.singleShot(5000, lambda: self.setToolTip(original_tooltip))
