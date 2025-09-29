from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QProgressBar, QFrame, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect
from PyQt6.QtGui import QFont, QPalette, QColor, QPainter, QPainterPath
import sys


class WorkspaceSwitchingProgress(QDialog):
    """
    VS Code-style progress popup for workspace switching
    Shows a modal dialog with progress bar and status updates
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        print(f"🎯 Progress popup: constructor called with parent: {parent}")
        self.setup_ui()
        self.setup_animations()
        print(f"🎯 Progress popup: setup complete")
        
    def setup_ui(self):
        """Setup the UI components"""
        # Window setup
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.Tool |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setFixedSize(400, 120)
        print(f"🎯 Progress popup: window flags set, size: {self.size()}")
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create the main container with rounded corners and shadow
        self.container = QFrame()
        self.container.setObjectName("ProgressContainer")
        self.container.setFixedSize(400, 120)
        
        # Apply shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 4)
        self.container.setGraphicsEffect(shadow)
        
        # Container layout
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(24, 20, 24, 20)
        container_layout.setSpacing(16)
        
        # Title
        self.title_label = QLabel("Switching Workspace")
        self.title_label.setObjectName("ProgressTitle")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Status text
        self.status_label = QLabel("Preparing workspace...")
        self.status_label.setObjectName("ProgressStatus")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setWordWrap(True)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("ProgressBar")
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        
        # Add widgets to container
        container_layout.addWidget(self.title_label)
        container_layout.addWidget(self.status_label)
        container_layout.addWidget(self.progress_bar)
        
        # Add container to main layout
        main_layout.addWidget(self.container)
        
        # Apply styling
        self.apply_styling()
        
    def apply_styling(self):
        """Apply VS Code-style styling"""
        if self.is_dark_mode():
            container_bg = "rgba(37, 37, 38, 0.97)"  # VS Code dark
            progress_bg = "rgba(255, 255, 255, 0.08)"
            text_color = "#F3F3F3"
        else:
            container_bg = "rgba(255, 255, 255, 0.97)"  # VS Code light
            progress_bg = "rgba(0, 0, 0, 0.08)"
            text_color = "#222222"
        progress_fill = "#007ACC"  # VS Code blue

        self.setStyleSheet(f"""
            QDialog {{
                background: transparent;
            }}
            QFrame#ProgressContainer {{
                background: {container_bg};
                border-radius: 12px;
                border: 1px solid rgba(0, 0, 0, 0.1);
            }}
            QLabel#ProgressTitle {{
                color: {text_color};
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 16px;
                font-weight: 600;
                margin: 0;
                padding: 0;
            }}
            QLabel#ProgressStatus {{
                color: {text_color};
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 13px;
                font-weight: 400;
                margin: 0;
                padding: 0;
                opacity: 0.8;
            }}
            QProgressBar#ProgressBar {{
                border: none;
                background: {progress_bg};
                border-radius: 3px;
                margin: 0;
                padding: 0;
            }}
            QProgressBar#ProgressBar::chunk {{
                background: {progress_fill};
                border-radius: 3px;
                margin: 0;
                padding: 0;
            }}
        """)
    
    def is_dark_mode(self):
        """Check if system is in dark mode"""
        try:
            palette = self.palette()
            bg_color = palette.color(QPalette.ColorRole.Window)
            # Simple heuristic: if background is dark, assume dark mode
            return bg_color.lightness() < 128
        except:
            return False
    
    def setup_animations(self):
        """Setup fade in/out animations"""
        # Fade in animation
        self.fade_in_anim = QPropertyAnimation(self, b"windowOpacity")
        self.fade_in_anim.setDuration(200)
        self.fade_in_anim.setStartValue(0.0)
        self.fade_in_anim.setEndValue(1.0)
        self.fade_in_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Fade out animation
        self.fade_out_anim = QPropertyAnimation(self, b"windowOpacity")
        self.fade_out_anim.setDuration(150)
        self.fade_out_anim.setStartValue(1.0)
        self.fade_out_anim.setEndValue(0.0)
        self.fade_out_anim.setEasingCurve(QEasingCurve.Type.InCubic)
        self.fade_out_anim.finished.connect(self.close)
    
    def show_progress(self, parent=None):
        """Show the progress dialog with fade in animation"""
        print(f"🎯 Progress popup: show_progress called with parent: {parent}")
        if parent:
            self.setParent(parent)
            # Center on parent
            parent_rect = parent.geometry()
            x = parent_rect.center().x() - self.width() // 2
            y = parent_rect.center().y() - self.height() // 2
            self.move(x, y)
            print(f"🎯 Progress popup: positioned at ({x}, {y})")
        
        self.show()
        print(f"🎯 Progress popup: show() called, visible: {self.isVisible()}")
        self.fade_in_anim.start()
        print(f"🎯 Progress popup: fade in animation started")
    
    def hide_progress(self):
        """Hide the progress dialog with fade out animation"""
        self.fade_out_anim.start()
    
    def update_status(self, status_text: str, progress_value: int | None = None):
        """Update the status text and optionally the progress value"""
        print(f"🎯 Progress popup: updating status to '{status_text}' with progress {progress_value}")
        self.status_label.setText(status_text)
        if progress_value is not None:
            self.progress_bar.setValue(progress_value)
            print(f"🎯 Progress popup: progress bar set to {progress_value}%")
    
    def set_progress(self, value: int):
        """Set the progress bar value (0-100)"""
        self.progress_bar.setValue(max(0, min(100, value)))
    
    def paintEvent(self, event):
        """Custom paint event for rounded corners"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
        painter.fillRect(self.rect(), Qt.GlobalColor.transparent) 