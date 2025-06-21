"""
Debug script to find the exact position of the notification button
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from src.ui.mainwindow import MainWindow

def debug_button_position(window):
    """Debug function to print button positions"""
    print(f"\n🔍 BUTTON POSITION DEBUG:")
    print(f"   Main window size: {window.width()}x{window.height()}")
    print(f"   Main window position: {window.pos().x()}, {window.pos().y()}")
    
    if hasattr(window, 'notification_button'):
        btn = window.notification_button
        btn_pos = btn.mapToGlobal(btn.rect().topLeft())
        btn_pos_relative = btn.mapTo(window, btn.rect().topLeft())
        
        print(f"   Notification button global position: {btn_pos.x()}, {btn_pos.y()}")
        print(f"   Notification button relative to window: {btn_pos_relative.x()}, {btn_pos_relative.y()}")
        print(f"   Notification button size: {btn.width()}x{btn.height()}")
        
        # Calculate where drawer should appear
        drawer_x = window.width() - 320  # Assuming 320px drawer width
        print(f"   Expected drawer X position: {drawer_x}")
        
        # Test if the button is on the right side
        if btn_pos_relative.x() > window.width() / 2:
            print(f"   ✅ Button is on RIGHT side of window")
        else:
            print(f"   ❌ Button is on LEFT side of window - this might be the issue!")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    
    # Wait a bit for window to fully load, then debug
    QTimer.singleShot(1000, lambda: debug_button_position(window))
    
    sys.exit(app.exec())
