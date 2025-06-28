#!/usr/bin/env python3
"""
Test JetBrains Mono loading specifically
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PyQt6.QtWidgets import QApplication
from src.ui.components.font_manager import font_manager

def test_jetbrains_loading():
    """Test JetBrains Mono loading specifically"""
    print("🔤 Testing JetBrains Mono Loading")
    print("=" * 40)
    
    app = QApplication(sys.argv)
    
    print(f"Loaded fonts before: {len(font_manager.loaded_fonts)}")
    for family, _, path in font_manager.loaded_fonts:
        print(f"  - {family} from {path}")
    
    print(f"\nAvailable font families: {font_manager.get_available_font_families()}")
    print(f"JetBrains Mono available: {font_manager.is_font_available('JetBrains Mono')}")
    
    app.quit()

if __name__ == "__main__":
    test_jetbrains_loading()
