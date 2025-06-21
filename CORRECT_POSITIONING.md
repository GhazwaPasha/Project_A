```
CORRECT NOTIFICATION DRAWER POSITIONING
======================================

WRONG APPROACH (What I was doing):
- Making drawer a child of content_widget
- This makes it part of the layout, not an overlay
- It gets clipped and positioned incorrectly

CORRECT APPROACH (Windows 11 Action Center style):
- Drawer should be a child of the main window (QMainWindow)
- It should be positioned as an absolute overlay
- It should cover the ENTIRE right side, from title bar to bottom
- It should slide in from off-screen (outside window bounds)

LAYOUT STRUCTURE:
================

QMainWindow (frameless) [1200x800]
├── main_container (central widget) [1200x800]
│   ├── title_bar [1200x40]
│   └── content_widget [1200x760]
│       ├── sidebar [80x760]
│       └── stack [1112x760]
│
└── notification_drawer (overlay) [320x800] ← Should be direct child of QMainWindow
    - Position: slides from x=1200 to x=880
    - Covers from y=0 to y=800 (full height including title bar area)
    - Overlays everything (title bar + content)

COORDINATES:
===========
- Parent: QMainWindow (not any child widget)
- Start position: (1200, 0) - off-screen to the right
- End position: (880, 0) - visible, 20% from right edge
- Full height: 800px (entire window height)
```
