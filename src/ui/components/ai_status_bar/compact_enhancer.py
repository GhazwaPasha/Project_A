"""
Compact AI Status Bar Enhancement - Additional animations and effects
"""
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QTimer, pyqtSignal
from PyQt6.QtWidgets import QGraphicsOpacityEffect
from PyQt6.QtGui import QFont


class CompactAIEnhancer:
    """Handles animations and visual enhancements for compact AI status bar"""
    
    def __init__(self, ai_container, status_text, avatar):
        self.ai_container = ai_container
        self.status_text = status_text
        self.avatar = avatar
        
        # Animation setup
        self.pulse_animation = None
        self.text_animation = None
        self.setup_animations()
    
    def setup_animations(self):
        """Setup smooth animations for the compact AI bar"""
        # Pulse animation for avatar
        self.pulse_animation = QPropertyAnimation(self.avatar, b"styleSheet")
        self.pulse_animation.setDuration(2000)
        self.pulse_animation.setLoopCount(-1)
        
        # Opacity animation for status text
        self.opacity_effect = QGraphicsOpacityEffect()
        self.status_text.setGraphicsEffect(self.opacity_effect)
        
        self.fade_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_animation.setDuration(500)
        self.fade_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)

    def pulse_avatar(self, mood="happy"):
        """Create pulsing effect on avatar based on mood with VS Code styling"""
        base_style = """
            QLabel {
                font-size: 14px;
                padding: 4px;
                border-radius: 4px;
                background: rgba(97, 175, 239, 0.15);
                border: 1px solid rgba(97, 175, 239, 0.3);
                min-width: 20px;
                max-width: 20px;
                min-height: 20px;
                max-height: 20px;
            }
        """
        
        # Mood-based color variations
        mood_colors = {
            "happy": "rgba(97, 175, 239, 0.25)",
            "excited": "rgba(255, 165, 0, 0.25)",
            "focused": "rgba(75, 175, 75, 0.25)",
            "tired": "rgba(128, 128, 128, 0.25)",
            "stressed": "rgba(255, 99, 99, 0.25)"
        }
        
        mood_color = mood_colors.get(mood, "rgba(97, 175, 239, 0.25)")
        pulse_style = base_style.replace("0.15)", mood_color + ")").replace("0.3)", mood_color.replace("0.25)", "0.5)"))
        
        self.pulse_animation.setStartValue(base_style)
        self.pulse_animation.setEndValue(pulse_style)
        self.pulse_animation.start()

    def animate_text_change(self, new_text):
        """Animate text changes with fade effect"""
        # Disconnect any previous connections to avoid multiple calls
        try:
            self.fade_animation.finished.disconnect()
        except:
            pass  # No previous connections
            
        def set_new_text():
            self.status_text.setText(new_text)
            # Fade back in
            self.fade_animation.setStartValue(0.0)
            self.fade_animation.setEndValue(1.0)
            try:
                self.fade_animation.finished.disconnect()
            except:
                pass
            self.fade_animation.start()
        
        # Fade out current text
        self.fade_animation.setStartValue(1.0)
        self.fade_animation.setEndValue(0.0)
        self.fade_animation.finished.connect(set_new_text)
        self.fade_animation.start()

    def highlight_urgent(self):
        """Highlight the entire bar for urgent notifications with VS Code warning styling"""
        highlight_style = """
            QFrame#CompactAIBar {
                background: #663300;
                border: 1px solid #ff9500;
                border-radius: 4px;
                margin: 2px;
            }
        """
        
        # Animate to highlight
        QTimer.singleShot(0, lambda: self.ai_container.setStyleSheet(highlight_style))
        
        # Return to normal after 3 seconds
        QTimer.singleShot(3000, self.return_to_normal)
    
    def return_to_normal(self):
        """Return to normal VS Code styling"""
        normal_style = """
            QFrame#CompactAIBar {
                background: #3c3c3c;
                border: 1px solid #5a5a5a;
                border-radius: 4px;
                margin: 2px;
            }
            QFrame#CompactAIBar:hover {
                border: 1px solid #0e639c;
            }
            QFrame#CompactAIBar:focus-within {
                border: 1px solid #007acc;
                box-shadow: 0 0 0 1px rgba(0, 122, 204, 0.4);
            }
        """
        self.ai_container.setStyleSheet(normal_style)
