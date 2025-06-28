#!/usr/bin/env python3
"""
Debug script to test font loading and listing
"""
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PyQt6.QtWidgets import QApplication
from src.ui.components.font_manager import FontManager

def test_font_manager():
    """Test the font manager functionality"""
    print("🔤 Testing Font Manager")
    print("=" * 40)
    
    # Create QApplication (required for Qt font operations)
    app = QApplication(sys.argv)
    
    try:
        # Initialize font manager
        font_manager = FontManager()
        
        # Load custom fonts
        print("📂 Loading custom fonts...")
        loaded_fonts = font_manager.load_custom_fonts()
        print(f"✅ Loaded {len(loaded_fonts)} custom fonts: {loaded_fonts}")
        
        # Get available font families for dropdown
        print("\n🎨 Getting available font families for settings dropdown...")
        available_fonts = font_manager.get_available_font_families()
        print(f"📋 Available fonts ({len(available_fonts)}):")
        for i, font in enumerate(available_fonts, 1):
            print(f"   {i:2d}. {font}")
        
        # Check if JetBrains Mono and Courier New are available
        print("\n🔍 Checking specific fonts...")
        jetbrains_available = font_manager.is_font_available("JetBrains Mono")
        courier_available = font_manager.is_font_available("Courier New")
        cascadia_available = font_manager.is_font_available("Cascadia Code")
        
        print(f"   JetBrains Mono: {'✅ Available' if jetbrains_available else '❌ Not available'}")
        print(f"   Courier New:    {'✅ Available' if courier_available else '❌ Not available'}")
        print(f"   Cascadia Code:  {'✅ Available' if cascadia_available else '❌ Not available'}")
        
        # Get all available fonts (including system fonts)
        print("\n🖥️ Getting all available fonts (system + custom)...")
        all_fonts = font_manager.get_all_available_fonts()
        print(f"📊 Total available fonts: {len(all_fonts)}")
        
        # Filter to show coding-related fonts
        coding_fonts = [font for font in all_fonts if any(keyword in font.lower() for keyword in ['mono', 'code', 'console', 'courier'])]
        print(f"💻 Coding-related fonts found ({len(coding_fonts)}):")
        for font in coding_fonts:
            print(f"   - {font}")
        
        app.quit()
        return True
        
    except Exception as e:
        print(f"❌ Error testing font manager: {e}")
        import traceback
        traceback.print_exc()
        app.quit()
        return False

if __name__ == "__main__":
    success = test_font_manager()
    if success:
        print("\n✅ Font manager test completed successfully!")
    else:
        print("\n❌ Font manager test failed.")
