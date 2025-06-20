import sys
import os
from PyQt6.QtWidgets import QApplication, QMessageBox
from src.ui.mainwindow import MainWindow

# Set Mistral API key as environment variable for local dev (for production, use a secure method)
os.environ['MISTRAL_API_KEY'] = '***REMOVED***'

if __name__ == "__main__":
    app = QApplication(sys.argv)
      # Hybrid mode with your existing local PostgreSQL
    # prefer_local=True for faster performance using your local database
    try:
        window = MainWindow(db_mode='hybrid', prefer_local=True, auto_sync=True)
        window.show()
    except Exception as e:
        QMessageBox.critical(None, "Startup Error", 
                           f"Failed to start application: {str(e)}\n\n"
                           f"Try running: python tools/setup_local_postgres.py")
        sys.exit(1)
    
    sys.exit(app.exec())
