"""
Frameless Window Manager
Provides complete frameless window functionality including:
- Window resizing from edges and corners
- Proper cursor management
- Windows native behavior integration
- Hit testing for system integration
"""

import sys
import ctypes
from ctypes import wintypes, windll
from enum import Enum, IntFlag
from PyQt6.QtCore import Qt, QPoint, QRect, QTimer
from PyQt6.QtGui import QCursor
from PyQt6.QtWidgets import QApplication

# Windows API constants
WM_NCHITTEST = 0x0084
WM_NCCALCSIZE = 0x0083
WM_GETMINMAXINFO = 0x0024
WM_DWMCOMPOSITIONCHANGED = 0x031E

# Hit test results
HTCLIENT = 1
HTCAPTION = 2
HTSYSMENU = 3
HTGROWBOX = 4
HTSIZE = HTGROWBOX
HTMENU = 5
HTHSCROLL = 6
HTVSCROLL = 7
HTMINBUTTON = 8
HTMAXBUTTON = 9
HTLEFT = 10
HTRIGHT = 11
HTTOP = 12
HTTOPLEFT = 13
HTTOPRIGHT = 14
HTBOTTOM = 15
HTBOTTOMLEFT = 16
HTBOTTOMRIGHT = 17
HTBORDER = 18
HTREDUCE = HTMINBUTTON
HTZOOM = HTMAXBUTTON
HTSIZEFIRST = HTLEFT
HTSIZELAST = HTBOTTOMRIGHT
HTCLOSE = 20

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

class FramelessWindowManager:
    """
    Complete frameless window management system that provides:
    - Edge and corner resizing
    - Proper cursor changes
    - Windows native integration
    - Hit testing for system behaviors
    """
    
    def __init__(self, window):
        self.window = window
        self.resize_border_width = 8  # Width of resize border in pixels
        self.title_bar_height = 40    # Height of title bar for dragging
        self.is_resizing = False
        self.resize_direction = ResizeDirection.NONE
        self.resize_start_pos = QPoint()
        self.resize_start_geometry = QRect()
        
        # Store original window proc
        self.original_window_proc = None
        
        # Initialize
        self._setup_window()
    
    def _setup_window(self):
        """Setup the frameless window with all necessary configurations."""
        # Set frameless window hint
        self.window.setWindowFlags(
            Qt.WindowType.Window | 
            Qt.WindowType.FramelessWindowHint        )
        
        # Enable native window behavior
        if sys.platform == "win32":
            self._setup_windows_integration()
    
    def _setup_windows_integration(self):
        """Setup Windows-specific integration for native behavior."""
        try:
            import ctypes.wintypes as wintypes
            
            # Get window handle - handle potential overflow
            hwnd_raw = self.window.winId()
            if isinstance(hwnd_raw, int):
                hwnd = hwnd_raw
            else:
                # Handle PyQt6 sip.voidptr
                hwnd = int(hwnd_raw)
            
            # Ensure hwnd is within valid range for Windows API
            if hwnd > 0x7FFFFFFF:  # If larger than max signed 32-bit int
                hwnd = hwnd - 0x100000000  # Convert to signed
            
            # Define window proc type with proper integer sizes
            if ctypes.sizeof(ctypes.c_void_p) == 8:  # 64-bit
                WNDPROC = ctypes.WINFUNCTYPE(ctypes.c_int64, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)
            else:  # 32-bit
                WNDPROC = ctypes.WINFUNCTYPE(ctypes.c_long, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)
            
            # Store original window proc
            self.original_window_proc = windll.user32.GetWindowLongPtrW(hwnd, -4)  # GWL_WNDPROC
            
            # Set our custom window proc
            self.custom_window_proc = WNDPROC(self._windows_proc)
            windll.user32.SetWindowLongPtrW(hwnd, -4, ctypes.cast(self.custom_window_proc, ctypes.c_void_p).value)
            
        except Exception as e:
            print(f"Failed to setup Windows integration: {e}")
            # Continue without Windows integration - basic functionality will still work
    
    def _windows_proc(self, hwnd, msg, wparam, lparam):
        """Custom Windows message handler for native integration."""
        # Handle hit testing for proper resize cursors and behavior
        if msg == WM_NCHITTEST:
            return self._handle_hit_test(hwnd, lparam)
        
        # Handle non-client area calculation
        elif msg == WM_NCCALCSIZE:
            if wparam:
                # Return 0 to indicate we want the entire window as client area
                return 0
        
        # Handle DWM composition changes
        elif msg == WM_DWMCOMPOSITIONCHANGED:
            # Reapply Mica effect if available
            if hasattr(self.window, '_reapply_mica_effect'):
                QTimer.singleShot(50, self.window._reapply_mica_effect)
        
        # Call original window proc for other messages
        return windll.user32.CallWindowProcW(self.original_window_proc, hwnd, msg, wparam, lparam)
    
    def _handle_hit_test(self, hwnd, lparam):
        """Handle hit testing for resize areas and title bar."""
        # Get cursor position in screen coordinates
        x = ctypes.c_short(lparam & 0xFFFF).value
        y = ctypes.c_short((lparam >> 16) & 0xFFFF).value
        
        # Convert to client coordinates
        point = QPoint(x, y)
        client_point = self.window.mapFromGlobal(point)
        
        # Get window geometry
        rect = self.window.rect()
        
        # Check if in resize border areas
        on_left = client_point.x() <= self.resize_border_width
        on_right = client_point.x() >= rect.width() - self.resize_border_width
        on_top = client_point.y() <= self.resize_border_width
        on_bottom = client_point.y() >= rect.height() - self.resize_border_width
        
        # Check for corner resize areas (higher priority)
        if on_top and on_left:
            return HTTOPLEFT
        elif on_top and on_right:
            return HTTOPRIGHT
        elif on_bottom and on_left:
            return HTBOTTOMLEFT
        elif on_bottom and on_right:
            return HTBOTTOMRIGHT
        
        # Check for edge resize areas
        elif on_left:
            return HTLEFT
        elif on_right:
            return HTRIGHT
        elif on_top:
            return HTTOP
        elif on_bottom:
            return HTBOTTOM
        
        # Check if in title bar area (for dragging)
        elif client_point.y() <= self.title_bar_height:
            # Check if clicking on window control buttons
            if self._is_in_window_controls(client_point):
                return HTCLIENT  # Let Qt handle button clicks
            return HTCAPTION  # Enable window dragging
        
        # Default to client area
        return HTCLIENT
    
    def _is_in_window_controls(self, point):
        """Check if point is within window control buttons area."""
        # Approximate area where window controls are located
        # This should be adjusted based on your actual title bar layout
        control_area_width = 120  # Width for minimize, maximize, close buttons
        return point.x() >= self.window.width() - control_area_width
    
    def get_resize_direction(self, pos):
        """Determine resize direction based on cursor position."""
        rect = self.window.rect()
        
        on_left = pos.x() <= self.resize_border_width
        on_right = pos.x() >= rect.width() - self.resize_border_width
        on_top = pos.y() <= self.resize_border_width
        on_bottom = pos.y() >= rect.height() - self.resize_border_width
        
        if on_top and on_left:
            return ResizeDirection.TOP_LEFT
        elif on_top and on_right:
            return ResizeDirection.TOP_RIGHT
        elif on_bottom and on_left:
            return ResizeDirection.BOTTOM_LEFT
        elif on_bottom and on_right:
            return ResizeDirection.BOTTOM_RIGHT
        elif on_left:
            return ResizeDirection.LEFT
        elif on_right:
            return ResizeDirection.RIGHT
        elif on_top:
            return ResizeDirection.TOP
        elif on_bottom:
            return ResizeDirection.BOTTOM
        
        return ResizeDirection.NONE
    
    def update_cursor(self, direction):
        """Update cursor based on resize direction."""
        cursor_map = {
            ResizeDirection.LEFT: Qt.CursorShape.SizeHorCursor,
            ResizeDirection.RIGHT: Qt.CursorShape.SizeHorCursor,
            ResizeDirection.TOP: Qt.CursorShape.SizeVerCursor,
            ResizeDirection.BOTTOM: Qt.CursorShape.SizeVerCursor,
            ResizeDirection.TOP_LEFT: Qt.CursorShape.SizeFDiagCursor,
            ResizeDirection.BOTTOM_RIGHT: Qt.CursorShape.SizeFDiagCursor,
            ResizeDirection.TOP_RIGHT: Qt.CursorShape.SizeBDiagCursor,
            ResizeDirection.BOTTOM_LEFT: Qt.CursorShape.SizeBDiagCursor,
            ResizeDirection.NONE: Qt.CursorShape.ArrowCursor
        }
        
        cursor = cursor_map.get(direction, Qt.CursorShape.ArrowCursor)
        self.window.setCursor(QCursor(cursor))
    
    def handle_mouse_move(self, event):
        """Handle mouse move events for cursor updates and resizing."""
        if not self.is_resizing:
            # Update cursor based on position
            direction = self.get_resize_direction(event.position().toPoint())
            self.update_cursor(direction)
        else:
            # Handle active resizing
            self._perform_resize(event.globalPosition().toPoint())
    
    def handle_mouse_press(self, event):
        """Handle mouse press events to start resizing."""
        if event.button() == Qt.MouseButton.LeftButton:
            direction = self.get_resize_direction(event.position().toPoint())
            
            if direction != ResizeDirection.NONE:
                self.is_resizing = True
                self.resize_direction = direction
                self.resize_start_pos = event.globalPosition().toPoint()
                self.resize_start_geometry = self.window.geometry()
                self.window.setMouseTracking(True)
                return True  # Event handled
        
        return False  # Event not handled
    
    def handle_mouse_release(self, event):
        """Handle mouse release events to stop resizing."""
        if event.button() == Qt.MouseButton.LeftButton and self.is_resizing:
            self.is_resizing = False
            self.resize_direction = ResizeDirection.NONE
            self.window.setMouseTracking(False)
            self.update_cursor(ResizeDirection.NONE)
            return True  # Event handled
        
        return False  # Event not handled
    
    def _perform_resize(self, global_pos):
        """Perform window resizing based on mouse movement."""
        delta = global_pos - self.resize_start_pos
        geometry = QRect(self.resize_start_geometry)
        
        # Apply resize based on direction
        if self.resize_direction == ResizeDirection.LEFT:
            geometry.setLeft(geometry.left() + delta.x())
        elif self.resize_direction == ResizeDirection.RIGHT:
            geometry.setRight(geometry.right() + delta.x())
        elif self.resize_direction == ResizeDirection.TOP:
            geometry.setTop(geometry.top() + delta.y())
        elif self.resize_direction == ResizeDirection.BOTTOM:
            geometry.setBottom(geometry.bottom() + delta.y())
        elif self.resize_direction == ResizeDirection.TOP_LEFT:
            geometry.setLeft(geometry.left() + delta.x())
            geometry.setTop(geometry.top() + delta.y())
        elif self.resize_direction == ResizeDirection.TOP_RIGHT:
            geometry.setRight(geometry.right() + delta.x())
            geometry.setTop(geometry.top() + delta.y())
        elif self.resize_direction == ResizeDirection.BOTTOM_LEFT:
            geometry.setLeft(geometry.left() + delta.x())
            geometry.setBottom(geometry.bottom() + delta.y())
        elif self.resize_direction == ResizeDirection.BOTTOM_RIGHT:
            geometry.setRight(geometry.right() + delta.x())
            geometry.setBottom(geometry.bottom() + delta.y())
        
        # Ensure minimum window size
        min_size = self.window.minimumSize()
        if geometry.width() < min_size.width():
            if self.resize_direction in [ResizeDirection.LEFT, ResizeDirection.TOP_LEFT, ResizeDirection.BOTTOM_LEFT]:
                geometry.setLeft(geometry.right() - min_size.width())
            else:
                geometry.setRight(geometry.left() + min_size.width())
        
        if geometry.height() < min_size.height():
            if self.resize_direction in [ResizeDirection.TOP, ResizeDirection.TOP_LEFT, ResizeDirection.TOP_RIGHT]:
                geometry.setTop(geometry.bottom() - min_size.height())
            else:
                geometry.setBottom(geometry.top() + min_size.height())
        
        # Apply the new geometry
        self.window.setGeometry(geometry)
    
    def handle_double_click(self, event):
        """Handle double-click events for maximize/restore."""
        # Check if double-click is in title bar area
        if event.position().y() <= self.title_bar_height:
            # Exclude window control buttons area
            if not self._is_in_window_controls(event.position().toPoint()):
                if self.window.isMaximized():
                    self.window.showNormal()
                else:
                    self.window.showMaximized()
                return True  # Event handled
        
        return False  # Event not handled
    
    def cleanup(self):
        """Cleanup resources when window is closed."""
        if self.original_window_proc and sys.platform == "win32":
            try:
                hwnd = int(self.window.winId())
                windll.user32.SetWindowLongPtrW(hwnd, -4, self.original_window_proc)
            except:
                pass
