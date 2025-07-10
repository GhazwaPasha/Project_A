from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget, QFrame, QPushButton, QLabel, QSizePolicy, QApplication, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt, QSize, QTimer, QEvent
from PyQt6.QtGui import QIcon, QPalette, QColor

# Import Supabase offline-capable system
from ..core.unified_accounting_system import UnifiedAccountingSystem as AccountingSystem

# Import resource manager for proper path handling
from ..core.resource_manager import ResourceManager

from .components.mica_effect import MicaEffect
from .components.styles import ModernStyles, GlassmorphismHelper
from .components.font_manager import font_manager
from .components.simple_ai_status_bar import SimpleAIStatusBar
import os
import logging
from datetime import datetime

# Import ResponsiveHelper for consistent responsive design
from .pages.dashboard import ResponsiveHelper

# Import AI components
from .components.enhanced_ai_processor import ContextAwareAI

# Frameless window functionality is now handled by MicaWindowWithBorders

# Import the border solution for Mica windows
from .components.mica_border_solution import MicaWindowWithBorders

class ModernSidebarButton(QPushButton):
    def __init__(self, icon_path, text, expanded=True, parent=None):
        super().__init__(parent)
        # Use resource manager to get proper icon path
        if isinstance(icon_path, str):
            # If it's a relative path, use resource manager
            if not os.path.isabs(icon_path):
                icon_path = ResourceManager.get_icon_path(icon_path)
            else:
                # If it's already an absolute path, use resource manager to resolve it
                icon_path = ResourceManager.get_resource_path(icon_path)
        
        self.icon = QIcon(icon_path) if icon_path else QIcon()
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
        border_radius = ResponsiveHelper.scale_size(16, 12, 20)
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
                border: none;            }}        """)

class MainWindow(QMainWindow, MicaWindowWithBorders):
    def __init__(self, auth_manager=None, session_manager=None):
        super().__init__()
        self.setWindowTitle("Accountuitive - Multi-Tenant SaaS")
        self.setMinimumSize(1200, 800)
          # Store authentication context
        self.auth_manager = auth_manager
        self.session_manager = session_manager
        
        # Initialize logging
        self.logger = logging.getLogger(__name__)
        
        # Initialize session tracking
        self.start_time = datetime.now()
        
        # Initialize the new Supabase-based accounting system
        self.accounting_system = self._initialize_accounting_system()
        # Keep backward compatibility for existing pages
        self.system = self.accounting_system
          # Initialize notification system
        from .components.notifications.notification_manager import NotificationManager
        self.notification_manager = NotificationManager()
        
        # Initialize optimized workspace switching components
        from ..core.page_manager import PageManager
        from ..core.batched_query_manager import BatchedQueryManager
        self.page_manager = PageManager(auth_manager, session_manager)
        self.batched_query_manager = BatchedQueryManager(auth_manager)
        
        # Connect PageManager to main window
        self.page_manager.set_current_page_getter(self._get_current_page_name)
        
        # AI processor removed - now handled by SimpleAIStatusBar
        
        self.sidebar_expanded = False  # Start collapsed for a cleaner look
        self.dark_mode = True  # Default to dark mode for better Mica effect
        self.currency_symbol = self._load_currency()
        self.mica_applied = False  # Track if Mica has been applied
        
        # Track window position for monitor switch detection
        self._previous_position = None
        self._previous_screen = None
        
          # Initialize font manager
        self.font_manager = font_manager
        # Initialize custom fonts
        self._load_custom_fonts()
        
        # Setup window first - CRITICAL: This must be done before any other UI setup
        self._setup_mica_window()
        
        # Setup basic UI structure (without borders yet)
        self._setup_ui()
        self._load_pages()
        
        # Apply global styling BEFORE seamless borders to avoid conflicts
        self._apply_global_consistent_styling()
        self._apply_font_settings()
        
        # Setup sync status updates - always enabled in new architecture
        self._setup_sync_updates()
        
        # AI context initialization removed - now handled by SimpleAIStatusBar
        
        # Install event filter for handling clicks outside notification drawer
        self.installEventFilter(self)
        
        # CRITICAL: Apply Mica effect FIRST with minimal delay
        QTimer.singleShot(50, self._apply_mica_effect_delayed)
        
        # Apply seamless borders AFTER Mica effect is applied
        QTimer.singleShot(150, self._apply_seamless_borders_delayed)
        
        # Update navigation visibility after everything is set up
        QTimer.singleShot(200, self._update_navigation_visibility)
        
        # Add a welcome notification after startup
        QTimer.singleShot(2000, self._add_welcome_notification)
        
    def closeEvent(self, event):
        """Handle window close event."""
        # AI processor cleanup removed - now handled by SimpleAIStatusBar
          # Clean up any other resources
        if hasattr(self.accounting_system, 'close'):
            self.accounting_system.close()
        elif hasattr(self.accounting_system, 'offline_manager'):
            # Perform final sync if online
            try:
                if self.accounting_system.is_online:
                    self.accounting_system.offline_manager.sync_pending_operations(
                        self.accounting_system.supabase
                    )
            except Exception as e:
                self.logger.error(f"Final sync failed: {e}")
        
        super().closeEvent(event)

    # AI signal connections removed - now handled by SimpleAIStatusBar

    def navigate_to_page(self, page_name: str, parameters: dict):
        """Navigate to a specific page based on its identifier, requested by the AI."""
        self.logger.info(f"AI navigation request: page='{page_name}', params={parameters}")

        # Map AI page identifiers to their corresponding names and indices
        page_map = {
            'dashboard': ("Dashboard", 0),
            'journal': ("Journal", 1),
            'ledger': ("Ledger", 2),
            'trial_balance': ("Trial Balance", 3),
            'reports': ("Reports", 4),
            'accounts': ("Accounts", 5),
            'reminders': ("Reminders", 6),
            'period_closing': ("Period Closing", 7),
            'team': ("Team", 8),
            'org_settings': ("Org Settings", 9),
            'user_mgmt': ("User Mgmt", 10),
            'platform': ("Platform", 11),
            'global_orgs': ("Global Orgs", 12),
            'settings': ("Settings", 13),
        }

        page_info = page_map.get(page_name.lower())
        if page_info:
            name, index = page_info
            self._on_page_changed(index)
            # Placeholder for applying parameters to the page
            if parameters:
                self.logger.info(f"Applying parameters to {name}: {parameters}")
                # current_page = self.stack.widget(index)
                # if hasattr(current_page, 'apply_filters'):
                #     current_page.apply_filters(parameters)
        else:
            self.logger.warning(f"Navigation failed: Page identifier '{page_name}' not found.")
            self.simple_ai_bar.set_error_message(f"Page '{page_name}' not found.")

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
            else:
                # Retry once if it fails
                print("⚠️  Mica effect failed, retrying...")
                QTimer.singleShot(100, self._retry_mica_effect)
    
    def _retry_mica_effect(self):
        """Retry applying Mica effect if it failed initially."""
        if not self.mica_applied:
            success = self._apply_mica_effect()
            if success:
                self.mica_applied = True
                self._force_window_refresh()
                QTimer.singleShot(200, self._final_mica_refresh)
                print("✅ Mica effect applied successfully on retry")
            else:
                print("❌ Mica effect failed on retry, using fallback")
                # Apply fallback styling
                fallback_style = self._get_fallback_style()
                self.setStyleSheet(fallback_style)
    
    def _apply_seamless_borders_delayed(self):
        """Apply seamless borders after Mica effect is applied."""
        try:
            from .components.seamless_border_layout import apply_seamless_borders
            apply_seamless_borders(self)
            print("✅ Seamless borders applied after Mica effect")
        except Exception as e:
            print(f"⚠️  Failed to apply seamless borders: {e}")
    
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
        
        # Initialize position tracking on first show
        if self._previous_screen is None:
            self._previous_screen = self.screen()
            self._previous_position = self.geometry().center()
            print(f"📍 Initial position tracking: screen={self._previous_screen.name()}, pos={self._previous_position}")
        
          # Apply Mica effect if not already applied and window is visible
        if not self.mica_applied and self.isVisible():
            print("🔄 Window shown, applying Mica effect...")
            QTimer.singleShot(50, self._apply_mica_effect_delayed)
        elif self.mica_applied and self.isVisible():
            # Refresh Mica effect when window becomes visible again
            print("🔄 Window shown, refreshing Mica effect...")
            QTimer.singleShot(50, self._refresh_mica_when_visible)
    
    def _refresh_mica_when_visible(self):
        """Refresh Mica effect when window becomes visible."""
        if self.mica_applied and self.isVisible():
            MicaEffect.refresh_mica(self, self.dark_mode)
            self.update()
            print("✅ Mica effect refreshed after window show")
    
    def resizeEvent(self, event):
        """Handle window resize to maintain Mica effect and reposition notification drawer."""
        super().resizeEvent(event)
        if self.mica_applied:
            # Reapply Mica effect after resize to ensure it's maintained
            QTimer.singleShot(10, self._reapply_mica_effect)
          # Reposition notification drawer if it's visible
        if hasattr(self, 'notification_drawer') and self.notification_drawer.isVisible():
            self._position_notification_drawer()
    
    def _reapply_mica_effect(self):
        """Reapply Mica effect (for resize/move events)."""
        if MicaEffect.is_windows11() and self.mica_applied:
            MicaEffect.refresh_mica(self, self.dark_mode)
            self.update()
    
    def changeEvent(self, event):
        """Handle window state changes (minimize, restore, etc.)."""
        super().changeEvent(event)
        
        if event.type() == QEvent.Type.WindowStateChange:
            # When window is restored from minimized state, refresh Mica
            if not self.isMinimized() and self.mica_applied:
                QTimer.singleShot(50, self._reapply_mica_effect)
        elif event.type() == QEvent.Type.ActivationChange:
            # When window gains focus, refresh Mica effect
            if self.isActiveWindow() and self.mica_applied:
                QTimer.singleShot(50, self._reapply_mica_effect)
    
    def moveEvent(self, event):
        """Handle window move events (for multi-monitor scenarios)."""
        super().moveEvent(event)
        
        # Get current screen and position
        current_screen = self.screen()
        current_position = self.geometry().center()
        
        # Check if this is a monitor switch
        if (self._previous_screen is not None and 
            self._previous_position is not None and
            current_screen != self._previous_screen):
            
            print(f"🔄 Monitor switch detected: {self._previous_screen.name()} -> {current_screen.name()}")
            # Handle monitor switch specifically
            QTimer.singleShot(100, self._handle_monitor_switch)
        
        # Update tracking variables
        self._previous_screen = current_screen
        self._previous_position = current_position
        
        # Regular move event handling
        if self.mica_applied:
            print("🔄 Window moved, refreshing Mica effect...")
            QTimer.singleShot(100, self._refresh_mica_after_move)
    
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
            try:
                # Ensure window is properly prepared for Mica
                self._prepare_window_for_mica()
                
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
            except Exception as e:
                print(f"❌ Error applying Mica effect: {e}")
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
    
    def _prepare_window_for_mica(self):
        """Prepare window for Mica effect application."""
        # Ensure window attributes are set correctly
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, False)
        
        # Force a repaint to ensure attributes are applied
        self.update()
        QApplication.processEvents()
    
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
                    color: black;                }                QFrame {
                    background-color: #ffffff;
                    border: 1px solid #d0d0d0;                }
            """
    
    def _setup_ui(self):
        """Setup the main UI components."""        # Main container with custom title bar and minimal background for mouse events
        self.main_container = QWidget()  # Store reference for notification drawer
        self.main_container.setStyleSheet("""
            QWidget {
                background: rgba(0, 0, 0, 0.01);
            }
        """)
        main_layout = QVBoxLayout(self.main_container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
          # Custom title bar (now includes AI status bar)
        self.title_bar = self._create_title_bar()
        main_layout.addWidget(self.title_bar)        # Content area - NO MARGINS to touch borders, minimal background for mouse events
        self.content_widget = QWidget()  # Store reference for notification drawer
        self.content_widget.setStyleSheet("""
            QWidget {
                background: rgba(0, 0, 0, 0.01);
            }
        """)
        content_layout = QHBoxLayout(self.content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins to eliminate gaps
        content_layout.setSpacing(0)  # Remove spacing for seamless layout# Sidebar
        self.sidebar = self._create_sidebar()
        # Add internal padding to sidebar for visual spacing
        sidebar_container = QWidget()
        sidebar_layout = QVBoxLayout(sidebar_container)
        sidebar_layout.setContentsMargins(8, 8, 4, 8)  # Left, top, right, bottom padding
        sidebar_layout.addWidget(self.sidebar)
        content_layout.addWidget(sidebar_container)
        
        # Main content stack
        self.stack = QStackedWidget()
        self.stack.setObjectName("MainContentStack")
        # Add internal padding to content for visual spacing
        content_container = QWidget()
        content_container_layout = QVBoxLayout(content_container)
        content_container_layout.setContentsMargins(4, 8, 8, 8)  # Left, top, right, bottom padding
        content_container_layout.addWidget(self.stack)
        content_layout.addWidget(content_container, 1)

        main_layout.addWidget(self.content_widget, 1)
        
        # Add bottom bar
        self._create_bottom_bar(main_layout)
        
        # Create notification drawer as overlay (initially hidden)
        from .components.notifications.notification_drawer import NotificationDrawer
        self.notification_drawer = NotificationDrawer(self.main_container, self.notification_manager)
        self.notification_drawer.hide()
        
        self.setCentralWidget(self.main_container)
        
    def _create_title_bar(self):
        """Create a custom title bar for the frameless window."""
        # Create a custom title bar class for mouse handling
        class DraggableTitleBar(QFrame):
            def __init__(self, parent_window):
                super().__init__()
                self.parent_window = parent_window
                
            def mousePressEvent(self, event):
                if event.button() == Qt.MouseButton.LeftButton:
                    self.parent_window.drag_position = event.globalPosition().toPoint() - self.parent_window.frameGeometry().topLeft()
                    event.accept()
                    
            def mouseMoveEvent(self, event):
                if event.buttons() == Qt.MouseButton.LeftButton and hasattr(self.parent_window, 'drag_position'):
                    self.parent_window.move(event.globalPosition().toPoint() - self.parent_window.drag_position)
                    event.accept()
                    
            def mouseDoubleClickEvent(self, event):
                if event.button() == Qt.MouseButton.LeftButton:
                    self.parent_window._handle_maximize_button()
                    event.accept()
        
        title_bar = DraggableTitleBar(self)
        title_bar.setObjectName("CustomTitleBar")
        title_bar.setFixedHeight(40)
        
        layout = QHBoxLayout(title_bar)
        layout.setContentsMargins(16, 0, 8, 0)
        layout.setSpacing(8)
        
        # Left side container for icon and title
        left_container = QWidget()
        left_layout = QHBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)
        
        # Window icon and title
        icon_label = QLabel()
        app_icon_path = ResourceManager.get_icon_path("app_logo.svg")
        if app_icon_path:
            icon_label.setPixmap(QIcon(app_icon_path).pixmap(20, 20))
        else:
            # Fallback to dashboard icon
            dashboard_icon_path = ResourceManager.get_icon_path("dashboard_new.svg")
            if dashboard_icon_path:
                icon_label.setPixmap(QIcon(dashboard_icon_path).pixmap(20, 20))
        left_layout.addWidget(icon_label)
        
        title_label = QLabel("Accountuitive")
        title_label.setObjectName("WindowTitle")
        left_layout.addWidget(title_label)
        left_layout.addStretch()  # Push title to left
          # Right side container for buttons and controls
        right_container = QWidget()
        right_layout = QHBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(2)  # Reduced spacing between buttons
        
        # Add stretch to push buttons to the right
        right_layout.addStretch()
        
        # Add compact connection indicator (WiFi-style)
        from .components.compact_connection_indicator import CompactConnectionIndicator
        self.connection_indicator = CompactConnectionIndicator()
        right_layout.addWidget(self.connection_indicator)
        
        # Initialize connection status immediately
        QTimer.singleShot(100, self._initial_connection_check)
        
        # Add user profile button
        from .components.user_profile_button import UserProfileButton
        self.user_profile_button = UserProfileButton(session_manager=self.session_manager)
        self.user_profile_button.sign_out_requested.connect(self._handle_sign_out)
        right_layout.addWidget(self.user_profile_button)
        
        # Add notification button
        from .components.notification_button import NotificationButton
        self.notification_button = NotificationButton(notification_manager=self.notification_manager)
        self.notification_button.notification_clicked.connect(self._show_notifications)
        right_layout.addWidget(self.notification_button)
        
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
        maximize_btn.clicked.connect(self._handle_maximize_button)
        
        close_btn = QPushButton()
        close_btn.setObjectName("WindowControlButtonClose")
        close_btn.setFixedSize(40, 32)
        close_btn.setToolTip("Close")
        close_btn.clicked.connect(self.close)
        
        # Set icons with fallback to Unicode symbols
        self._set_window_control_icons(minimize_btn, maximize_btn, close_btn)
        
        right_layout.addWidget(minimize_btn)
        right_layout.addWidget(maximize_btn)
        right_layout.addWidget(close_btn)
        
        # AI Status Bar - always centered between left and right containers
        self.ai_status_bar = self._create_simple_ai_status_bar()        
        # Add all containers to main layout with equal stretch for perfect centering
        layout.addWidget(left_container, 1)  # Left side takes 1/3
        layout.addWidget(self.ai_status_bar, 1)  # Center AI status takes 1/3 
        layout.addWidget(right_container, 1)  # Right side takes 1/3
        return title_bar
    
    def _create_simple_ai_status_bar(self):
        """Create simple AI status bar for title bar integration"""
        try:
            from .components.simple_ai_status_bar import SimpleAIStatusBar
            
            # Create a container that will hold the AI status bar
            container = QFrame()
            container.setObjectName("AIStatusContainer")
            container.setMaximumHeight(40)  # Match title bar height for proper alignment
            container.setMinimumHeight(40)  # Ensure consistent height
            
            layout = QHBoxLayout(container)
            layout.setContentsMargins(20, 0, 20, 0)  # Add horizontal margins for better centering
            layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            # Create the simple AI status bar
            self.simple_ai_bar = SimpleAIStatusBar(self)
            self.simple_ai_bar.setMaximumHeight(30)  # AI bar height
            self.simple_ai_bar.setMinimumHeight(30)  # Ensure consistent height
            layout.addWidget(self.simple_ai_bar)
            
            return container
            
        except Exception as e:
            print(f"Error creating simple AI status bar: {e}")
            # Return placeholder
            placeholder = QLabel("AI Assistant")
            placeholder.setStyleSheet("color: #cccccc; font-size: 12px; padding: 4px;")
            return placeholder

    def _update_ai_status(self):
        """Update AI status message periodically"""
        try:
            # Update the simple AI status bar if available
            if hasattr(self, 'simple_ai_bar'):
                context = self._get_current_context()
                self.simple_ai_bar.set_context(context.get('page', 'dashboard'), context)
                
        except Exception as e:
            print(f"Error updating AI status: {e}")
    
    def _get_current_context(self):
        """Get current application context for AI analysis"""
        try:
            current_index = self.stack.currentIndex() if hasattr(self, 'stack') else 0
            context_map = {
                0: "dashboard",
                1: "journal", 
                2: "ledger",
                3: "trial_balance",
                4: "reports",
                5: "accounts",
                6: "reminders",
                7: "period_closing",
                8: "team",
                9: "org_settings",
                10: "user_mgmt",
                11: "platform",
                12: "global_orgs",
                13: "settings"
            }
            
            context = context_map.get(current_index, "dashboard")
            
            return {
                "page": context,
                "time": datetime.now().isoformat(),
                "session_duration": (datetime.now() - self.start_time).total_seconds() / 3600,
                "user_active": True
            }
        except Exception as e:
            print(f"Error getting AI context: {e}")
            return {"page": "dashboard", "time": datetime.now().isoformat()}

    def _update_ai_context(self):
        """Update AI context when page changes"""
        # Update simple AI status bar with new context
        if hasattr(self, 'simple_ai_bar'):
            try:
                self._update_ai_status()
            except Exception as e:
                print(f"Error updating AI context: {e}")
    
    def _on_page_changed(self, index: int):
        """Handle page changes and update AI context"""
        self.stack.setCurrentIndex(index)
        
        # Update AI context with new page information
        page_names = ['dashboard', 'journal', 'ledger', 'trial_balance', 'reports', 
                     'accounts', 'reminders', 'period_closing', 'team_management',
                     'organization_settings', 'user_management', 'platform_overview',
                     'global_organizations', 'settings']
        if 0 <= index < len(page_names):
            page_name = page_names[index]
            self._update_ai_page_context(page_name)
            
            # Ensure page has fresh data for current workspace
            if hasattr(self, 'stack') and index < self.stack.count():
                current_page = self.stack.widget(index)
                if current_page:
                    self._ensure_page_data_loaded(current_page, page_name)
        
        # Update which sidebar button is checked
        for i, btn in enumerate(self.sidebar_buttons):
            btn.setChecked(i == index)
    
    def _ensure_page_data_loaded(self, page, page_name: str):
        """Ensure page has fresh data loaded for current workspace"""
        try:
            if hasattr(self, 'session_manager') and self.session_manager:
                current_org_id = self.session_manager.get_current_organization_id()
                if current_org_id and hasattr(self, 'page_manager'):
                    # Check if we have cached data for this page
                    cached_data = self.page_manager.get_page_data(page_name, current_org_id)
                    
                    if not cached_data or cached_data.get('status') != 'loaded':
                        # No cached data, load it now
                        self.logger.info(f"🔄 Loading data for {page_name} on navigation")
                        from src.core.page_manager import LoadingPriority
                        self.page_manager._load_page_priority(page_name, current_org_id, LoadingPriority.HIGH)
                        
                        # Refresh the page after loading
                        if hasattr(page, 'refresh_data'):
                            page.refresh_data()
                    
        except Exception as e:
            self.logger.error(f"Error ensuring page data loaded: {e}")
        
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
        menu_icon_path = ResourceManager.get_icon_path("menu_modern.svg")
        if menu_icon_path:
            self.toggle_btn.setIcon(QIcon(menu_icon_path))
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
        self._style_toggle_button()        # Add toggle button directly to main layout to maintain alignment
        layout.addWidget(self.toggle_btn)        # Navigation buttons with modern icons - expanded for multi-org support + period closing
        nav_items = [
            ("Dashboard", "dashboard_new.svg"),
            ("Journal", "journal_new.svg"),
            ("Ledger", "ledger_new.svg"),
            ("Trial Balance", "trial_balance_new.svg"),
            ("Reports", "reports_new.svg"),
            ("Accounts", "accounts_new.svg"),
            ("Reminders", "ledger_note.svg"),  # Reminders & Tasks
            ("Period Closing", "period_closing_modern.svg"),  # Period closing & audit
            ("Team", "team_new.svg"),  # Team management
            ("Org Settings", "org_settings_new.svg"),  # Organization settings
            ("User Mgmt", "user_mgmt_new.svg"),  # User management (admin only)
            ("Platform", "platform_new.svg"),  # Platform overview (super admin)
            ("Global Orgs", "global_orgs_new.svg"),  # Global organizations (super admin)
            ("Settings", "settings_new.svg"),
        ]# Add navigation buttons directly to main layout for proper alignment
        self.sidebar_buttons = []
        for idx, (label, icon_path) in enumerate(nav_items):
            btn = ModernSidebarButton(icon_path, label, expanded=self.sidebar_expanded)
            btn.clicked.connect(lambda checked, i=idx: self._on_page_changed(i))
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
                border: 1px solid rgba(255, 255, 255, 0.05);                border-radius: {border_radius}px;
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
        from .pages.reminders_tasks import RemindersTasksPage
        from .pages.period_closing import PeriodClosingPage
        from .pages.team_management import TeamManagementPage
        from .pages.organization_settings import OrganizationSettingsPage
        from .pages.user_management import UserManagementPage
        from .pages.platform_overview import PlatformOverviewPage
        from .pages.global_organizations import GlobalOrganizationsPage
        from .pages.settings import SettingsPage
        
        # Standard pages (always visible)
        standard_pages = [
            DashboardPage, JournalPage, LedgerPage, TrialBalancePage, 
            ReportsPage, HierarchicalAccountsPage, RemindersTasksPage, PeriodClosingPage
        ]
        
        # Organization management pages (visible to organization members)
        org_pages = [TeamManagementPage, OrganizationSettingsPage]
        
        # Admin pages (visible to organization admins)
        admin_pages = [UserManagementPage]
        
        # Super admin pages (visible to super admins only)
        super_admin_pages = [PlatformOverviewPage, GlobalOrganizationsPage]
        
        # Add all pages to stack in the same order as navigation buttons
        # Order must match nav_items: Dashboard, Journal, Ledger, Trial Balance, Reports, Accounts,
        # Reminders, Period Closing, Team, Org Settings, User Mgmt, Platform, Global Orgs, Settings
        page_classes_in_order = [
            DashboardPage, JournalPage, LedgerPage, TrialBalancePage, 
            ReportsPage, HierarchicalAccountsPage, RemindersTasksPage, PeriodClosingPage,
            TeamManagementPage, OrganizationSettingsPage, UserManagementPage,
            PlatformOverviewPage, GlobalOrganizationsPage, SettingsPage
        ]
        
        for idx, PageClass in enumerate(page_classes_in_order):
            if PageClass in [TeamManagementPage, OrganizationSettingsPage, UserManagementPage, 
                           PlatformOverviewPage, GlobalOrganizationsPage]:
                # Pass auth_manager for organization/user management pages
                page = PageClass(self.system, auth_manager=self.auth_manager, parent=self)
            elif PageClass == SettingsPage:
                # Pass auth_manager and session_manager for settings page
                page = PageClass(self.system, auth_manager=self.auth_manager, session_manager=self.session_manager, parent=self)
            elif PageClass == RemindersTasksPage:
                # Pass notification manager for reminders integration
                page = PageClass(self.system, notification_manager=self.notification_manager, parent=self)
            else:
                # Standard accounting pages
                page = PageClass(self.system, parent=self)
            self.stack.addWidget(page)
        
        # Set default page
        self.stack.setCurrentIndex(0)
        self.sidebar_buttons[0].setChecked(True)
          # Apply role-based visibility
        self._update_navigation_visibility()
        
    def _handle_maximize_button(self):
        """Handle maximize button click."""
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()
    
    def _handle_sign_out(self):
        """Handle user sign out request"""
        try:
            from PyQt6.QtWidgets import QMessageBox
            
            # Confirm sign out
            reply = QMessageBox.question(
                self, 
                "Sign Out", 
                "Are you sure you want to sign out?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.logger.info("User signing out...")
                
                # Clear session data
                if self.session_manager:
                    self.session_manager.clear_session()
                
                # Close current window and restart application
                self.close()
                
                # Restart the application to show login screen
                import sys
                import os
                python_executable = sys.executable
                
                # Get the main script path (go up from src/ui/mainwindow.py to run.py)
                current_file = os.path.abspath(__file__)
                project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
                script_path = os.path.join(project_root, "run.py")
                
                if os.path.exists(script_path):
                    # Restart the application
                    import subprocess
                    subprocess.Popen([python_executable, script_path])
                else:
                    self.logger.error(f"Could not find run.py at: {script_path}")
                
        except Exception as e:
            self.logger.error(f"Error during sign out: {e}")
            import traceback
            traceback.print_exc()
    
    def _toggle_maximize(self):
        """Legacy method - use _handle_maximize_button instead."""
        self._handle_maximize_button()
            
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
        self._style_toggle_button()        # Update button states
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
            "Reminders": 6,
            "Period Closing": 7,
            "Team": 8,
            "Org Settings": 9,
            "User Mgmt": 10,
            "Platform": 11,
            "Global Orgs": 12,
            "Settings": 13,
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
          # Try to load SVG icons from files first using resource manager
        try:
            minimize_icon_path = ResourceManager.get_icon_path("minimize.svg")
            maximize_icon_path = ResourceManager.get_icon_path("maximize.svg")
            close_icon_path = ResourceManager.get_icon_path("close.svg")
            
            if minimize_icon_path:
                minimize_icon = QIcon(minimize_icon_path)
                if not minimize_icon.isNull():
                    minimize_btn.setIcon(minimize_icon)
                    minimize_btn.setIconSize(QSize(16, 16))
                    minimize_btn.setText("")  # Clear text when icon is set
                else:
                    minimize_btn.setText("─")
            else:
                minimize_btn.setText("─")
                
            if maximize_icon_path:
                maximize_icon = QIcon(maximize_icon_path)
                if not maximize_icon.isNull():
                    maximize_btn.setIcon(maximize_icon)
                    maximize_btn.setIconSize(QSize(16, 16))
                    maximize_btn.setText("")  # Clear text when icon is set
                else:
                    maximize_btn.setText("□")
            else:
                maximize_btn.setText("□")
                
            if close_icon_path:
                close_icon = QIcon(close_icon_path)
                if not close_icon.isNull():
                    close_btn.setIcon(close_icon)
                    close_btn.setIconSize(QSize(16, 16))
                    close_btn.setText("")  # Clear text when icon is set
                else:
                    close_btn.setText("×")
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
        
        # F6: Force complete Mica refresh (for debugging monitor switching)
        if event.key() == Qt.Key.Key_F6:
            print("🔄 Force Mica refresh triggered (F6)")
            self.force_mica_refresh()
        
        # F7: Trigger monitor switch handling (for debugging)
        if event.key() == Qt.Key.Key_F7:
            print("🔄 Monitor switch handling triggered (F7)")
            self._handle_monitor_switch()
                
    def eventFilter(self, obj, event):
        """Filter events to handle click-outside-to-close for notification drawer and AI status bar."""
        from PyQt6.QtCore import QEvent
        from PyQt6.QtGui import QMouseEvent
        
        # Only handle mouse press events
        if event.type() == QEvent.Type.MouseButtonPress:
            if isinstance(event, QMouseEvent):
                global_pos = event.globalPosition().toPoint()
                
                # Check if notification drawer is open
                if hasattr(self, 'notification_drawer') and self.notification_drawer.isVisible():
                    # Convert to notification drawer's coordinate system
                    drawer_pos = self.notification_drawer.mapFromGlobal(global_pos)
                    
                    # Check if click is outside the drawer
                    if not self.notification_drawer.rect().contains(drawer_pos):
                        # Also check if click is not on the notification button
                        if hasattr(self, 'notification_button'):
                            btn_pos = self.notification_button.mapFromGlobal(global_pos)
                            if not self.notification_button.rect().contains(btn_pos):
                                # Click is outside both drawer and button, close drawer
                                self.notification_drawer.hide()
                                return True  # Event handled
                
                # Check if AI status bar is expanded
                if hasattr(self, 'simple_ai_bar') and self.simple_ai_bar.is_expanded:
                    # Convert to AI status bar's coordinate system
                    ai_bar_pos = self.simple_ai_bar.mapFromGlobal(global_pos)
                    
                    # Check if click is outside the AI status bar
                    if not self.simple_ai_bar.rect().contains(ai_bar_pos):
                        # Click is outside AI status bar, collapse it
                        self.simple_ai_bar._collapse_to_normal()
                        return True  # Event handled
        
        # Continue with normal event processing
        return super().eventFilter(obj, event)
                
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
                    page._apply_styling()        # Force a style refresh        self.style().unpolish(self)
        self.style().polish(self)
    
    def _initialize_accounting_system(self):
        """Initialize Supabase-first accounting system with offline support and multi-tenant context."""
        try:
            self.logger.info(f"Initializing Supabase offline-capable accounting system...")
            
            # Get organization context from session manager
            organization_id = None
            user_id = None
            
            if self.session_manager:
                organization_id = self.session_manager.get_active_organization_id()
                user_id = self.session_manager.get_current_user_id()
                self.logger.info(f"Using organization context: {organization_id}, user: {user_id}")
            
            # Initialize the unified accounting system
            accounting_system = AccountingSystem(self.auth_manager)
            
            # Set organization context
            if organization_id:
                success = accounting_system.set_organization(organization_id)
                if not success:
                    self.logger.error(f"Failed to set organization context: {organization_id}")
            
            # Test connectivity
            if accounting_system.is_online:
                self.logger.info("✅ Unified accounting system online")
            else:
                self.logger.warning("📱 Starting in offline mode with cached data")
              # Wrap with enhanced features if available
            try:
                from ..core.enhanced_accounting_system import EnhancedAccountingSystem
                enhanced_system = EnhancedAccountingSystem(
                    base_accounting_system=accounting_system,
                    organization_id=organization_id,
                    user_id=user_id
                )
                
                # Initialize enhanced features
                init_results = enhanced_system.initialize_enhanced_features()
                self.logger.info(f"Enhanced features initialization results: {init_results}")
                
                return enhanced_system
                
            except Exception as e:
                self.logger.warning(f"Enhanced features not available, using base system: {e}")
                return accounting_system
                
        except Exception as e:
            self.logger.error(f"Accounting system initialization failed: {e}")
            raise Exception(f"Failed to initialize accounting database: {e}")
    
    def _setup_sync_updates(self):
        """Setup periodic connection status updates."""
        self.sync_timer = QTimer()
        self.sync_timer.timeout.connect(self._update_connection_status)
        self.sync_timer.start(5000)  # Update every 5 seconds
        # Initial status update
        self._update_connection_status()
    
    def _update_connection_status(self):
        """Update connection status from offline manager."""
        if not hasattr(self, 'connection_indicator'):
            return
            
        try:
            # Check if accounting system is available and properly initialized
            if hasattr(self, 'accounting_system') and self.accounting_system:
                # Get connection status from accounting system
                is_online = getattr(self.accounting_system, 'is_online', False)
                
                # If accounting system says offline, do a quick internet test
                if not is_online:
                    is_online = self._test_internet_connectivity()
                
                # Handle connecting state
                if hasattr(self.accounting_system, 'offline_manager') and self.accounting_system.offline_manager:
                    offline_mgr = self.accounting_system.offline_manager
                    sync_status = getattr(offline_mgr, 'sync_status', None)
                    
                    if sync_status:
                        is_syncing = getattr(sync_status, 'is_syncing', False)
                        self.connection_indicator.set_connecting_state(is_syncing)
                        
                        # Check for sync issues (notifications only)
                        failed_ops = getattr(sync_status, 'failed_operations', 0)
                        pending_ops = getattr(offline_mgr, 'pending_operations', 0)
                        
                        if failed_ops > 0:
                            self.add_sync_notification(
                                "Sync Issues",
                                f"{failed_ops} operations failed to sync. Check your connection.",
                                "warning"
                            )
                        elif pending_ops > 0 and not is_online:
                            self.add_sync_notification(
                                "Working Offline",
                                f"{pending_ops} changes will sync when online.",
                                "info"
                            )
                
                # Update connection indicator (no quality - just connected/disconnected)
                self.connection_indicator.update_connection_status(is_online)
                self.logger.debug(f"Connection status updated: online={is_online}")
                
            else:
                # No accounting system available - test basic internet connectivity
                is_online = self._test_internet_connectivity()
                self.connection_indicator.update_connection_status(is_online)
                self.logger.debug(f"No accounting system - basic internet test: online={is_online}")
                    
        except Exception as e:
            self.logger.error(f"Failed to update connection status: {e}")
            # Set offline state on error
            if hasattr(self, 'connection_indicator'):
                self.connection_indicator.update_connection_status(False)
                
    def _initial_connection_check(self):
        """Perform initial connection check when UI is ready"""
        try:
            if hasattr(self, 'connection_indicator'):
                # Start with a basic internet connectivity test
                is_online = self._test_internet_connectivity()
                self.connection_indicator.update_connection_status(is_online)
                self.logger.debug(f"Initial connection check: online={is_online}")
        except Exception as e:
            self.logger.error(f"Initial connection check failed: {e}")
            if hasattr(self, 'connection_indicator'):
                self.connection_indicator.update_connection_status(False)
    
    def _test_internet_connectivity(self):
        """Quick test for internet connectivity"""
        try:
            import urllib.request
            import socket
            
            # First try a quick socket connection to Google DNS
            socket.create_connection(("8.8.8.8", 53), timeout=2)
            return True
        except (socket.timeout, socket.error, OSError):
            try:
                # Fallback: try Cloudflare DNS
                socket.create_connection(("1.1.1.1", 53), timeout=2)
                return True
            except (socket.timeout, socket.error, OSError):
                try:
                    # Last attempt: try HTTP request to a reliable site
                    urllib.request.urlopen('http://www.google.com', timeout=3)
                    return True
                except:
                    return False

    def _show_notifications(self):
        """Notification button clicked - show/hide notification drawer"""
        if hasattr(self, 'notification_drawer'):
            if self.notification_drawer.is_visible:
                self.notification_drawer.hide_drawer()
            else:
                self._position_notification_drawer()
                self.notification_drawer.show_drawer()
        
    def _position_notification_drawer(self):
        """Position the notification drawer on the right side"""
        if not hasattr(self, 'notification_drawer'):
            return
        
        # Simple positioning - let the drawer handle its own positioning logic
        # The drawer will position itself relative to its parent (main_container)
        pass
        
    def add_notification(self, title, message, notification_type="info"):
        """Add a notification using the notification manager"""
        if hasattr(self, 'notification_manager'):
            self.notification_manager.add_notification(title, message, notification_type)
        else:
            # Fallback to console logging
            print(f"📊 Notification: {title} - {message} ({notification_type})")
            
    def _add_welcome_notification(self):
        """Add a welcome notification to test the notification system."""
        try:
            self.add_notification(
                "Welcome to Accountuitive!",
                "Your intelligent accounting companion is ready to help you manage your finances.",
                "info"
            )
        except Exception as e:
            print(f"Error adding welcome notification: {e}")
    
    def log_activity(self, message):
        """Log an activity - connection indicator shows status automatically."""
        # Connection indicator automatically shows status based on accounting system
        pass
    
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
    
    def set_session_manager(self, session_manager):
        """Set or update the session manager and refresh UI accordingly"""
        self.session_manager = session_manager
        self.logger.info("Session manager updated - refreshing navigation visibility")
        self._update_navigation_visibility()
        
        # Update user profile button with new session
        if hasattr(self, 'user_profile_button'):
            self.user_profile_button.update_user_profile(session_manager)
        
        # Organization context has changed - workspace switcher will be updated via signal

    def refresh_navigation_for_testing(self):
        """Manual method to refresh navigation - useful for testing"""
        print("🔄 Manually refreshing navigation visibility...")
        if self.session_manager:
            print(f"   Current role: {self.session_manager.get_current_user_role()}")
            print(f"   Is super admin: {self.session_manager.is_super_admin()}")
            print(f"   Active org: {self.session_manager.get_active_organization_id()}")
        else:
            print("   No session manager available")
        self._update_navigation_visibility()

    def _update_navigation_visibility(self):
        """Update sidebar navigation visibility based on database-driven permissions."""
        print("🔍 DEBUG: _update_navigation_visibility() called")
        
        try:
            if not hasattr(self, 'sidebar_buttons') or not self.sidebar_buttons:
                print("🔍 DEBUG: No sidebar buttons available")
                return
                
            print(f"🔍 DEBUG: Found {len(self.sidebar_buttons)} sidebar buttons")
            
            if not self.session_manager:
                print("🔍 DEBUG: No session manager - showing all buttons")
                for button in self.sidebar_buttons:
                    button.show()
                return
            
            print("🔍 DEBUG: Session manager found, getting org info...")
            
            # Get current organization and auth manager
            org_id = self.session_manager.get_active_organization_id()
            auth_manager = getattr(self.session_manager, 'auth_manager', None)
            
            print(f"🔍 DEBUG: org_id = {org_id}, auth_manager = {auth_manager is not None}")
            
            if not auth_manager or not org_id:
                print("🔍 DEBUG: No auth manager or organization - showing basic pages")
                for i, button in enumerate(self.sidebar_buttons):
                    button.setVisible(i in [0, 13])  # Only Dashboard and Settings
                return
            
            print("🔍 DEBUG: Getting user role and org type...")
            
            user_role = self.session_manager.get_current_user_role()
            org_type = self.session_manager.get_current_organization_type()
            
            print(f"🔍 DEBUG: Role: {user_role}, Org Type: {org_type}")
            
            # Define page key mappings for nav_items indices:
            page_mappings = {
                0: 'dashboard',
                1: 'journal_entries',
                2: 'journal_entries',  # Ledger uses same permissions as journal
                3: 'reports',  # Trial Balance is a type of report
                4: 'reports',
                5: 'accounts',
                6: 'dashboard',  # Reminders/tasks use dashboard permissions for now
                7: 'settings',  # Period closing needs admin permissions
                8: 'team_management',  # Team management
                9: 'organization_settings',  # Org settings
                10: 'user_management',  # User management
                11: 'platform_overview',  # Platform overview - use database permissions
                12: 'global_organizations',  # Global organizations - use database permissions
                13: 'settings'  # General settings
            }
            
            # Pages that should be hidden for personal workspaces (single-user orgs)
            personal_workspace_hidden = [8, 9, 10] if org_type == 'personal' else []  # Team, Org Settings, User Mgmt
            
            print(f"🔍 DEBUG: Personal workspace hidden pages: {personal_workspace_hidden}")
            
            # Get all permissions in a single call to minimize RPC calls
            all_permissions = auth_manager.get_all_page_permissions_single_rpc(org_id)
            
            # Update button visibility based on permissions
            visible_count = 0
            for i, button in enumerate(self.sidebar_buttons):
                should_show = False
                
                # Skip pages that don't make sense for personal workspaces
                if i in personal_workspace_hidden:
                    should_show = False
                    print(f"🔍 DEBUG: Page {i} hidden for personal workspace")
                elif page_mappings.get(i):
                    # Use the all permissions result
                    page_key = page_mappings[i]
                    page_perms = all_permissions.get(page_key, {})
                    can_view = page_perms.get('view', False)
                    should_show = can_view
                    print(f"🔍 DEBUG: Page {i} ({page_key}): can_view = {can_view}")
                        
                else:
                    # No specific permission mapping - default behavior
                    should_show = (i == 0)  # Show dashboard by default
                    print(f"🔍 DEBUG: Page {i} - no mapping, showing: {should_show}")
                
                button.setVisible(should_show)
                if should_show:
                    visible_count += 1
                    
            print(f"🔍 DEBUG: Navigation updated: {visible_count}/{len(self.sidebar_buttons)} tabs visible")
            
        except Exception as e:
            print(f"🔍 DEBUG: Error in navigation visibility: {e}")
            import traceback
            traceback.print_exc()
            # Fallback: show all buttons
            if hasattr(self, 'sidebar_buttons'):
                for button in self.sidebar_buttons:
                    button.show()

    def _on_organization_changed(self, org_id):
        org_id = self.session_manager.get_active_organization_id()
        auth_manager = getattr(self.session_manager, 'auth_manager', None)
        
        if not auth_manager or not org_id:
            self.logger.debug("Navigation visibility check skipped - no auth manager or organization")
            # Show basic pages when no organization context
            for i, button in enumerate(self.sidebar_buttons):
                button.setVisible(i in [0, 13])  # Only Dashboard and Settings
            return
        
        user_role = self.session_manager.get_current_user_role()
        org_type = self.session_manager.get_current_organization_type()
        
        # Debug logging for permission-based visibility
        self.logger.info(f"🔐 Navigation visibility check - Role: {user_role}, Org Type: {org_type}, Org: {org_id}")
        self.logger.info(f"� Navigation visibility check - Role: {user_role}, Super Admin: False, Org: {org_id}")
        
        # Define page key mappings for nav_items indices:
        # 0: Dashboard, 1: Journal, 2: Ledger, 3: Trial Balance, 4: Reports, 5: Accounts
        # 6: Reminders, 7: Period Closing, 8: Team, 9: Org Settings, 10: User Mgmt
        # 11: Platform, 12: Global Orgs, 13: Settings
        page_mappings = {
            0: 'dashboard',
            1: 'journal_entries',
            2: 'journal_entries',  # Ledger uses same permissions as journal
            3: 'reports',  # Trial Balance is a type of report
            4: 'reports',
            5: 'accounts',
            6: 'dashboard',  # Reminders/tasks use dashboard permissions for now
            7: 'settings',  # Period closing needs admin permissions
            8: 'team_management',  # Team management
            9: 'organization_settings',  # Org settings
            10: 'user_management',  # User management
            11: 'platform_overview',  # Platform overview - use database permissions
            12: 'global_organizations',  # Global organizations - use database permissions
            13: 'settings'  # General settings
        }
        
        # Pages that should be hidden for personal workspaces (single-user orgs)
        personal_workspace_hidden = [8, 9, 10] if org_type == 'personal' else []  # Team, Org Settings, User Mgmt
        
        # Batch check permissions for all pages to reduce RPC calls
        pages_to_check = []
        page_indices = []
        
        for i, button in enumerate(self.sidebar_buttons):
            if i not in personal_workspace_hidden and page_mappings.get(i):
                pages_to_check.append(page_mappings[i])
                page_indices.append(i)
        
        # Batch check permissions
        if pages_to_check:
            try:
                permissions = auth_manager.batch_check_page_permissions(org_id, pages_to_check, 'view')
                self.logger.debug(f"Batch permission check completed for {len(pages_to_check)} pages")
            except Exception as e:
                self.logger.error(f"Error in batch permission check: {e}")
                permissions = {page: False for page in pages_to_check}
        else:
            permissions = {}
        
        # Update button visibility based on permissions
        for i, button in enumerate(self.sidebar_buttons):
            should_show = False
            
            # Skip pages that don't make sense for personal workspaces
            if i in personal_workspace_hidden:
                should_show = False
                self.logger.debug(f"Page {i} hidden for personal workspace")
            elif page_mappings.get(i):
                # Use batch-checked permissions
                page_key = page_mappings[i]
                can_view = permissions.get(page_key, False)
                should_show = can_view
                self.logger.debug(f"Page {i} ({page_key}): can_view = {can_view}")
            else:
                # No specific permission mapping - default behavior
                should_show = (i == 0)  # Show dashboard by default
            
            button.setVisible(should_show)
            
        # Log summary
        visible_count = sum(1 for button in self.sidebar_buttons if button.isVisible())
        self.logger.info(f"Navigation updated: {visible_count}/{len(self.sidebar_buttons)} tabs visible for {org_type} workspace (role: '{user_role}')")
    
    def _on_organization_changed(self, org_id):
        """Handle organization change from the organization switcher."""
        try:
            if self.session_manager:
                success = self.session_manager.set_active_organization(org_id)
                if success:
                    # Reinitialize accounting system with new organization context
                    self.accounting_system = self._initialize_accounting_system(None)
                    self.system = self.accounting_system
                    
                    # Update all pages with new organization context
                    for i in range(self.stack.count()):
                        page = self.stack.widget(i)
                        if hasattr(page, 'refresh_organization_context'):
                            page.refresh_organization_context(self.system)
                      # Update navigation visibility for new organization role
                    self._update_navigation_visibility()
                    
                    self.logger.info(f"Organization context changed to: {org_id}")
                else:
                    self.logger.error("Failed to change organization context")
                    
        except Exception as e:
            self.logger.error(f"Error changing organization: {e}")
    
    def _update_sidebar_visibility(self):
        """Update sidebar button visibility."""
        self._update_navigation_visibility()
    
    def add_sync_notification(self, title, message, notification_type="sync"):
        """Add a sync-related notification with sync icon."""
        self.add_notification(title, message, notification_type)
    
    def notify_sync_started(self):
        """Notify that sync has started."""
        self.add_sync_notification(
            "Sync Started",
            "Synchronizing your data with the server...",
            "sync"
        )
    
    def notify_sync_completed(self, details=None):
        """Notify that sync has completed successfully."""
        message = "Your data has been successfully synchronized with the server."
        if details:
            message += f" {details}"
        self.add_sync_notification(
            "Sync Completed",
            message,
            "success"
        )
    
    def notify_sync_failed(self, error_msg):
        """Notify that sync has failed."""
        self.add_sync_notification(
            "Sync Failed",
            f"Failed to synchronize data: {error_msg}",
            "error"
        )
    
    def notify_sync_conflict(self, conflict_count):
        """Notify about sync conflicts."""
        message = f"{conflict_count} conflicts detected during sync. Manual resolution may be required."
        self.add_sync_notification(
            "Sync Conflicts",
            message,
            "warning"
        )
    
    def notify_connection_lost(self):
        """Notify that connection to server was lost."""
        self.add_sync_notification(
            "Connection Lost",
            "Lost connection to the server. Working in offline mode.",
            "warning"
        )
    
    def notify_connection_restored(self):
        """Notify that connection to server was restored."""
        self.add_sync_notification(
            "Connection Restored",            "Connection to the server has been restored. Sync will resume automatically.",
            "success"
        )
    
    # AI command processing removed - now handled by SimpleAIStatusBar
    
    def _handle_ai_response(self, response_text: str):
        """Handle AI response text"""
        # The status bar will handle displaying the response
        pass
    
    def _handle_ai_navigation(self, page_name: str, parameters: dict):
        """Unified navigation handler for all pages, reports, and account-specific views"""
        print(f"🎯 MainWindow received navigation request: page='{page_name}', params={parameters}")
        self.logger.info(f"Enhanced AI navigation: page='{page_name}', params={parameters}")
        
        # Update AI context before navigation
        self._update_ai_context_for_navigation(page_name, parameters)
        
        # Handle specific account navigation
        if page_name == 'ledger' and parameters.get('specific_account'):
            account_name = parameters.get('account_name')
            if account_name:
                print(f"🎯 Handling specific account navigation: {account_name}")
                success = self.navigate_to_specific_account_ledger(
                    account_name, 
                    parameters.get('start_date'), 
                    parameters.get('end_date')
                )
                if success:
                    print(f"✅ Successfully navigated to {account_name} ledger")
                else:
                    print(f"⚠️ Could not find account: {account_name}")
                return
        
        # Handle reports with specific report types and date ranges
        if page_name == 'reports' and parameters.get('report_type'):
            report_type = parameters.get('report_type')
            start_date = parameters.get('start_date')
            end_date = parameters.get('end_date')
            
            print(f"🎯 Handling report generation: {report_type}")
            
            if report_type == 'trial_balance':
                self._navigate_to_trial_balance(start_date, end_date)
            elif report_type == 'general_ledger':
                self._navigate_to_ledger(start_date, end_date)  
            elif report_type == 'income_statement':
                self._navigate_to_income_statement(start_date, end_date)
            elif report_type == 'balance_sheet':
                self._navigate_to_balance_sheet(end_date)
            elif report_type == 'cash_flow':
                self._navigate_to_cash_flow(start_date, end_date)
            else:
                # Default to reports page with parameters
                self._navigate_to_reports_page_with_params(parameters)
            return
        
        # Perform standard navigation
        page_mapping = {
            'dashboard': 0, 'journal': 1, 'ledger': 2, 'trial_balance': 3,
            'reports': 4, 'accounts': 5, 'reminders': 6, 'period_closing': 7,
            'settings': -1  # Settings is usually last
        }
        
        if page_name in page_mapping:
            target_index = page_mapping[page_name]
            print(f"📍 Navigating to index {target_index} for page {page_name}")
            if target_index >= 0:
                self.stack.setCurrentIndex(target_index)
                print(f"✅ Stack index set to {target_index}")
                if target_index < len(self.sidebar_buttons):
                    # Update sidebar selection
                    for btn in self.sidebar_buttons:
                        btn.setChecked(False)
                    self.sidebar_buttons[target_index].setChecked(True)
                    print(f"✅ Sidebar button {target_index} checked")
            
            # Apply parameters to the target page
            self._apply_navigation_parameters(page_name, parameters)
            
            # Update AI context with new page state
            self._update_ai_page_context(page_name)
        else:
            print(f"❌ Page '{page_name}' not found in mapping")
            
    def _navigate_to_reports_page_with_params(self, parameters: dict):
        """Navigate to reports page and apply parameters"""
        print(f"🎯 Navigating to Reports page with parameters: {parameters}")
        self.stack.setCurrentIndex(4)  # Reports page index
        for btn in self.sidebar_buttons:
            btn.setChecked(False)
        self.sidebar_buttons[4].setChecked(True)
        
        # Apply parameters to reports page
        reports_page = self.stack.currentWidget()
        if hasattr(reports_page, 'set_date_range'):
            start_date = parameters.get('start_date')
            end_date = parameters.get('end_date')
            if start_date and end_date:
                reports_page.set_date_range(start_date, end_date)
                print(f"✅ Applied date range to Reports page: {start_date} to {end_date}")
        
        print(f"✅ Successfully navigated to Reports page")
    
    def _handle_ai_report_request(self, report_type: str, parameters: dict):
        """Handle AI-requested report generation using NL dialogue intelligence with main window integration"""
        self.logger.info(f"AI report request: type='{report_type}', params={parameters}")
        print(f"🚀 Processing AI report request: {report_type} with params: {parameters}")
        
        try:
            # Use NL dialogue intelligence to parse the request
            raw_prompt = parameters.get('original_prompt', '')
            parsed_request = self._parse_nl_report_request(raw_prompt or report_type, parameters)
            
            report_type = parsed_request['report_type']
            start_date = parsed_request.get('start_date')
            end_date = parsed_request.get('end_date')
            as_of_date = parsed_request.get('as_of_date')
            
            print(f"🧠 Parsed request: type={report_type}, dates={start_date} to {end_date}, as_of={as_of_date}")
            
            # Route to appropriate page using the parsed information
            if report_type in ['trial_balance', 'trial']:
                self._navigate_to_trial_balance(start_date, end_date)
                
            elif report_type in ['general_ledger', 'ledger']:
                self._navigate_to_ledger(start_date, end_date)
                
            elif report_type == 'income_statement':
                self._navigate_to_income_statement(start_date, end_date)
                
            elif report_type == 'balance_sheet':
                self._navigate_to_balance_sheet(as_of_date or end_date)
                
            elif report_type == 'cash_flow':
                self._navigate_to_cash_flow(start_date, end_date)
                
            else:
                # For unrecognized reports, show intelligent guidance using real data
                self._show_intelligent_report_guidance(raw_prompt, parsed_request)
                
            print(f"🎉 Successfully processed {report_type} report request!")
            self.logger.info(f"Successfully processed {report_type} report request")
                
        except Exception as e:
            print(f"❌ Error in report generation: {e}")
            self.logger.error(f"Failed to process report request: {e}")
            # Show error message to user
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self,
                "Report Error", 
                f"Could not process report request.\nError: {str(e)}",
                QMessageBox.StandardButton.Ok
            )
    
    def _parse_nl_report_request(self, prompt: str, parameters: dict):
        """Parse natural language report request using NL dialogue intelligence"""
        import re
        import calendar
        import dateutil.parser
        from PyQt6.QtCore import QDate
        
        prompt_lc = prompt.lower()
        result = {
            'report_type': None,
            'start_date': None,
            'end_date': None,
            'as_of_date': None
        }
        
        # Extract report type using NL dialogue patterns
        if any(term in prompt_lc for term in ["income statement", "profit loss", "p&l", "pnl"]):
            result['report_type'] = "income_statement"
        elif any(term in prompt_lc for term in ["balance sheet", "financial position"]):
            result['report_type'] = "balance_sheet"
        elif any(term in prompt_lc for term in ["cash flow", "cashflow"]):
            result['report_type'] = "cash_flow"
        elif any(term in prompt_lc for term in ["trial balance", "trial"]):
            result['report_type'] = "trial_balance"
        elif any(term in prompt_lc for term in ["general ledger", "ledger"]):
            result['report_type'] = "general_ledger"
        else:
            # Fallback to parameters if no clear type found
            result['report_type'] = parameters.get('report_type', 'unknown')
        
        # Extract dates using NL dialogue patterns
        today = QDate.currentDate().toString("yyyy-MM-dd")
        
        # Look for specific month/year patterns
        month_year = re.search(r'(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{4})', prompt_lc)
        year_only = re.search(r'\b(20\d{2})\b', prompt_lc)
        as_of = re.search(r'as of (\w+ \d{1,2},? \d{4})', prompt_lc)
        
        # Check for relative dates
        if "last month" in prompt_lc:
            last_month_date = QDate.currentDate().addMonths(-1)
            result['start_date'] = last_month_date.toString("yyyy-MM-01")
            result['end_date'] = QDate(last_month_date.year(), last_month_date.month(), 
                                     calendar.monthrange(last_month_date.year(), last_month_date.month())[1]).toString("yyyy-MM-dd")
        elif "this month" in prompt_lc or "current month" in prompt_lc:
            current_date = QDate.currentDate()
            result['start_date'] = current_date.toString("yyyy-MM-01")
            result['end_date'] = today
        elif "last year" in prompt_lc:
            last_year = QDate.currentDate().year() - 1
            result['start_date'] = f"{last_year}-01-01"
            result['end_date'] = f"{last_year}-12-31"
        elif "this year" in prompt_lc or "current year" in prompt_lc:
            current_year = QDate.currentDate().year()
            result['start_date'] = f"{current_year}-01-01"
            result['end_date'] = today
        elif month_year:
            # Specific month and year
            month = list(calendar.month_name).index(month_year.group(1).capitalize())
            year_val = int(month_year.group(2))
            result['start_date'] = f"{year_val}-{month:02d}-01"
            result['end_date'] = f"{year_val}-{month:02d}-{calendar.monthrange(year_val, month)[1]:02d}"
        elif as_of:
            # As of date for balance sheet
            try:
                result['as_of_date'] = dateutil.parser.parse(as_of.group(1)).strftime("%Y-%m-%d")
            except:
                result['as_of_date'] = today
        elif year_only:
            # Full year
            year_val = int(year_only.group(1))
            result['start_date'] = f"{year_val}-01-01"
            result['end_date'] = f"{year_val}-12-31"
        else:
            # Use parameters or default to current month
            date_range = parameters.get('date_range', {})
            if date_range:
                result['start_date'] = date_range.get('start')
                result['end_date'] = date_range.get('end')
            else:
                # Default to current month
                current_date = QDate.currentDate()
                result['start_date'] = current_date.toString("yyyy-MM-01")
                result['end_date'] = today
        
        return result
    
    def _navigate_to_trial_balance(self, start_date: str, end_date: str):
        """Navigate to Trial Balance page with date range"""
        print(f"📍 Navigating to Trial Balance page")
        self.stack.setCurrentIndex(3)
        for btn in self.sidebar_buttons:
            btn.setChecked(False)
        self.sidebar_buttons[3].setChecked(True)
        
        # Apply date range using the new method
        trial_balance_page = self.stack.currentWidget()
        if hasattr(trial_balance_page, 'set_date_range') and start_date and end_date:
            success = trial_balance_page.set_date_range(start_date, end_date)
            if success:
                print(f"✅ Successfully set Trial Balance date range: {start_date} to {end_date}")
            else:
                print(f"⚠️ Could not set date range on Trial Balance page")
        else:
            print(f"⚠️ Trial Balance page doesn't support date range setting")
        
        print(f"✅ Successfully navigated to Trial Balance page")
    
    def _navigate_to_ledger(self, start_date: str, end_date: str):
        """Navigate to Ledger page with date range"""
        print(f"📍 Navigating to General Ledger page")
        self.stack.setCurrentIndex(2)
        for btn in self.sidebar_buttons:
            btn.setChecked(False)
        self.sidebar_buttons[2].setChecked(True)
        
        # Apply date range using the new method
        ledger_page = self.stack.currentWidget()
        if hasattr(ledger_page, 'set_date_range') and start_date and end_date:
            success = ledger_page.set_date_range(start_date, end_date)
            if success:
                print(f"✅ Successfully set Ledger date range: {start_date} to {end_date}")
            else:
                print(f"⚠️ Could not set date range on Ledger page")
        else:
            print(f"⚠️ Ledger page doesn't support date range setting")
        
        print(f"✅ Successfully navigated to Ledger page")
    
    def navigate_to_specific_account_ledger(self, account_name: str, start_date: str = None, end_date: str = None):
        """Navigate to specific account ledger (for AI navigation)"""
        print(f"📍 Navigating to specific account ledger: {account_name}")
        
        # Navigate to ledger page first
        self.stack.setCurrentIndex(2)
        for btn in self.sidebar_buttons:
            btn.setChecked(False)
        self.sidebar_buttons[2].setChecked(True)
        
        # Get the ledger page
        ledger_page = self.stack.currentWidget()
        
        # Set date range if provided
        if start_date and end_date and hasattr(ledger_page, 'set_date_range'):
            ledger_page.set_date_range(start_date, end_date)
        
        # Show specific account
        if hasattr(ledger_page, 'show_specific_account'):
            success = ledger_page.show_specific_account(account_name)
            if success:
                print(f"✅ Successfully navigated to account: {account_name}")
                return True
            else:
                print(f"⚠️ Account not found, showing filtered results for: {account_name}")
                return False
        else:
            print(f"⚠️ Ledger page doesn't support specific account navigation")
            return False
    
    def _navigate_to_income_statement(self, start_date: str, end_date: str):
        """Navigate to Reports page and trigger Income Statement view"""
        print(f"📍 Navigating to Reports page for Income Statement")
        self.stack.setCurrentIndex(4)
        for btn in self.sidebar_buttons:
            btn.setChecked(False)
        self.sidebar_buttons[4].setChecked(True)
        
        # Wait for page to load then trigger Income Statement
        QTimer.singleShot(100, lambda: self._trigger_income_statement(start_date, end_date))
    
    def _navigate_to_balance_sheet(self, as_of_date: str):
        """Navigate to Reports page and trigger Balance Sheet view"""
        print(f"📍 Navigating to Reports page for Balance Sheet")
        self.stack.setCurrentIndex(4)
        for btn in self.sidebar_buttons:
            btn.setChecked(False)
        self.sidebar_buttons[4].setChecked(True)
        
        # Wait for page to load then trigger Balance Sheet
        QTimer.singleShot(100, lambda: self._trigger_balance_sheet(as_of_date))
    
    def _navigate_to_cash_flow(self, start_date: str, end_date: str):
        """Navigate to Reports page and trigger Cash Flow view"""
        print(f"📍 Navigating to Reports page for Cash Flow Statement")
        self.stack.setCurrentIndex(4)
        for btn in self.sidebar_buttons:
            btn.setChecked(False)
        self.sidebar_buttons[4].setChecked(True)
        
        # Wait for page to load then trigger Cash Flow
        QTimer.singleShot(100, lambda: self._trigger_cash_flow(start_date, end_date))
    
    def _show_intelligent_report_guidance(self, original_prompt: str, parsed_request: dict):
        """Show intelligent guidance using real accounting data like NL dialogue"""
        try:
            # Navigate to Reports page first
            self.stack.setCurrentIndex(4)
            for btn in self.sidebar_buttons:
                btn.setChecked(False)
            self.sidebar_buttons[4].setChecked(True)
            
            # Get real data summary like NL dialogue does
            data_summary = self._get_accounting_data_summary(parsed_request)
            
            # Show intelligent guidance with real data
            from PyQt6.QtWidgets import QMessageBox
            
            message = f"🤖 AI Assistant - Report Analysis\n\n"
            message += f"Your request: \"{original_prompt}\"\n\n"
            message += f"I've analyzed your accounting data:\n"
            message += f"{data_summary}\n\n"
            message += f"Available reports in this page:\n"
            message += f"• Income Statement - Click to view P&L\n"
            message += f"• Balance Sheet - Click to view financial position\n"
            message += f"• Cash Flow Statement - Click to view cash analysis\n"
            message += f"• Trial Balance - Navigate to Trial Balance page\n"
            message += f"• General Ledger - Navigate to Ledger page\n\n"
            message += f"Please click on the appropriate report card or ask me more specifically!"
            
            QMessageBox.information(
                self,
                "AI Assistant - Smart Report Guide",
                message,
                QMessageBox.StandardButton.Ok
            )
            
        except Exception as e:
            print(f"❌ Error showing intelligent guidance: {e}")
            # Fallback to basic guidance
            self._show_reports_help(original_prompt)
    
    def _get_accounting_data_summary(self, parsed_request: dict):
        """Get a summary of accounting data like NL dialogue does"""
        try:
            start_date = parsed_request.get('start_date')
            end_date = parsed_request.get('end_date')
            as_of_date = parsed_request.get('as_of_date')
            
            summary = []
            
            # Get trial balance summary
            if hasattr(self.system, 'get_trial_balance'):
                try:
                    trial_balance = self.system.get_trial_balance(start_date, end_date)
                    if trial_balance:
                        total_debits = sum(acc.get('debit', 0) for acc in trial_balance)
                        total_credits = sum(acc.get('credit', 0) for acc in trial_balance)
                        summary.append(f"Trial Balance: {len(trial_balance)} accounts, Total Debits: ${total_debits:,.2f}, Total Credits: ${total_credits:,.2f}")
                except:
                    pass
            
            # Get accounts summary
            if hasattr(self.system, 'get_accounts'):
                try:
                    accounts = self.system.get_accounts()
                    if accounts:
                        account_types = {}
                        for acc in accounts:
                            acc_type = acc.get('type', 'Unknown')
                            account_types[acc_type] = account_types.get(acc_type, 0) + 1
                        summary.append(f"Chart of Accounts: {len(accounts)} accounts ({', '.join([f'{count} {type_}' for type_, count in account_types.items()])})")
                except:
                    pass
            
            # Get recent transactions
            if hasattr(self.system, 'get_journal_entries'):
                try:
                    entries = self.system.get_journal_entries(limit=10)
                    if entries:
                        summary.append(f"Recent Activity: {len(entries)} recent transactions")
                except:
                    pass
            
            return '\n'.join(summary) if summary else "Accounting data available for analysis."
            
        except Exception as e:
            return f"Data analysis in progress..."
    
    def _handle_ai_reminder_creation(self, reminder_data: dict):
        """Handle AI-created reminders with rich data structure"""
        self.logger.info(f"AI reminder creation: {reminder_data}")
        print(f"🔔 Processing AI reminder: {reminder_data}")
        
        try:
            # Get the reminders page from the stack (index 6)
            reminders_page = self.stack.widget(6)  # Reminders page is at index 6
            
            if reminders_page and hasattr(reminders_page, 'add_reminder_from_ai'):
                print(f"📝 Adding reminder to reminders page...")
                
                # Pass the complete reminder data instead of extracting individual fields
                # This prevents duplicate reminder creation by reusing the AI plugin's data
                reminder_id = reminders_page.add_reminder_from_ai(reminder_data=reminder_data)
                
                print(f"✅ Successfully created reminder with ID: {reminder_id}")
                self.logger.info(f"Successfully created reminder: {title} (ID: {reminder_id})")
                
                # Also add to notification manager if available for immediate alerts
                if hasattr(self, 'notification_manager'):
                    self.notification_manager.add_notification(
                        title="Reminder Created",
                        message=f"New reminder: {title}",
                        notification_type="success"
                    )
                
                # Update AI context with new reminder data
                self._update_ai_reminders_context()
                
            else:
                print(f"❌ Reminders page not available or doesn't support AI reminders")
                self.logger.error("Reminders page not available for AI reminder creation")
                
                # Fallback: just save to notification manager
                if hasattr(self, 'notification_manager'):
                    self.notification_manager.add_notification(
                        title="Reminder Created",
                        message=f"New reminder: {reminder_data.get('title', 'Untitled')}",
                        notification_type="info"
                    )
                
        except Exception as e:
            print(f"❌ Error creating AI reminder: {e}")
            self.logger.error(f"Failed to create reminder: {e}")
            
            # Show error notification
            if hasattr(self, 'notification_manager'):
                self.notification_manager.add_notification(
                    title="Reminder Error",
                    message=f"Failed to create reminder: {str(e)}",
                    notification_type="error"
                )
    
    def _handle_ai_action(self, action_type: str, results: dict):
        """Handle various AI-executed actions"""
        self.logger.info(f"AI action executed: {action_type} -> {results}")
        
        # Handle different action types
        if action_type == "data_export":
            self._handle_data_export(results)
        elif action_type == "filter_applied":
            self._handle_filter_application(results)
        elif action_type == "calculation_performed":
            self._handle_calculation_results(results)
        # Add more action handlers as needed
    
    def _handle_ai_context_update(self, context_data: dict):
        """Handle AI context updates to keep the assistant informed"""
        self.logger.debug(f"AI context updated: {context_data}")
        # Context updates are primarily for AI awareness, minimal UI action needed
    
    def _update_ai_context_for_navigation(self, target_page: str, parameters: dict):
        """Update AI context before navigation to help with parameter application"""
        # AI context updates now handled by SimpleAIStatusBar
        pass
    
    def _update_ai_page_context(self, page_name: str):
        """Update AI context with current page state and available data"""
        # AI context updates now handled by SimpleAIStatusBar
        pass
    
    def _update_ai_reminders_context(self):
        """Update AI context with current reminders data"""
        # AI context updates now handled by SimpleAIStatusBar
        pass
    
    def _apply_navigation_parameters(self, page_name: str, parameters: dict):
        """Apply AI-provided parameters to the target page"""
        if not parameters:
            return
        
        current_widget = self.stack.currentWidget()
        
        try:
            # Handle common parameters
            if 'date_range' in parameters:
                date_range = parameters['date_range']
                if hasattr(current_widget, 'set_date_range'):
                    current_widget.set_date_range(date_range.get('start'), date_range.get('end'))
            
            if 'filters' in parameters:
                filters = parameters['filters']
                if hasattr(current_widget, 'apply_filters'):
                    current_widget.apply_filters(filters)
            
            if 'account_filter' in parameters:
                account = parameters['account_filter']
                if hasattr(current_widget, 'filter_by_account'):
                    current_widget.filter_by_account(account)
            
            # Add more parameter handling as needed
            self.logger.info(f"Applied parameters to {page_name}: {parameters}")
            
        except Exception as e:
            self.logger.warning(f"Could not apply parameters to {page_name}: {e}")
    
    def _handle_data_export(self, results: dict):
        """Handle data export actions initiated by AI"""
        # Placeholder for data export handling
        self.logger.info(f"Data export requested: {results}")
    
    def _handle_filter_application(self, results: dict):
        """Handle filter application actions initiated by AI"""
        # Placeholder for filter handling
       
        self.logger.info(f"Filters applied: {results}")
    
    def _handle_calculation_results(self, results: dict):
        """Handle calculation results from AI"""
        # Placeholder for calculation results handling
        self.logger.info(f"Calculation results: {results}")

    # AI context initialization removed - now handled by SimpleAIStatusBar
    
    def _gather_current_accounting_data(self):
        """Gather current accounting data for AI context"""
        try:
            accounting_data = {}
            
            # Get basic account information
            if hasattr(self.accounting_system, 'get_accounts'):
                try:
                    accounts = self.accounting_system.get_accounts()
                    accounting_data['total_accounts'] = len(accounts) if accounts else 0
                    accounting_data['account_types'] = list(set([acc.get('type', 'Unknown') for acc in accounts[:10]]))  # Sample of types
                except Exception as e:
                    self.logger.warning(f"Could not fetch accounts: {e}")
            
            # Get recent transactions (last 10)
            if hasattr(self.accounting_system, 'get_journal_entries'):
                try:
                    recent_entries = self.accounting_system.get_journal_entries(limit=10)
                    accounting_data['recent_transactions_count'] = len(recent_entries) if recent_entries else 0
                    if recent_entries:
                        accounting_data['latest_transaction_date'] = recent_entries[0].get('date', 'Unknown')
                except Exception as e:
                    self.logger.warning(f"Could not fetch recent transactions: {e}")
            
            # Get account balances summary
            if hasattr(self.accounting_system, 'get_trial_balance'):
                try:
                    trial_balance = self.accounting_system.get_trial_balance()
                    if trial_balance:
                        total_debits = sum([acc.get('debit', 0) for acc in trial_balance])
                        total_credits = sum([acc.get('credit', 0) for acc in trial_balance])
                        accounting_data['trial_balance_summary'] = {
                            'total_debits': total_debits,
                            'total_credits': total_credits,
                            'in_balance': abs(total_debits - total_credits) < 0.01
                        }
                except Exception as e:
                    self.logger.warning(f"Could not fetch trial balance: {e}")
            
            return accounting_data
            
        except Exception as e:
            self.logger.error(f"Error gathering accounting data: {e}")
            return {}
    
    # AI data update removed - now handled by SimpleAIStatusBar

    # AI Report Integration Helper Methods
    def _trigger_income_statement(self, start_date: str, end_date: str):
        """Trigger Income Statement view within Reports page"""
        try:
            reports_page = self.stack.currentWidget()
            if hasattr(reports_page, '_handle_statement_click'):
                print(f"🎯 Triggering Income Statement with dates: {start_date} to {end_date}")
                # Set date range first if possible
                if hasattr(reports_page, 'date_selector') and start_date and end_date:
                    from PyQt6.QtCore import QDate
                    start_qdate = QDate.fromString(start_date, "yyyy-MM-dd")
                    end_qdate = QDate.fromString(end_date, "yyyy-MM-dd")
                    if start_qdate.isValid() and end_qdate.isValid():
                        reports_page.date_selector.set_date_range(start_qdate, end_qdate)
                
                # Trigger Income Statement
                reports_page._handle_statement_click("Income Statement")
                print(f"✅ Successfully triggered Income Statement")
            else:
                print(f"❌ Reports page doesn't support statement clicks")
        except Exception as e:
            print(f"❌ Error triggering Income Statement: {e}")
            self.logger.error(f"Failed to trigger Income Statement: {e}")

    def _trigger_balance_sheet(self, end_date: str):
        """Trigger Balance Sheet view within Reports page"""
        try:
            reports_page = self.stack.currentWidget()
            if hasattr(reports_page, '_handle_statement_click'):
                print(f"🎯 Triggering Balance Sheet as of: {end_date}")
                # Set date range first if possible
                if hasattr(reports_page, 'date_selector') and end_date:
                    from PyQt6.QtCore import QDate
                    end_qdate = QDate.fromString(end_date, "yyyy-MM-dd")
                    if end_qdate.isValid():
                        # For balance sheet, set both dates to the same (as of date)
                        reports_page.date_selector.set_date_range(end_qdate, end_qdate)
                
                # Trigger Balance Sheet
                reports_page._handle_statement_click("Balance Sheet")
                print(f"✅ Successfully triggered Balance Sheet")
            else:
                print(f"❌ Reports page doesn't support statement clicks")
        except Exception as e:
            print(f"❌ Error triggering Balance Sheet: {e}")
            self.logger.error(f"Failed to trigger Balance Sheet: {e}")

    def _trigger_cash_flow(self, start_date: str, end_date: str):
        """Trigger Cash Flow Statement view within Reports page"""
        try:
            reports_page = self.stack.currentWidget()
            if hasattr(reports_page, '_handle_statement_click'):
                print(f"🎯 Triggering Cash Flow Statement with dates: {start_date} to {end_date}")
                # Set date range first if possible
                if hasattr(reports_page, 'date_selector') and start_date and end_date:
                    from PyQt6.QtCore import QDate
                    start_qdate = QDate.fromString(start_date, "yyyy-MM-dd")
                    end_qdate = QDate.fromString(end_date, "yyyy-MM-dd")
                    if start_qdate.isValid() and end_qdate.isValid():
                        reports_page.date_selector.set_date_range(start_qdate, end_qdate)
                
                # Trigger Cash Flow Statement
                reports_page._handle_statement_click("Cash Flow Statement")
                print(f"✅ Successfully triggered Cash Flow Statement")
            else:
                print(f"❌ Reports page doesn't support statement clicks")
        except Exception as e:
            print(f"❌ Error triggering Cash Flow Statement: {e}")
            self.logger.error(f"Failed to trigger Cash Flow Statement: {e}")

    def _show_reports_help(self, report_type: str):
        """Show helpful information about available reports"""
        try:
            from PyQt6.QtWidgets import QMessageBox
            
            # Create a helpful message about the reports available
            available_reports = [
                "• Trial Balance - Navigate to Trial Balance page",
                "• General Ledger - Navigate to Ledger page", 
                "• Income Statement - Available in Reports page",
                "• Balance Sheet - Available in Reports page",
                "• Cash Flow Statement - Available in Reports page",
                "• Financial Ratios - Available in Reports page",
                "• Budget Analysis - Available in Reports page"
            ]
            
            message = f"🤖 AI Assistant - Report Generation\n\n"
            message += f"I've navigated you to the Reports page. Here are the available reports:\n\n"
            message += "\n".join(available_reports)
            message += f"\n\nYou can click on any report card to generate it, or use the date selector to set a specific time period."
            
            if report_type not in ['trial_balance', 'ledger', 'income_statement', 'balance_sheet', 'cash_flow']:
                message += f"\n\nNote: '{report_type.replace('_', ' ').title()}' isn't directly available, but you can find similar reports above."
            
            QMessageBox.information(
                self,
                "AI Assistant - Reports Guide",
                message,
                QMessageBox.StandardButton.Ok
            )
            
        except Exception as e:
            print(f"❌ Error showing reports help: {e}")
            self.logger.error(f"Failed to show reports help: {e}")

    def _create_bottom_bar(self, main_layout):
        """Create the bottom bar with workspace switcher and status info"""
        try:
            from .components.bottom_bar import BottomBar
            
            # Create bottom bar with auth context if available
            self.bottom_bar = BottomBar(
                auth_manager=self.auth_manager,
                session_manager=self.session_manager,
                parent=self
            )
            
            # Add the bottom bar to the main layout
            main_layout.addWidget(self.bottom_bar)
            
            # Connect workspace switcher signal if available
            if hasattr(self.bottom_bar, 'workspace_switcher'):
                self.bottom_bar.workspace_switcher.workspace_changed.connect(self._on_workspace_changed)
            
            self.logger.debug("Bottom bar created successfully")
            
        except Exception as e:
            self.logger.error(f"Error creating bottom bar: {e}")
            # Fallback to spacer if bottom bar creation fails
            bottom_spacer = QFrame()
            bottom_spacer.setObjectName("BottomSpacer")
            bottom_spacer.setFixedHeight(5)
            bottom_spacer.setStyleSheet("""
                QFrame#BottomSpacer {
                    background: rgba(0, 0, 0, 0.01);
                    border: none;
                }
            """)
            main_layout.addWidget(bottom_spacer)

    def _initial_connection_check(self):
        """Perform initial connection check when UI is ready"""
        try:
            if hasattr(self, 'connection_indicator'):
                # Start with a basic internet connectivity test
                is_online = self._test_internet_connectivity()
                self.connection_indicator.update_connection_status(is_online)
                self.logger.debug(f"Initial connection check: online={is_online}")
        except Exception as e:
            self.logger.error(f"Initial connection check failed: {e}")
            if hasattr(self, 'connection_indicator'):
                self.connection_indicator.update_connection_status(False)
    
    def _on_workspace_changed(self, organization_id: str, organization_name: str):
        """Handle workspace/organization change with optimized loading"""
        try:
            self.logger.info(f"🚀 Starting optimized workspace switch to: {organization_name}")
            
            # PHASE 0: FREEZE UI IMMEDIATELY - Prevent user interaction during switch
            self._freeze_ui_during_switch()
            
            # PHASE 1: IMMEDIATE UI UPDATES (Optimistic) - Non-blocking
            self._perform_immediate_ui_updates(organization_id, organization_name)
            
            # PHASE 2: BACKGROUND DATA LOADING - Asynchronous
            QTimer.singleShot(0, lambda: self._start_background_data_loading(organization_id, organization_name))
            
        except Exception as e:
            self.logger.error(f"Error in optimized workspace switch: {e}")
            self._handle_workspace_switch_error(e)
    
    def _perform_immediate_ui_updates(self, organization_id: str, organization_name: str):
        """Perform immediate UI updates that don't require data loading"""
        try:
            # Show progress popup immediately to indicate switching is in progress
            from .components.workspace_switching_progress import WorkspaceSwitchingProgress
            self.progress_popup = WorkspaceSwitchingProgress(self)
            self.progress_popup.show_progress(self)
            self.progress_popup.update_status("Switching workspace...", 25)
            
            # Update window title immediately
            base_title = "Modern Accounting"
            self.setWindowTitle(f"{base_title} - {organization_name}")
            
            # Update workspace switcher immediately
            if hasattr(self, 'bottom_bar') and hasattr(self.bottom_bar, 'workspace_switcher'):
                self.bottom_bar.workspace_switcher.set_current_workspace(organization_id)
            
            # Update session manager context asynchronously
            if hasattr(self, 'session_manager') and self.session_manager:
                QTimer.singleShot(0, lambda: self.session_manager.set_active_organization(organization_id))
            
            # Invalidate RPC cache for the new organization
            from src.core.rpc_cache_manager import rpc_cache
            rpc_cache.invalidate_org_cache(organization_id)
            
            # Update accounting system context asynchronously
            if hasattr(self, 'accounting_system') and self.accounting_system:
                QTimer.singleShot(0, lambda: self.accounting_system.set_organization(organization_id))
            
            # Update navigation visibility asynchronously to avoid blocking
            QTimer.singleShot(0, self._update_navigation_visibility)
            
            # Update progress to show immediate updates are complete
            if hasattr(self, 'progress_popup'):
                self.progress_popup.update_status("Loading data...", 50)
            
            # NOTE: UI remains frozen - will be unfrozen after background loading completes
            self.logger.info(f"✅ Immediate UI updates completed for {organization_name}")
            
        except Exception as e:
            self.logger.error(f"Error in immediate UI updates: {e}")
            raise
    
    def _start_background_data_loading(self, organization_id: str, organization_name: str):
        """Start background data loading using PageManager"""
        try:
            # Use PageManager for optimized data loading
            def on_loading_complete():
                """Callback when background loading is complete"""
                try:
                    # Update progress popup
                    if hasattr(self, 'progress_popup'):
                        self.progress_popup.update_status("Workspace switch complete!", 100)
                        QTimer.singleShot(500, self.progress_popup.hide_progress)
                    
                    # Refresh current page with new data
                    self._refresh_current_page_with_cached_data(organization_id)
                    
                    # UNFREEZE UI - Now that all data loading is complete
                    self._unfreeze_ui_after_switch()
                    
                    self.logger.info(f"✅ Background data loading completed for {organization_name}")
                    
                except Exception as e:
                    self.logger.error(f"Error in loading completion callback: {e}")
                    # Ensure UI is unfrozen even if there's an error
                    self._unfreeze_ui_after_switch()
            
            # Ensure all pages are loaded for the new workspace
            self.page_manager.ensure_all_pages_loaded(organization_id)
            
            # Start optimized workspace switching
            self.page_manager.switch_workspace(organization_id, organization_name, on_loading_complete)
            
            # Update progress to show background loading
            if hasattr(self, 'progress_popup'):
                self.progress_popup.update_status("Loading data in background...", 75)
            
        except Exception as e:
            self.logger.error(f"Error starting background data loading: {e}")
            # Ensure UI is unfrozen even if there's an error
            self._unfreeze_ui_after_switch()
            raise
    
    def _refresh_current_page_with_cached_data(self, organization_id: str):
        """Refresh all pages with cached data after workspace switch"""
        try:
            if hasattr(self, 'stack'):
                total_pages = self.stack.count()
                self.logger.info(f"🔄 Refreshing all {total_pages} pages with new workspace data")
                
                # Refresh pages asynchronously to avoid blocking UI
                def refresh_pages():
                    for i in range(total_pages):
                        page = self.stack.widget(i)
                        if page and hasattr(page, 'refresh_data'):
                            page_name = type(page).__name__
                            self.logger.debug(f"🔄 Refreshing page {i+1}/{total_pages}: {page_name}")
                            
                            try:
                                # Get cached data for this page
                                cached_data = self.page_manager.get_page_data(page_name, organization_id)
                                
                                if cached_data and cached_data.get('status') == 'loaded':
                                    # Update page with cached data if available
                                    if hasattr(page, 'update_with_cached_data'):
                                        page.update_with_cached_data(cached_data)
                                    else:
                                        # Fallback to regular refresh
                                        page.refresh_data()
                                else:
                                    # No cached data, use regular refresh
                                    page.refresh_data()
                                    
                            except Exception as e:
                                self.logger.error(f"❌ Error refreshing page {page_name}: {e}")
                                # Still try to refresh with regular method
                                try:
                                    page.refresh_data()
                                except Exception as fallback_error:
                                    self.logger.error(f"❌ Fallback refresh also failed for {page_name}: {fallback_error}")
                    
                    self.logger.info(f"✅ All pages refreshed for workspace {organization_id}")
                
                # Use QTimer to defer page refresh to next event loop cycle
                QTimer.singleShot(0, refresh_pages)
                    
        except Exception as e:
            self.logger.error(f"Error refreshing pages: {e}")
    
    def _handle_workspace_switch_error(self, error: Exception):
        """Handle workspace switching errors"""
        try:
            # Ensure UI is unfrozen immediately
            self._unfreeze_ui_after_switch()
            
            # Update progress popup with error
            if hasattr(self, 'progress_popup'):
                self.progress_popup.update_status("Error occurred during switch", 100)
                QTimer.singleShot(1000, self.progress_popup.hide_progress)
            
            # Log error
            import traceback
            traceback.print_exc()
            
            # Show error notification to user
            self.add_notification(
                "Workspace Switch Error", 
                f"Failed to switch workspace: {str(error)}", 
                "error"
            )
            
        except Exception as e:
            self.logger.error(f"Error handling workspace switch error: {e}")
            # Final fallback - ensure UI is enabled
            try:
                self.setEnabled(True)
                self.setCursor(Qt.CursorShape.ArrowCursor)
            except:
                pass
    
    def _get_current_page_name(self) -> str:
        """Get current page name for PageManager"""
        try:
            if hasattr(self, 'stack'):
                current_page = self.stack.currentWidget()
                if current_page:
                    return type(current_page).__name__
            return "DashboardPage"  # Default
        except Exception as e:
            self.logger.error(f"Error getting current page name: {e}")
            return "DashboardPage"
    
    def refresh_workspace_switcher(self):
        """Refresh the workspace switcher with current organizations"""
        try:
            if hasattr(self, 'bottom_bar') and hasattr(self.bottom_bar, 'refresh_workspace_info'):
                self.bottom_bar.refresh_workspace_info()
                self.logger.debug("Workspace switcher refreshed")
        except Exception as e:
            self.logger.error(f"Error refreshing workspace switcher: {e}")
    
    def _freeze_ui_during_switch(self):
        """Freeze UI during workspace switch to prevent glitches and improve performance"""
        try:
            # Disable main window interactions
            self.setEnabled(False)
            
            # Disable sidebar to prevent navigation during switch
            if hasattr(self, 'sidebar'):
                self.sidebar.setEnabled(False)
            
            # Disable content area to prevent page interactions
            if hasattr(self, 'stack'):
                self.stack.setEnabled(False)
            
            # Disable bottom bar to prevent workspace switcher interactions
            if hasattr(self, 'bottom_bar'):
                self.bottom_bar.setEnabled(False)
            
            # Show loading indicator if available
            if hasattr(self, 'connection_indicator'):
                self.connection_indicator.show_loading_state("Switching workspace...")
            
            # Disable workspace switcher specifically to prevent rapid switching
            if hasattr(self, 'bottom_bar') and hasattr(self.bottom_bar, 'workspace_switcher'):
                self.bottom_bar.workspace_switcher.setEnabled(False)
            
            # Disable title bar buttons to prevent window operations during switch
            if hasattr(self, 'title_bar'):
                self.title_bar.setEnabled(False)
            
            # Set cursor to wait cursor to indicate processing
            self.setCursor(Qt.CursorShape.WaitCursor)
            
            self.logger.info("🔒 UI frozen during workspace switch")
            
        except Exception as e:
            self.logger.error(f"Error freezing UI: {e}")
    
    def _unfreeze_ui_after_switch(self):
        """Unfreeze UI after workspace switch is complete"""
        try:
            # Re-enable main window interactions
            self.setEnabled(True)
            
            # Re-enable sidebar
            if hasattr(self, 'sidebar'):
                self.sidebar.setEnabled(True)
            
            # Re-enable content area
            if hasattr(self, 'stack'):
                self.stack.setEnabled(True)
            
            # Re-enable bottom bar
            if hasattr(self, 'bottom_bar'):
                self.bottom_bar.setEnabled(True)
            
            # Hide loading indicator if available
            if hasattr(self, 'connection_indicator'):
                self.connection_indicator.hide_loading_state()
            
            # Re-enable workspace switcher specifically
            if hasattr(self, 'bottom_bar') and hasattr(self.bottom_bar, 'workspace_switcher'):
                self.bottom_bar.workspace_switcher.setEnabled(True)
            
            # Re-enable title bar buttons
            if hasattr(self, 'title_bar'):
                self.title_bar.setEnabled(True)
            
            # Restore normal cursor
            self.setCursor(Qt.CursorShape.ArrowCursor)
            
            self.logger.info("🔓 UI unfrozen after workspace switch")
            
        except Exception as e:
            self.logger.error(f"Error unfreezing UI: {e}")

    def _refresh_mica_after_move(self):
        """Refresh Mica effect after window move (especially for monitor switching)."""
        if self.mica_applied and self.isVisible():
            try:
                # Force a complete refresh for monitor switching
                MicaEffect.refresh_mica(self, self.dark_mode)
                self.update()
                self.repaint()
                QApplication.processEvents()
                print("✅ Mica effect refreshed after window move")
            except Exception as e:
                print(f"⚠️  Error refreshing Mica after move: {e}")
    
    def _handle_monitor_switch(self):
        """Handle monitor switching specifically - this is what fixes the Mica issue."""
        if self.mica_applied and self.isVisible():
            try:
                print("🔄 Detected monitor switch, applying special Mica refresh...")
                
                # Force window to redraw completely
                self.hide()
                QApplication.processEvents()
                self.show()
                QApplication.processEvents()
                
                # Reapply Mica effect after window is shown again
                QTimer.singleShot(100, self._reapply_mica_after_monitor_switch)
                
            except Exception as e:
                print(f"⚠️  Error handling monitor switch: {e}")
    
    def _reapply_mica_after_monitor_switch(self):
        """Reapply Mica effect after monitor switch."""
        if self.mica_applied and self.isVisible():
            try:
                # Reapply window attributes
                self._prepare_window_for_mica()
                
                # Reapply Mica effect
                success = MicaEffect.apply_mica(self, self.dark_mode)
                if success:
                    # Reapply Mica stylesheet
                    mica_style = MicaEffect.get_mica_stylesheet(self.dark_mode)
                    self.setStyleSheet(mica_style)
                    
                    # Force complete refresh
                    self.update()
                    self.repaint()
                    QApplication.processEvents()
                    
                    print("✅ Mica effect reapplied after monitor switch")
                else:
                    print("❌ Failed to reapply Mica after monitor switch")
                    
            except Exception as e:
                print(f"⚠️  Error reapplying Mica after monitor switch: {e}")
    
    def force_mica_refresh(self):
        """Force a complete Mica refresh for debugging purposes"""
        if MicaEffect.is_windows11():
            try:
                print("🔄 Force refreshing Mica effect...")
                
                # Reapply window attributes to ensure they're set correctly
                self._prepare_window_for_mica()
                
                # Force a complete refresh
                MicaEffect.refresh_mica(self, self.dark_mode)
                self.update()
                self.repaint()
                QApplication.processEvents()
                
                # Additional refresh after a short delay
                QTimer.singleShot(50, lambda: self._final_mica_refresh())
                
                print("✅ Mica effect force refreshed")
                return True
            except Exception as e:
                print(f"❌ Error force refreshing Mica: {e}")
                self.logger.error(f"Failed to force Mica refresh: {e}")
                return False
        else:
            print("⚠️  Windows 11 not detected, cannot refresh Mica")
            return False


