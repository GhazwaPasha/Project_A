from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QToolTip
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QIcon, QPalette, QColor, QFont
import os

class SyncIndicator(QWidget):
    """Simple sync status indicator widget."""
    
    sync_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(30)
        self.setup_ui()
        
        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_status)
        self.update_timer.start(5000)  # Update every 5 seconds
        
        # Connection status
        self.connection_status = {
            'local_available': False,
            'remote_available': False,
            'is_syncing': False,
            'last_sync': None,
            'pending_operations': 0,
            'failed_operations': 0
        }
    
    def setup_ui(self):
        """Setup the sync indicator UI."""
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(8)
        
        # Database status indicators
        self.local_indicator = QLabel("●")
        self.local_indicator.setFixedSize(12, 12)
        self.local_indicator.setStyleSheet("color: #666; font-size: 16px;")
        self.local_indicator.setToolTip("Local Database")
        
        self.remote_indicator = QLabel("●")
        self.remote_indicator.setFixedSize(12, 12)
        self.remote_indicator.setStyleSheet("color: #666; font-size: 16px;")
        self.remote_indicator.setToolTip("Remote Database")
        
        # Sync status label
        self.sync_label = QLabel("Offline")
        self.sync_label.setStyleSheet("""
            QLabel {
                color: #888;
                font-size: 11px;
                font-weight: 500;
            }
        """)
        
        # Manual sync button
        self.sync_button = QPushButton("↻")
        self.sync_button.setFixedSize(20, 20)
        self.sync_button.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
                color: #888;
                font-size: 14px;
                font-weight: bold;
                border-radius: 10px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.1);
                color: #fff;
            }
            QPushButton:pressed {
                background: rgba(255, 255, 255, 0.05);
            }
        """)
        self.sync_button.setToolTip("Manual Sync")
        self.sync_button.clicked.connect(self.sync_requested.emit)
        
        # Add widgets to layout
        layout.addWidget(QLabel("DB:"))
        layout.addWidget(self.local_indicator)
        layout.addWidget(self.remote_indicator)
        layout.addWidget(self.sync_label)
        layout.addStretch()
        layout.addWidget(self.sync_button)
        
        self.setLayout(layout)
    
    def update_connection_status(self, status):
        """Update the connection status from database manager."""
        self.connection_status = status
        self.update_indicators()
    
    def update_indicators(self):
        """Update visual indicators based on connection status."""
        # Local database indicator
        if self.connection_status.get('local_available', False):
            self.local_indicator.setStyleSheet("color: #4CAF50; font-size: 16px;")
            self.local_indicator.setToolTip("Local Database: Connected")
        else:
            self.local_indicator.setStyleSheet("color: #f44336; font-size: 16px;")
            self.local_indicator.setToolTip("Local Database: Disconnected")
        
        # Remote database indicator
        if self.connection_status.get('remote_available', False):
            self.remote_indicator.setStyleSheet("color: #4CAF50; font-size: 16px;")
            self.remote_indicator.setToolTip("Remote Database: Connected")
        else:
            self.remote_indicator.setStyleSheet("color: #f44336; font-size: 16px;")
            self.remote_indicator.setToolTip("Remote Database: Disconnected")
        
        # Sync status label
        sync_status = self.connection_status.get('sync_status', {})
        
        if sync_status.get('is_syncing', False):
            self.sync_label.setText("Syncing...")
            self.sync_label.setStyleSheet("QLabel { color: #2196F3; font-size: 11px; font-weight: 500; }")
            self.sync_button.setEnabled(False)
        elif (self.connection_status.get('local_available', False) and 
              self.connection_status.get('remote_available', False)):
            
            pending = sync_status.get('pending_operations', 0)
            failed = sync_status.get('failed_operations', 0)
            last_sync = sync_status.get('last_sync')
            
            if failed > 0:
                self.sync_label.setText(f"Sync Error ({failed})")
                self.sync_label.setStyleSheet("QLabel { color: #f44336; font-size: 11px; font-weight: 500; }")
            elif pending > 0:
                self.sync_label.setText(f"Pending ({pending})")
                self.sync_label.setStyleSheet("QLabel { color: #FF9800; font-size: 11px; font-weight: 500; }")
            elif last_sync:
                self.sync_label.setText("Synced")
                self.sync_label.setStyleSheet("QLabel { color: #4CAF50; font-size: 11px; font-weight: 500; }")
            else:
                self.sync_label.setText("Ready")
                self.sync_label.setStyleSheet("QLabel { color: #4CAF50; font-size: 11px; font-weight: 500; }")
            
            self.sync_button.setEnabled(True)
        else:
            self.sync_label.setText("Offline")
            self.sync_label.setStyleSheet("QLabel { color: #888; font-size: 11px; font-weight: 500; }")
            self.sync_button.setEnabled(False)
    
    def update_status(self):
        """Periodic status update - to be connected to database manager."""
        # This will be called by the main window to update status
        pass
    
    def show_sync_animation(self):
        """Show syncing animation."""
        self.sync_button.setText("⟳")
        QTimer.singleShot(1000, lambda: self.sync_button.setText("↻"))
