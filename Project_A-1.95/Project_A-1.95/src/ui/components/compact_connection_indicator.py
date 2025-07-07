"""
Compact Connection Indicator - WiFi Icon Based
Shows internet/Supabase connection status using WiFi icon with different states
"""
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QPixmap, QIcon
import logging
import os

class CompactConnectionIndicator(QWidget):
    """WiFi icon-based connection indicator"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("CompactConnectionIndicator")
        self.setFixedSize(40, 32)  # Match window control button size exactly
        self.setToolTip("Connection Status")
        
        # Apply window control button styling
        self._apply_styling()
        
        # Connection states
        self.is_online = False
        self.is_connecting = False
        
        # Animation for connecting state
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self._animate_connecting)
        self.animation_phase = 0
        
        # Load WiFi icon
        self.wifi_icon = self._load_wifi_icon()
        
        self.logger = logging.getLogger(__name__)
    
    def _load_wifi_icon(self):
        """Load the WiFi icon from the assets/icons directory"""
        # Get the project root directory (3 levels up from src/ui/components/)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
        
        # Use WiFi PNG icon only
        wifi_icon_path = os.path.join(project_root, "assets", "icons", "wifi.png")
        
        if os.path.exists(wifi_icon_path):
            pixmap = QPixmap(wifi_icon_path)
            if not pixmap.isNull():
                # Scale the icon to proper size for window control button alignment (16x16 pixels)
                return pixmap.scaled(16, 16, Qt.AspectRatioMode.KeepAspectRatio, 
                                   Qt.TransformationMode.SmoothTransformation)
        
        # If no icon found, return None
        self.logger.warning(f"WiFi icon not found at: {wifi_icon_path}")
        return None
    
    def _apply_styling(self):
        """Apply window control button styling to match other buttons"""
        self.setStyleSheet("""
            QWidget#CompactConnectionIndicator {
                background: transparent;
                border: none;
                border-radius: 6px;
                padding: 0px;
                margin: 0px;
            }
            QWidget#CompactConnectionIndicator:hover {
                background: rgba(255, 255, 255, 0.1);
            }
        """)
        
    def enterEvent(self, event):
        """Handle mouse enter for hover effect"""
        self.setStyleSheet("""
            QWidget#CompactConnectionIndicator {
                background: rgba(255, 255, 255, 0.1);
                border: none;
                border-radius: 6px;
                padding: 0px;
                margin: 0px;
            }
        """)
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        """Handle mouse leave to remove hover effect"""
        self.setStyleSheet("""
            QWidget#CompactConnectionIndicator {
                background: transparent;
                border: none;
                border-radius: 6px;
                padding: 0px;
                margin: 0px;
            }
        """)
        super().leaveEvent(event)
        
    def update_connection_status(self, is_online, connection_quality=None):
        """Update connection status
        
        Args:
            is_online (bool): Whether connected to internet/Supabase
            connection_quality (str): Ignored - we just show connected/disconnected
        """
        was_online = self.is_online
        self.is_online = is_online
        
        # Update tooltip
        self._update_tooltip()
        
        # Handle connection state changes
        if not was_online and is_online:
            self.logger.info("Connection established")
        elif was_online and not is_online:
            self.logger.info("Connection lost")
        
        self.update()  # Trigger repaint
        
    def set_connecting_state(self, is_connecting):
        """Set connecting animation state"""
        if is_connecting and not self.is_connecting:
            self.is_connecting = True
            self.animation_timer.start(300)  # 300ms intervals for smooth icon animation
            self.logger.info("Connection attempt started")
        elif not is_connecting and self.is_connecting:
            self.is_connecting = False
            self.animation_timer.stop()
            self.animation_phase = 0
            self.logger.info("Connection attempt finished")
        
        self.update()
        
    def _update_tooltip(self):
        """Update tooltip with connection details"""
        if self.is_connecting:
            self.setToolTip("🔄 Connecting...")
        elif self.is_online:
            self.setToolTip("📶 Connected\\nData syncing in real-time")
        else:
            self.setToolTip("📶 Disconnected\\nUsing offline cache")
            
    def _animate_connecting(self):
        """Animate connecting state"""
        self.animation_phase = (self.animation_phase + 1) % 4
        self.update()
        
    def paintEvent(self, event):
        """Custom paint to draw WiFi icon with connection states"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        if self.wifi_icon is None:
            # No fallback label - just return if icon not available
            return
        
        # Get widget center
        center_x = self.width() // 2
        center_y = self.height() // 2
        
        # Calculate icon position (centered)
        icon_x = center_x - self.wifi_icon.width() // 2
        icon_y = center_y - self.wifi_icon.height() // 2
        
        # Save painter state
        painter.save()
        
        if self.is_connecting:
            # Draw animated connecting state
            self._draw_connecting_icon(painter, icon_x, icon_y)
        elif self.is_online:
            # Draw connected state (white)
            self._draw_connected_icon(painter, icon_x, icon_y)
        else:
            # Draw offline/disconnected state (dark grey)
            self._draw_offline_icon(painter, icon_x, icon_y)
        
        # Restore painter state
        painter.restore()
    
    def _draw_connected_icon(self, painter, icon_x, icon_y):
        """Draw WiFi icon in connected state (white color)"""
        # Simply draw the icon with white color using composition
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
        
        # Create a white version of the icon
        colored_pixmap = QPixmap(self.wifi_icon.size())
        colored_pixmap.fill(Qt.GlobalColor.transparent)
        
        temp_painter = QPainter(colored_pixmap)
        temp_painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
        temp_painter.drawPixmap(0, 0, self.wifi_icon)
        
        # Apply white color
        temp_painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        temp_painter.fillRect(colored_pixmap.rect(), QColor(255, 255, 255))
        temp_painter.end()
        
        # Draw the colored icon
        painter.drawPixmap(icon_x, icon_y, colored_pixmap)
    
    def _draw_connecting_icon(self, painter, icon_x, icon_y):
        """Draw WiFi icon in connecting state (pulsing white)"""
        # Create pulsing effect by varying opacity
        pulse_phases = [0.4, 0.6, 0.8, 1.0]  # Opacity levels for animation
        opacity = pulse_phases[self.animation_phase]
        
        # Create a white version of the icon with pulsing opacity
        colored_pixmap = QPixmap(self.wifi_icon.size())
        colored_pixmap.fill(Qt.GlobalColor.transparent)
        
        temp_painter = QPainter(colored_pixmap)
        temp_painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
        temp_painter.drawPixmap(0, 0, self.wifi_icon)
        
        # Apply white color with pulsing opacity
        temp_painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        white_color = QColor(255, 255, 255, int(255 * opacity))
        temp_painter.fillRect(colored_pixmap.rect(), white_color)
        temp_painter.end()
        
        # Draw the colored icon
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
        painter.drawPixmap(icon_x, icon_y, colored_pixmap)
    
    def _draw_offline_icon(self, painter, icon_x, icon_y):
        """Draw WiFi icon in offline state (dark grey color)"""
        # Create a grey version of the icon
        colored_pixmap = QPixmap(self.wifi_icon.size())
        colored_pixmap.fill(Qt.GlobalColor.transparent)
        
        temp_painter = QPainter(colored_pixmap)
        temp_painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
        temp_painter.drawPixmap(0, 0, self.wifi_icon)
        
        # Apply dark grey color
        temp_painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        temp_painter.fillRect(colored_pixmap.rect(), QColor(80, 80, 80))
        temp_painter.end()
        
        # Draw the colored icon
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
        painter.drawPixmap(icon_x, icon_y, colored_pixmap)
