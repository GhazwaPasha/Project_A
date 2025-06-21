```
MAIN WINDOW LAYOUT ANALYSIS
===========================

QMainWindow (frameless) [1200x800]
└── main_container (QWidget) [1200x800] ← Notification drawer parent
    └── main_layout (QVBoxLayout)
        ├── title_bar (QFrame) [1200x40]
        │   └── title_layout (QHBoxLayout)
        │       ├── icon + title
        │       ├── AI status bar (stretch=1)
        │       ├── sync button
        │       ├── notification button ← Bell icon here
        │       └── window controls
        │
        └── content_widget (QWidget) [1200x760] ← Main content area
            └── content_layout (QHBoxLayout) [margins: 8,0,8,8]
                ├── sidebar (QWidget) [~80px width when collapsed]
                └── stack (QStackedWidget) [~1112px width, stretch=1]

PROBLEM ANALYSIS:
================

Current notification drawer positioning:
- Parent: main_container (1200x800)
- Position calculation: x = parent_width = 1200px (off-screen)
- Animation: from x=1200 to x=880 (1200-320)

But the coordinates are relative to main_container (0,0), so:
- x=0 = left edge of main_container
- x=1200 = right edge of main_container 
- x=880 = 320px from right edge

The issue: When the drawer appears at x=880, it's positioning relative to 
main_container, but it should position relative to the CONTENT AREA, not 
the entire main_container!

SOLUTION:
=========

The notification drawer should be positioned relative to content_widget, 
not main_container, because:

1. content_widget is where the actual app content is (sidebar + stack)
2. The drawer should overlay the stack area (main content), not extend 
   beyond the title bar
3. The right edge should align with the right edge of content_widget

CORRECT POSITIONING:
===================

QMainWindow [1200x800]
└── main_container [1200x800]
    ├── title_bar [1200x40]
    └── content_widget [1200x760] ← Drawer should be child of this!
        ├── sidebar [80x760]
        ├── stack [1112x760] ← Drawer should overlay this area
        └── notification_drawer [320x760] ← Should slide from right edge
```
