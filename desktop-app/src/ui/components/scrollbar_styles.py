"""
Shared scrollbar styles for consistent UI design across the application.
This module provides the modern scrollbar styling used in Charts of Accounts.
"""

from ..pages.dashboard import ResponsiveHelper

class ModernScrollbarStyles:
    """Modern scrollbar styles for consistent UI design."""
    
    @staticmethod
    def get_vertical_scrollbar_style():
        """
        Get the modern vertical scrollbar style used in Charts of Accounts.
        
        Returns:
            str: CSS stylesheet for vertical scrollbars
        """
        return """
            QScrollBar:vertical {
                width: 12px;
                background: transparent;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.2);
                border-radius: 6px;
                min-height: 40px;
                margin: 2px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(255, 255, 255, 0.3);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
            }
            QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical,
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: transparent;
            }
        """
    
    @staticmethod
    def get_horizontal_scrollbar_style():
        """
        Get the modern horizontal scrollbar style matching the vertical design.
        
        Returns:
            str: CSS stylesheet for horizontal scrollbars
        """
        return """
            QScrollBar:horizontal {
                height: 12px;
                background: transparent;
                margin: 0;
            }
            QScrollBar::handle:horizontal {
                background: rgba(255, 255, 255, 0.2);
                border-radius: 6px;
                min-width: 40px;
                margin: 2px;
            }
            QScrollBar::handle:horizontal:hover {
                background: rgba(255, 255, 255, 0.3);
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0;
            }
            QScrollBar::left-arrow:horizontal, QScrollBar::right-arrow:horizontal,
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: transparent;
            }
        """
    
    @staticmethod
    def get_combined_scrollbar_style():
        """
        Get both vertical and horizontal scrollbar styles combined.
        
        Returns:
            str: CSS stylesheet for both scrollbar orientations
        """
        return (
            ModernScrollbarStyles.get_vertical_scrollbar_style() + 
            ModernScrollbarStyles.get_horizontal_scrollbar_style()
        )
    
    @staticmethod
    def apply_to_widget(widget):
        """
        Apply the modern scrollbar style to a widget.
        
        Args:
            widget: Qt widget to apply scrollbar styling to
        """
        current_style = widget.styleSheet()
        scrollbar_style = ModernScrollbarStyles.get_combined_scrollbar_style()
        
        # Combine with existing styles if any
        if current_style:
            widget.setStyleSheet(current_style + "\n" + scrollbar_style)
        else:
            widget.setStyleSheet(scrollbar_style)
    
    @staticmethod
    def get_responsive_scrollbar_style():
        """
        Get responsive scrollbar style that adapts to screen size.
        
        Returns:
            str: CSS stylesheet with responsive values
        """
        scrollbar_width = ResponsiveHelper.scale_size(12, 10, 14)
        handle_radius = ResponsiveHelper.scale_size(6, 5, 7)
        handle_min_height = ResponsiveHelper.scale_size(40, 35, 45)
        handle_margin = ResponsiveHelper.scale_size(2, 1, 3)
        
        return f"""
            QScrollBar:vertical {{
                width: {scrollbar_width}px;
                background: transparent;
                margin: 0;
            }}
            QScrollBar::handle:vertical {{
                background: rgba(255, 255, 255, 0.2);
                border-radius: {handle_radius}px;
                min-height: {handle_min_height}px;
                margin: {handle_margin}px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: rgba(255, 255, 255, 0.3);
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
            }}
            QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical,
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: transparent;
            }}
            QScrollBar:horizontal {{
                height: {scrollbar_width}px;
                background: transparent;
                margin: 0;
            }}
            QScrollBar::handle:horizontal {{
                background: rgba(255, 255, 255, 0.2);
                border-radius: {handle_radius}px;
                min-width: {handle_min_height}px;
                margin: {handle_margin}px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background: rgba(255, 255, 255, 0.3);
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width: 0;
            }}
            QScrollBar::left-arrow:horizontal, QScrollBar::right-arrow:horizontal,
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
                background: transparent;
            }}
        """
