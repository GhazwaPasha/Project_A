from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QSize
from PyQt6.QtGui import QPixmap, QFont, QPalette, QColor, QIcon
from ...core.resource_manager import ResourceManager
from .styles import ModernStyles


class LoadingScreen(QWidget):
    """Loading screen with app logo and animated message"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # Set window icon for taskbar
        app_icon_path = ResourceManager.get_icon_path("app-icon.ico")
        if app_icon_path:
            self.setWindowIcon(QIcon(app_icon_path))
        self.setup_ui()
        self.start_animation()
        
    def setup_ui(self):
        """Setup the loading screen UI"""
        # Set window properties
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create main container with glassmorphism effect
        container = QFrame()
        container.setObjectName("loadingContainer")
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(60, 60, 60, 60)
        container_layout.setSpacing(40)
        
        # App logo
        logo_label = QLabel()
        logo_label.setObjectName("appLogo")
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Load app logo
        logo_path = ResourceManager.get_icon_path("app-icon.png")
        if logo_path:
            pixmap = QPixmap(logo_path)
            # Scale logo to reasonable size (200x200)
            scaled_pixmap = pixmap.scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            logo_label.setPixmap(scaled_pixmap)
        else:
            # Fallback text logo
            logo_label.setText("Accountuitive")
            logo_label.setStyleSheet("font-size: 48px; font-weight: bold; color: white;")
        
        # Loading message
        self.message_label = QLabel("GOOD THINGS TAKE TIME")
        self.message_label.setObjectName("loadingMessage")
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Animated dots
        self.dots_label = QLabel("...")
        self.dots_label.setObjectName("loadingDots")
        self.dots_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Add widgets to container
        container_layout.addWidget(logo_label)
        container_layout.addWidget(self.message_label)
        container_layout.addWidget(self.dots_label)
        
        # Add container to main layout
        layout.addWidget(container)
        
        # Apply styling
        self.apply_styling()
        
    def apply_styling(self):
        """Apply modern glassmorphism styling"""
        self.setStyleSheet("""
            QWidget#loadingContainer {
                background: rgba(20, 20, 20, 0.85);
                border-radius: 20px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
            
            QLabel#loadingMessage {
                color: rgba(255, 255, 255, 0.9);
                font-size: 18px;
                font-weight: 500;
                background: transparent;
                border: none;
            }
            
            QLabel#loadingDots {
                color: rgba(255, 255, 255, 0.7);
                font-size: 24px;
                font-weight: bold;
                background: transparent;
                border: none;
            }
            
            QLabel#appLogo {
                background: transparent;
                border: none;
            }
        """)
        
    def start_animation(self):
        """Start the dots animation"""
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.animate_dots)
        self.animation_timer.start(500)  # Update every 500ms
        self.dot_count = 0
        
    def animate_dots(self):
        """Animate the loading dots"""
        self.dot_count = (self.dot_count + 1) % 4
        dots = "." * self.dot_count
        self.dots_label.setText(dots)
        
    def show_loading_screen(self):
        """Show the loading screen centered on the screen."""
        self.show()
        from PyQt6.QtWidgets import QApplication
        QApplication.processEvents()  # Ensure geometry is updated

        # Get screen geometry
        screen = QApplication.primaryScreen()
        if screen:
            screen_geometry = screen.availableGeometry()
            window_geometry = self.frameGeometry()
            x = screen_geometry.x() + (screen_geometry.width() - window_geometry.width()) // 2
            y = screen_geometry.y() + (screen_geometry.height() - window_geometry.height()) // 2
            self.move(x, y)

        self.raise_()
        self.activateWindow()
        
    def hide_loading_screen(self):
        """Hide the loading screen"""
        if self.animation_timer:
            self.animation_timer.stop()
        self.hide() 