"""
Modern sync indicator with spinning arrow and status field component.
Provides real-time sync status and activity updates similar to VS Code's status bar.
"""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QGraphicsOpacityEffect
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtSignal
from PyQt6.QtGui import QPainter, QPen, QFont, QColor
from PyQt6.QtSvgWidgets import QSvgWidget
import math
import os


class SpinningArrowWidget(QSvgWidget):
    """A spinning arrow widget for sync animation."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(16, 16)
        self.rotation_angle = 0
        self.spinning = False
        
        # Create the arrow SVG content
        self.arrow_svg = """<?xml version="1.0" encoding="UTF-8"?>
<svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M8 2L8 14M8 2L12 6M8 2L4 6" stroke="#4A90E2" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
    <circle cx="8" cy="8" r="7" stroke="#4A90E2" stroke-width="1" fill="none" opacity="0.3"/>
</svg>"""
        
        # Load the SVG
        self.load(self.arrow_svg.encode())
        
        # Animation timer
        self.timer = QTimer()
        self.timer.timeout.connect(self._rotate)
        self.timer.setInterval(50)  # 50ms for smooth rotation
        
    def start_spinning(self):
        """Start the spinning animation."""
        if not self.spinning:
            self.spinning = True
            self.timer.start()
            
    def stop_spinning(self):
        """Stop the spinning animation."""
        if self.spinning:
            self.spinning = False
            self.timer.stop()
            self.rotation_angle = 0
            self.update()
            
    def _rotate(self):
        """Rotate the arrow."""
        self.rotation_angle = (self.rotation_angle + 10) % 360
        self.update()
        
    def paintEvent(self, event):
        """Custom paint event to handle rotation."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Translate to center and rotate
        painter.translate(8, 8)
        painter.rotate(self.rotation_angle)
        painter.translate(-8, -8)
        
        # Draw the SVG
        super().paintEvent(event)


class ModernSyncStatusIndicator(QWidget):
    """
    Modern sync indicator with spinning arrow and VS Code-style status field.
    Shows real-time sync status and activity updates.
    """
    
    sync_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # Remove fixed height - allow it to be set by parent container
        self.setMinimumWidth(200)
        
        # Status tracking
        self.is_syncing = False
        self.local_connected = False
        self.remote_connected = False
        self.last_activity = "Ready"
        self.activity_log = []
        
        self._setup_ui()
        self._apply_styling()
        
        # Update timer for activity cycling
        self.activity_timer = QTimer()
        self.activity_timer.timeout.connect(self._cycle_activity)
        self.activity_timer.start(3000)  # Change activity every 3 seconds
        
    def _setup_ui(self):
        """Setup the UI components."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)  # Increased vertical margins for better spacing
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)  # Center vertically
        
        # Spinning arrow (only visible when syncing remote)
        self.arrow = SpinningArrowWidget()
        self.arrow.setVisible(False)  # Hidden by default
        layout.addWidget(self.arrow, 0, Qt.AlignmentFlag.AlignVCenter)
        
        # Status text field (like VS Code status bar)
        self.status_label = QLabel("Ready")
        self.status_label.setObjectName("StatusLabel")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Center content in label
        layout.addWidget(self.status_label, 0, Qt.AlignmentFlag.AlignVCenter)
        
        # No stretch - keep content to the right to stay next to window controls
        
    def _apply_styling(self):
        """Apply modern styling to the component."""
        self.setStyleSheet("""
            ModernSyncStatusIndicator {
                background: transparent;
                border: none;
            }
            
            QLabel#StatusLabel {
                color: rgba(255, 255, 255, 0.8);
                font-size: 11px;
                font-weight: 500;
                font-family: 'Segoe UI', Arial, sans-serif;
                padding: 4px 8px;
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 6px;
                min-width: 120px;
                qproperty-alignment: AlignCenter;
            }
            
            QLabel#StatusLabel:hover {
                background: rgba(255, 255, 255, 0.08);
                border-color: rgba(255, 255, 255, 0.15);
            }
        """)
        
    def update_connection_status(self, status):
        """Update connection status from database manager."""
        self.local_connected = status.get('local_available', False)
        self.remote_connected = status.get('remote_available', False)
        sync_info = status.get('sync_status', {})
        
        was_syncing = self.is_syncing
        self.is_syncing = sync_info.get('is_syncing', False)
        
        # Handle spinning arrow visibility
        if self.is_syncing and self.remote_connected:
            if not was_syncing:  # Just started syncing
                self.arrow.setVisible(True)
                self.arrow.start_spinning()
                self._add_activity("Syncing to remote database...")
        else:
            if was_syncing:  # Just finished syncing
                self.arrow.stop_spinning()
                self.arrow.setVisible(False)
                self._add_activity("Sync completed")
                
        self._update_status_text(sync_info)
        
    def _update_status_text(self, sync_info):
        """Update the status text based on current state."""
        if self.is_syncing:
            pending = sync_info.get('pending_operations', 0)
            if pending > 0:
                text = f"Syncing ({pending} operations)..."
            else:
                text = "Syncing..."
        elif not self.remote_connected and not self.local_connected:
            text = "Offline - No database connection"
        elif not self.remote_connected:
            text = "Local only - Remote unavailable"
        elif not self.local_connected:
            text = "Remote only - Local unavailable"
        else:
            # Both connected
            failed = sync_info.get('failed_operations', 0)
            pending = sync_info.get('pending_operations', 0)
            
            if failed > 0:
                text = f"Sync error - {failed} failed operations"
            elif pending > 0:
                text = f"Pending sync - {pending} operations"
            else:
                last_sync = sync_info.get('last_sync')
                if last_sync:
                    text = "Synced - All databases up to date"
                else:
                    text = "Ready - Databases connected"
                    
        self.status_label.setText(text)
        self.last_activity = text
        
    def _add_activity(self, activity):
        """Add activity to the log."""
        self.activity_log.append(activity)
        # Keep only last 5 activities
        if len(self.activity_log) > 5:
            self.activity_log.pop(0)
            
    def _cycle_activity(self):
        """Cycle through recent activities like VS Code status bar."""
        if not self.is_syncing and len(self.activity_log) > 1:
            # Find current activity index
            current_text = self.status_label.text()
            try:
                current_index = self.activity_log.index(current_text)
                next_index = (current_index + 1) % len(self.activity_log)
                self.status_label.setText(self.activity_log[next_index])
            except (ValueError, IndexError):
                # Fallback to last activity
                if self.activity_log:
                    self.status_label.setText(self.activity_log[-1])
                    
    def manual_sync_requested(self):
        """Handle manual sync request."""
        if self.remote_connected and not self.is_syncing:
            self._add_activity("Manual sync requested...")
            self.sync_requested.emit()
            
    def mousePressEvent(self, event):
        """Handle mouse clicks on the status field."""
        if event.button() == Qt.MouseButton.LeftButton:
            # Show tooltip with recent activities
            if self.activity_log:
                tooltip_text = "Recent Activity:\n" + "\n".join(self.activity_log[-3:])
                self.setToolTip(tooltip_text)
        elif event.button() == Qt.MouseButton.RightButton:
            # Right-click for manual sync
            self.manual_sync_requested()
            
    def add_log_entry(self, message):
        """Add a log entry for real-time updates."""
        self._add_activity(message)
        if not self.is_syncing:
            self.status_label.setText(message)
            
    def show_error(self, error_message):
        """Show an error message."""
        self._add_activity(f"Error: {error_message}")
        self.status_label.setText(f"Error: {error_message}")
        self.status_label.setStyleSheet("""
            QLabel#StatusLabel {
                color: #ff6b6b;
                font-size: 11px;
                font-weight: 500;
                font-family: 'Segoe UI', Arial, sans-serif;
                padding: 2px 6px;
                background: rgba(255, 107, 107, 0.1);
                border: 1px solid rgba(255, 107, 107, 0.3);
                border-radius: 4px;
                min-width: 120px;
            }
        """)
        
        # Reset style after 5 seconds
        QTimer.singleShot(5000, self._apply_styling)
        
    def show_success(self, message):
        """Show a success message."""
        self._add_activity(message)
        self.status_label.setText(message)
        self.status_label.setStyleSheet("""
            QLabel#StatusLabel {
                color: #4ecdc4;
                font-size: 11px;
                font-weight: 500;
                font-family: 'Segoe UI', Arial, sans-serif;
                padding: 2px 6px;
                background: rgba(78, 205, 196, 0.1);
                border: 1px solid rgba(78, 205, 196, 0.3);
                border-radius: 4px;
                min-width: 120px;
            }
        """)
        
        # Reset style after 3 seconds
        QTimer.singleShot(3000, self._apply_styling)
