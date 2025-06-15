"""
Enhanced styling module for the accounting application.
Provides modern glassmorphism, Mica effects, and beautiful visual styling.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPalette
from ..common import ResponsiveHelper


class ModernStyles:
    """Modern styling constants and utilities for the application."""
    
    # Color scheme
    COLORS = {
        'primary': '#2196F3',
        'secondary': '#1976D2', 
        'success': '#4CAF50',
        'warning': '#FF9800',
        'error': '#F44336',
        'info': '#00BCD4',
        'background': 'rgba(16, 16, 16, 0.95)',
        'surface': 'rgba(32, 32, 32, 0.85)',
        'surface_variant': 'rgba(48, 48, 48, 0.75)',
        'text_primary': '#FFFFFF',
        'text_secondary': 'rgba(255, 255, 255, 0.7)',
        'border': 'rgba(255, 255, 255, 0.2)',
        'shadow': 'rgba(0, 0, 0, 0.3)',
        'accent_gradient': 'qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #2196F3, stop:1 #1976D2)',
        'glass': 'rgba(255, 255, 255, 0.08)',
        'glass_border': 'rgba(255, 255, 255, 0.15)'
    }
    
    @staticmethod
    def get_page_style():
        """Get the main page styling with glassmorphism effect."""
        return f"""
            QWidget {{
                background: transparent;
                color: {ModernStyles.COLORS['text_primary']};
                font-family: 'Segoe UI', Arial, sans-serif;
            }}
            
            /* Main container with glass effect */
            QWidget[class="main-container"] {{                background: {ModernStyles.COLORS['glass']};
                border: 1px solid {ModernStyles.COLORS['glass_border']};
                border-radius: {ResponsiveHelper.scale_size(16, 12, 20)}px;
            }}        """
    
    @staticmethod
    def get_card_style(accent_color=None):
        """Get card styling with glassmorphism effect."""
        accent = accent_color or ModernStyles.COLORS['primary']
        return f"""
            QFrame[class="glass-card"] {{
                background: {ModernStyles.COLORS['glass']};
                border: 1px solid {ModernStyles.COLORS['glass_border']};
                border-radius: {ResponsiveHelper.scale_size(12, 8, 16)}px;
                padding: {ResponsiveHelper.scale_size(20, 16, 24)}px;
            }}
              QFrame[class="glass-card"]:hover {{
                background: rgba(255, 255, 255, 0.12);
                border: 1px solid rgba(255, 255, 255, 0.25);
            }}
            
            QFrame[class="metric-card"] {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                           stop:0 rgba(255, 255, 255, 0.1), 
                           stop:1 rgba(255, 255, 255, 0.05));
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: {ResponsiveHelper.scale_size(16, 12, 20)}px;
                padding: {ResponsiveHelper.scale_size(24, 18, 32)}px;
                min-height: {ResponsiveHelper.scale_size(160, 140, 180)}px;
                max-height: {ResponsiveHelper.scale_size(200, 180, 220)}px;
            }}
            
            QFrame[class="metric-card"]:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                           stop:0 rgba(255, 255, 255, 0.15), 
                           stop:1 rgba(255, 255, 255, 0.08));
                border: 1px solid rgba(255, 255, 255, 0.25);
            }}
        """
    
    @staticmethod
    def get_button_style():
        """Get modern button styling with glassmorphism."""
        return f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                           stop:0 {ModernStyles.COLORS['primary']}, 
                           stop:1 {ModernStyles.COLORS['secondary']});
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: {ResponsiveHelper.scale_size(8, 6, 10)}px;
                padding: {ResponsiveHelper.scale_size(12, 8, 16)}px {ResponsiveHelper.scale_size(24, 18, 32)}px;
                font-size: {ResponsiveHelper.scale_size(14, 12, 16)}px;
                font-weight: 500;
            }}
            
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                           stop:0 rgba(33, 150, 243, 0.9), 
                           stop:1 rgba(25, 118, 210, 0.9));
                border: 1px solid rgba(255, 255, 255, 0.5);
            }}
            
            QPushButton:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                           stop:0 rgba(21, 101, 192, 0.9), 
                           stop:1 rgba(13, 71, 161, 0.9));
            }}
            
            QPushButton[accent="success"] {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                           stop:0 {ModernStyles.COLORS['success']}, 
                           stop:1 rgba(56, 142, 60, 1));
            }}
            
            QPushButton[accent="warning"] {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                           stop:0 {ModernStyles.COLORS['warning']}, 
                           stop:1 rgba(239, 108, 0, 1));
            }}
            
            QPushButton[accent="error"] {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                           stop:0 {ModernStyles.COLORS['error']},                           stop:1 rgba(211, 47, 47, 1));
            }}
        """
    
    @staticmethod
    def get_table_style():
        """Get modern table styling with glassmorphism."""
        return f"""
            QTableWidget {{
                background: rgba(255, 255, 255, 0.05);
                alternate-background-color: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: {ResponsiveHelper.scale_size(12, 8, 16)}px;
                gridline-color: rgba(255, 255, 255, 0.1);
                color: {ModernStyles.COLORS['text_primary']};
                font-size: {ResponsiveHelper.scale_size(13, 11, 15)}px;
            }}
            
            QTableWidget::item {{
                padding: {ResponsiveHelper.scale_size(8, 6, 10)}px;
                border: none;
            }}
            
            QTableWidget::item:selected {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                           stop:0 rgba(33, 150, 243, 0.3), 
                           stop:1 rgba(25, 118, 210, 0.3));
                color: white;
            }}
            
            QHeaderView::section {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                           stop:0 rgba(255, 255, 255, 0.15), 
                           stop:1 rgba(255, 255, 255, 0.08));
                border: 1px solid rgba(255, 255, 255, 0.1);
                padding: {ResponsiveHelper.scale_size(10, 8, 12)}px;
                color: {ModernStyles.COLORS['text_primary']};
                font-weight: 600;
                font-size: {ResponsiveHelper.scale_size(12, 10, 14)}px;
            }}
            
            QScrollBar:vertical {{
                background: rgba(255, 255, 255, 0.1);
                width: {ResponsiveHelper.scale_size(12, 8, 16)}px;
                border-radius: {ResponsiveHelper.scale_size(6, 4, 8)}px;
            }}
            
            QScrollBar::handle:vertical {{
                background: rgba(255, 255, 255, 0.3);
                border-radius: {ResponsiveHelper.scale_size(6, 4, 8)}px;
                min-height: 20px;
            }}
              QScrollBar::handle:vertical:hover {{
                background: rgba(255, 255, 255, 0.5);
            }}
        """
    
    @staticmethod
    def get_input_style():
        """Get modern input field styling."""
        return f"""
            QLineEdit, QComboBox, QSpinBox, QDateEdit {{
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: {ResponsiveHelper.scale_size(8, 6, 10)}px;
                padding: {ResponsiveHelper.scale_size(8, 6, 10)}px {ResponsiveHelper.scale_size(12, 8, 16)}px;
                color: {ModernStyles.COLORS['text_primary']};
                font-size: {ResponsiveHelper.scale_size(13, 11, 15)}px;
            }}
            
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDateEdit:focus {{
                border: 1px solid {ModernStyles.COLORS['primary']};
                background: rgba(255, 255, 255, 0.12);
            }}
            
            QComboBox::drop-down {{
                border: none;
                width: {ResponsiveHelper.scale_size(20, 16, 24)}px;
            }}
            
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid {ModernStyles.COLORS['text_secondary']};
            }}
        """
    
    @staticmethod
    def get_header_style():
        """Get page header styling."""
        return f"""
            QLabel[class="page-title"] {{
                color: {ModernStyles.COLORS['text_primary']};
                font-size: {ResponsiveHelper.scale_size(32, 24, 40)}px;
                font-weight: 700;
                background: transparent;
                margin: 0px 0px {ResponsiveHelper.scale_size(8, 6, 10)}px 0px;
            }}
            
            QLabel[class="page-subtitle"] {{
                color: {ModernStyles.COLORS['text_secondary']};
                font-size: {ResponsiveHelper.scale_size(16, 14, 18)}px;
                font-weight: 400;
                background: transparent;
                margin: 0px 0px {ResponsiveHelper.scale_size(24, 18, 32)}px 0px;
            }}
            
            QLabel[class="section-title"] {{
                color: {ModernStyles.COLORS['text_primary']};
                font-size: {ResponsiveHelper.scale_size(20, 16, 24)}px;
                font-weight: 600;
                background: transparent;
                margin: {ResponsiveHelper.scale_size(16, 12, 20)}px 0px {ResponsiveHelper.scale_size(12, 8, 16)}px 0px;            }}        """
    
    @staticmethod
    def get_complete_stylesheet():
        """Get the complete application stylesheet."""
        return f"""
            {ModernStyles.get_page_style()}
            {ModernStyles.get_card_style()}
            {ModernStyles.get_button_style()}
            {ModernStyles.get_table_style()}
            {ModernStyles.get_input_style()}
            {ModernStyles.get_header_style()}
            
            /* Label styling - remove all outlines */
            QLabel {{
                outline: none;
                border: none;
            }}
            
            QLabel:focus {{
                outline: none;
                border: none;
            }}
            
            /* Tabs styling */
            QTabWidget::pane {{
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: {ResponsiveHelper.scale_size(12, 8, 16)}px;
            }}
            
            QTabBar::tab {{
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.15);
                padding: {ResponsiveHelper.scale_size(8, 6, 10)}px {ResponsiveHelper.scale_size(16, 12, 20)}px;
                margin-right: 2px;
                border-radius: {ResponsiveHelper.scale_size(8, 6, 10)}px;
                color: {ModernStyles.COLORS['text_secondary']};
            }}
            
            QTabBar::tab:selected {{
                background: {ModernStyles.COLORS['accent_gradient']};
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.3);
            }}
            
            QTabBar::tab:hover:!selected {{
                background: rgba(255, 255, 255, 0.12);
                color: {ModernStyles.COLORS['text_primary']};
            }}
        """


class GlassmorphismHelper:
    """Helper class for applying glassmorphism effects to widgets."""
    
    @staticmethod
    def apply_glass_effect(widget, blur_radius=20, opacity=0.08):
        """Apply glassmorphism effect to a widget."""
        widget.setProperty("class", "glass-card")
        widget.setStyleSheet(f"""            QFrame[class="glass-card"] {{
                background: rgba(255, 255, 255, {opacity});
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: {ResponsiveHelper.scale_size(12, 8, 16)}px;
            }}
        """)
    
    @staticmethod
    def apply_metric_card_effect(widget):
        """Apply special glassmorphism effect for metric cards."""
        widget.setProperty("class", "metric-card")
        widget.setStyleSheet(ModernStyles.get_card_style())
    
    @staticmethod
    def apply_main_container_effect(widget):
        """Apply glassmorphism effect to main page container."""
        widget.setProperty("class", "main-container")
        widget.setStyleSheet(ModernStyles.get_page_style())
