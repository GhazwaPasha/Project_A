"""
Font Manager for the accounting application.
Provides font management, custom font loading, and font setting utilities.
"""

import os
import sys
from PyQt6.QtGui import QFontDatabase, QFont
from PyQt6.QtCore import QSettings

class FontManager:
    """
    Font Manager for handling custom fonts in the application.
    This class provides utilities for loading, managing, and setting custom fonts.
    """
    # Curated font families for the application
    FONT_FAMILIES = {
        'default': 'Segoe UI',
        'code_cascadia': 'Cascadia Code',
        'code_mono': 'Cascadia Mono',
        'code_courier': 'Courier New',
        'serif_classic': 'Times New Roman',
        'code_jetbrains': 'JetBrains Mono',
        'sans_lucida': 'Lucida Sans Unicode',
        'script_corsiva': 'Monotype Corsiva',
        'sans_helvetica': 'Helvetica'
    }
    
    # Font weights for the application
    FONT_WEIGHTS = {
        'light': 300,
        'regular': 400,
        'medium': 500,
        'semibold': 600,
        'bold': 700
    }

    def __init__(self):
        """Initialize the font manager."""
        self.settings = QSettings("AccountingApp", "Fonts")
        self.loaded_fonts = []  # Will store (font_family_name, font_id, font_path)
        self.current_font_family = self.settings.value("font_family", self.FONT_FAMILIES['default'])
        self.current_font_scale = float(self.settings.value("font_scale", 1.0))
    
    def load_custom_fonts(self, font_directory=None):
        """
        Load JetBrains Mono fonts from assets directory.
        """
        if font_directory is None:
            # Get the application directory path
            if getattr(sys, 'frozen', False):
                app_path = os.path.dirname(sys.executable)
            else:
                app_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            font_directory = os.path.join(app_path, 'assets', 'fonts')
        
        loaded_families = []
        if os.path.exists(font_directory):
            # Only load JetBrains Mono fonts
            jetbrains_fonts = ['JetBrainsMono-Regular.ttf', 'JetBrainsMono-Bold.ttf']
            for filename in jetbrains_fonts:
                font_path = os.path.join(font_directory, filename)
                if os.path.exists(font_path):
                    font_id = QFontDatabase.addApplicationFont(font_path)
                    if font_id != -1:
                        font_families = QFontDatabase.applicationFontFamilies(font_id)
                        for family in font_families:
                            if family not in loaded_families:
                                loaded_families.append(family)
                                self.loaded_fonts.append((family, font_id, font_path))
        
        return loaded_families
    
    def get_all_available_fonts(self):
        """
        Return the preferred fonts including custom loaded ones.
        """
        preferred = [
            'Segoe UI', 'Cascadia Code', 'Cascadia Mono', 'Courier New', 'Times New Roman',
            'JetBrains Mono', 'Lucida Sans Unicode', 'Monotype Corsiva', 'Helvetica'
        ]
        system_fonts = QFontDatabase.families()
        custom_fonts = [family for family, _, _ in self.loaded_fonts]
        
        # Combine custom and system fonts, keeping only preferred ones
        all_fonts = custom_fonts + [f for f in preferred if f in system_fonts]
        return list(dict.fromkeys(all_fonts))  # Remove duplicates while preserving order
    
    def get_font_family(self):
        """
        Get the current font family name.
        
        Returns:
            str: Current font family name.
        """
        return self.current_font_family
    
    def set_font_family(self, family_name):
        """
        Set the current font family.
        
        Args:
            family_name (str): Name of the font family to set.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        available_fonts = self.get_all_available_fonts()
        if family_name in available_fonts or family_name in self.FONT_FAMILIES.values():
            self.current_font_family = family_name
            self.settings.setValue("font_family", family_name)
            return True
        return False
    
    def get_font_scale(self):
        """
        Get the current font scale factor.
        
        Returns:
            float: Current font scale factor.
        """
        return self.current_font_scale
    
    def set_font_scale(self, scale):
        """
        Set the font scale factor.
        
        Args:
            scale (float): Scale factor between 0.8 and 1.5.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        # Limit the scale to a reasonable range
        if 0.8 <= scale <= 1.5:
            self.current_font_scale = scale
            self.settings.setValue("font_scale", scale)
            return True
        return False
    
    def get_font(self, size=12, weight='regular'):
        """
        Get a QFont with the current family, given size and weight.
        
        Args:
            size (int): Font size in points.
            weight (str): Font weight name from FONT_WEIGHTS.
            
        Returns:
            QFont: Font with the specified properties.
        """
        font = QFont(self.current_font_family, int(size * self.current_font_scale))
        
        # Set weight if valid
        if weight in self.FONT_WEIGHTS:
            font.setWeight(self.FONT_WEIGHTS[weight])
            
        return font
    
    def get_stylesheet_font_family(self):
        """
        Get the font-family CSS string for use in stylesheets.
        
        Returns:
            str: font-family CSS value.
        """
        return f"font-family: '{self.current_font_family}', Arial, sans-serif;"
    
    def apply_font_to_application(self, app):
        """
        Apply the current font to the entire application.
        
        Args:
            app: QApplication instance.
        """
        default_font = self.get_font(12, 'regular')
        app.setFont(default_font)
        
    def is_font_available(self, font_name):
        """
        Check if a font is available on the system.
        
        Args:
            font_name (str): The name of the font to check
            
        Returns:
            bool: True if the font is available, False otherwise
        """
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtGui import QFont, QFontInfo
        
        # Try to create a font and see if the system substitutes it
        font = QFont(font_name)
        info = QFontInfo(font)
        
        # If the requested family matches the actual family, the font exists
        requested_family = font_name.lower()
        actual_family = info.family().lower()
        
        # Check if the font family was successfully set (not substituted)
        # Either exact match or the font name is contained in the resulting family
        return requested_family == actual_family or requested_family in actual_family
        
    def get_available_font_families(self):
        """
        Return the user's preferred fonts including custom loaded ones.
        """
        preferred = [
            'Segoe UI', 'Cascadia Code', 'Cascadia Mono', 'Courier New', 'Times New Roman',
            'JetBrains Mono', 'Lucida Sans Unicode', 'Monotype Corsiva', 'Helvetica'
        ]
        system_fonts = QFontDatabase.families()
        custom_fonts = [family for family, _, _ in self.loaded_fonts]
        
        # Combine custom and system fonts, keeping only preferred ones
        available = custom_fonts + [f for f in preferred if f in system_fonts]
        return list(dict.fromkeys(available))  # Remove duplicates while preserving order
        
    def install_developer_fonts(self):
        """
        Manually install developer fonts (Cascadia Code and JetBrains Mono)
        from assets directory.
        
        Returns:
            list: List of installed font families
        """
        import os
        from PyQt6.QtGui import QFontDatabase
        
        # Check if developer fonts are already available
        available_families = QFontDatabase.families()
        dev_fonts_needed = []
        
        # Check if Cascadia Code is already available
        cascadia_available = any('cascadia' in family.lower() for family in available_families)
        if not cascadia_available:
            dev_fonts_needed.extend(['CascadiaCode.ttf', 'CascadiaCodePL.ttf'])
            
        # Check if JetBrains Mono is already available  
        jetbrains_available = any('jetbrains' in family.lower() for family in available_families)
        if not jetbrains_available:
            dev_fonts_needed.append('jetbrains')  # Will handle downloading
        
        # If all fonts are already available, return early
        if not dev_fonts_needed:
            return [f for f in available_families if 'cascadia' in f.lower() or 'jetbrains' in f.lower()]
        
        # Get the application directory path
        app_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        assets_fonts_dir = os.path.join(app_path, 'assets', 'fonts')
        
        # Ensure the fonts directory exists
        if not os.path.exists(assets_fonts_dir):
            os.makedirs(assets_fonts_dir)
        
        # Track installed fonts
        installed_families = []
          # First install Cascadia Code
        cascadia_fonts = ['CascadiaCode.ttf', 'CascadiaCodePL.ttf']
        for font_file in cascadia_fonts:
            font_path = os.path.join(assets_fonts_dir, font_file)
            if os.path.exists(font_path):
                font_id = QFontDatabase.addApplicationFont(font_path)
                if font_id != -1:
                    families = QFontDatabase.applicationFontFamilies(font_id)
                    if families:
                        installed_families.extend(families)
          # Now handle JetBrains Mono - download if not present
        jetbrains_files = [f for f in os.listdir(assets_fonts_dir) if f.lower().startswith('jetbrainsmono')]
        if not jetbrains_files:
            downloaded_files = self._download_jetbrains_mono(assets_fonts_dir)
            jetbrains_files = [os.path.basename(f) for f in downloaded_files]
          # Install JetBrains Mono fonts
        for font_file in jetbrains_files:
            font_path = os.path.join(assets_fonts_dir, font_file)
            if os.path.exists(font_path):
                font_id = QFontDatabase.addApplicationFont(font_path)
                if font_id != -1:
                    families = QFontDatabase.applicationFontFamilies(font_id)
                    if families:
                        installed_families.extend(families)
          # Verify the fonts were installed successfully (quietly)
        dev_font_names = ['Cascadia Code', 'JetBrains Mono']
        for font_name in dev_font_names:
            for family in installed_families:
                if font_name.lower() in family.lower():
                    break
        
        # Update the loaded fonts list with installed families
        if installed_families:
            self.loaded_fonts.extend([(family, -1) for family in installed_families])
            self.loaded_fonts = list(set((family, id) for family, id in self.loaded_fonts))
            
        return installed_families
        
    def _download_jetbrains_mono(self, fonts_dir):
        """
        Download JetBrains Mono font if it's not already in the assets folder.
        
        Args:
            fonts_dir (str): Path to the assets/fonts directory
            
        Returns:
            list: List of downloaded font file paths
        """
        import os
        import tempfile
        import zipfile
        import shutil
        
        try:
            # First check if we already have JetBrains Mono font files
            jetbrains_files = [f for f in os.listdir(fonts_dir) if f.lower().startswith('jetbrainsmono')]
            if jetbrains_files:
                print(f"JetBrains Mono fonts already exist: {', '.join(jetbrains_files)}")
                return [os.path.join(fonts_dir, f) for f in jetbrains_files]
            
            # If not, download from GitHub
            import urllib.request
            
            print("Downloading JetBrains Mono font...")
            url = "https://github.com/JetBrains/JetBrainsMono/releases/download/v2.304/JetBrainsMono-2.304.zip"
            
            # Create a temporary file to store the downloaded zip
            temp_dir = tempfile.mkdtemp()
            zip_path = os.path.join(temp_dir, 'jetbrains_mono.zip')
            
            # Download the font
            urllib.request.urlretrieve(url, zip_path)
            print(f"Downloaded JetBrains Mono to {zip_path}")
              # Extract the needed fonts
            downloaded_files = []
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                font_files = [f for f in zip_ref.namelist() if f.endswith('.ttf') and 'fonts/ttf' in f]
                for font_file in font_files[:4]:  # Extract first 4 fonts (regular, bold, etc.)
                    source = zip_ref.open(font_file)
                    font_name = os.path.basename(font_file)
                    target_path = os.path.join(fonts_dir, font_name)
                    
                    with open(target_path, 'wb') as target:
                        shutil.copyfileobj(source, target)
                    
                    downloaded_files.append(target_path)
                    print(f"Extracted {font_name} to {target_path}")
            
            # Clean up - with better error handling
            try:
                shutil.rmtree(temp_dir)
            except Exception as cleanup_error:
                print(f"Warning: Could not clean up temporary directory: {cleanup_error}")
                # Try to at least remove the zip file
                try:
                    os.remove(zip_path)
                except:
                    pass
            
            return downloaded_files
            
        except Exception as e:
            print(f"Error downloading JetBrains Mono font: {e}")
            return []

# Initialize a global instance (fonts will be loaded when application starts)
font_manager = FontManager()
