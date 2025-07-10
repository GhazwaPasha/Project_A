"""
Seamless Border Layout for Mica Windows
Creates a layout where content fills the entire window area and borders are positioned
around the edges without creating gaps or empty spaces.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFrame
from PyQt6.QtCore import Qt, QPoint, QRect
from PyQt6.QtGui import QCursor, QMouseEvent
from enum import Enum

class ResizeDirection(Enum):
    NONE = 0
    LEFT = 1
    RIGHT = 2
    TOP = 3
    BOTTOM = 4
    TOP_LEFT = 5
    TOP_RIGHT = 6
    BOTTOM_LEFT = 7
    BOTTOM_RIGHT = 8

class SeamlessResizeBorder(QFrame):
    """A border widget that handles resizing without creating visual gaps"""
    
    def __init__(self, direction: ResizeDirection, parent=None):
        super().__init__(parent)
        self.direction = direction
        self.is_resizing = False
        self.resize_start_pos = QPoint()
        self.resize_start_geometry = QRect()
        
        # Set cursor based on direction
        self.setCursor(self._get_cursor_for_direction())        # Make border more transparent but still functional for mouse events
        self.setStyleSheet("""
            QFrame {
                background: rgba(0, 0, 0, 0.01);
                border: none;
            }
        """)
        
        # Set size - very thin but functional
        if direction in [ResizeDirection.LEFT, ResizeDirection.RIGHT]:
            self.setFixedWidth(2)  # Thinner borders
        elif direction in [ResizeDirection.TOP, ResizeDirection.BOTTOM]:
            self.setFixedHeight(2)  # Thinner borders
        else:  # Corners
            self.setFixedSize(4, 4)  # Smaller corners
    
    def _get_cursor_for_direction(self):
        """Get appropriate cursor for resize direction"""
        cursor_map = {
            ResizeDirection.LEFT: Qt.CursorShape.SizeHorCursor,
            ResizeDirection.RIGHT: Qt.CursorShape.SizeHorCursor,
            ResizeDirection.TOP: Qt.CursorShape.SizeVerCursor,
            ResizeDirection.BOTTOM: Qt.CursorShape.SizeVerCursor,
            ResizeDirection.TOP_LEFT: Qt.CursorShape.SizeFDiagCursor,
            ResizeDirection.TOP_RIGHT: Qt.CursorShape.SizeBDiagCursor,
            ResizeDirection.BOTTOM_LEFT: Qt.CursorShape.SizeBDiagCursor,
            ResizeDirection.BOTTOM_RIGHT: Qt.CursorShape.SizeFDiagCursor,
        }
        return QCursor(cursor_map.get(self.direction, Qt.CursorShape.ArrowCursor))
    
    def mousePressEvent(self, event):
        """Start resize operation"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_resizing = True
            self.resize_start_pos = event.globalPosition().toPoint()
            self.resize_start_geometry = self.window().geometry()
            event.accept()
    
    def mouseMoveEvent(self, event):
        """Handle resize dragging"""
        if self.is_resizing:
            delta = event.globalPosition().toPoint() - self.resize_start_pos
            self._resize_window(delta)
            event.accept()
    
    def mouseReleaseEvent(self, event):
        """End resize operation"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_resizing = False
            event.accept()
    
    def _resize_window(self, delta):
        """Resize window based on direction and delta"""
        window = self.window()
        if not window:
            return
            
        new_geo = QRect(self.resize_start_geometry)
        
        # Adjust geometry based on direction
        if self.direction == ResizeDirection.LEFT:
            new_geo.setLeft(new_geo.left() + delta.x())
        elif self.direction == ResizeDirection.RIGHT:
            new_geo.setRight(new_geo.right() + delta.x())
        elif self.direction == ResizeDirection.TOP:
            new_geo.setTop(new_geo.top() + delta.y())
        elif self.direction == ResizeDirection.BOTTOM:
            new_geo.setBottom(new_geo.bottom() + delta.y())
        elif self.direction == ResizeDirection.TOP_LEFT:
            new_geo.setTopLeft(new_geo.topLeft() + delta)
        elif self.direction == ResizeDirection.TOP_RIGHT:
            new_geo.setTop(new_geo.top() + delta.y())
            new_geo.setRight(new_geo.right() + delta.x())
        elif self.direction == ResizeDirection.BOTTOM_LEFT:
            new_geo.setLeft(new_geo.left() + delta.x())
            new_geo.setBottom(new_geo.bottom() + delta.y())
        elif self.direction == ResizeDirection.BOTTOM_RIGHT:
            new_geo.setBottomRight(new_geo.bottomRight() + delta)
        
        # Enforce minimum size
        min_size = window.minimumSize()
        if new_geo.width() < min_size.width():
            if self.direction in [ResizeDirection.LEFT, ResizeDirection.TOP_LEFT, ResizeDirection.BOTTOM_LEFT]:
                new_geo.setLeft(new_geo.right() - min_size.width())
            else:
                new_geo.setWidth(min_size.width())
        
        if new_geo.height() < min_size.height():
            if self.direction in [ResizeDirection.TOP, ResizeDirection.TOP_LEFT, ResizeDirection.TOP_RIGHT]:
                new_geo.setTop(new_geo.bottom() - min_size.height())
            else:
                new_geo.setHeight(min_size.height())
        
        window.setGeometry(new_geo)

class SeamlessBorderLayout:
    """Creates a seamless border layout for frameless windows"""
    
    @staticmethod
    def apply_to_window(window):
        """Apply seamless border layout to a window"""
        print("🔧 Applying seamless border layout...")
        
        # Get the current central widget
        current_widget = window.centralWidget()
        if not current_widget:
            print("❌ No central widget found")
            return        # Create main container with borders and minimal background for mouse events
        main_container = QWidget()
        # Use minimal opacity to capture mouse events while preserving Mica  
        main_container.setStyleSheet("""
            QWidget {
                background: rgba(0, 0, 0, 0.01);
            }
        """)
        
        # DO NOT apply Mica to the border container - let the main window handle Mica
        # This prevents conflicts with the main window's Mica effect
        # try:
        #     from .mica_effect import MicaEffect
        #     MicaEffect.apply_mica(main_container, dark_mode=True)
        # except:
        #     pass  # Continue without Mica if it fails
        
        # Main layout with borders
        main_layout = QVBoxLayout(main_container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Top row: corners and top border
        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(0)
        
        top_left = SeamlessResizeBorder(ResizeDirection.TOP_LEFT)
        top_border = SeamlessResizeBorder(ResizeDirection.TOP)
        top_right = SeamlessResizeBorder(ResizeDirection.TOP_RIGHT)
        
        top_row.addWidget(top_left)
        top_row.addWidget(top_border, 1)  # Stretch to fill
        top_row.addWidget(top_right)
        
        top_container = QWidget()
        top_container.setLayout(top_row)
        main_layout.addWidget(top_container)
        
        # Middle row: left border, content, right border
        middle_row = QHBoxLayout()
        middle_row.setContentsMargins(0, 0, 0, 0)
        middle_row.setSpacing(0)
        
        left_border = SeamlessResizeBorder(ResizeDirection.LEFT)
        right_border = SeamlessResizeBorder(ResizeDirection.RIGHT)
        
        middle_row.addWidget(left_border)
        middle_row.addWidget(current_widget, 1)  # Content takes all space
        middle_row.addWidget(right_border)
        
        middle_container = QWidget()
        middle_container.setLayout(middle_row)
        main_layout.addWidget(middle_container, 1)  # Content area stretches
        
        # Bottom row: corners and bottom border
        bottom_row = QHBoxLayout()
        bottom_row.setContentsMargins(0, 0, 0, 0)
        bottom_row.setSpacing(0)
        
        bottom_left = SeamlessResizeBorder(ResizeDirection.BOTTOM_LEFT)
        bottom_border = SeamlessResizeBorder(ResizeDirection.BOTTOM)
        bottom_right = SeamlessResizeBorder(ResizeDirection.BOTTOM_RIGHT)
        
        bottom_row.addWidget(bottom_left)
        bottom_row.addWidget(bottom_border, 1)  # Stretch to fill
        bottom_row.addWidget(bottom_right)
        
        bottom_container = QWidget()
        bottom_container.setLayout(bottom_row)
        main_layout.addWidget(bottom_container)
        
        # Set the new container as central widget
        window.setCentralWidget(main_container)
        
        print("✅ Seamless border layout applied!")

def apply_seamless_borders(window):
    """Convenience function to apply seamless borders"""
    SeamlessBorderLayout.apply_to_window(window)
