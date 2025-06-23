# Frameless Window Implementation Guide

## Overview

This document describes the complete frameless window implementation that provides Windows native API integration with Mica effects, including proper window resizing, dragging, and native behaviors.

## Components

### 1. FramelessWindowManager (`frameless_window_manager.py`)
**Purpose**: Core functionality for frameless window management
**Features**:
- Edge and corner resizing (8 resize directions)
- Proper cursor management (resize cursors)
- Windows native integration (hit testing)
- Window dragging from title bar
- Double-click maximize/restore
- Windows Snap functionality support

**Key Methods**:
- `handle_mouse_move()`: Updates cursors and handles active resizing
- `handle_mouse_press()`: Initiates resize operations
- `handle_mouse_release()`: Completes resize operations
- `handle_double_click()`: Toggles maximize state
- `_handle_hit_test()`: Windows native hit testing for system integration

### 2. FramelessWindowMixin (`frameless_window_mixin.py`)
**Purpose**: Easy integration mixin for any QMainWindow
**Features**:
- Simple one-line integration: `self.setup_frameless_window()`
- Automatic event handler override
- Backward compatibility with existing mouse handlers
- Clean resource management

**Usage**:
```python
class MyWindow(QMainWindow, FramelessWindowMixin):
    def __init__(self):
        super().__init__()
        self.setup_frameless_window()  # Enable complete frameless functionality
```

### 3. VisualResizeBorder (`visual_resize_border.py`)
**Purpose**: Visual feedback for resize areas
**Features**:
- Subtle border highlighting on hover
- Corner resize indicators
- Auto-hide functionality
- Transparent overlay design

## Integration with Existing Code

### Before (Basic Implementation)
```python
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # Basic frameless setup
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        
        # Manual title bar mouse handling
        title_bar.mousePressEvent = self._title_bar_mouse_press
        title_bar.mouseMoveEvent = self._title_bar_mouse_move
        
    def _title_bar_mouse_press(self, event):
        # Basic dragging implementation
        pass
```

### After (Complete Implementation)
```python
class MainWindow(QMainWindow, FramelessWindowMixin):
    def __init__(self):
        super().__init__()
        # Complete frameless functionality
        self.setup_frameless_window()
        
        # Title bar no longer needs manual mouse handling
        # All window management is handled automatically
```

## Features Added

### ✅ Window Resizing
- **8-direction resizing**: Left, Right, Top, Bottom, and all 4 corners
- **Proper cursors**: Automatic cursor changes when hovering over resize areas
- **Minimum size respect**: Honors window minimum size constraints
- **Smooth resizing**: Real-time window geometry updates

### ✅ Native Windows Integration
- **Hit testing**: Proper WM_NCHITTEST handling for system integration
- **Windows Snap**: Works with Windows 10/11 snap features (Win+Arrow keys)
- **DWM integration**: Proper Desktop Window Manager integration
- **System behaviors**: Native window behaviors maintained

### ✅ Enhanced User Experience
- **Double-click maximize**: Double-click title bar to maximize/restore
- **Visual feedback**: Optional visual borders for resize areas
- **Responsive cursors**: Immediate cursor feedback on resize areas
- **Edge detection**: Precise edge and corner detection (8px border width)

### ✅ Mica Effect Compatibility
- **Preserved transparency**: Frameless functionality works with Mica effects
- **DWM refresh**: Automatic Mica refresh on window state changes
- **Clean integration**: No interference with existing Mica implementation

## Configuration Options

### Resize Border Width
```python
# Set custom resize border width (default: 8px)
self.set_resize_border_width(10)
```

### Title Bar Height
```python
# Set custom title bar height for dragging (default: 40px)
self.set_title_bar_height(35)
```

### Visual Feedback
```python
# Enable/disable visual resize borders
if hasattr(self, 'frameless_manager'):
    visual_border = EnhancedFramelessBorder(self)
    visual_border.set_visual_feedback(True)
```

## Technical Details

### Windows API Integration
The implementation uses proper Windows API calls for native integration:
- `WM_NCHITTEST`: Hit testing for resize areas and title bar
- `WM_NCCALCSIZE`: Non-client area calculation
- `WM_DWMCOMPOSITIONCHANGED`: DWM composition change handling

### Hit Test Results
- `HTTOPLEFT`, `HTTOPRIGHT`, etc.: Corner resize areas
- `HTLEFT`, `HTRIGHT`, etc.: Edge resize areas  
- `HTCAPTION`: Title bar (dragging area)
- `HTCLIENT`: Client area (normal interaction)

### Cursor Management
Automatic cursor updates based on hover position:
- `SizeHorCursor`: Left/Right resize
- `SizeVerCursor`: Top/Bottom resize
- `SizeFDiagCursor`: Top-Left/Bottom-Right resize
- `SizeBDiagCursor`: Top-Right/Bottom-Left resize

## Troubleshooting

### Common Issues

1. **Resize not working**:
   - Ensure `setup_frameless_window()` is called
   - Check that window flags are properly set
   - Verify mouse tracking is enabled

2. **Mica effect not showing**:
   - Confirm Windows 11 compatibility
   - Check DWM composition is enabled
   - Verify transparency attributes are set

3. **Title bar dragging not working**:
   - Ensure title bar height is properly configured
   - Check that window control buttons area is excluded
   - Verify hit testing implementation

### Performance Considerations
- Mouse tracking is only enabled during resize operations
- Windows API calls are cached where possible
- Visual feedback is optional and can be disabled for performance

## Migration Guide

### Step 1: Add Mixin
```python
# Before
class MainWindow(QMainWindow):

# After  
class MainWindow(QMainWindow, FramelessWindowMixin):
```

### Step 2: Setup Frameless Window
```python
def __init__(self):
    super().__init__()
    self.setup_frameless_window()  # Add this line
```

### Step 3: Remove Manual Handlers
```python
# Remove these lines
title_bar.mousePressEvent = self._title_bar_mouse_press
title_bar.mouseMoveEvent = self._title_bar_mouse_move
```

### Step 4: Update Button Handlers
```python
# Before
maximize_btn.clicked.connect(self._toggle_maximize)

# After
maximize_btn.clicked.connect(self._handle_maximize_button)
```

## Testing Checklist

- [ ] Window can be resized from all 8 directions (4 edges + 4 corners)
- [ ] Cursor changes appropriately when hovering over resize areas
- [ ] Title bar dragging works correctly
- [ ] Double-click title bar toggles maximize/restore
- [ ] Window controls (minimize, maximize, close) work properly
- [ ] Mica effect remains functional
- [ ] Windows Snap features work (Win+Arrow keys)
- [ ] Minimum window size is respected during resize
- [ ] Window can be moved between monitors
- [ ] Visual resize borders appear when configured

## Future Enhancements

### Planned Features
1. **Touch support**: Multi-touch resize and drag
2. **Animations**: Smooth resize and maximize animations
3. **Themes**: Customizable resize border appearance
4. **Accessibility**: Screen reader and keyboard navigation support
5. **Multi-monitor**: Enhanced multi-monitor snap support

### API Extensions
1. **Custom resize areas**: Define non-standard resize zones
2. **Resize constraints**: Advanced minimum/maximum size handling
3. **Event callbacks**: Custom callbacks for resize events
4. **Performance modes**: Low-latency vs visual quality modes
