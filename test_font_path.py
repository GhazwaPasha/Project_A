#!/usr/bin/env python3
"""
Debug script to test font loading path resolution
"""
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFontDatabase

def test_font_path_resolution():
    """Test font path resolution"""
    print("📂 Testing Font Path Resolution")
    print("=" * 40)
    
    # Get the application directory path (same logic as in font_manager)
    if getattr(sys, 'frozen', False):
        # If the application is frozen (compiled with PyInstaller)
        app_path = os.path.dirname(sys.executable)
    else:
        # If running from source code
        current_file = os.path.abspath(__file__)
        print(f"Current file: {current_file}")
        
        # Go up levels: file -> Project_A -> assets/fonts
        app_path = os.path.dirname(current_file)  # Project_A
        print(f"App path: {app_path}")
        
    font_directory = os.path.join(app_path, 'assets', 'fonts')
    print(f"Font directory: {font_directory}")
    print(f"Directory exists: {os.path.exists(font_directory)}")
    
    if os.path.exists(font_directory):
        print("📁 Files in font directory:")
        for filename in os.listdir(font_directory):
            file_path = os.path.join(font_directory, filename)
            print(f"   - {filename} (size: {os.path.getsize(file_path)} bytes)")
    
    # Test loading one font manually
    app = QApplication(sys.argv)
    
    jetbrains_path = os.path.join(font_directory, "JetBrainsMono-Regular.ttf")
    if os.path.exists(jetbrains_path):
        print(f"\n🔤 Attempting to load: {jetbrains_path}")
        font_id = QFontDatabase.addApplicationFont(jetbrains_path)
        if font_id != -1:
            font_families = QFontDatabase.applicationFontFamilies(font_id)
            print(f"✅ Successfully loaded font ID {font_id}")
            print(f"📋 Font families: {font_families}")
        else:
            print(f"❌ Failed to load font")
    else:
        print(f"❌ Font file not found: {jetbrains_path}")
    
    app.quit()

if __name__ == "__main__":
    test_font_path_resolution()
