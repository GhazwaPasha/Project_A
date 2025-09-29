"""
Settings page for the accounting application.
This module provides application configuration and preferences management.
"""

import urllib.request
import tempfile
import os
from ..common import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QLineEdit, QComboBox, QDateEdit,
    ResponsiveHelper, Qt
)
from ..components.widgets import PageHeader
from ..components.styles import ModernStyles, GlassmorphismHelper
from ..components.mica_effect import MicaEffect
from ..components.font_manager import font_manager


class SettingsPage(QWidget):
    """Settings page for application configuration and preferences."""
    
    def __init__(self, system, auth_manager=None, session_manager=None, parent=None):
        super().__init__(parent)
        self.system = system
        self.auth_manager = auth_manager
        self.session_manager = session_manager
        self._setup_ui()
        self._apply_styling()
        
    def _apply_styling(self):
        """Apply beautiful glassmorphism styling to the settings page."""
        MicaEffect.apply_mica(self, dark_mode=True)
        GlassmorphismHelper.apply_main_container_effect(self)
        self.setStyleSheet(ModernStyles.get_complete_stylesheet())
    def _setup_ui(self):
        """Setup the settings page UI."""
        # Main layout with responsive margins
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create scroll area for settings content
        from PyQt6.QtWidgets import QScrollArea
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        
        # Style the scroll area
        scroll_area.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollArea > QWidget > QWidget {
                background: transparent;
            }
            QScrollBar:vertical {
                background: rgba(255, 255, 255, 0.1);
                width: 12px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.2);
                min-height: 20px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(255, 255, 255, 0.3);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
        
        # Create content widget to hold all settings
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        
        responsive_margin = ResponsiveHelper.scale_size(32, 24, 48)
        content_layout.setContentsMargins(responsive_margin, 0,  # Remove top margin for seamless flow
                                         responsive_margin, responsive_margin)
        content_layout.setSpacing(16)  # Standardized spacing
        
        # Page header
        header = PageHeader("Settings", "Application configuration and preferences")
        content_layout.addWidget(header)
        
        # Settings sections
        self._create_general_settings(content_layout)
        self._create_appearance_settings(content_layout)
        self._create_accounting_settings(content_layout)
        self._create_organization_settings(content_layout)
        
        content_layout.addStretch()
          # Style the scroll area
        scroll_area.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollArea > QWidget > QWidget {
                background: transparent;
            }
            QScrollBar:vertical {
                background: rgba(255, 255, 255, 0.1);
                width: 12px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.2);
                min-height: 20px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(255, 255, 255, 0.3);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
        
        # Set the content widget to the scroll area and add to main layout
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)
        
    def _create_general_settings(self, main_layout):
        """Create general settings section."""
        # Section title
        general_title = QLabel("General Settings")
        general_title.setStyleSheet(f"""
            QLabel {{
                color: white;
                font-size: {ResponsiveHelper.scale_size(18, 16, 20)}px;
                font-weight: 600;
                background: transparent;
                margin: {ResponsiveHelper.scale_size(16, 12, 20)}px 0px {ResponsiveHelper.scale_size(12, 8, 16)}px 0px;
            }}
        """)
        main_layout.addWidget(general_title)
        
        # Settings container
        settings_frame = QFrame()
        settings_frame.setStyleSheet(f"""
            QFrame {{
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: {ResponsiveHelper.scale_size(12, 8, 16)}px;
                padding: {ResponsiveHelper.scale_size(20, 16, 24)}px;
            }}
        """)
        settings_layout = QVBoxLayout(settings_frame)
        
        # Currency setting
        currency_layout = QHBoxLayout()
        currency_label = QLabel("Default Currency:")
        currency_label.setStyleSheet(f"""
            QLabel {{
                color: rgba(255, 255, 255, 0.9);
                font-size: {ResponsiveHelper.scale_size(14, 12, 16)}px;
                background: transparent;
            }}
        """)
        
        self.currency_combo = QComboBox()
        self.currency_combo.addItems([
            "USD ($)", "EUR (€)", "GBP (£)", "JPY (¥)", "CAD (C$)", 
            "AUD (A$)", "CHF (CHF)", "CNY (¥)", "INR (₹)", "PKR (Rs)", 
            "SAR (ر.س)", "AED (د.إ)", "KWD (د.ك)", "QAR (ر.ق)"
        ])
        self.currency_combo.setStyleSheet(ModernStyles.get_input_style())
        
        currency_layout.addWidget(currency_label)
        currency_layout.addWidget(self.currency_combo)
        currency_layout.addStretch()
        settings_layout.addLayout(currency_layout)
        
        # Date format setting
        date_layout = QHBoxLayout()
        date_label = QLabel("Date Format:")
        date_label.setStyleSheet(f"""
            QLabel {{
                color: rgba(255, 255, 255, 0.9);
                font-size: {ResponsiveHelper.scale_size(14, 12, 16)}px;
                background: transparent;
            }}
        """)
        
        self.date_combo = QComboBox()
        self.date_combo.addItems(["MM/DD/YYYY", "DD/MM/YYYY", "YYYY-MM-DD"])
        self.date_combo.setStyleSheet(ModernStyles.get_input_style())
        
        date_layout.addWidget(date_label)
        date_layout.addWidget(self.date_combo)
        date_layout.addStretch()
        settings_layout.addLayout(date_layout)
        
        main_layout.addWidget(settings_frame)
        
    def _create_appearance_settings(self, main_layout):
        """Create appearance settings section."""
        # Section title
        appearance_title = QLabel("Appearance")
        appearance_title.setStyleSheet(f"""
            QLabel {{
                color: white;
                font-size: {ResponsiveHelper.scale_size(18, 16, 20)}px;
                font-weight: 600;
                background: transparent;
                margin: {ResponsiveHelper.scale_size(16, 12, 20)}px 0px {ResponsiveHelper.scale_size(12, 8, 16)}px 0px;
            }}
        """)
        main_layout.addWidget(appearance_title)
        
        # Appearance container
        appearance_frame = QFrame()
        appearance_frame.setStyleSheet(f"""
            QFrame {{
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: {ResponsiveHelper.scale_size(12, 8, 16)}px;
                padding: {ResponsiveHelper.scale_size(20, 16, 24)}px;
            }}
        """)
        appearance_layout = QVBoxLayout(appearance_frame)
        
        # Theme setting
        theme_layout = QHBoxLayout()
        theme_label = QLabel("Theme:")
        theme_label.setStyleSheet(f"""
            QLabel {{
                color: rgba(255, 255, 255, 0.9);
                font-size: {ResponsiveHelper.scale_size(14, 12, 16)}px;
                background: transparent;
            }}
        """)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark (Mica)", "Light", "Auto"])
        self.theme_combo.setStyleSheet(ModernStyles.get_input_style())
        
        theme_layout.addWidget(theme_label)
        theme_layout.addWidget(self.theme_combo)
        theme_layout.addStretch()
        appearance_layout.addLayout(theme_layout)
        
        # Font family setting
        font_family_layout = QHBoxLayout()
        font_family_label = QLabel("Font Family:")
        font_family_label.setStyleSheet(f"""
            QLabel {{
                color: rgba(255, 255, 255, 0.9);
                font-size: {ResponsiveHelper.scale_size(14, 12, 16)}px;
                background: transparent;
            }}
        """)
        self.font_family_combo = QComboBox()
        # Add available font families
        available_fonts = font_manager.get_available_font_families()
        self.font_family_combo.addItems(available_fonts)
        
        # Set current font family
        current_font = font_manager.get_font_family()
        if current_font in available_fonts:
            self.font_family_combo.setCurrentText(current_font)
        
        self.font_family_combo.setStyleSheet(ModernStyles.get_input_style())
        
        font_family_layout.addWidget(font_family_label)
        font_family_layout.addWidget(self.font_family_combo)
        font_family_layout.addStretch()
        appearance_layout.addLayout(font_family_layout)
        
        # Font scale slider layout
        font_scale_layout = QHBoxLayout()
        font_scale_label = QLabel("Font Size:")
        font_scale_label.setStyleSheet(f"""
            QLabel {{
                color: rgba(255, 255, 255, 0.9);
                font-size: {ResponsiveHelper.scale_size(14, 12, 16)}px;
                background: transparent;
            }}
        """)
        
        self.font_scale_combo = QComboBox()
        self.font_scale_combo.addItems(["Small (80%)", "Normal (100%)", "Large (120%)", "Extra Large (150%)"])
        
        # Set current font scale
        current_scale = font_manager.get_font_scale()
        if current_scale <= 0.8:
            self.font_scale_combo.setCurrentIndex(0)
        elif current_scale <= 1.0:
            self.font_scale_combo.setCurrentIndex(1)
        elif current_scale <= 1.2:
            self.font_scale_combo.setCurrentIndex(2)
        else:
            self.font_scale_combo.setCurrentIndex(3)
            
        self.font_scale_combo.setStyleSheet(ModernStyles.get_input_style())
        
        font_scale_layout.addWidget(font_scale_label)
        font_scale_layout.addWidget(self.font_scale_combo)
        font_scale_layout.addStretch()
        appearance_layout.addLayout(font_scale_layout)
        
        # Custom fonts button
        custom_fonts_layout = QHBoxLayout()
        custom_fonts_layout.addStretch()
        
        self.custom_fonts_btn = QPushButton("Import Custom Fonts")
        self.custom_fonts_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.15);
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 8px;
                padding: 8px 16px;
                color: white;
                font-size: 13px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.25);
            }
        """)
        self.custom_fonts_btn.clicked.connect(self._import_custom_fonts)
        custom_fonts_layout.addWidget(self.custom_fonts_btn)
        appearance_layout.addLayout(custom_fonts_layout)
        
        main_layout.addWidget(appearance_frame)
        
    def _create_accounting_settings(self, main_layout):
        """Create accounting settings section."""
        # Section title
        accounting_title = QLabel("Accounting Preferences")
        accounting_title.setStyleSheet(f"""
            QLabel {{
                color: white;
                font-size: {ResponsiveHelper.scale_size(18, 16, 20)}px;
                font-weight: 600;
                background: transparent;
                margin: {ResponsiveHelper.scale_size(16, 12, 20)}px 0px {ResponsiveHelper.scale_size(12, 8, 16)}px 0px;
            }}
        """)
        main_layout.addWidget(accounting_title)
        
        # Accounting container
        accounting_frame = QFrame()
        accounting_frame.setStyleSheet(f"""
            QFrame {{
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: {ResponsiveHelper.scale_size(12, 8, 16)}px;
                padding: {ResponsiveHelper.scale_size(20, 16, 24)}px;
            }}
        """)
        accounting_layout = QVBoxLayout(accounting_frame)
        
        # Fiscal year setting
        fiscal_layout = QHBoxLayout()
        fiscal_label = QLabel("Fiscal Year Start:")
        fiscal_label.setStyleSheet(f"""
            QLabel {{
                color: rgba(255, 255, 255, 0.9);
                font-size: {ResponsiveHelper.scale_size(14, 12, 16)}px;
                background: transparent;
            }}
        """)
        
        self.fiscal_combo = QComboBox()
        self.fiscal_combo.addItems(["January", "April", "July", "October"])
        self.fiscal_combo.setStyleSheet(ModernStyles.get_input_style())
        
        fiscal_layout.addWidget(fiscal_label)
        fiscal_layout.addWidget(self.fiscal_combo)
        fiscal_layout.addStretch()
        accounting_layout.addLayout(fiscal_layout)
          # Save button section
        save_layout = QHBoxLayout()
        save_layout.addStretch()
        
        save_btn = QPushButton("Save Settings")
        save_btn.setStyleSheet(ModernStyles.get_button_style())
        save_btn.clicked.connect(self._save_settings)
        save_layout.addWidget(save_btn)
        
        # Reset button
        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.setStyleSheet("""
            QPushButton {
                background: rgba(244, 67, 54, 0.8);
                border: 1px solid rgba(244, 67, 54, 0.6);
                border-radius: 8px;
                padding: 12px 24px;
                color: white;
                font-size: 14px;
                font-weight: 600;
                min-width: 120px;
            }
            QPushButton:hover {
                background: rgba(244, 67, 54, 1.0);
                border-color: rgba(244, 67, 54, 0.8);
            }
            QPushButton:pressed {
                background: rgba(211, 47, 47, 1.0);
            }
        """)
        reset_btn.clicked.connect(self._reset_settings)
        save_layout.addWidget(reset_btn)
        
        accounting_layout.addLayout(save_layout)
        
        main_layout.addWidget(accounting_frame)
        
    def _create_organization_settings(self, main_layout):
        """Create organization management section."""
        # Only show this section if user is authenticated
        if not self.auth_manager or not self.session_manager:
            return
            
        # Section title
        org_title = QLabel("Organization Management")
        org_title.setStyleSheet(f"""
            QLabel {{
                color: white;
                font-size: {ResponsiveHelper.scale_size(18, 16, 20)}px;
                font-weight: 600;
                background: transparent;
                margin: {ResponsiveHelper.scale_size(16, 12, 20)}px 0px {ResponsiveHelper.scale_size(12, 8, 16)}px 0px;
            }}
        """)
        main_layout.addWidget(org_title)
        
        # Organization container
        org_frame = QFrame()
        org_frame.setStyleSheet(f"""
            QFrame {{
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: {ResponsiveHelper.scale_size(12, 8, 16)}px;
                padding: {ResponsiveHelper.scale_size(20, 16, 24)}px;
            }}
        """)
        org_layout = QVBoxLayout(org_frame)
        
        # Current organization info
        current_org = self.session_manager.get_current_organization()
        if current_org:
            org_name = current_org.get('name', 'Unknown')
            org_type = self.session_manager.get_current_organization_type()
            user_role = self.session_manager.get_current_user_role()
            
            info_text = f"""
            <div style='color: rgba(255, 255, 255, 0.9); font-size: 14px;'>
                <strong>Current Organization:</strong> {org_name}<br>
                <strong>Type:</strong> {org_type.title()}<br>
                <strong>Your Role:</strong> {user_role.replace('_', ' ').title()}
            </div>
            """
            
            info_label = QLabel(info_text)
            info_label.setWordWrap(True)
            info_label.setStyleSheet("""
                QLabel {
                    background: rgba(255, 255, 255, 0.05);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 8px;
                    padding: 12px;
                    margin-bottom: 16px;
                }
            """)
            org_layout.addWidget(info_label)
        
        # Create organization button
        create_org_layout = QHBoxLayout()
        create_org_layout.addStretch()
        
        self.create_org_btn = QPushButton("Create New Organization")
        self.create_org_btn.setStyleSheet("""
            QPushButton {
                background: rgba(100, 150, 255, 0.8);
                border: 1px solid rgba(100, 150, 255, 0.6);
                border-radius: 8px;
                padding: 12px 24px;
                color: white;
                font-size: 14px;
                font-weight: 600;
                min-width: 180px;
            }
            QPushButton:hover {
                background: rgba(100, 150, 255, 1.0);
                border-color: rgba(100, 150, 255, 0.8);
            }
            QPushButton:pressed {
                background: rgba(80, 120, 200, 1.0);
            }
        """)
        self.create_org_btn.clicked.connect(self._show_create_organization_dialog)
        create_org_layout.addWidget(self.create_org_btn)
        org_layout.addLayout(create_org_layout)
        
        # Description
        desc_label = QLabel(
            "Create a new multi-user organization for team collaboration. "
            "You'll be set as the organization owner and can invite team members."
        )
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.7);
                font-size: 13px;
                background: transparent;
                margin-top: 12px;
            }
        """)
        org_layout.addWidget(desc_label)
        
        main_layout.addWidget(org_frame)
        
    def _show_create_organization_dialog(self):
        """Show the create organization dialog"""
        if not self.auth_manager:
            return
            
        from ..components.dialogs import CreateOrganizationDialog
        dialog = CreateOrganizationDialog(self.auth_manager, self)
        
        if dialog.exec() == dialog.DialogCode.Accepted:
            # Refresh the session manager to get updated organizations
            if self.session_manager:
                # Refresh organizations list
                organizations = self.auth_manager.get_user_organizations()
                if organizations:
                    # Update session manager with new organizations
                    self.session_manager.refresh_organizations(organizations)
                    
                    # Refresh workspace switcher in main window
                    if hasattr(self.window(), 'refresh_workspace_switcher'):
                        self.window().refresh_workspace_switcher()
                    
                    # Show success message
                    from PyQt6.QtWidgets import QMessageBox
                    QMessageBox.information(
                        self,
                        "Organization Created",
                        "Your new organization has been created successfully!\n\n"
                        "You can now switch to it using the workspace switcher in the bottom bar."
                    )
        
        # Load current settings
        self._load_current_settings()
        
    def _load_current_settings(self):
        """Load current settings into the form."""
        # Load currency setting from main window if available
        main_window = self.window()
        if hasattr(main_window, 'currency_symbol'):
            current_currency = main_window.currency_symbol
            # Set currency combo based on symbol - updated mapping for all currencies
            currency_map = {
                "$": 0, "€": 1, "£": 2, "¥": 3, "C$": 4, "A$": 5, 
                "CHF": 6, "₹": 8, "Rs": 9, "ر.س": 10, "د.إ": 11, 
                "د.ك": 12, "ر.ق": 13
            }
            index = currency_map.get(current_currency, 0)
            self.currency_combo.setCurrentIndex(index)
        
        # Set other defaults
        self.date_combo.setCurrentIndex(0)  # MM/DD/YYYY
        self.theme_combo.setCurrentIndex(0)  # Dark (Mica)
        self.fiscal_combo.setCurrentIndex(0)  # January
    def _import_custom_fonts(self):
        """Import custom fonts from user-selected files or install developer fonts."""
        from PyQt6.QtWidgets import QFileDialog, QMessageBox, QDialog, QVBoxLayout, QPushButton, QLabel, QHBoxLayout
        
        # Create a custom dialog for font import options
        dialog = QDialog(self)
        dialog.setWindowTitle("Font Import Options")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        info_label = QLabel(
            "Choose to import custom fonts from files or install developer fonts (Cascadia Code and JetBrains Mono)"
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Developer fonts option
        dev_fonts_btn = QPushButton("Install Developer Fonts")
        dev_fonts_btn.setStyleSheet(ModernStyles.get_button_style())
        
        # Import from files option
        import_files_btn = QPushButton("Import Font Files")
        import_files_btn.setStyleSheet(ModernStyles.get_button_style())
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.15);
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 8px;
                padding: 8px 16px;
                color: white;
            }
        """)
        
        button_layout = QHBoxLayout()
        button_layout.addWidget(dev_fonts_btn)
        button_layout.addWidget(import_files_btn)
        layout.addLayout(button_layout)
        layout.addWidget(cancel_btn)
        
        file_paths = []
        install_dev_fonts = False
        
        def on_dev_fonts():
            nonlocal install_dev_fonts
            install_dev_fonts = True
            dialog.accept()
            
        def on_import_files():
            nonlocal file_paths
            file_paths_selected, _ = QFileDialog.getOpenFileNames(
                self,
                "Select Font Files",
                "",
                "Font Files (*.ttf *.otf)"
            )
            if file_paths_selected:
                file_paths = file_paths_selected
                dialog.accept()
                
        dev_fonts_btn.clicked.connect(on_dev_fonts)
        import_files_btn.clicked.connect(on_import_files)
        cancel_btn.clicked.connect(dialog.reject)
        
        dialog.exec()
        
        if not file_paths and not install_dev_fonts:
            return
            
        try:
            imported_fonts = []
            
            # Handle developer font installation
            if install_dev_fonts:
                from PyQt6.QtWidgets import QMessageBox
                
                # Install developer fonts from assets
                installed_fonts = font_manager.install_developer_fonts()
                
                if installed_fonts:
                    imported_fonts = installed_fonts
                    QMessageBox.information(
                        self,
                        "Developer Fonts Installed",
                        f"Successfully installed {len(installed_fonts)} developer font families:\n" +
                        "\n".join(f"- {font}" for font in installed_fonts)
                    )
                else:
                    QMessageBox.warning(
                        self,
                        "Installation Failed",
                        "Failed to install developer fonts. The font files may be missing or corrupted."
                    )
                    
                # Refresh the font family list
                self.font_family_combo.clear()
                available_fonts = font_manager.get_available_font_families()
                self.font_family_combo.addItems(available_fonts)
                return
            
            # Import user-selected font files
            # Get the fonts directory
            import os
            import shutil
            
            # Get the application directory path
            app_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            fonts_dir = os.path.join(app_path, 'assets', 'fonts')
            
            # Create fonts directory if it doesn't exist
            if not os.path.exists(fonts_dir):
                os.makedirs(fonts_dir)
            
            # Handle developer fonts installation
            if install_dev_fonts:
                # URLs for developer fonts (GitHub releases)
                dev_fonts = {
                    "cascadia_code": {
                        "url": "https://github.com/microsoft/cascadia-code/releases/download/v2111.01/CascadiaCode-2111.01.zip",
                        "filename": "CascadiaCode.zip",
                        "extract_files": ["ttf/CascadiaCode.ttf", "ttf/CascadiaCodePL.ttf"]
                    },
                    "jetbrains_mono": {
                        "url": "https://github.com/JetBrains/JetBrainsMono/releases/download/v2.304/JetBrainsMono-2.304.zip",
                        "filename": "JetBrainsMono.zip",
                        "extract_files": ["fonts/ttf/JetBrainsMono-Regular.ttf", "fonts/ttf/JetBrainsMono-Bold.ttf"]
                    }
                }
                
                # Show progress dialog
                from PyQt6.QtWidgets import QProgressDialog
                progress = QProgressDialog("Installing developer fonts...", "Cancel", 0, len(dev_fonts) * 2, self)
                progress.setWindowTitle("Installing Fonts")
                progress.setMinimumDuration(0)
                progress.setValue(0)
                progress.show()
                
                import zipfile
                import tempfile
                import time
                
                # Download and extract fonts
                for i, (font_name, font_info) in enumerate(dev_fonts.items()):
                    # Update progress
                    progress.setValue(i * 2)
                    if progress.wasCanceled():
                        break
                        
                    # Create a temporary directory for downloads
                    with tempfile.TemporaryDirectory() as temp_dir:
                        # Download the font zip file
                        zip_path = os.path.join(temp_dir, font_info["filename"])
                        try:
                            urllib.request.urlretrieve(font_info["url"], zip_path)
                        except Exception as e:
                            QMessageBox.warning(self, "Download Error", f"Failed to download {font_name}: {e}")
                            continue
                            
                        # Update progress
                        progress.setValue(i * 2 + 1)
                        if progress.wasCanceled():
                            break
                            
                        # Extract font files
                        try:
                            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                                for extract_file in font_info["extract_files"]:
                                    try:
                                        # Extract the file to the fonts directory
                                        font_filename = os.path.basename(extract_file)
                                        dest_path = os.path.join(fonts_dir, font_filename)
                                        
                                        # Extract the file from the zip to the fonts directory
                                        source = zip_ref.open(extract_file)
                                        with open(dest_path, 'wb') as target:
                                            target.write(source.read())
                                        
                                        imported_fonts.append(font_filename)
                                    except Exception as file_e:
                                        print(f"Failed to extract {extract_file}: {file_e}")
                        except Exception as zip_e:
                            QMessageBox.warning(self, "Extraction Error", f"Failed to extract {font_name}: {zip_e}")
                
                # Close progress
                progress.setValue(len(dev_fonts) * 2)
                
                QMessageBox.information(self, "Installation Complete", 
                                       f"Developer fonts have been installed.\n\n"
                                       f"Installed font files: {', '.join(imported_fonts)}")
            
            # Handle user-selected font files
            elif file_paths:
                # Copy fonts to the fonts directory
                for font_path in file_paths:
                    font_name = os.path.basename(font_path)
                    dest_path = os.path.join(fonts_dir, font_name)
                    
                    try:
                        shutil.copy2(font_path, dest_path)
                        imported_fonts.append(font_name)
                    except Exception as e:
                        QMessageBox.warning(self, "Import Error", f"Failed to import {font_name}: {e}")
            
            if imported_fonts:
                # Load the newly imported fonts
                loaded_families = font_manager.load_custom_fonts()
                
                # Add the new font families to the combo box
                current_items = [self.font_family_combo.itemText(i) for i in range(self.font_family_combo.count())]
                for family in loaded_families:
                    if family not in current_items:
                        self.font_family_combo.addItem(family)
                        
                # Refresh font family list
                self.font_family_combo.clear()
                available_fonts = font_manager.get_available_font_families()
                self.font_family_combo.addItems(available_fonts)
                
                # Show success message for user-imported fonts
                if file_paths and not install_dev_fonts:
                    QMessageBox.information(
                        self,
                        "Fonts Imported",
                        f"Successfully imported {len(imported_fonts)} fonts:\n" +
                        "\n".join(f"- {font}" for font in imported_fonts)
                    )
        
        except Exception as e:
            QMessageBox.warning(self, "Import Error", f"Failed to import fonts: {e}")
                
        except Exception as e:
            QMessageBox.warning(self, "Import Error", f"Failed to import fonts: {e}")
    
    def _save_settings(self):
        """Save settings to configuration."""
        try:
            # Get selected values
            currency_text = self.currency_combo.currentText()
            # Extract symbol from text like "PKR (Rs)" -> "Rs"
            if "(" in currency_text and ")" in currency_text:
                currency_symbol = currency_text.split("(")[1].split(")")[0]
            else:
                currency_symbol = "$"  # fallback
                
            date_format = self.date_combo.currentText()
            theme = self.theme_combo.currentText()
            fiscal_month = self.fiscal_combo.currentText()
            
            # Get font settings
            font_family = self.font_family_combo.currentText()
            font_scale_text = self.font_scale_combo.currentText()
            
            # Parse font scale from text
            if font_scale_text == "Small (80%)":
                font_scale = 0.8
            elif font_scale_text == "Normal (100%)":
                font_scale = 1.0
            elif font_scale_text == "Large (120%)":
                font_scale = 1.2
            else:  # "Extra Large (150%)"
                font_scale = 1.5
            
            # Apply font settings
            font_manager.set_font_family(font_family)
            font_manager.set_font_scale(font_scale)
            
            # Update ModernStyles to use the new font
            from ..components.styles import ModernStyles
            ModernStyles.set_font_family(font_family)
            
            # Update main window currency if available
            main_window = self.window()
            if hasattr(main_window, 'set_currency_symbol'):
                main_window.set_currency_symbol(currency_symbol)
            
            # Apply font changes to the application and refresh UI
            from PyQt6.QtWidgets import QApplication
            app = QApplication.instance()
            if app:
                font_manager.apply_font_to_application(app)
                
                # Force refresh the main window UI
                if hasattr(main_window, '_update_global_stylesheets'):
                    main_window._update_global_stylesheets()
            
            # Show success message
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(
                self, 
                "Settings Saved", 
                f"Settings have been saved successfully!\n\n"
                f"Currency: {currency_symbol}\n"
                f"Date Format: {date_format}\n"
                f"Theme: {theme}\n"
                f"Fiscal Year: {fiscal_month}\n"
                f"Font: {font_family}\n"
                f"Font Size: {font_scale_text}"
            )
            
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Error", f"Failed to save settings: {e}")
            
    def _reset_settings(self):
        """Reset settings to defaults."""
        from PyQt6.QtWidgets import QMessageBox
        
        reply = QMessageBox.question(
            self, "Reset Settings",
            "Are you sure you want to reset all settings to their default values?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Reset to defaults
            self.currency_combo.setCurrentIndex(0)  # USD
            self.date_combo.setCurrentIndex(0)  # MM/DD/YYYY
            self.theme_combo.setCurrentIndex(0)  # Dark
            self.fiscal_combo.setCurrentIndex(0)  # January
            
            # Reset font settings
            default_font = font_manager.FONT_FAMILIES['default']
            self.font_family_combo.setCurrentText(default_font)
            self.font_scale_combo.setCurrentIndex(1)  # Normal (100%)
            
            # Apply and save
            self._save_settings()
            
            QMessageBox.information(self, "Settings Reset", "All settings have been reset to defaults.")
    
    def refresh_data(self):
        """Refresh settings data when organization context changes."""
        try:
            print("🔄 Settings: Refreshing data due to organization context change...")
            self._load_current_settings()
        except Exception as e:
            print(f"Error refreshing settings data: {e}")
