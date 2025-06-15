"""
Settings page for the accounting application.
This module provides application configuration and preferences management.
"""

from ..common import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QLineEdit, QComboBox, QDateEdit,
    ResponsiveHelper, Qt
)
from ..components.widgets import PageHeader
from ..components.styles import ModernStyles, GlassmorphismHelper
from ..components.mica_effect import MicaEffect


class SettingsPage(QWidget):
    """Settings page for application configuration and preferences."""
    
    def __init__(self, system, parent=None):
        super().__init__(parent)
        self.system = system
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
        responsive_margin = ResponsiveHelper.scale_size(32, 24, 48)
        main_layout.setContentsMargins(responsive_margin, responsive_margin, 
                                     responsive_margin, responsive_margin)
        main_layout.setSpacing(ResponsiveHelper.scale_size(32, 24, 48))
          # Page header
        header = PageHeader("Settings", "Application configuration and preferences")
        main_layout.addWidget(header)
        
        # Settings sections
        self._create_general_settings(main_layout)
        self._create_appearance_settings(main_layout)
        self._create_accounting_settings(main_layout)
        
        main_layout.addStretch()
        
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
        self.currency_combo.addItems(["USD ($)", "EUR (€)", "GBP (£)", "CAD (C$)", "AUD (A$)"])
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
        
        # Load current settings
        self._load_current_settings()
        
    def _load_current_settings(self):
        """Load current settings into the form."""
        # Load currency setting from main window if available
        main_window = self.window()
        if hasattr(main_window, 'currency_symbol'):
            current_currency = main_window.currency_symbol
            # Set currency combo based on symbol
            currency_map = {"$": 0, "€": 1, "£": 2, "C$": 3, "A$": 4}
            index = currency_map.get(current_currency, 0)
            self.currency_combo.setCurrentIndex(index)
        
        # Set other defaults
        self.date_combo.setCurrentIndex(0)  # MM/DD/YYYY
        self.theme_combo.setCurrentIndex(0)  # Dark (Mica)
        self.fiscal_combo.setCurrentIndex(0)  # January
        
    def _save_settings(self):
        """Save settings to configuration."""
        try:
            # Get selected values
            currency_text = self.currency_combo.currentText()
            currency_symbol = currency_text.split("(")[1].split(")")[0]  # Extract symbol
            date_format = self.date_combo.currentText()
            theme = self.theme_combo.currentText()
            fiscal_month = self.fiscal_combo.currentText()
            
            # Update main window currency if available
            main_window = self.window()
            if hasattr(main_window, 'currency_symbol'):
                main_window.currency_symbol = currency_symbol
                # Refresh dashboard to show new currency
                if hasattr(main_window, 'refresh_all_pages'):
                    main_window.refresh_all_pages()
            
            # Show success message
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(
                self, 
                "Settings Saved", 
                f"Settings have been saved successfully!\n\n"
                f"Currency: {currency_symbol}\n"
                f"Date Format: {date_format}\n"
                f"Theme: {theme}\n"
                f"Fiscal Year: {fiscal_month}"
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
            
            # Apply and save
            self._save_settings()
            
            QMessageBox.information(self, "Settings Reset", "All settings have been reset to defaults.")
