#!/usr/bin/env python3
"""
Setup tool for hybrid sync with existing local PostgreSQL database.
"""

import os
import sys
import subprocess
import logging
import time
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PostgreSQLSetup:
    """Setup local PostgreSQL database for hybrid sync using existing installation."""
    
    def __init__(self):
        self.db_name = "accounting_local"
        self.username = "postgres"
        self.password = "postgres"  # Your local PostgreSQL password
        self.host = "localhost"
        self.port = "5432"
    
    def test_postgresql_connection(self):
        """Test connection to existing PostgreSQL installation."""
        logger.info("🔍 Testing connection to existing PostgreSQL...")
        
        try:
            import psycopg2
            
            # First, try to connect to the default postgres database
            conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                database="postgres",  # Connect to default database first
                user=self.username,
                password=self.password
            )
            conn.close()
            logger.info("✅ Successfully connected to existing PostgreSQL installation")
            return True
            
        except psycopg2.OperationalError as e:
            logger.error(f"❌ Failed to connect to PostgreSQL: {e}")
            logger.error("Please check that:")
            logger.error("1. PostgreSQL is running")
            logger.error("2. Username 'postgres' exists")
            logger.error("3. Password is 'postgres'")
            logger.error("4. PostgreSQL is listening on localhost:5432")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            return False
    
    def create_local_database(self):
        """Create the local accounting database."""
        logger.info(f"🗄️ Creating local database '{self.db_name}'...")
        
        try:
            import psycopg2
            from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
            
            # Connect to PostgreSQL server (to create database)
            conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                database="postgres",
                user=self.username,
                password=self.password
            )
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            
            cursor = conn.cursor()
            
            # Check if database already exists
            cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (self.db_name,))
            if cursor.fetchone():
                logger.info(f"✅ Database '{self.db_name}' already exists")
            else:
                # Create the database
                cursor.execute(f'CREATE DATABASE "{self.db_name}"')
                logger.info(f"✅ Database '{self.db_name}' created successfully")
            
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create database: {e}")
            return False
    
    def _test_local_database_connection(self):
        """Test connection to the new local database."""
        try:
            import psycopg2
            conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.db_name,
                user=self.username,
                password=self.password
            )
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Local database connection test failed: {e}")
            return False
    
    def create_env_file(self):
        """Create or update .env file with local database settings."""
        logger.info("📝 Creating/updating .env file...")
        
        env_path = Path.cwd() / '.env'
        env_content = []
        
        # Read existing .env if it exists
        if env_path.exists():
            with open(env_path, 'r') as f:
                env_content = f.readlines()
        
        # Local database settings to add/update
        local_settings = {
            'LOCAL_POSTGRES_HOST': self.host,
            'LOCAL_POSTGRES_PORT': self.port,
            'LOCAL_POSTGRES_DB': self.db_name,
            'LOCAL_POSTGRES_USER': self.username,
            'LOCAL_POSTGRES_PASSWORD': self.password
        }
        
        # Update or add local settings
        for key, value in local_settings.items():
            found = False
            for i, line in enumerate(env_content):
                if line.strip().startswith(f'{key}='):
                    env_content[i] = f'{key}={value}\n'
                    found = True
                    break
            if not found:
                env_content.append(f'{key}={value}\n')
        
        # Write updated .env file
        with open(env_path, 'w') as f:
            f.writelines(env_content)
        
        logger.info("✅ .env file updated with local database settings")
        return True
    
    def setup_database_schema(self):
        """Setup database schema in local PostgreSQL."""
        logger.info("🏗️ Setting up database schema...")
        
        try:
            # Import database manager to create tables
            sys.path.append(str(Path.cwd()))
            from src.core.database_manager import DatabaseManager
            
            # Create database manager with local settings
            db_manager = DatabaseManager(prefer_local=True, auto_sync=False)
            
            # Create tables
            db_manager.create_tables()
            
            logger.info("✅ Database schema created successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to setup database schema: {e}")
            return False
    
    def full_setup(self):
        """Perform full setup of local PostgreSQL with hybrid sync."""
        logger.info("🚀 Starting hybrid sync setup with existing PostgreSQL...")
        
        steps = [
            ("Testing PostgreSQL connection", self.test_postgresql_connection),
            ("Creating local database", self.create_local_database),
            ("Creating .env configuration", self.create_env_file),
            ("Setting up database schema", self.setup_database_schema),
        ]
        
        for step_name, step_func in steps:
            logger.info(f"📋 {step_name}...")
            if not step_func():
                logger.error(f"❌ Failed: {step_name}")
                return False
            logger.info(f"✅ Completed: {step_name}")
        
        logger.info("🎉 Hybrid sync setup completed successfully!")
        logger.info("📋 You can now run the application with: python main_hybrid.py --mode hybrid")
        return True
    
    def status(self):
        """Show current setup status."""
        logger.info("📊 Hybrid Sync Setup Status:")
        
        # Check PostgreSQL connection
        if self.test_postgresql_connection():
            logger.info("PostgreSQL Server: ✅ Available")
        else:
            logger.info("PostgreSQL Server: ❌ Not Available")
        
        # Check local database
        if self._test_local_database_connection():
            logger.info(f"Local Database ({self.db_name}): ✅ Available")
        else:
            logger.info(f"Local Database ({self.db_name}): ❌ Not Available")
        
        # Check .env file
        env_exists = Path.cwd().joinpath('.env').exists()
        logger.info(f".env Configuration: {'✅ Exists' if env_exists else '❌ Missing'}")

def main():
    """Main setup function."""
    if len(sys.argv) > 1 and sys.argv[1] == '--status':
        setup = PostgreSQLSetup()
        setup.status()
    else:
        setup = PostgreSQLSetup()
        setup.full_setup()

if __name__ == "__main__":
    main()
