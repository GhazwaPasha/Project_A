#!/usr/bin/env python3
"""
Convert sync.png to SVG format for use in the manual sync button.
"""

import os
from PIL import Image
import base64

def png_to_svg(png_path, svg_path):
    """Convert PNG to SVG by embedding the PNG as base64 data."""
    try:
        # Open and verify the PNG image
        with Image.open(png_path) as img:
            # Get image dimensions
            width, height = img.size
            print(f"Original image size: {width}x{height}")
            
            # Resize to 16x16 for window control button if needed
            if width != 16 or height != 16:
                img = img.resize((16, 16), Image.Resampling.LANCZOS)
                print("Resized to 16x16 for window control button")
            
            # Convert to RGBA if not already
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            # Save to temporary PNG to get base64 data
            temp_path = png_path.replace('.png', '_temp.png')
            img.save(temp_path, 'PNG')
            
            # Read as base64
            with open(temp_path, 'rb') as f:
                img_data = base64.b64encode(f.read()).decode()
            
            # Clean up temp file
            os.remove(temp_path)
            
        # Create SVG with embedded PNG
        svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="16" height="16" viewBox="0 0 16 16" xmlns="http://www.w3.org/2000/svg">
    <image href="data:image/png;base64,{img_data}" width="16" height="16"/>
</svg>'''
        
        # Write SVG file
        with open(svg_path, 'w', encoding='utf-8') as f:
            f.write(svg_content)
            
        print(f"✅ Successfully converted {png_path} to {svg_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error converting PNG to SVG: {e}")
        return False

def create_fallback_sync_svg(svg_path):
    """Create a fallback sync icon SVG if conversion fails."""
    try:
        svg_content = '''<?xml version="1.0" encoding="UTF-8"?>
<svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
    <!-- Sync/Refresh icon with two curved arrows -->
    <path d="M4 4V2L1 5L4 8V6C5.7 6 7 7.3 7 9S5.7 12 4 12" 
          stroke="rgba(255, 255, 255, 0.8)" 
          stroke-width="1.2" 
          stroke-linecap="round" 
          stroke-linejoin="round" 
          fill="none"/>
    <path d="M12 12V14L15 11L12 8V10C10.3 10 9 8.7 9 7S10.3 4 12 4" 
          stroke="rgba(255, 255, 255, 0.8)" 
          stroke-width="1.2" 
          stroke-linecap="round" 
          stroke-linejoin="round" 
          fill="none"/>
</svg>'''
        
        with open(svg_path, 'w', encoding='utf-8') as f:
            f.write(svg_content)
            
        print(f"✅ Created fallback sync icon SVG at {svg_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error creating fallback SVG: {e}")
        return False

def main():
    png_path = "sync.png"
    svg_path = os.path.join("assets", "icons", "sync.svg")
    
    print("🔄 Converting sync icon to SVG format...")
    
    # Ensure the assets/icons directory exists
    os.makedirs(os.path.dirname(svg_path), exist_ok=True)
    
    # Try to convert PNG to SVG
    if os.path.exists(png_path):
        print(f"Found sync.png, converting to SVG...")
        success = png_to_svg(png_path, svg_path)
        
        if not success:
            print("PNG conversion failed, creating fallback SVG...")
            success = create_fallback_sync_svg(svg_path)
    else:
        print("sync.png not found, creating fallback SVG...")
        success = create_fallback_sync_svg(svg_path)
    
    if success:
        print(f"\n🎉 Sync icon is ready at: {svg_path}")
        print("The manual sync button will now use this SVG icon!")
    else:
        print("\n❌ Failed to create sync icon SVG")

if __name__ == "__main__":
    main()
