from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from PyQt6.QtWidgets import QApplication
from .loading_screen import LoadingScreen


class BackgroundLoader(QObject):
    """Background loader that initializes main window while showing loading screen"""
    
    # Signals
    loading_complete = pyqtSignal(object)  # Emits the initialized main window
    loading_error = pyqtSignal(str)  # Emits error message
    
    def __init__(self, auth_manager=None, session_manager=None):
        super().__init__()
        self.auth_manager = auth_manager
        self.session_manager = session_manager
        self.loading_screen = None
        self.main_window = None
        
    def start_loading(self):
        """Start the background loading process"""
        # Create and show loading screen
        self.loading_screen = LoadingScreen()
        self.loading_screen.resize(400, 300)
        self.loading_screen.show_loading_screen()
        
        # Process events to ensure loading screen is displayed
        QApplication.processEvents()
        
        # Use a timer to delay the main window creation
        # This allows the loading screen to be displayed first
        self.loading_timer = QTimer()
        self.loading_timer.timeout.connect(self.initialize_main_window)
        self.loading_timer.setSingleShot(True)
        self.loading_timer.start(100)  # Start after 100ms to ensure loading screen is visible
        
    def initialize_main_window(self):
        """Initialize the main window after a short delay"""
        try:
            # Import here to avoid circular imports
            from ..mainwindow import MainWindow
            
            # Create main window
            main_window = MainWindow(
                auth_manager=self.auth_manager,
                session_manager=self.session_manager
            )
            
            # Hide loading screen
            if self.loading_screen:
                self.loading_screen.hide_loading_screen()
                self.loading_screen.deleteLater()
                self.loading_screen = None
            
            # Emit completion signal
            self.loading_complete.emit(main_window)
            
        except Exception as e:
            # Hide loading screen
            if self.loading_screen:
                self.loading_screen.hide_loading_screen()
                self.loading_screen.deleteLater()
                self.loading_screen = None
            
            # Emit error signal
            self.loading_error.emit(str(e)) 