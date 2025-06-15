import sys
import os
from PyQt6.QtWidgets import QApplication
from src.ui.mainwindow import MainWindow

# Set Mistral API key as environment variable for local dev (for production, use a secure method)
os.environ['MISTRAL_API_KEY'] = '***REMOVED***'

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())
