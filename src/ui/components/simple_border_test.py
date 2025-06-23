"""
Simple Border Test - Minimal implementation to test if border widgets work
"""

from PyQt6.QtWidgets import QWidget, QFrame, QVBoxLayout, QHBoxLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCursor

class SimpleBorderTest(QFrame):
    """Simple test border widget"""
    
    def __init__(self, direction_name, parent=None):
        super().__init__(parent)
        self.direction_name = direction_name
        self.setFixedSize(8, 8) if 'corner' in direction_name else (
            self.setFixedWidth(8) if 'left' in direction_name or 'right' in direction_name 
            else self.setFixedHeight(8)
        )
        
        # Make very visible for testing
        self.setStyleSheet("""
            QFrame {
                background: rgba(255, 0, 0, 0.8);
                border: 2px solid yellow;
            }
        """)
        
        self.setCursor(QCursor(Qt.CursorShape.SizeAllCursor))
        
    def mousePressEvent(self, event):
        print(f"🎯 CLICKED ON {self.direction_name} BORDER!")
        super().mousePressEvent(event)

def add_simple_test_borders(window):
    """Add simple test borders to see if they work at all"""
    print("🧪 Adding simple test borders...")
    
    # Get the current central widget
    current_widget = window.centralWidget()
    if not current_widget:
        print("❌ No central widget found")
        return
    
    # Create a container
    container = QWidget()
    layout = QVBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)
    
    # Top border
    top_border = SimpleBorderTest("top")
    layout.addWidget(top_border)
    
    # Middle: left border + content + right border
    middle = QHBoxLayout()
    middle.setContentsMargins(0, 0, 0, 0)
    middle.setSpacing(0)
    
    left_border = SimpleBorderTest("left")
    right_border = SimpleBorderTest("right")
    
    middle.addWidget(left_border)
    middle.addWidget(current_widget, 1)
    middle.addWidget(right_border)
    
    layout.addLayout(middle, 1)
    
    # Bottom border
    bottom_border = SimpleBorderTest("bottom")
    layout.addWidget(bottom_border)
    
    # Set the container as the new central widget
    window.setCentralWidget(container)
    print("✅ Simple test borders added!")
