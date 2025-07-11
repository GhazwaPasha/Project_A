"""
Resource Manager for handling file paths in both development and executable environments
"""
import os
import sys
from pathlib import Path

class ResourceManager:
    """Manages resource paths for both development and executable environments"""
    
    @staticmethod
    def get_resource_path(relative_path):
        """
        Get the absolute path to a resource file.
        Works in both development and PyInstaller executable environments.
        
        Args:
            relative_path (str): Relative path from project root (e.g., "assets/icons/dashboard_new.svg")
            
        Returns:
            str: Absolute path to the resource file
        """
        try:
            # Check if we're running in a PyInstaller executable
            if getattr(sys, 'frozen', False):
                # Running in executable - use sys._MEIPASS
                base_path = sys._MEIPASS
            else:
                # Running in development - use project root
                # Get the directory containing this file
                current_dir = os.path.dirname(os.path.abspath(__file__))
                # Go up to project root (src/core -> src -> project root)
                base_path = os.path.dirname(os.path.dirname(current_dir))
            
            # Join with the relative path
            full_path = os.path.join(base_path, relative_path)
            
            # Verify the file exists
            if os.path.exists(full_path):
                return full_path
            else:
                print(f"Warning: Resource not found: {full_path}")
                return None
                
        except Exception as e:
            print(f"Error getting resource path for {relative_path}: {e}")
            return None
    
    @staticmethod
    def get_icon_path(icon_name):
        """
        Get the path to an icon file.
        
        Args:
            icon_name (str): Name of the icon file (e.g., "dashboard_new.svg")
            
        Returns:
            str: Absolute path to the icon file
        """
        return ResourceManager.get_resource_path(f"assets/icons/{icon_name}")
    
    @staticmethod
    def get_font_path(font_name):
        """
        Get the path to a font file.
        
        Args:
            font_name (str): Name of the font file (e.g., "CascadiaCode.ttf")
            
        Returns:
            str: Absolute path to the font file
        """
        return ResourceManager.get_resource_path(f"assets/fonts/{font_name}")
    
    @staticmethod
    def list_available_icons():
        """List all available icon files for debugging"""
        icons_dir = ResourceManager.get_resource_path("assets/icons")
        if icons_dir and os.path.exists(icons_dir):
            return [f for f in os.listdir(icons_dir) if f.endswith(('.svg', '.png'))]
        return []
    
    @staticmethod
    def verify_resources():
        """Verify that all required resources are available"""
        required_icons = [
            "dashboard_new.svg",
            "journal_new.svg", 
            "ledger_new.svg",
            "trial_balance_new.svg",
            "reports_new.svg",
            "accounts_new.svg",
            "ledger_note.svg",
            "period_closing_modern.svg",
            "team_new.svg",
            "org_settings_new.svg",
            "user_mgmt_new.svg",
            "platform_new.svg",
            "global_orgs_new.svg",
            "settings_new.svg",
            "menu_modern.svg",
            "minimize.svg",
            "maximize.svg",
            "close.svg",
            "notification_modern.svg",
            "wifi.png",
            "app-icon.png"
        ]
        
        missing_icons = []
        for icon in required_icons:
            if not ResourceManager.get_icon_path(icon):
                missing_icons.append(icon)
        
        if missing_icons:
            print(f"Missing icons: {missing_icons}")
            return False
        else:
            print("All required icons found!")
            return True 