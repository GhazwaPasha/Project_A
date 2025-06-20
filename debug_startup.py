import sys
import traceback
import os
import logging
from PyQt6.QtWidgets import QApplication, QMessageBox

# Set Mistral API key as environment variable for local dev (for production, use a secure method)
os.environ['MISTRAL_API_KEY'] = '***REMOVED***'

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('accounting_app.log'),
        logging.StreamHandler()
    ]
)

def check_database_setup():
    try:
        from src.core.config import DatabaseConfig
        DatabaseConfig.validate_config()
        
        from src.core.database_manager import DatabaseManager
        db_manager = DatabaseManager()
        
        if db_manager.test_connection():
            logging.info('✅ PostgreSQL database connected successfully')
            return True
        else:
            raise Exception('PostgreSQL connection test failed')
            
    except Exception as e:
        logging.error(f'PostgreSQL setup failed: {e}')
        return False

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # Check database setup
    postgresql_available = check_database_setup()
    
    if not postgresql_available:
        print('Database setup failed')
        sys.exit(1)
    
    logging.info('Starting application with PostgreSQL backend')
    
    try:
        print("About to import MainWindow...")
        from src.ui.mainwindow import MainWindow
        print("MainWindow imported successfully")
        
        print("About to create MainWindow instance...")
        window = MainWindow()
        print('MainWindow created successfully')
        
        print("About to show MainWindow...")
        window.show()
        print('MainWindow shown successfully')
        
    except Exception as e:
        logging.error(f'Application startup failed: {e}')
        print(f'Full traceback:')
        traceback.print_exc()
        sys.exit(1)
