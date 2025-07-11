#!/usr/bin/env python3
"""
Build script for creating executable with embedded environment variables and assets
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path

def create_embedded_config():
    """Create embedded configuration with environment variables from .env file"""
    import os
    from dotenv import load_dotenv
    
    # Load environment variables from .env file
    load_dotenv()
    
    # Get credentials from .env file
    supabase_url = os.getenv('SUPABASE_URL', 'https://your-project.supabase.co')
    supabase_anon_key = os.getenv('SUPABASE_ANON_KEY', 'your-anon-key-here')
    supabase_service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY', 'your-service-role-key-here')
    app_env = os.getenv('APP_ENV', 'production')
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    mistral_api_key = os.getenv('MISTRAL_API_KEY', '')
    
    with open('embedded_config.py', 'w') as f:
        f.write(f'''"""
Embedded configuration for the accounting application
"""
import os

# Embedded environment variables from .env file
EMBEDDED_CONFIG = {{
    'SUPABASE_URL': '{supabase_url}',
    'SUPABASE_ANON_KEY': '{supabase_anon_key}',
    'SUPABASE_SERVICE_ROLE_KEY': '{supabase_service_key}',
    'APP_ENV': '{app_env}',
    'LOG_LEVEL': '{log_level}',
    'MISTRAL_API_KEY': '{mistral_api_key}'
}}

def setup_embedded_environment():
    """Setup environment variables from embedded config"""
    for key, value in EMBEDDED_CONFIG.items():
        if not os.getenv(key):  # Only set if not already set
            os.environ[key] = value

# Auto-setup when imported
setup_embedded_environment()
''')
    
    print("✅ Created embedded configuration from .env file")

def create_spec_file():
    """Create PyInstaller spec file with assets"""
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Collect all assets
assets = [
    ('assets/icons/*.svg', 'assets/icons'),
    ('assets/icons/*.png', 'assets/icons'),
    ('assets/fonts/*.ttf', 'assets/fonts'),
    ('embedded_config.py', '.'),
]

a = Analysis(
    ['run.py'],
    pathex=[],
    binaries=[],
    datas=assets,
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'supabase',
        'psycopg2',
        'pandas',
        'matplotlib',
        'pyqtgraph',
        'openpyxl',
        'requests',
        'python-dotenv',
        'openai'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='AccountingApp',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icons/app-icon.png'
)
'''
    
    with open('AccountingApp.spec', 'w') as f:
        f.write(spec_content)
    
    print("✅ Created PyInstaller spec file")

def modify_run_py():
    """Modify run.py to import embedded config"""
    try:
        with open('run.py', 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        # Fallback to different encoding
        with open('run.py', 'r', encoding='latin-1') as f:
            content = f.read()
    
    # Add import at the top
    if 'import embedded_config' not in content:
        lines = content.split('\n')
        # Find the first import line
        for i, line in enumerate(lines):
            if line.startswith('import ') or line.startswith('from '):
                lines.insert(i, 'import embedded_config  # Embedded configuration')
                break
        
        # Write back
        with open('run.py', 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
    
    print("✅ Modified run.py to use embedded config")

def build_executable():
    """Build the executable using PyInstaller"""
    print("🔨 Building executable...")
    
    # Install PyInstaller if not installed
    try:
        import PyInstaller
    except ImportError:
        print("📦 Installing PyInstaller...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller'])
    
    # Build the executable
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--onefile',
        '--windowed',
        '--name=AccountingApp',
        '--add-data=assets/icons;assets/icons',
        '--add-data=assets/fonts;assets/fonts',
        '--add-data=embedded_config.py;.',
        '--hidden-import=PyQt6.QtCore',
        '--hidden-import=PyQt6.QtGui',
        '--hidden-import=PyQt6.QtWidgets',
        '--hidden-import=supabase',
        '--hidden-import=psycopg2',
        '--hidden-import=pandas',
        '--hidden-import=matplotlib',
        '--hidden-import=pyqtgraph',
        '--hidden-import=openpyxl',
        '--hidden-import=requests',
        '--hidden-import=python-dotenv',
        '--hidden-import=openai',
        '--hidden-import=src.core.resource_manager',
        'run.py'
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Executable built successfully!")
        print("📁 Location: dist/AccountingApp.exe")
    else:
        print("❌ Build failed:")
        print(result.stderr)

def main():
    """Main build process"""
    print("🚀 Starting executable build process...")
    
    # Step 1: Create embedded configuration
    create_embedded_config()
    
    # Step 2: Create spec file
    create_spec_file()
    
    # Step 3: Modify run.py
    modify_run_py()
    
    # Step 4: Build executable
    build_executable()
    
    print("\n🎉 Build process completed!")
    print("📝 Next steps:")
    print("1. Update embedded_config.py with your actual Supabase credentials")
    print("2. Run build_exe.py again to create the final executable")
    print("3. Test the executable in dist/AccountingApp.exe")

if __name__ == '__main__':
    main() 