"""
A modern circular progress dialog for showing import progress.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QProgressBar,
    QWidget, QPushButton
)
from PyQt6.QtCore import Qt, QTimer
from ..components.styles import ModernStyles, GlassmorphismHelper

class CircularProgressDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.cancelled = False
        self._setup_ui()

    def set_progress(self, value, status=None):
        """Update progress bar value and optionally status text."""
        self.progress_bar.setValue(value)
        if status:
            self.status_label.setText(status)
            
    def _handle_cancel(self):
        """Handle cancel button click."""
        self.cancelled = True
        self.status_label.setText("Cancelling...")
        self.cancel_btn.setEnabled(False)
        
    def was_cancelled(self):
        """Check if the operation was cancelled."""
        return self.cancelled

    def _setup_ui(self):
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)  # Increased margins

        # Container widget with solid background
        container = QWidget(self)
        container.setStyleSheet("""
            QWidget {
                background: rgb(40, 44, 52);
                border-radius: 20px;
                border: 2px solid rgba(255, 255, 255, 0.3);
                color: white;
            }
        """)
        
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(30, 30, 30, 30)  # Increased internal padding
        container_layout.setSpacing(20)  # Increased spacing between elements

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 15px;
                background: rgb(30, 33, 39);
                height: 30px;
                text-align: center;
                margin: 0px 15px;
                font-size: 16px;
                color: white;
            }
            QProgressBar::chunk {
                border-radius: 15px;
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3498db,
                    stop:1 #2980b9
                );
            }
        """)
        
        # Status label
        self.status_label = QLabel("Processing...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 16px;
                margin: 10px;
            }
        """)

        # Cancel button
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                color: white;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 14px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.15);
                border: 1px solid rgba(255, 255, 255, 0.3);
            }
            QPushButton:pressed {
                background: rgba(255, 255, 255, 0.05);
            }
            QPushButton:disabled {
                background: rgba(255, 255, 255, 0.05);
                color: rgba(255, 255, 255, 0.3);
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
        """)
        self.cancel_btn.clicked.connect(self._handle_cancel)
        
        # Add widgets to layout
        container_layout.addWidget(self.progress_bar)
        container_layout.addWidget(self.status_label)
        container_layout.addWidget(self.cancel_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Add container to main layout
        layout.addWidget(container)
        
        # Set dialog size - increased from 400x200 to 500x250
        self.setFixedSize(500, 300)  # Made slightly taller for cancel button
        
        # Set the dialog's background color to match container
        self.setStyleSheet("""
            QDialog {
                background: rgb(40, 44, 52);
            }
        """)
