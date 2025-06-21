import sys
import ctypes
from ctypes import wintypes, windll
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QWidget

# Windows API constants
DWM_WINDOW_CORNER_PREFERENCE = 33
DWM_WINDOW_CORNER_ROUND = 2
DWM_WINDOW_CORNER_SQUARE = 1
DWMWA_USE_IMMERSIVE_DARK_MODE = 20
DWMWA_SYSTEMBACKDROP_TYPE = 38
DWMSBT_MAINWINDOW = 2

class MicaEffect:
    @staticmethod
    def is_windows11():
        try:
            version = sys.getwindowsversion()
            return version.major == 10 and version.build >= 22000
        except:
            return False
    
    @staticmethod
    def get_windows_build():
        try:
            return sys.getwindowsversion().build
        except:
            return 0
    
    @staticmethod
    def apply_mica(widget, dark_mode=True, backdrop_type=2):
        if not MicaEffect.is_windows11():
            return False
        try:
            hwnd = widget.winId().__int__()
            
            # Ensure DWM composition is enabled
            try:
                windll.dwmapi.DwmIsCompositionEnabled(ctypes.byref(wintypes.BOOL()))
            except:
                pass
            
            # Apply dark mode first
            dark_value = wintypes.BOOL(dark_mode)
            windll.dwmapi.DwmSetWindowAttribute(
                hwnd, 
                DWMWA_USE_IMMERSIVE_DARK_MODE, 
                ctypes.byref(dark_value), 
                ctypes.sizeof(dark_value)
            )
            
            # Apply Mica backdrop
            backdrop_value = wintypes.DWORD(backdrop_type)
            result = windll.dwmapi.DwmSetWindowAttribute(
                hwnd, 
                DWMWA_SYSTEMBACKDROP_TYPE, 
                ctypes.byref(backdrop_value), 
                ctypes.sizeof(backdrop_value)
            )
            
            # Apply square corners (flat corners)
            corner_value = wintypes.DWORD(DWM_WINDOW_CORNER_SQUARE)
            windll.dwmapi.DwmSetWindowAttribute(
                hwnd, 
                DWM_WINDOW_CORNER_PREFERENCE, 
                ctypes.byref(corner_value), 
                ctypes.sizeof(corner_value)
            )
            
            # Force DWM to update immediately
            windll.dwmapi.DwmFlush()
            
            # Additional flush with delay to ensure effect takes hold
            import time
            time.sleep(0.01)
            windll.dwmapi.DwmFlush()
            
            print(f"Mica effect applied with result: {result}")
            print(f"Square corners should now be applied (DWM_WINDOW_CORNER_SQUARE)")
            return result == 0
            
        except Exception as e:
            print(f'Mica error: {e}')
            return False
    
    @staticmethod
    def get_mica_palette(dark_mode=True):
        palette = QPalette()
        if dark_mode:
            palette.setColor(QPalette.ColorRole.Window, QColor(0, 0, 0, 0))
            palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
        else:
            palette.setColor(QPalette.ColorRole.Window, QColor(255, 255, 255, 0))
            palette.setColor(QPalette.ColorRole.WindowText, QColor(0, 0, 0))
        return palette
    
    @staticmethod
    def get_mica_stylesheet(dark_mode=True):
        if dark_mode:
            return 'QMainWindow { background: transparent; border-radius: 0px; } QWidget { color: white; background: transparent; } QFrame { background: rgba(32, 32, 32, 0.3); border-radius: 8px; }'
        else:
            return 'QMainWindow { background: transparent; border-radius: 0px; } QWidget { color: black; background: transparent; } QFrame { background: rgba(255, 255, 255, 0.3); border-radius: 8px; }'
    
    @staticmethod
    def refresh_mica(widget, dark_mode=True):
        """Force refresh of Mica effect - useful for window state changes."""
        if not MicaEffect.is_windows11():
            return False
        
        try:
            hwnd = widget.winId().__int__()
            
            # Force DWM to refresh the window's backdrop
            windll.dwmapi.DwmFlush()
            
            # Reapply the backdrop effect
            backdrop_value = wintypes.DWORD(2)  # DWMSBT_MAINWINDOW
            windll.dwmapi.DwmSetWindowAttribute(
                hwnd, 
                DWMWA_SYSTEMBACKDROP_TYPE, 
                ctypes.byref(backdrop_value), 
                ctypes.sizeof(backdrop_value)
            )
            
            # Force another flush
            windll.dwmapi.DwmFlush()
            return True
            
        except Exception as e:
            print(f'Mica refresh error: {e}')
            return False
