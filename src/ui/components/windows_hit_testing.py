"""
Windows API Hit Testing Solution
Uses Windows native hit testing to handle border resize areas
This integrates with Windows' built-in window management
"""

import sys
import ctypes
from ctypes import wintypes, windll
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget

# Windows API constants
WM_NCHITTEST = 0x0084
WM_NCCALCSIZE = 0x0083
WNDPROC = ctypes.WINFUNCTYPE(ctypes.c_long, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)

# Hit test results
HTCLIENT = 1
HTCAPTION = 2
HTLEFT = 10
HTRIGHT = 11
HTTOP = 12
HTTOPLEFT = 13
HTTOPRIGHT = 14
HTBOTTOM = 15
HTBOTTOMLEFT = 16
HTBOTTOMRIGHT = 17

class WindowsHitTestMixin:
    """Mixin to add Windows API hit testing for proper border handling"""
    
    def setup_windows_hit_testing(self):
        """Setup Windows API hit testing for borders"""
        if sys.platform != "win32":
            return
        
        self.border_width = 8
        self.title_bar_height = 40
        
        try:
            # Get window handle
            hwnd = int(self.winId())
            
            # Store original window procedure
            self.original_wndproc = windll.user32.GetWindowLongPtrW(hwnd, -4)
            
            # Set our custom window procedure
            self.custom_wndproc = WNDPROC(self._windows_proc)
            windll.user32.SetWindowLongPtrW(hwnd, -4, 
                ctypes.cast(self.custom_wndproc, ctypes.c_void_p).value)
            
        except Exception as e:
            print(f"Failed to setup Windows hit testing: {e}")
    
    def _windows_proc(self, hwnd, msg, wparam, lparam):
        """Custom Windows message handler"""
        
        if msg == WM_NCHITTEST:
            # Get cursor position
            x = ctypes.c_short(lparam & 0xFFFF).value
            y = ctypes.c_short((lparam >> 16) & 0xFFFF).value
            
            # Convert to client coordinates
            from PyQt6.QtCore import QPoint
            point = QPoint(x, y)
            client_point = self.mapFromGlobal(point)
            
            # Get window rect
            rect = self.rect()
            
            # Check border areas
            on_left = client_point.x() <= self.border_width
            on_right = client_point.x() >= rect.width() - self.border_width
            on_top = client_point.y() <= self.border_width
            on_bottom = client_point.y() >= rect.height() - self.border_width
            
            # Return appropriate hit test result
            if on_top and on_left:
                return HTTOPLEFT
            elif on_top and on_right:
                return HTTOPRIGHT
            elif on_bottom and on_left:
                return HTBOTTOMLEFT
            elif on_bottom and on_right:
                return HTBOTTOMRIGHT
            elif on_left:
                return HTLEFT
            elif on_right:
                return HTRIGHT
            elif on_top:
                return HTTOP
            elif on_bottom:
                return HTBOTTOM
            elif client_point.y() <= self.title_bar_height:
                # Check if in window controls area
                if self._is_in_window_controls(client_point):
                    return HTCLIENT
                return HTCAPTION
            
            return HTCLIENT
        
        elif msg == WM_NCCALCSIZE:
            # Return 0 to use entire window as client area
            if wparam:
                return 0
        
        # Call original window procedure
        return windll.user32.CallWindowProcW(self.original_wndproc, hwnd, msg, wparam, lparam)
    
    def _is_in_window_controls(self, point):
        """Check if point is in window control buttons area"""
        control_area_width = 120  # Approximate width of window controls
        return point.x() >= self.width() - control_area_width
    
    def cleanup_windows_hit_testing(self):
        """Cleanup Windows API integration"""
        if hasattr(self, 'original_wndproc') and sys.platform == "win32":
            try:
                hwnd = int(self.winId())
                windll.user32.SetWindowLongPtrW(hwnd, -4, self.original_wndproc)
            except:
                pass
