from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget, QFrame, QPushButton, QLabel, QSizePolicy, QApplication, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt, QSize, QTimer, QEvent
from PyQt6.QtGui import QIcon, QPalette, QColor

# Import PostgreSQL accounting system
from ..core.accounting_system_postgresql import AccountingSystemPostgreSQL as AccountingSystem

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
from .components.ai_command_processor import AICommandProcessor

# Import the frameless window mixin for complete window management
from .components.frameless_window_mixin import FramelessWindowMixin

# Import the border solution for Mica windows
from .components.mica_border_solution import MicaWindowWithBorders

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
                border: none;            }}        """)

class MainWindow(QMainWindow, MicaWindowWithBorders):
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
        
        # Initialize session tracking
        self.start_time = datetime.now()
        
        # Use single database file in project root
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'accounting.db')        # Initialize accounting system with PostgreSQL or SQLite fallback
        self.accounting_system = self._initialize_accounting_system(db_path)        
        # Keep backward compatibility for existing pages
        self.system = self.accounting_system
        
        # Initialize notification system
        from .components.notifications.notification_manager import NotificationManager
        self.notification_manager = NotificationManager()
        
        # Initialize AI command processor
        from .components.ai_command_processor import AICommandProcessor
        self.ai_processor = AICommandProcessor(self)
        
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
        self._load_pages()        # Setup resize borders after UI is created
        from .components.seamless_border_layout import apply_seamless_borders
        apply_seamless_borders(self)
        
        # Connect AI processor signals after UI is created
        self._connect_ai_signals()
        
        # Apply global styling first
        self._apply_global_consistent_styling()
        
        # Apply font settings to the application
        self._apply_font_settings()
        
        # Setup sync status updates if in hybrid mode
        if self.db_mode == 'hybrid':
            self._setup_sync_updates()
          # Install event filter for handling clicks outside notification drawer        self.installEventFilter(self)
        
        # Use QTimer to apply Mica effect after window is fully shown
        QTimer.singleShot(100, self._apply_mica_effect_delayed)
        
        # Add a welcome notification after startup
        QTimer.singleShot(2000, self._add_welcome_notification)
        
    def closeEvent(self, event):
        """Handle window close event."""
        # Clean up AI processor thread
        if self.ai_processor and self.ai_processor.processing_thread:
            self.ai_processor.stop_processing()
        
        # Clean up any other resources
        self.accounting_system.close()
        
        super().closeEvent(event)

    def _connect_ai_signals(self):
        """Connect signals from the AI processor to the main window slots."""
        self.ai_processor.response_ready.connect(self.simple_ai_bar.set_ai_response)
        self.ai_processor.error_occurred.connect(self.simple_ai_bar.set_error_message)
        self.ai_processor.processing_started.connect(self.simple_ai_bar.show_processing_indicator)
        self.ai_processor.processing_finished.connect(self.simple_ai_bar.hide_processing_indicator)
        
        # Connect command execution signals
        self.ai_processor.navigation_requested.connect(self.navigate_to_page)
        # self.ai_processor.report_requested.connect(self.generate_report) # Placeholder
        # self.ai_processor.reminder_created.connect(self.add_reminder) # Placeholder
        
        # Connect the AI bar's command submission to the processor
        if hasattr(self, 'simple_ai_bar'):
            self.simple_ai_bar.ai_command_submitted.connect(self.ai_processor.process_command)

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
                    color: black;                }                QFrame {
                    background-color: #ffffff;
                    border: 1px solid #d0d0d0;                }
            """
    
    def _setup_ui(self):
        """Setup the main UI components."""        # Main container with custom title bar and proper background for mouse events
        self.main_container = QWidget()  # Store reference for notification drawer
        self.main_container.setStyleSheet("""
            QWidget {
                background: rgba(0, 0, 0, 0.05);
            }
        """)
        main_layout = QVBoxLayout(self.main_container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
          # Custom title bar (now includes AI status bar)
        self.title_bar = self._create_title_bar()
        main_layout.addWidget(self.title_bar)        # Content area - NO MARGINS to touch borders, proper background for mouse events
        self.content_widget = QWidget()  # Store reference for notification drawer
        self.content_widget.setStyleSheet("""
            QWidget {
                background: rgba(0, 0, 0, 0.05);
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
        icon_label.setPixmap(QIcon(os.path.join("assets", "icons", "dashboard_new.svg")).pixmap(20, 20))
        left_layout.addWidget(icon_label)
        
        title_label = QLabel("AI Accountant")
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
        
        # Add compact sync button
        from .components.compact_sync_button import CompactSyncButton
        self.sync_button = CompactSyncButton()
        self.sync_button.sync_requested.connect(self._manual_sync)
        right_layout.addWidget(self.sync_button)
        
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
            from .components.simple_ai_status_bar import SimpleAIStatusBar            # Create a container that will hold the AI status bar
            container = QFrame()
            container.setObjectName("AIStatusContainer")
            container.setMaximumHeight(40)  # Match title bar height for proper alignment
            container.setMinimumHeight(40)  # Ensure consistent height
            
            layout = QHBoxLayout(container)
            layout.setContentsMargins(20, 0, 20, 0)  # Add horizontal margins for better centering
            layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
              # Create the simple AI status bar
            self.simple_ai_bar = SimpleAIStatusBar(self)
            self.simple_ai_bar.setMaximumHeight(30)  # AI bar height            self.simple_ai_bar.setMinimumHeight(30)  # Ensure consistent height
            layout.addWidget(self.simple_ai_bar)
            
            return container
            
        except Exception as e:
            print(f"Error creating simple AI status bar: {e}")            # Return placeholder
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
        """Update AI context when page changes"""        # Update simple AI status bar with new context
        if hasattr(self, 'simple_ai_bar'):
            try:
                self._update_ai_status()
            except Exception as e:
                print(f"Error updating AI context: {e}")
    
    def _on_page_changed(self, index: int):
        """Handle page changes and update AI context"""
        self.stack.setCurrentIndex(index)
        self._update_ai_context()
        
        # Update which sidebar button is checked
        for i, btn in enumerate(self.sidebar_buttons):
            btn.setChecked(i == index)
        
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
        self._style_toggle_button()        # Add toggle button directly to main layout to maintain alignment
        layout.addWidget(self.toggle_btn)# Navigation buttons with modern icons - expanded for multi-org support + period closing
        nav_items = [
            ("Dashboard", os.path.join("assets", "icons", "dashboard_new.svg")),
            ("Journal", os.path.join("assets", "icons", "journal_new.svg")),
            ("Ledger", os.path.join("assets", "icons", "ledger_new.svg")),
            ("Trial Balance", os.path.join("assets", "icons", "trial_balance_new.svg")),
            ("Reports", os.path.join("assets", "icons", "reports_new.svg")),
            ("Accounts", os.path.join("assets", "icons", "accounts_new.svg")),
            ("Reminders", os.path.join("assets", "icons", "ledger_note.svg")),  # Reminders & Tasks
            ("Period Closing", os.path.join("assets", "icons", "period_closing_modern.svg")),  # Period closing & audit
            ("Team", os.path.join("assets", "icons", "team_new.svg")),  # Team management
            ("Org Settings", os.path.join("assets", "icons", "org_settings_new.svg")),  # Organization settings
            ("User Mgmt", os.path.join("assets", "icons", "user_mgmt_new.svg")),  # User management (admin only)
            ("Platform", os.path.join("assets", "icons", "platform_new.svg")),  # Platform overview (super admin)
            ("Global Orgs", os.path.join("assets", "icons", "global_orgs_new.svg")),  # Global organizations (super admin)
            ("Settings", os.path.join("assets", "icons", "settings_new.svg")),
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
        
        # Settings page (always visible)
        settings_pages = [SettingsPage]          # Add all pages to stack with proper initialization
        all_pages = standard_pages + org_pages + admin_pages + super_admin_pages + settings_pages
        for idx, PageClass in enumerate(all_pages):
            if PageClass in [TeamManagementPage, OrganizationSettingsPage, UserManagementPage, 
                           PlatformOverviewPage, GlobalOrganizationsPage]:
                # Pass auth_manager and session_manager for organization/user management pages
                page = PageClass(self.system, auth_manager=self.auth_manager, parent=self)
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
                
    def _set_window_control_icons(self, minimize_btn, maximize_btn, close_btn, sync_btn=None):
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
            
            # Load sync icon and create white version for dark theme
            if sync_btn:
                from PyQt6.QtGui import QPainter, QPixmap
                sync_icon = QIcon("assets/icons/sync.svg")
                
                # Create a white version of the sync icon for dark theme
                if not sync_icon.isNull():
                    # Get the original pixmap
                    original_pixmap = sync_icon.pixmap(QSize(16, 16))
                    
                    # Create a white version
                    white_pixmap = QPixmap(16, 16)
                    white_pixmap.fill(Qt.GlobalColor.transparent)
                    
                    painter = QPainter(white_pixmap)
                    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
                    
                    # Draw the original as a mask and fill with white
                    painter.drawPixmap(0, 0, original_pixmap)
                    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
                    painter.fillRect(white_pixmap.rect(), Qt.GlobalColor.white)
                    painter.end()
                    
                    # Create new icon with white pixmap
                    sync_icon = QIcon(white_pixmap)
            else:
                sync_icon = None
            
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
                close_btn.setText("×")            # Handle sync button icon
            if sync_btn:
                if sync_icon and not sync_icon.isNull():
                    sync_btn.setIcon(sync_icon)
                    sync_btn.setIconSize(QSize(16, 16))
                    sync_btn.setText("")  # Clear text when icon is set
                else:
                    sync_btn.setText("↻")  # Sync/refresh symbol
                
        except Exception as e:
            print(f"Failed to load window control icons: {e}")
            # Fallback to Unicode symbols
            minimize_btn.setText("─")
            maximize_btn.setText("□")
            close_btn.setText("×")
            if sync_btn:
                sync_btn.setText("↻")
                  # Apply the styling
        minimize_btn.setStyleSheet(window_control_style)
        maximize_btn.setStyleSheet(window_control_style)
        close_btn.setStyleSheet(window_control_style)
        if sync_btn:
            sync_btn.setStyleSheet(window_control_style)
        
    def keyPressEvent(self, event):
        """Handle keyboard shortcuts."""
        super().keyPressEvent(event)
          # F5: Force refresh Mica effect (for testing/debugging)
        if event.key() == Qt.Key.Key_F5:
            print("🔄 Manual Mica refresh triggered (F5)")
            if self.mica_applied:
                MicaEffect.refresh_mica(self, self.dark_mode)
                self.update()
            else:                self._apply_mica_effect_delayed()
                
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
                    page._apply_styling()        # Force a style refresh
        self.style().unpolish(self)
        self.style().polish(self)
    
    def _initialize_accounting_system(self, db_path):
        """Initialize PostgreSQL accounting system with enhanced features and multi-tenant context."""
        try:
            self.logger.info(f"Initializing enhanced accounting system in {self.db_mode} mode...")
            
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
                base_system = AccountingSystem(
                    organization_id=organization_id,
                    user_id=user_id
                )
                base_system.db_manager = db_manager
                self.logger.info(f"✅ Hybrid multi-tenant accounting system initialized for org: {organization_id}")
            else:
                # Use standard PostgreSQL system with multi-tenant context
                base_system = AccountingSystem(
                    organization_id=organization_id,
                    user_id=user_id
                )
                self.logger.info(f"✅ PostgreSQL multi-tenant accounting system initialized for org: {organization_id}")
            
            # Initialize enhanced accounting system with advanced features
            from ..core.enhanced_accounting_system import EnhancedAccountingSystem
            enhanced_system = EnhancedAccountingSystem(
                db_manager=base_system.db_manager if hasattr(base_system, 'db_manager') else None,
                base_accounting_system=base_system,
                organization_id=organization_id,
                user_id=user_id
            )
            
            # Initialize enhanced features
            try:
                init_results = enhanced_system.initialize_enhanced_features()
                self.logger.info(f"Enhanced features initialization results: {init_results}")
                
                # Store the enhanced system as the main system
                enhanced_system.base_system = base_system  # Keep reference to base system
                return enhanced_system
                
            except Exception as e:
                self.logger.warning(f"Enhanced features initialization failed, using base system: {e}")
                return base_system
                
        except Exception as e:
            self.logger.error(f"Accounting system initialization failed: {e}")
            raise Exception(f"Failed to initialize accounting database: {e}")
    
    def _setup_sync_updates(self):
        """Setup periodic sync status updates."""
        self.sync_timer = QTimer()
        self.sync_timer.timeout.connect(self._update_sync_status)
        self.sync_timer.start(5000)  # Update every 5 seconds        # Initial status update
        self._update_sync_status()
    
    def _update_sync_status(self):
        """Update sync status from database manager."""
        if hasattr(self, 'sync_button') and hasattr(self.accounting_system, 'db_manager'):
            try:
                status = self.accounting_system.db_manager.get_connection_status()
                self.sync_button.update_connection_status(status)
                  # Check for sync status changes and notify
                sync_status = status.get('sync_status', {})
                if sync_status.get('failed_operations', 0) > 0:
                    self.add_sync_notification(
                        "Sync Issues",
                        f"{sync_status['failed_operations']} operations failed to sync. Check your connection.",
                        "warning"
                    )
                elif sync_status.get('conflicts', 0) > 0:
                    self.notify_sync_conflict(sync_status['conflicts'])
                    
            except Exception as e:
                self.logger.error(f"Failed to update sync status: {e}")
                self.sync_button.show_error(f"Status update failed")
                  # Add notification for status update failure
                self.add_sync_notification(
                    "Sync Status Error",
                    "Failed to check synchronization status. Please check your connection.",
                    "error"
                )
                
    def _manual_sync(self):
        """Trigger manual synchronization."""
        if hasattr(self.accounting_system, 'db_manager'):
            try:
                self.logger.info("Manual sync requested...")
                
                # Notify that sync is starting
                self.notify_sync_started()
                
                # Trigger sync (this will be implemented in the sync manager)
                self.accounting_system.db_manager._perform_sync()
                
                # Show success in sync button
                if hasattr(self, 'sync_button'):
                    self.sync_button.show_success("Sync completed")
                
                # Notify sync completion
                self.notify_sync_completed()
                
            except Exception as e:
                self.logger.error(f"Manual sync failed: {e}")
                
                # Show error in sync button
                if hasattr(self, 'sync_button'):
                    self.sync_button.show_error(f"Sync failed")
                
                # Notify sync failure
                self.notify_sync_failed(str(e))

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
                "Welcome to AI Accountant!",
                "Your intelligent accounting companion is ready to help you manage your finances.",
                "info"
            )
        except Exception as e:
            print(f"Error adding welcome notification: {e}")
    
    def log_activity(self, message):
        """Log an activity to the sync button."""
        # Compact sync button doesn't log activities - it only shows status
        pass
            
    def show_sync_success(self, message):
        """Show a success message in the sync button."""
        if hasattr(self, 'sync_button'):
            self.sync_button.show_success(message)
            
    def show_sync_error(self, message):
        """Show an error message in the sync button.""" 
        if hasattr(self, 'sync_button'):
            self.sync_button.show_error(message)
    
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
    
    def _update_navigation_visibility(self):
        """Update sidebar navigation visibility based on user role."""
        if not self.session_manager or not hasattr(self, 'sidebar_buttons'):
            return
            
        # Define which buttons are visible for which roles
        user_role = self.session_manager.get_current_user_role()
        is_super_admin = self.session_manager.is_super_admin()
        can_manage_users = self.session_manager.can_manage_users()
        
        # Standard pages (always visible): Dashboard, Journal, Ledger, Trial Balance, Reports, Accounts
        always_visible = [0, 1, 2, 3, 4, 5]
        
        # Organization pages: Team (6), Org Settings (7) - visible to all org members
        org_visible = [6, 7] if self.session_manager.get_active_organization_id() else []
        
        # Admin pages: User Mgmt (8) - visible to admins and owners
        admin_visible = [8] if can_manage_users else []
        
        # Super admin pages: Platform (9), Global Orgs (10) - visible to super admins only
        super_admin_visible = [9, 10] if is_super_admin else []
        
        # Settings (11) - always visible
        settings_visible = [11]
        
        # Combine all visible indices
        visible_indices = always_visible + org_visible + admin_visible + super_admin_visible + settings_visible
        
        # Update button visibility
        for i, button in enumerate(self.sidebar_buttons):
            if i in visible_indices:
                button.show()
            else:
                button.hide()
    
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
    
    def _process_ai_command(self):
        """Process command from AI status bar"""
        if hasattr(self, 'simple_ai_bar') and hasattr(self, 'ai_processor'):
            user_input = self.simple_ai_bar.text().strip()
            if user_input and user_input != self.simple_ai_bar.placeholder_text:
                # Get current context
                context = self._get_current_context()                # Process the command
                self.ai_processor.process_command(user_input)
    
    def _handle_ai_response(self, response_text: str):
        """Handle AI response text"""
        # The status bar will handle displaying the response
        pass
    
    def _handle_ai_navigation(self, page: str, parameters: dict):
        """Handle AI navigation requests"""
        try:
            # Map page names to tab indices
            page_map = {
                'dashboard': 0,
                'journal': 1,
                'ledger': 2,
                'trial_balance': 3,
                'reports': 4,
                'accounts': 5,
                'reminders': 6,
                'team': 7,
                'settings': 8,
                'budget': 9
            }
            
            if page in page_map:
                tab_index = page_map[page]
                if hasattr(self, 'tab_widget'):
                    self.tab_widget.setCurrentIndex(tab_index)
                    # Apply any additional parameters if needed
                    if parameters:
                        self._apply_navigation_parameters(page, parameters)
            else:
                self.logger.warning(f"Unknown page for navigation: {page}")
                
        except Exception as e:
            self.logger.error(f"Navigation error: {e}")
    
    def _handle_ai_report(self, report_type: str, parameters: dict):
        """Handle AI report generation requests"""
        try:
            # Switch to reports tab first
            if hasattr(self, 'tab_widget'):
                self.tab_widget.setCurrentIndex(4)  # Reports tab
            
            # Generate the requested report
            if report_type == 'trial_balance':
                self._generate_trial_balance_report(parameters)
            elif report_type == 'balance_sheet':
                self._generate_balance_sheet_report(parameters)
            elif report_type == 'income_statement':
                self._generate_income_statement_report(parameters)
            elif report_type == 'cash_flow':
                self._generate_cash_flow_report(parameters)
            else:
                self.logger.warning(f"Unknown report type: {report_type}")
                
        except Exception as e:
            self.logger.error(f"Report generation error: {e}")
    
    def _handle_ai_reminder(self, reminder_data: dict):
        """Handle AI reminder creation"""
        try:
            # Use the existing reminder manager if available
            if hasattr(self, 'reminder_manager'):
                self.reminder_manager.add_reminder(reminder_data)
            else:
                # Fallback: save to reminders file
                self._save_reminder_to_file(reminder_data)
                
        except Exception as e:
            self.logger.error(f"Reminder creation error: {e}")
    
    def _apply_navigation_parameters(self, page: str, parameters: dict):
        """Apply additional parameters for navigation"""
        # Handle date ranges, filters, etc. based on the page
        if page == 'journal' and 'date_from' in parameters:
            # Apply date filter to journal view
            pass
        elif page == 'accounts' and 'account_type' in parameters:
            # Filter accounts by type
            pass
    
    def _generate_trial_balance_report(self, parameters: dict):
        """Generate trial balance report with parameters"""
        # Implement trial balance generation
        pass
    
    def _generate_balance_sheet_report(self, parameters: dict):
        """Generate balance sheet report with parameters"""
        # Implement balance sheet generation
        pass
    
    def _generate_income_statement_report(self, parameters: dict):
        """Generate income statement report with parameters"""
        # Implement income statement generation
        pass
    
    def _generate_cash_flow_report(self, parameters: dict):
        """Generate cash flow report with parameters"""
        # Implement cash flow generation
        pass
    
    def _save_reminder_to_file(self, reminder_data: dict):
        """Save reminder to file as fallback"""
        try:
            import json
            reminders_file = 'reminders_data.json'
            
            # Load existing reminders
            try:
                with open(reminders_file, 'r') as f:
                    data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                data = {'reminders': []}
            
            # Add new reminder
            reminder_data['id'] = f"ai_reminder_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            reminder_data['created_at'] = datetime.now().isoformat()
            reminder_data['acknowledged'] = False
            
            data['reminders'].append(reminder_data)
            
            # Save back to file
            with open(reminders_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error saving reminder to file: {e}")
            
    def _handle_navigation_command(self, parameters: dict):
        """Handle navigation commands"""
        page = parameters.get('page', '').lower()
        page_map = {
            'dashboard': 0,
            'journal': 1,
            'ledger': 2,
            'trial balance': 3,
            'trial_balance': 3,
            'reports': 4,
            'accounts': 5,
            'reminders': 6,
            'tasks': 6,
            'team': 7,
            'org settings': 8,
            'settings': 11
        }
        
        page_index = page_map.get(page)
        if page_index is not None and hasattr(self, 'stack'):
            self.stack.setCurrentIndex(page_index)
            # Update sidebar button selection
            if hasattr(self, 'sidebar_buttons') and page_index < len(self.sidebar_buttons):
                for btn in self.sidebar_buttons:
                    btn.setChecked(False)
                self.sidebar_buttons[page_index].setChecked(True)
                
    def _handle_data_query_command(self, parameters: dict):
        """Handle data query commands"""
        query_type = parameters.get('query', '')
        
        # Implement basic data queries
        if 'balance' in query_type.lower():
            # For now, show a placeholder response
            self._show_ai_notification("Data query feature coming soon! You asked about: " + query_type)
        else:
            self._show_ai_notification(f"Searching for: {query_type}")
            
    def _handle_reminder_command(self, parameters: dict):
        """Handle reminder commands"""
        reminder_text = parameters.get('reminder_text', '')
        reminder_time = parameters.get('reminder_time', '')
        recurring = parameters.get('recurring', 'none')
        
        if reminder_text:
            # Navigate to reminders page if not already there
            current_page = self.stack.currentIndex() if hasattr(self, 'stack') else 0
            if current_page != 6:  # Reminders page index
                self._handle_navigation_command({'page': 'reminders'})
            
            # Add reminder via notification
            self._show_ai_notification(f"Reminder set: {reminder_text}")
            
    def _handle_notification_command(self, parameters: dict, message: str):
        """Handle notification commands"""
        self._show_ai_notification(message)
        
    def _show_ai_notification(self, message: str):
        """Show AI notification"""
        if hasattr(self, 'notification_manager'):
            self.notification_manager.add_notification(
                title="AI Assistant",
                message=message,
                notification_type="info"
            )
            
    def _show_ai_error(self, error_msg: str):
        """Show AI error message"""
        if hasattr(self, 'notification_manager'):
            self.notification_manager.add_notification(
                title="AI Error",
                message=error_msg,
                notification_type="error"
            )
            
    def _on_ai_processing_started(self):
        """Handle AI processing started"""
        if hasattr(self, 'simple_ai_bar'):
            self.simple_ai_bar.is_processing = True
            self.simple_ai_bar.setReadOnly(True)
            self.simple_ai_bar.setText("Processing...")
            self.simple_ai_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.simple_ai_bar.setCursor(Qt.CursorShape.ArrowCursor)
    def _on_ai_processing_finished(self):
        """Handle AI processing finished"""
        if hasattr(self, 'simple_ai_bar'):
            self.simple_ai_bar.is_processing = False
        
    def _on_ai_error(self, error_msg: str):
        """Handle AI processing error"""
        self._show_ai_error(error_msg)
    
    def _connect_ai_signals(self):
        """Connect AI processor signals to handlers"""
        # Connect AI status bar signals to command processor
        if hasattr(self, 'simple_ai_bar'):
            self.simple_ai_bar.returnPressed.connect(self._process_ai_command)        # Connect AI processor signals
        if hasattr(self, 'ai_processor'):
            self.ai_processor.response_ready.connect(self._handle_ai_response)
            self.ai_processor.navigation_requested.connect(self._handle_ai_navigation)
            self.ai_processor.report_requested.connect(self._handle_ai_report)
            self.ai_processor.reminder_created.connect(self._handle_ai_reminder)
            self.ai_processor.processing_started.connect(self._on_ai_processing_started)
            self.ai_processor.processing_finished.connect(self._on_ai_processing_finished)
            self.ai_processor.error_occurred.connect(self._on_ai_error)
            
            # Connect AI processor to status bar
            if hasattr(self, 'simple_ai_bar'):
                self.ai_processor.response_ready.connect(self.simple_ai_bar.handle_ai_response)
                self.ai_processor.processing_started.connect(self.simple_ai_bar.handle_processing_started)
                self.ai_processor.processing_finished.connect(self.simple_ai_bar.handle_processing_finished)
                self.ai_processor.error_occurred.connect(self.simple_ai_bar.handle_ai_error)
                  
    def _on_workspace_changed(self, org_id: str, org_name: str):
        """Handle workspace change"""
        try:
            self.logger.info(f"Switching to workspace: {org_name} (ID: {org_id})")
            
            # Update session manager
            if self.session_manager:
                success = self.session_manager.set_active_organization(org_id)
                if success:
                    # Refresh all pages that depend on organization context
                    self._refresh_organization_dependent_pages()
                    
                    # Update window title to show current workspace
                    self.setWindowTitle(f"AI Accountant - {org_name}")
                    
                    # Show notification
                    if hasattr(self, 'notification_manager'):
                        self.notification_manager.show_notification(
                            f"Switched to {org_name}",
                            f"Now working in {'personal workspace' if 'Workspace' in org_name else 'organization'}: {org_name}",
                            "info"
                        )
                else:
                    self.logger.error(f"Failed to switch to workspace {org_name}")
            
        except Exception as e:
            self.logger.error(f"Error switching workspace: {e}")
            if hasattr(self, 'notification_manager'):
                self.notification_manager.show_notification(
                    "Workspace Switch Failed",
                    f"Could not switch to {org_name}. Please try again.",
                    "error"                )
    
    def _refresh_organization_dependent_pages(self):
        """Refresh pages that depend on organization context"""
        try:
            # Iterate through all pages in the stack
            for i in range(self.stack.count()):
                page = self.stack.widget(i)
                  # Try common refresh method names
                if hasattr(page, 'refresh_data'):
                    page.refresh_data()
                elif hasattr(page, 'load_data'):
                    page.load_data()
                elif hasattr(page, '_load_data'):
                    page._load_data()
                elif hasattr(page, 'refresh_organization_data'):
                    page.refresh_organization_data()
                elif hasattr(page, 'load_dashboard_data'):
                    # Specifically for dashboard page
                    page.load_dashboard_data()
                elif hasattr(page, '_load_team_members'):
                    # Specifically for team management page
                    page._load_team_members()
                elif hasattr(page, '_load_users'):
                    # Specifically for user management page  
                    page._load_users()
                    
            self.logger.info("Refreshed organization-dependent pages")
                    
        except Exception as e:
            self.logger.error(f"Error refreshing organization-dependent pages: {e}")
    
    def refresh_workspace_switcher(self):
        """Refresh the workspace switcher (call when user joins/leaves organizations)"""
        if hasattr(self, 'bottom_bar'):
            self.bottom_bar.refresh_workspace_info()
    
    def _create_bottom_bar(self, main_layout):
        """Create and add bottom bar to the main window"""
        from .components.bottom_bar import BottomBar
        
        self.bottom_bar = BottomBar(
            auth_manager=self.auth_manager,
            session_manager=self.session_manager,
            parent=self
        )
        
        # Connect workspace change signal if workspace switcher is available
        if hasattr(self.bottom_bar, 'workspace_switcher'):
            self.bottom_bar.workspace_switcher.workspace_changed.connect(self._on_workspace_changed)
        
        main_layout.addWidget(self.bottom_bar)
