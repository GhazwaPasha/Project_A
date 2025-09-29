"""
A modern Windows 11 style progress dialog for showing import progress.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QProgressBar,
    QWidget, QPushButton
)
from PyQt6.QtCore import Qt


class CircularProgressDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
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
        # Main layout for the dialog
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Create a container widget with proper curved edges
        container = QWidget()
        container.setStyleSheet("""
            QWidget {
                background: rgb(24, 28, 34);
                border-radius: 12px;
            }
        """)

        # Container layout with proper spacing
        layout = QVBoxLayout(container)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(24)

        # Title label with proper sizing
        title_label = QLabel("Processing")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.9);
                font-size: 18px;
                font-weight: 600;
                background: transparent;
                border: none;
                padding: 4px 0px;
            }
        """)
          # Progress bar with modern Windows 11 style
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 8px;
                background: rgba(255, 255, 255, 0.1);
                height: 28px;
                text-align: center;
                font-size: 13px;
                font-weight: 500;
                color: rgba(255, 255, 255, 0.9);
                padding: 2px;
            }
            QProgressBar::chunk {
                border-radius: 8px;
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(100, 181, 246, 0.8),
                    stop:1 rgba(100, 181, 246, 1.0)
                );
            }
        """)
        
        # Status label with modern styling
        self.status_label = QLabel("Preparing...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.7);
                font-size: 13px;
                font-weight: 400;
                background: transparent;
                border: none;
                padding: 4px 0px;
            }
        """)        # Cancel button with Windows 11 styling
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.3);
                color: rgba(255, 255, 255, 0.9);
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: 500;
                min-width: 80px;
                min-height: 36px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.15);
                border: 1px solid rgba(100, 181, 246, 0.3);
                color: white;
            }
            QPushButton:pressed {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(100, 181, 246, 0.2);
            }
            QPushButton:disabled {
                background: rgba(255, 255, 255, 0.05);
                color: rgba(255, 255, 255, 0.4);
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
        """)
        self.cancel_btn.clicked.connect(self._handle_cancel)
        
        # Add widgets to container layout
        layout.addWidget(title_label)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.status_label)
        layout.addWidget(self.cancel_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Add container to main layout
        main_layout.addWidget(container)
        
        # Set dialog size
        self.setFixedSize(400, 280)
        
        # Make dialog background transparent so container shows with curved edges
        self.setStyleSheet("""
            QDialog {
                background: transparent;
            }
        """)
