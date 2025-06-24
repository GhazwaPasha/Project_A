"""
Compact Connection Indicator - WiFi Icon Based
Shows internet/Supabase connection status using WiFi icon with different states
"""
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QPixmap
import logging
import os

class CompactConnectionIndicator(QWidget):
    """WiFi icon-based connection indicator"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("CompactConnectionIndicator")
        self.setFixedSize(32, 32)  # Exact size of window control buttons
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
        wifi_icon_path = os.path.join(project_root, "assets", "icons", "wifi.png")
        
        if os.path.exists(wifi_icon_path):
            pixmap = QPixmap(wifi_icon_path)
            if not pixmap.isNull():
                # Scale the icon to match window control button size (14x14 pixels)
                return pixmap.scaled(14, 14, Qt.AspectRatioMode.KeepAspectRatio, 
                                   Qt.TransformationMode.SmoothTransformation)
        
        # If icon doesn't exist or failed to load, return None
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
        # Set white color for connected state
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
        painter.setOpacity(1.0)
        
        # Fill with white color
        painter.fillRect(icon_x, icon_y, self.wifi_icon.width(), self.wifi_icon.height(), 
                        QColor(255, 255, 255))  # Pure white
        
        # Apply the icon as a mask
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_DestinationIn)
        painter.drawPixmap(icon_x, icon_y, self.wifi_icon)
    
    def _draw_connecting_icon(self, painter, icon_x, icon_y):
        """Draw WiFi icon in connecting state (pulsing white)"""
        # Create pulsing effect by varying opacity between white and grey
        pulse_phases = [0.4, 0.6, 0.8, 1.0]  # Opacity levels for animation
        opacity = pulse_phases[self.animation_phase]
        
        # Use white color with pulsing opacity
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
        painter.setOpacity(1.0)
        
        # Fill with white at varying opacity for pulsing effect
        white_color = QColor(255, 255, 255, int(255 * opacity))
        painter.fillRect(icon_x, icon_y, self.wifi_icon.width(), self.wifi_icon.height(), 
                        white_color)
        
        # Apply the icon as a mask
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_DestinationIn)
        painter.drawPixmap(icon_x, icon_y, self.wifi_icon)
    
    def _draw_offline_icon(self, painter, icon_x, icon_y):
        """Draw WiFi icon in offline state (dark grey color)"""
        # Set dark grey color for disconnected state
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
        painter.setOpacity(1.0)
        
        # Fill with dark grey color
        painter.fillRect(icon_x, icon_y, self.wifi_icon.width(), self.wifi_icon.height(), 
                        QColor(80, 80, 80))  # Dark grey
        
        # Apply the icon as a mask
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_DestinationIn)
        painter.drawPixmap(icon_x, icon_y, self.wifi_icon)
