"""
Compact Sync Button - Window control style sync indicator and manual sync button
Shows connection status with icon and acts as manual sync trigger
"""
from PyQt6.QtWidgets import QPushButton, QToolTip
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QSize
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QIcon
import logging
import os

class CompactSyncButton(QPushButton):
    """Compact sync button that shows connection status and triggers manual sync"""
    
    # Signals
    sync_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("CompactSyncButton")
        self.setFixedSize(40, 32)  # Same size as window control buttons
        self.setToolTip("Connection Status - Click to sync")
        
        # Load the new sync icon
        self._load_sync_icon()
        
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
    
    def _load_sync_icon(self):
        """Load the new sync SVG icon"""
        try:
            icon_path = os.path.join("assets", "icons", "sync_modern.svg")
            if os.path.exists(icon_path):
                self.setIcon(QIcon(icon_path))
                self.setIconSize(QSize(16, 16))  # Match window control button size
            else:
                # Fallback to text if icon not found
                self.setText("↻")
        except Exception as e:
            print(f"Failed to load sync icon: {e}")
            self.setText("↻")
        
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
        
        # No custom painting needed, icon will be shown
        # If syncing, we could potentially animate the icon here (e.g., rotation)
        if self.is_syncing:
            self.setIconSize(QSize(16, 16))  # Reset to original size
            # Potentially apply rotation or other animation to the icon
        else:
            self.setIconSize(QSize(16, 16))  # Reset to original size
        
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
