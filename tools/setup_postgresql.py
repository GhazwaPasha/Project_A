#!/usr/bin/env python3
"""
Quick setup script for PostgreSQL migration testing.
Provides options for Docker, Supabase, or local PostgreSQL setup.
"""

import os
import sys
import subprocess
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_docker():
    """Check if Docker is available."""
    try:
        result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            logger.info(f"✅ Docker found: {result.stdout.strip()}")
            return True
        else:
            logger.warning("❌ Docker not found")
            return False
    except FileNotFoundError:
        logger.warning("❌ Docker not found")
        return False

def setup_docker_postgres():
    """Set up PostgreSQL using Docker."""
    logger.info("Setting up PostgreSQL using Docker...")
    
    container_name = "accounting-postgres"
    postgres_password = "testpass123"
    port = "5432"
    
    try:
        # Check if container already exists
        result = subprocess.run(['docker', 'ps', '-a', '--filter', f'name={container_name}'], 
                              capture_output=True, text=True)
        
        if container_name in result.stdout:
            logger.info("Container already exists. Stopping and removing...")
            subprocess.run(['docker', 'stop', container_name], capture_output=True)
            subprocess.run(['docker', 'rm', container_name], capture_output=True)
        
        # Run new PostgreSQL container
        cmd = [
            'docker', 'run', '--name', container_name,
            '-e', f'POSTGRES_PASSWORD={postgres_password}',
            '-e', 'POSTGRES_DB=accounting_test',
            '-p', f'{port}:5432',
            '-d', 'postgres:15'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info(f"✅ PostgreSQL container started successfully!")
            logger.info(f"Container ID: {result.stdout.strip()}")
            
            # Update .env file
            env_content = f"""# Docker PostgreSQL Configuration (Auto-generated)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=accounting_test
POSTGRES_USER=postgres
POSTGRES_PASSWORD={postgres_password}

# Supabase (not configured for Docker setup)
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=

# Application Settings
APP_ENV=development
LOG_LEVEL=INFO
ENABLE_POSTGRESQL=true
FALLBACK_TO_SQLITE=true
"""
            
            with open('.env', 'w') as f:
                f.write(env_content)
            
            logger.info("✅ .env file updated with Docker PostgreSQL settings")
            
            # Wait a moment for container to start
            import time
            logger.info("Waiting for PostgreSQL to start...")
            time.sleep(5)
            
            return True
        else:
            logger.error(f"❌ Failed to start PostgreSQL container: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Docker setup failed: {e}")
        return False

def setup_supabase_instructions():
    """Provide Supabase setup instructions."""
    logger.info("""
🔧 Supabase Setup Instructions:

1. Go to https://supabase.com and create a free account
2. Create a new project
3. Go to Settings > API to get your credentials
4. Update your .env file with:
   - SUPABASE_URL (from API settings)
   - SUPABASE_ANON_KEY (from API settings)
   - POSTGRES_HOST (from Database settings - usually db.xxx.supabase.co)
   - POSTGRES_DB=postgres
   - POSTGRES_USER=postgres
   - POSTGRES_PASSWORD (from Database settings)

5. Your .env should look like:
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_ANON_KEY=your-anon-key
   POSTGRES_HOST=db.your-project.supabase.co
   POSTGRES_PORT=5432
   POSTGRES_DB=postgres
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=your-password
""")

def test_current_setup():
    """Test the current setup."""
    logger.info("Testing current PostgreSQL setup...")
    
    try:
        # Try to run the test script
        result = subprocess.run([sys.executable, 'tools/test_postgresql_setup.py'], 
                              capture_output=True, text=True, cwd='.')
        
        if result.returncode == 0:
            logger.info("✅ PostgreSQL setup test passed!")
            return True
        else:
            logger.error("❌ PostgreSQL setup test failed:")
            logger.error(result.stdout)
            logger.error(result.stderr)
            return False
            
    except Exception as e:
        logger.error(f"❌ Test execution failed: {e}")
        return False

def main():
    """Main setup function."""
    logger.info("🚀 PostgreSQL Setup Assistant for Accounting App Migration")
    
    print("\nChoose your PostgreSQL setup option:")
    print("1. Docker PostgreSQL (Quick local testing)")
    print("2. Supabase (Cloud-hosted, recommended for production)")
    print("3. Local PostgreSQL (If you have PostgreSQL installed)")
    print("4. Test current setup")
    print("5. Export SQLite data only (no PostgreSQL needed)")
    
    choice = input("\nEnter your choice (1-5): ").strip()
    
    if choice == "1":
        if check_docker():
            if setup_docker_postgres():
                logger.info("✅ Docker PostgreSQL setup complete!")
                if test_current_setup():
                    logger.info("🎉 Ready to migrate! Run: python tools/migrate_to_postgresql.py")
                else:
                    logger.error("Setup completed but tests failed. Check the logs above.")
            else:
                logger.error("Docker setup failed. Try option 2 (Supabase) instead.")
        else:
            logger.error("Docker not available. Please install Docker or choose option 2 (Supabase).")
    
    elif choice == "2":
        setup_supabase_instructions()
        logger.info("After setting up Supabase, run: python tools/test_postgresql_setup.py")
    
    elif choice == "3":
        logger.info("""
🔧 Local PostgreSQL Setup:

1. Install PostgreSQL on your system
2. Create a database: createdb accounting_test
3. Update your .env file with your local PostgreSQL credentials
4. Run: python tools/test_postgresql_setup.py
""")
    
    elif choice == "4":
        test_current_setup()
    
    elif choice == "5":
        logger.info("Exporting SQLite data only...")
        try:
            # Run export only
            result = subprocess.run([sys.executable, 'tools/migrate_to_postgresql.py', '--export-only'], 
                                  cwd='.')
            if result.returncode == 0:
                logger.info("✅ SQLite data exported to CSV files")
            else:
                logger.error("❌ Export failed")
        except Exception as e:
            logger.error(f"Export failed: {e}")
    
    else:
        logger.error("Invalid choice. Please run the script again.")

if __name__ == "__main__":
    main()
