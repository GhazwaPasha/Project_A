"""
Simple Border Solution for Mica Window
Creates resize borders as Qt widgets inside the MainWindow
This ensures they're part of the Mica-applied area and receive input properly
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

class ResizeBorderWidget(QFrame):
    """A border widget that handles resizing for one edge/corner"""
    
    def __init__(self, direction: ResizeDirection, parent=None):
        super().__init__(parent)
        self.direction = direction
        self.is_resizing = False
        self.resize_start_pos = QPoint()
        self.resize_start_geometry = QRect()
        
        # Set cursor based on direction
        self.setCursor(self._get_cursor_for_direction())
          # Make border invisible but functional
        self.setStyleSheet("""
            QFrame {
                background: rgba(255, 0, 0, 0.3);
                border: 1px solid red;
            }
        """)
        
        # Set minimum size
        if direction in [ResizeDirection.LEFT, ResizeDirection.RIGHT]:
            self.setFixedWidth(8)
        elif direction in [ResizeDirection.TOP, ResizeDirection.BOTTOM]:
            self.setFixedHeight(8)
        else:  # Corners
            self.setFixedSize(8, 8)
    
    def _get_cursor_for_direction(self):
        """Get appropriate cursor for resize direction"""
        cursor_map = {
            ResizeDirection.LEFT: Qt.CursorShape.SizeHorCursor,
            ResizeDirection.RIGHT: Qt.CursorShape.SizeHorCursor,
            ResizeDirection.TOP: Qt.CursorShape.SizeVerCursor,
            ResizeDirection.BOTTOM: Qt.CursorShape.SizeVerCursor,
            ResizeDirection.TOP_LEFT: Qt.CursorShape.SizeFDiagCursor,
            ResizeDirection.BOTTOM_RIGHT: Qt.CursorShape.SizeFDiagCursor,
            ResizeDirection.TOP_RIGHT: Qt.CursorShape.SizeBDiagCursor,
            ResizeDirection.BOTTOM_LEFT: Qt.CursorShape.SizeBDiagCursor,        }
        return QCursor(cursor_map.get(self.direction, Qt.CursorShape.ArrowCursor))
    
    def mousePressEvent(self, event):
        """Start resize operation"""
        print(f"🖱️ Border {self.direction.name} clicked!")
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_resizing = True
            self.resize_start_pos = event.globalPosition().toPoint()
            self.resize_start_geometry = self.window().geometry()
            self.setCursor(self._get_cursor_for_direction())
            print(f"🔄 Starting resize from {self.resize_start_pos}")
    
    def mouseMoveEvent(self, event):
        """Handle resize dragging"""
        if self.is_resizing:
            self._perform_resize(event.globalPosition().toPoint())
    
    def mouseReleaseEvent(self, event):
        """End resize operation"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_resizing = False
            self.setCursor(self._get_cursor_for_direction())
    
    def _perform_resize(self, global_pos):
        """Perform the actual window resizing"""
        window = self.window()
        delta = global_pos - self.resize_start_pos
        geometry = QRect(self.resize_start_geometry)
        
        # Apply resize based on direction
        if self.direction == ResizeDirection.LEFT:
            geometry.setLeft(geometry.left() + delta.x())
        elif self.direction == ResizeDirection.RIGHT:
            geometry.setRight(geometry.right() + delta.x())
        elif self.direction == ResizeDirection.TOP:
            geometry.setTop(geometry.top() + delta.y())
        elif self.direction == ResizeDirection.BOTTOM:
            geometry.setBottom(geometry.bottom() + delta.y())
        elif self.direction == ResizeDirection.TOP_LEFT:
            geometry.setLeft(geometry.left() + delta.x())
            geometry.setTop(geometry.top() + delta.y())
        elif self.direction == ResizeDirection.TOP_RIGHT:
            geometry.setRight(geometry.right() + delta.x())
            geometry.setTop(geometry.top() + delta.y())
        elif self.direction == ResizeDirection.BOTTOM_LEFT:
            geometry.setLeft(geometry.left() + delta.x())
            geometry.setBottom(geometry.bottom() + delta.y())
        elif self.direction == ResizeDirection.BOTTOM_RIGHT:
            geometry.setRight(geometry.right() + delta.x())
            geometry.setBottom(geometry.bottom() + delta.y())
        
        # Ensure minimum window size
        min_size = window.minimumSize()
        if geometry.width() < min_size.width():
            if self.direction in [ResizeDirection.LEFT, ResizeDirection.TOP_LEFT, ResizeDirection.BOTTOM_LEFT]:
                geometry.setLeft(geometry.right() - min_size.width())
            else:
                geometry.setRight(geometry.left() + min_size.width())
        
        if geometry.height() < min_size.height():
            if self.direction in [ResizeDirection.TOP, ResizeDirection.TOP_LEFT, ResizeDirection.TOP_RIGHT]:
                geometry.setTop(geometry.bottom() - min_size.height())
            else:
                geometry.setBottom(geometry.top() + min_size.height())
        
        # Apply the new geometry
        window.setGeometry(geometry)

class MicaWindowWithBorders:
    """Mixin to add resize borders to a Mica window"""
    
    def setup_resize_borders(self):
        """Add resize borders to the window"""
        print("🔧 Setting up resize borders...")
        
        # Store original central widget
        if hasattr(self, 'centralWidget') and self.centralWidget():
            original_widget = self.centralWidget()
            print(f"✅ Found central widget: {type(original_widget)}")
            
            # Create container with border layout
            container = QWidget()
            layout = QVBoxLayout(container)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)
            
            # Top row: Top-left corner, Top border, Top-right corner
            top_row = QHBoxLayout()
            top_row.setContentsMargins(0, 0, 0, 0)
            top_row.setSpacing(0)
            
            # Make corners slightly larger to eliminate gaps
            self.top_left_border = ResizeBorderWidget(ResizeDirection.TOP_LEFT)
            self.top_left_border.setFixedSize(10, 10)  # Larger corners
            
            self.top_border = ResizeBorderWidget(ResizeDirection.TOP)
            self.top_border.setFixedHeight(8)
            
            self.top_right_border = ResizeBorderWidget(ResizeDirection.TOP_RIGHT)
            self.top_right_border.setFixedSize(10, 10)  # Larger corners
            
            top_row.addWidget(self.top_left_border)
            top_row.addWidget(self.top_border, 1)
            top_row.addWidget(self.top_right_border)
            
            # Middle row: Left border, Content, Right border
            middle_row = QHBoxLayout()
            middle_row.setContentsMargins(0, 0, 0, 0)
            middle_row.setSpacing(0)
            
            self.left_border = ResizeBorderWidget(ResizeDirection.LEFT)
            self.left_border.setFixedWidth(8)
            
            self.right_border = ResizeBorderWidget(ResizeDirection.RIGHT)
            self.right_border.setFixedWidth(8)
            
            middle_row.addWidget(self.left_border)
            middle_row.addWidget(original_widget, 1)
            middle_row.addWidget(self.right_border)
            
            # Bottom row: Bottom-left corner, Bottom border, Bottom-right corner
            bottom_row = QHBoxLayout()
            bottom_row.setContentsMargins(0, 0, 0, 0)
            bottom_row.setSpacing(0)
            
            # Make corners slightly larger to eliminate gaps
            self.bottom_left_border = ResizeBorderWidget(ResizeDirection.BOTTOM_LEFT)
            self.bottom_left_border.setFixedSize(10, 10)  # Larger corners
            
            self.bottom_border = ResizeBorderWidget(ResizeDirection.BOTTOM)
            self.bottom_border.setFixedHeight(8)
            
            self.bottom_right_border = ResizeBorderWidget(ResizeDirection.BOTTOM_RIGHT)
            self.bottom_right_border.setFixedSize(10, 10)  # Larger corners
            
            bottom_row.addWidget(self.bottom_left_border)
            bottom_row.addWidget(self.bottom_border, 1)
            bottom_row.addWidget(self.bottom_right_border)
            
            # Add all rows to main layout
            layout.addLayout(top_row)
            layout.addLayout(middle_row, 1)
            layout.addLayout(bottom_row)
            
            # Set the new container as central widget
            self.setCentralWidget(container)
            print("✅ Resize borders setup complete!")
        else:
            print("❌ No central widget found - cannot setup borders")
    
    def set_border_width(self, width):
        """Change the width of resize borders"""
        borders = [
            self.left_border, self.right_border,
            self.top_left_border, self.top_border, self.top_right_border,
            self.bottom_left_border, self.bottom_border, self.bottom_right_border
        ]
        
        for border in borders:
            if hasattr(border, 'direction'):
                if border.direction in [ResizeDirection.LEFT, ResizeDirection.RIGHT]:
                    border.setFixedWidth(width)
                elif border.direction in [ResizeDirection.TOP, ResizeDirection.BOTTOM]:
                    border.setFixedHeight(width)
                else:  # Corners
                    border.setFixedSize(width, width)
