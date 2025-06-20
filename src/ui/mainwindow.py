from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget, QFrame, QPushButton, QLabel, QSizePolicy, QApplication, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt, QSize, QTimer
from PyQt6.QtGui import QIcon, QPalette, QColor

# Import PostgreSQL accounting system
from ..core.accounting_system_postgresql import AccountingSystemPostgreSQL as AccountingSystem

from .components.mica_effect import MicaEffect
from .components.styles import ModernStyles, GlassmorphismHelper
from .components.font_manager import font_manager
import os
import logging

# Import ResponsiveHelper for consistent responsive design
from .pages.dashboard import ResponsiveHelper

class ModernSidebarButton(QPushButton):
    def __init__(self, icon_path, text, expanded=True, parent=None):
        super().__init__(parent)
        self.icon = QIcon(icon_path)
        self.text_label = text
        self.expanded = expanded
          # Set icon with responsive sizing
        self.setIcon(self.icon)
        icon_size = ResponsiveHelper.scale_size(24, 20, 28)
        self.setIconSize(QSize(icon_size, icon_size))
        
        # Ensure icon is always positioned to the left
        from PyQt6.QtCore import Qt
        self.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
          # Configure button properties
        self.setCheckable(True)
        self.setAutoExclusive(True)
        self.update_text()
        self.setObjectName("ModernSidebarButton")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        # Responsive height
        button_height = ResponsiveHelper.scale_size(48, 44, 56)
        self.setMinimumHeight(button_height)
          # Apply modern styling
        self._apply_modern_styling()
        
    def set_expanded(self, expanded):
        self.expanded = expanded
        self.update_text()
        self._apply_modern_styling()  # Reapply styling when state changes
        
    def update_text(self):
        # Always keep the text for proper left alignment, but make it invisible when collapsed
        if self.expanded:
            self.setText(self.text_label)
        else:
            self.setText("")  # Remove text when collapsed
        self.setToolTip(self.text_label)
        
    def _apply_modern_styling(self):
        """Apply modern responsive styling to the sidebar button with translucent design."""
        # Get responsive values
        font_size = ResponsiveHelper.scale_size(14, 12, 16)
        border_radius = ResponsiveHelper.scale_size(10, 8, 12)
        padding_v = ResponsiveHelper.scale_size(12, 10, 16)
        
        # CRITICAL: Different padding for expanded vs collapsed to center icon properly
        if self.expanded:
            # When expanded, use standard left padding for text+icon layout
            icon_padding_left = ResponsiveHelper.scale_size(16, 12, 20)
        else:
            # When collapsed, center the icon by using equal left/right padding
            button_width = ResponsiveHelper.scale_size(80, 70, 90)  # Collapsed sidebar width
            icon_size = ResponsiveHelper.scale_size(24, 20, 28)
            # Calculate padding to center icon horizontally
            icon_padding_left = max(4, (button_width - icon_size - 32) // 2)  # -32 for total margins
        
        self.setStyleSheet(f"""
            QPushButton#ModernSidebarButton {{
                background: transparent;
                border: none;
                border-radius: {border_radius}px;
                padding: {padding_v}px {icon_padding_left}px;
                color: rgba(255, 255, 255, 0.7);
                font-size: {font_size}px;
                font-weight: 500;
                text-align: left;
                margin: 2px 0px;
                outline: none;
                qproperty-iconSize: {ResponsiveHelper.scale_size(24, 20, 28)}px {ResponsiveHelper.scale_size(24, 20, 28)}px;
            }}
            QPushButton#ModernSidebarButton:hover {{
                background: rgba(255, 255, 255, 0.05);
                color: rgba(255, 255, 255, 0.9);
                outline: none;
            }}
            QPushButton#ModernSidebarButton:pressed {{
                background: rgba(255, 255, 255, 0.03);
                color: rgba(255, 255, 255, 0.8);
                outline: none;
            }}
            QPushButton#ModernSidebarButton:checked {{
                background: rgba(255, 255, 255, 0.07);
                color: white;
                font-weight: 600;
                outline: none;
            }}
            QPushButton#ModernSidebarButton:checked:hover {{
                background: rgba(255, 255, 255, 0.1);
                color: white;
                outline: none;
            }}
            QPushButton#ModernSidebarButton:focus {{
                outline: none;
                border: none;
            }}        """)

class MainWindow(QMainWindow):
    def __init__(self, db_mode='postgresql', prefer_local=False, auto_sync=False, 
                 auth_manager=None, session_manager=None):
        super().__init__()
        self.setWindowTitle("AI Accountant - Multi-Tenant SaaS")
        self.setMinimumSize(1200, 800)
        
        # Store sync settings
        self.db_mode = db_mode
        self.prefer_local = prefer_local
        self.auto_sync = auto_sync
        
        # Store authentication context
        self.auth_manager = auth_manager
        self.session_manager = session_manager
        
        # Initialize logging
        self.logger = logging.getLogger(__name__)
        
        # Use single database file in project root
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'accounting.db')
          # Initialize accounting system with PostgreSQL or SQLite fallback
        self.accounting_system = self._initialize_accounting_system(db_path)
        
        # Keep backward compatibility for existing pages
        self.system = self.accounting_system
        
        self.sidebar_expanded = False  # Start collapsed for a cleaner look
        self.dark_mode = True  # Default to dark mode for better Mica effect
        self.currency_symbol = self._load_currency()
        self.mica_applied = False  # Track if Mica has been applied
          # Initialize font manager
        self.font_manager = font_manager
        # Initialize custom fonts
        self._load_custom_fonts()
        
        # Setup window first
        self._setup_mica_window()
        self._setup_ui()
        self._load_pages()
        
        # Apply global styling first
        self._apply_global_consistent_styling()
        
        # Apply font settings to the application
        self._apply_font_settings()
        
        # Setup sync status updates if in hybrid mode
        if self.db_mode == 'hybrid':
            self._setup_sync_updates()
        
        # Show the window first, then apply Mica effect
        self.show()
        
        # Use QTimer to apply Mica effect after window is fully shown
        QTimer.singleShot(100, self._apply_mica_effect_delayed)
        
    def _apply_mica_effect_delayed(self):
        """Apply Mica effect after window is fully initialized and shown."""
        if not self.mica_applied:
            success = self._apply_mica_effect()
            if success:
                self.mica_applied = True
                
                # Force a complete window refresh
                self._force_window_refresh()
                
                # Additional refresh after a short delay to ensure visibility
                QTimer.singleShot(200, self._final_mica_refresh)
    
    def _final_mica_refresh(self):
        """Final refresh to ensure Mica effect is fully visible."""
        if self.mica_applied:
            MicaEffect.refresh_mica(self, self.dark_mode)
            self.update()
            print("🔄 Final Mica refresh completed")
    
    def _force_window_refresh(self):
        """Force a complete window refresh to ensure Mica effect is visible."""
        # Multiple refresh techniques to ensure effect is visible
        self.update()
        self.repaint()
        QApplication.processEvents()
        
        # Trigger a slight window geometry change to force refresh
        current_geometry = self.geometry()
        self.setGeometry(current_geometry.x(), current_geometry.y(), 
                        current_geometry.width() + 1, current_geometry.height())
        QApplication.processEvents()
        self.setGeometry(current_geometry.x(), current_geometry.y(), 
                        current_geometry.width(), current_geometry.height())
        QApplication.processEvents()
    
    def showEvent(self, event):
        """Handle window show event to ensure Mica effect is applied."""
        super().showEvent(event)
        
        # Apply Mica effect if not already applied and window is visible
        if not self.mica_applied and self.isVisible():
            QTimer.singleShot(50, self._apply_mica_effect_delayed)
    
    def resizeEvent(self, event):
        """Handle window resize to maintain Mica effect."""
        super().resizeEvent(event)
        if self.mica_applied:
            # Reapply Mica effect after resize to ensure it's maintained
            QTimer.singleShot(10, self._reapply_mica_effect)
    
    def _reapply_mica_effect(self):
        """Reapply Mica effect (for resize/move events)."""
        if MicaEffect.is_windows11() and self.mica_applied:
            MicaEffect.refresh_mica(self, self.dark_mode)
            self.update()
    
    def changeEvent(self, event):
        """Handle window state changes (minimize, restore, etc.)."""
        super().changeEvent(event)
        
        if event.type() == event.Type.WindowStateChange:
            # When window is restored from minimized state, refresh Mica
            if not self.isMinimized() and self.mica_applied:
                QTimer.singleShot(50, self._reapply_mica_effect)
        elif event.type() == event.Type.ActivationChange:
            # When window gains focus, refresh Mica effect
            if self.isActiveWindow() and self.mica_applied:
                QTimer.singleShot(50, self._reapply_mica_effect)
    
    def moveEvent(self, event):
        """Handle window move events (for multi-monitor scenarios)."""
        super().moveEvent(event)
        
        # When window is moved (including between monitors), refresh Mica
        if self.mica_applied:
            QTimer.singleShot(100, self._reapply_mica_effect)
        
    def _setup_mica_window(self):
        """Configure window for Mica effect."""
        # CRITICAL: Set window flags BEFORE setting other attributes
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        
        # Enable transparency for Mica to show through
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        
        # Ensure window is properly configured for composition
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, False)
        
        # Set completely transparent background
        self.setStyleSheet("""
            QMainWindow {
                background: transparent;
            }
        """)
        
        # Apply Mica-optimized palette
        palette = MicaEffect.get_mica_palette(self.dark_mode)
        self.setPalette(palette)
        QApplication.instance().setPalette(palette)
        
    def _apply_mica_effect(self):
        """Apply Windows 11 Mica effect."""
        print(f"Attempting to apply Mica effect...")
        print(f"Windows 11 detected: {MicaEffect.is_windows11()}")
        print(f"Windows build: {MicaEffect.get_windows_build()}")
        print(f"Window visible: {self.isVisible()}")
        print(f"Window ID: {self.winId()}")
        
        if MicaEffect.is_windows11() and self.isVisible():
            # Apply Mica effect
            success = MicaEffect.apply_mica(self, self.dark_mode)
            
            if success:
                # Apply Mica stylesheet only AFTER successful Mica application
                mica_style = MicaEffect.get_mica_stylesheet(self.dark_mode)
                self.setStyleSheet(mica_style)
                print("✅ Mica effect and styling applied successfully")
                
                # Ensure window is positioned properly to show Mica effect
                self._optimize_for_mica()
                return True
            else:
                print("❌ Failed to apply Mica effect, using fallback styling")
                # Fallback styling for non-Mica windows
                fallback_style = self._get_fallback_style()
                self.setStyleSheet(fallback_style)
                return False
        else:
            if not MicaEffect.is_windows11():
                print("⚠️  Windows 11 not detected, using fallback styling")
            else:
                print("⚠️  Window not visible yet, delaying Mica application")
            fallback_style = self._get_fallback_style()
            self.setStyleSheet(fallback_style)
            return False
            
    def _optimize_for_mica(self):
        """Optimize window settings to make Mica effect more visible."""
        # Move window slightly so it's not covering the entire screen
        screen = QApplication.primaryScreen().geometry()
        window_width = min(1400, screen.width() - 200)
        window_height = min(900, screen.height() - 200)
        
        # Center the window but offset slightly
        x = (screen.width() - window_width) // 2
        y = (screen.height() - window_height) // 2 - 50
        
        self.setGeometry(x, y, window_width, window_height)
        
        # Force a repaint to ensure Mica is visible
        self.update()
        self.repaint()
        
    def _get_fallback_style(self):
        """Get fallback styling for non-Mica systems."""
        if self.dark_mode:
            return """
                QMainWindow {
                    background-color: #202020;
                    color: white;
                }
                QFrame {
                    background-color: #2d2d2d;
                    border: 1px solid #404040;
                }
            """
        else:
            return """
                QMainWindow {
                    background-color: #f0f0f0;
                    color: black;
                }
                QFrame {
                    background-color: #ffffff;
                    border: 1px solid #d0d0d0;
                }
            """
            
    def _setup_ui(self):
        """Setup the main UI components."""
        # Main container with custom title bar
        main_container = QWidget()
        main_layout = QVBoxLayout(main_container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Custom title bar
        title_bar = self._create_title_bar()
        main_layout.addWidget(title_bar)
        
        # Content area
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(8, 0, 8, 8)
        content_layout.setSpacing(8)
        
        # Sidebar
        self.sidebar = self._create_sidebar()
        content_layout.addWidget(self.sidebar)
        
        # Main content stack
        self.stack = QStackedWidget()
        self.stack.setObjectName("MainContentStack")
        content_layout.addWidget(self.stack, 1)
        
        main_layout.addWidget(content_widget, 1)
        self.setCentralWidget(main_container)
        
    def _create_title_bar(self):
        """Create a custom title bar for the frameless window."""
        title_bar = QFrame()
        title_bar.setObjectName("CustomTitleBar")
        title_bar.setFixedHeight(40)
        title_bar.mousePressEvent = self._title_bar_mouse_press
        title_bar.mouseMoveEvent = self._title_bar_mouse_move
        
        layout = QHBoxLayout(title_bar)
        layout.setContentsMargins(16, 0, 8, 0)
        
        # Window icon and title
        icon_label = QLabel()
        icon_label.setPixmap(QIcon(os.path.join("assets", "icons", "dashboard_modern.svg")).pixmap(20, 20))
        layout.addWidget(icon_label)
        
        title_label = QLabel("AI Accountant")
        title_label.setObjectName("WindowTitle")
        layout.addWidget(title_label)
        
        layout.addStretch()
        
        # Add sync indicator (always show, but functionality depends on mode)
        from .components.sync_indicator import SyncIndicator
        self.sync_indicator = SyncIndicator()
        self.sync_indicator.sync_requested.connect(self._manual_sync)
        layout.addWidget(self.sync_indicator)
        
        # Window controls with icons
        minimize_btn = QPushButton()
        minimize_btn.setObjectName("WindowControlButton")
        minimize_btn.setFixedSize(40, 32)
        minimize_btn.setToolTip("Minimize")
        minimize_btn.clicked.connect(self.showMinimized)
        
        maximize_btn = QPushButton()
        maximize_btn.setObjectName("WindowControlButton")
        maximize_btn.setFixedSize(40, 32)
        maximize_btn.setToolTip("Maximize")
        maximize_btn.clicked.connect(self._toggle_maximize)
        
        close_btn = QPushButton()
        close_btn.setObjectName("WindowControlButtonClose")
        close_btn.setFixedSize(40, 32)
        close_btn.setToolTip("Close")
        close_btn.clicked.connect(self.close)
        
        # Set icons with fallback to Unicode symbols
        self._set_window_control_icons(minimize_btn, maximize_btn, close_btn)
        
        layout.addWidget(minimize_btn)
        layout.addWidget(maximize_btn)
        layout.addWidget(close_btn)
        
        return title_bar
        
    def _create_sidebar(self):
        """Create the modern sidebar with responsive design and translucent styling."""
        sidebar = QFrame()
        sidebar.setObjectName("ModernSidebar")
          # Responsive sidebar width - increased collapsed width for better icon display
        expanded_width = ResponsiveHelper.scale_size(280, 260, 320)
        collapsed_width = ResponsiveHelper.scale_size(80, 70, 90)  # Increased from 70,60,80
        sidebar.setFixedWidth(expanded_width if self.sidebar_expanded else collapsed_width)
        
        # Add subtle shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(ResponsiveHelper.scale_size(20, 15, 25))
        shadow.setXOffset(ResponsiveHelper.scale_size(2, 1, 3))
        shadow.setYOffset(0)
        shadow.setColor(QColor(0, 0, 0, 40))
        sidebar.setGraphicsEffect(shadow)
          # Main layout with responsive margins
        layout = QVBoxLayout(sidebar)
        margin_h = ResponsiveHelper.scale_size(16, 12, 20)
        margin_v = ResponsiveHelper.scale_size(20, 16, 24)
        # Use consistent spacing between all buttons (toggle + navigation)
        spacing = ResponsiveHelper.scale_size(8, 6, 10)
        layout.setContentsMargins(margin_h, margin_v, margin_h, margin_v)
        layout.setSpacing(spacing)        # Toggle button with modern styling (matched to other icons)
        self.toggle_btn = QPushButton()
        self.toggle_btn.setIcon(QIcon(os.path.join("assets", "icons", "menu_modern.svg")))
        toggle_icon_size = ResponsiveHelper.scale_size(24, 20, 28)  # Increased to match other icons
        self.toggle_btn.setIconSize(QSize(toggle_icon_size, toggle_icon_size))
        
        # Ensure icon is always positioned to the left
        from PyQt6.QtCore import Qt
        self.toggle_btn.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        # Don't use fixed size - use the same sizing approach as ModernSidebarButton
        button_height = ResponsiveHelper.scale_size(48, 44, 56)
        self.toggle_btn.setMinimumHeight(button_height)
        self.toggle_btn.setObjectName("SidebarToggle")
        self.toggle_btn.setCheckable(True)  # Make it checkable but won't be used for visual state
        self.toggle_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.toggle_btn.clicked.connect(self.toggle_sidebar)
        self._style_toggle_button()
        
        # Add toggle button directly to main layout to maintain alignment
        layout.addWidget(self.toggle_btn)
        
        # Navigation buttons with modern icons
        nav_items = [
            ("Dashboard", os.path.join("assets", "icons", "dashboard_modern.svg")),
            ("Journal", os.path.join("assets", "icons", "journal_modern.svg")),
            ("Ledger", os.path.join("assets", "icons", "ledger_modern.svg")),
            ("Trial Balance", os.path.join("assets", "icons", "balance_modern.svg")),
            ("Reports", os.path.join("assets", "icons", "reports_modern.svg")),
            ("Accounts", os.path.join("assets", "icons", "accounts_modern.svg")),
            ("Settings", os.path.join("assets", "icons", "settings_modern.svg")),
        ]
          # Add navigation buttons directly to main layout for proper alignment
        self.sidebar_buttons = []
        for idx, (label, icon_path) in enumerate(nav_items):
            btn = ModernSidebarButton(icon_path, label, expanded=self.sidebar_expanded)
            btn.clicked.connect(lambda checked, i=idx: self.stack.setCurrentIndex(i))
            layout.addWidget(btn)
            self.sidebar_buttons.append(btn)
        
        layout.addStretch()        # Apply translucent sidebar styling
        self._apply_sidebar_styling(sidebar)
        return sidebar
        
    def _style_toggle_button(self):
        """Apply modern translucent styling to the toggle button that EXACTLY matches ModernSidebarButton."""
        # Using the exact same styling values as ModernSidebarButton for perfect consistency
        font_size = ResponsiveHelper.scale_size(14, 12, 16)
        border_radius = ResponsiveHelper.scale_size(10, 8, 12)
        padding_v = ResponsiveHelper.scale_size(12, 10, 16)
        
        # For toggle button, always center the icon since it never has text
        if self.sidebar_expanded:
            # When sidebar is expanded, align with other buttons that have text
            icon_padding_left = ResponsiveHelper.scale_size(16, 12, 20)
        else:
            # When sidebar is collapsed, center the icon like other collapsed buttons
            button_width = ResponsiveHelper.scale_size(80, 70, 90)  # Collapsed sidebar width
            icon_size = ResponsiveHelper.scale_size(24, 20, 28)
            # Calculate padding to center icon horizontally
            icon_padding_left = max(4, (button_width - icon_size - 32) // 2)  # -32 for total margins
        
        # Get the same icon size as used for the toggle button
        toggle_icon_size = ResponsiveHelper.scale_size(24, 20, 28)
        
        self.toggle_btn.setStyleSheet(f"""
            QPushButton#SidebarToggle {{
                background: transparent;
                border: none;
                border-radius: {border_radius}px;
                padding: {padding_v}px {icon_padding_left}px;
                color: rgba(255, 255, 255, 0.7);
                font-size: {font_size}px;
                font-weight: 500;
                text-align: left;
                margin: 2px 0px;
                outline: none;
                qproperty-iconSize: {toggle_icon_size}px {toggle_icon_size}px;
            }}
            QPushButton#SidebarToggle:hover {{
                background: rgba(255, 255, 255, 0.05);
                color: rgba(255, 255, 255, 0.9);
                outline: none;
            }}
            QPushButton#SidebarToggle:pressed {{
                background: rgba(255, 255, 255, 0.03);
                color: rgba(255, 255, 255, 0.8);
                outline: none;
            }}
            QPushButton#SidebarToggle:focus {{
                outline: none;
                border: none;
            }}
            /* We don't use the checked state for the toggle button */
        """)
        
    def _apply_sidebar_styling(self, sidebar):
        """Apply comprehensive translucent styling to the sidebar."""
        border_radius = ResponsiveHelper.scale_size(16, 12, 20)
        sidebar.setStyleSheet(f"""
            QFrame#ModernSidebar {{
                background: rgba(20, 20, 20, 0.25);
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: {border_radius}px;
                margin: 0px;
            }}
        """)
        
    def _load_pages(self):
        """Load and setup all application pages."""
        from .pages.dashboard import DashboardPage
        from .pages.journal import JournalPage
        from .pages.ledger import LedgerPage
        from .pages.trial_balance import TrialBalancePage
        from .pages.reports import ReportsPage
        from .pages.accounts_hierarchy import HierarchicalAccountsPage
        from .pages.settings import SettingsPage
        
        pages = [DashboardPage, JournalPage, LedgerPage, TrialBalancePage, ReportsPage, HierarchicalAccountsPage, SettingsPage]
        for idx, Page in enumerate(pages):
            page = Page(self.system, parent=self)
            self.stack.addWidget(page)
            
        # Set default page
        self.stack.setCurrentIndex(0)
        self.sidebar_buttons[0].setChecked(True)
        
    def _title_bar_mouse_press(self, event):
        """Handle title bar mouse press for window dragging."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            
    def _title_bar_mouse_move(self, event):
        """Handle title bar mouse move for window dragging."""
        if hasattr(self, 'drag_position') and event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            
    def _toggle_maximize(self):
        """Toggle window maximize state."""
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()
            
    def toggle_sidebar(self):
        """Toggle sidebar expanded/collapsed state."""
        self.sidebar_expanded = not self.sidebar_expanded
        
        # Get responsive widths
        expanded_width = ResponsiveHelper.scale_size(280, 260, 320)
        collapsed_width = ResponsiveHelper.scale_size(80, 70, 90)
        
        # Animate sidebar width transition
        from PyQt6.QtCore import QPropertyAnimation, QEasingCurve
        self.animation = QPropertyAnimation(self.sidebar, b"minimumWidth")
        self.animation.setDuration(250)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.animation.setStartValue(self.sidebar.width())
        self.animation.setEndValue(expanded_width if self.sidebar_expanded else collapsed_width)
        self.animation.start()
          # Reset the checked state of the toggle button - should not be highlighted
        self.toggle_btn.setChecked(False)
        
        # Update toggle button styling to match sidebar state
        self._style_toggle_button()
        
        # Update button states
        for btn in self.sidebar_buttons:
            btn.set_expanded(self.sidebar_expanded)
            
    def setCurrentIndexByName(self, name):
        """Set current page by name."""
        label_to_index = {
            "Dashboard": 0,
            "Journal": 1,
            "Ledger": 2,
            "Trial Balance": 3,
            "Reports": 4,
            "Accounts": 5,
            "Settings": 6,
        }
        idx = label_to_index.get(name)
        if idx is not None:
            self.stack.setCurrentIndex(idx)
            if 0 <= idx < len(self.sidebar_buttons):
                self.sidebar_buttons[idx].setChecked(True)
                
    def toggle_theme(self):
        """Toggle between dark and light mode."""
        self.dark_mode = not self.dark_mode
        
        # Update palette and stylesheet
        palette = MicaEffect.get_mica_palette(self.dark_mode)
        self.setPalette(palette)
        QApplication.instance().setPalette(palette)
        
        mica_style = MicaEffect.get_mica_stylesheet(self.dark_mode)
        self.setStyleSheet(mica_style)
          # Reapply Mica effect with new mode
        QTimer.singleShot(50, self._apply_mica_effect)
        
    def get_currency_symbol(self):
        """Get current currency symbol."""
        return getattr(self, 'currency_symbol', '$')

    def set_currency_symbol(self, symbol):
        """Set currency symbol and notify pages."""
        self.currency_symbol = symbol
        self._save_currency(symbol)
        self.notify_currency_change()

    def _save_currency(self, symbol):
        """Save currency symbol to config file."""
        try:
            with open('currency.cfg', 'w', encoding='utf-8') as f:
                f.write(symbol)
        except Exception:
            pass

    def _load_currency(self):
        """Load currency symbol from config file."""
        try:
            with open('currency.cfg', 'r', encoding='utf-8') as f:
                symbol = f.read().strip()
                # Support all currencies from our expanded list
                supported_currencies = [
                    "$", "€", "£", "¥", "C$", "A$", "CHF", "₹", "Rs", 
                    "ر.س", "د.إ", "د.ك", "ر.ق"
                ]
                if symbol in supported_currencies:
                    return symbol
        except Exception:
            pass
        return '$'
        
    def notify_currency_change(self):
        """Notify all pages of currency change."""
        if hasattr(self, 'stack'):
            for i in range(self.stack.count()):
                page = self.stack.widget(i)
                if hasattr(page, 'refresh_currency_display'):
                    page.refresh_currency_display()
                    
    def _apply_global_consistent_styling(self):
        """Apply global consistent styling while preserving Mica effects."""
        try:
            # Apply modern glassmorphism styling to the entire application
            app = QApplication.instance()
            if app:
                # Get the complete modern stylesheet but exclude MainWindow background
                # to preserve Mica effect
                modern_style = ModernStyles.get_complete_stylesheet()
                
                # Remove any MainWindow background overrides that would interfere with Mica
                mica_compatible_style = modern_style.replace(
                    "QMainWindow { background:", "/* QMainWindow background disabled for Mica */ QMainWindow_disabled { background:"
                )
                
                app.setStyleSheet(mica_compatible_style)
                print("✅ Beautiful modern glassmorphism styling applied successfully (Mica-compatible)")
        except Exception as e:
            print(f"⚠️  Failed to apply modern styling: {e}")
            # Fallback to basic styling
            try:
                from .common import GLOBAL_NO_OUTLINE_STYLE
                app = QApplication.instance()
                if app:
                    app.setStyleSheet(GLOBAL_NO_OUTLINE_STYLE)
                    print("✅ Fallback styling applied")
            except:
                print("⚠️  All styling failed")
                
    def _set_window_control_icons(self, minimize_btn, maximize_btn, close_btn):
        """Set icons for window control buttons with modern styling."""
        # Apply modern borderless styling to all window control buttons
        window_control_style = """
            QPushButton[objectName="WindowControlButton"] {
                background: transparent;
                border: none;
                border-radius: 6px;
                color: rgba(255, 255, 255, 0.8);
                font-size: 16px;
                font-weight: normal;
                padding: 0px;
                margin: 0px;
            }
            QPushButton[objectName="WindowControlButton"]:hover {
                background: rgba(255, 255, 255, 0.1);
                color: white;
            }
            QPushButton[objectName="WindowControlButton"]:pressed {
                background: rgba(255, 255, 255, 0.05);
            }
            
            QPushButton[objectName="WindowControlButtonClose"] {
                background: transparent;
                border: none;
                border-radius: 6px;
                color: rgba(255, 255, 255, 0.8);
                font-size: 16px;
                font-weight: normal;
                padding: 0px;
                margin: 0px;
            }
            QPushButton[objectName="WindowControlButtonClose"]:hover {
                background: rgba(232, 17, 35, 0.9);
                color: white;
            }
            QPushButton[objectName="WindowControlButtonClose"]:pressed {
                background: rgba(232, 17, 35, 0.7);
            }
        """
        
        # Try to load SVG icons from files first
        try:
            minimize_icon = QIcon("assets/icons/minimize.svg")
            maximize_icon = QIcon("assets/icons/maximize.svg")
            close_icon = QIcon("assets/icons/close.svg")
            
            if not minimize_icon.isNull():
                minimize_btn.setIcon(minimize_icon)
                minimize_btn.setIconSize(QSize(16, 16))
                minimize_btn.setText("")  # Clear text when icon is set
            else:
                minimize_btn.setText("─")
                
            if not maximize_icon.isNull():
                maximize_btn.setIcon(maximize_icon)
                maximize_btn.setIconSize(QSize(16, 16))
                maximize_btn.setText("")  # Clear text when icon is set
            else:
                maximize_btn.setText("□")
                
            if not close_icon.isNull():
                close_btn.setIcon(close_icon)
                close_btn.setIconSize(QSize(16, 16))
                close_btn.setText("")  # Clear text when icon is set
            else:
                close_btn.setText("×")
                
        except Exception as e:
            print(f"Failed to load window control icons: {e}")
            # Fallback to Unicode symbols
            minimize_btn.setText("─")
            maximize_btn.setText("□")  
            close_btn.setText("×")
        
        # Apply the styling
        minimize_btn.setStyleSheet(window_control_style)
        maximize_btn.setStyleSheet(window_control_style)
        close_btn.setStyleSheet(window_control_style)
        
    def keyPressEvent(self, event):
        """Handle keyboard shortcuts."""
        super().keyPressEvent(event)
          # F5: Force refresh Mica effect (for testing/debugging)
        if event.key() == Qt.Key.Key_F5:
            print("🔄 Manual Mica refresh triggered (F5)")
            if self.mica_applied:
                MicaEffect.refresh_mica(self, self.dark_mode)
                self.update()
            else:
                self._apply_mica_effect_delayed()
                
    def _load_custom_fonts(self):
        """Load custom fonts from the assets/fonts directory."""
        # Load custom fonts using the font manager (only from local files)
        loaded_families = self.font_manager.load_custom_fonts()
        
        # Skip developer font installation to speed up startup
        # Dev fonts are already loaded if they exist in assets/fonts/
    def _apply_font_settings(self):
        """Apply font settings to the application."""
        # Apply font settings to the application using the font manager
        app = QApplication.instance()
        if app:
            self.font_manager.apply_font_to_application(app)
        
        # Update ModernStyles to use the current font family
        self._update_global_stylesheets()
        
    def _update_global_stylesheets(self):
        """Update global stylesheets to use the current font family from the font manager."""
        # Get the current font family from the font manager
        font_family = self.font_manager.get_font_family()
        
        # Update the ModernStyles font family
        ModernStyles.set_font_family(font_family)
        
        # Force a complete update of all UI elements
        self._apply_global_consistent_styling()        # Update child widgets
        if hasattr(self, 'stack'):
            for i in range(self.stack.count()):
                page = self.stack.widget(i)
                if hasattr(page, '_apply_styling') and callable(page._apply_styling):
                    page._apply_styling()        # Force a style refresh
        self.style().unpolish(self)
        self.style().polish(self)
    
    def _initialize_accounting_system(self, db_path):
        """Initialize PostgreSQL accounting system with sync support and multi-tenant context."""
        try:
            self.logger.info(f"Initializing accounting system in {self.db_mode} mode...")
            
            # Get organization context from session manager
            organization_id = None
            user_id = None
            
            if self.session_manager:
                organization_id = self.session_manager.get_active_organization_id()
                user_id = self.session_manager.get_current_user_id()
            
            if self.db_mode == 'hybrid':
                # Use enhanced database manager with local/remote sync and multi-tenant context
                from ..core.database_manager import DatabaseManager
                db_manager = DatabaseManager(
                    prefer_local=self.prefer_local,
                    auto_sync=self.auto_sync,
                    organization_id=organization_id,
                    user_id=user_id
                )
                system = AccountingSystem(
                    organization_id=organization_id,
                    user_id=user_id
                )
                system.db_manager = db_manager
                self.logger.info(f"✅ Hybrid multi-tenant accounting system initialized for org: {organization_id}")
            else:
                # Use standard PostgreSQL system with multi-tenant context
                system = AccountingSystem(
                    organization_id=organization_id,
                    user_id=user_id
                )
                self.logger.info(f"✅ PostgreSQL multi-tenant accounting system initialized for org: {organization_id}")
            
            return system
                
        except Exception as e:
            self.logger.error(f"Accounting system initialization failed: {e}")
            raise Exception(f"Failed to initialize accounting database: {e}")
    
    def _setup_sync_updates(self):
        """Setup periodic sync status updates."""
        self.sync_timer = QTimer()
        self.sync_timer.timeout.connect(self._update_sync_status)
        self.sync_timer.start(5000)  # Update every 5 seconds
        
        # Initial status update
        self._update_sync_status()
    
    def _update_sync_status(self):
        """Update sync status from database manager."""
        if hasattr(self, 'sync_indicator') and hasattr(self.accounting_system, 'db_manager'):
            try:
                status = self.accounting_system.db_manager.get_connection_status()
                self.sync_indicator.update_connection_status(status)
            except Exception as e:
                self.logger.error(f"Failed to update sync status: {e}")
    
    def _manual_sync(self):
        """Trigger manual synchronization."""
        if hasattr(self.accounting_system, 'db_manager'):
            try:
                self.logger.info("Manual sync requested...")
                if hasattr(self, 'sync_indicator'):
                    self.sync_indicator.show_sync_animation()
                
                # Trigger sync (this will be implemented in the sync manager)
                self.accounting_system.db_manager._perform_sync()
                
            except Exception as e:
                self.logger.error(f"Manual sync failed: {e}")
    
    def get_connection_status(self):
        """Get connection status for external access."""
        if hasattr(self.accounting_system, 'db_manager'):
            return self.accounting_system.db_manager.get_connection_status()
        else:
            return {
                'local_available': False,
                'remote_available': True,  # Assume remote is available for non-hybrid mode
                'prefer_local': False,
                'auto_sync_enabled': False,
                'sync_status': {
                    'last_sync': None,
                    'pending_operations': 0,
                    'failed_operations': 0,
                    'conflicts': 0,
                    'is_syncing': False
                }
            }
