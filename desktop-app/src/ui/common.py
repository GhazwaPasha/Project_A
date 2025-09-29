"""
Common imports and utilities for the UI modules.
This module centralizes common imports and provides utility classes.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit, QComboBox,
    QDateEdit, QCompleter, QDialog, QMessageBox, QFileDialog,
    QAbstractScrollArea, QApplication, QSizePolicy, QTabWidget,
    QCheckBox, QSpinBox, QButtonGroup, QScrollArea, QGridLayout,
    QSpacerItem, QTreeWidget, QTreeWidgetItem, QTextEdit, QSplitter,
    QGroupBox, QStackedWidget, QProgressBar, QDialogButtonBox
)
from PyQt6.QtCore import Qt, QDate, QStringListModel, QSize
from PyQt6.QtGui import QColor, QIcon, QFont, QPainter
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog

# ResponsiveHelper utility class
class ResponsiveHelper:
    """Utility class for responsive design elements."""
    
    @staticmethod
    def scale_size(base_size, min_size=None, max_size=None):
        """Scale size based on screen dimensions."""
        try:
            from PyQt6.QtGui import QScreen
            screen = QApplication.primaryScreen()
            if screen:
                screen_size = screen.size()
                width = screen_size.width()
                
                # Scale based on screen width
                if width <= 1366:  # Small screens
                    scale_factor = 0.8
                elif width >= 2560:  # Large screens
                    scale_factor = 1.2
                else:  # Medium screens
                    scale_factor = 1.0
                
                scaled_size = int(base_size * scale_factor)
                
                if min_size is not None and scaled_size < min_size:
                    return min_size
                if max_size is not None and scaled_size > max_size:
                    return max_size
                
                return scaled_size
        except:
            pass
        
        return base_size
    
    @staticmethod
    def get_responsive_margins():
        """Get responsive margins based on screen size."""
        return ResponsiveHelper.scale_size(24, 16, 32)
    
    @staticmethod
    def get_responsive_spacing():
        """Get responsive spacing based on screen size."""
        return ResponsiveHelper.scale_size(16, 12, 24)

# Common styling constants
MODERN_BUTTON_STYLE = """
    QPushButton {
        background: rgba(255, 255, 255, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 8px;
        color: white;
        font-weight: 500;
        padding: 8px 16px;
        min-height: 24px;
        outline: none;
    }
    QPushButton:hover {
        background: rgba(255, 255, 255, 0.12);
        border: 1px solid rgba(255, 255, 255, 0.2);
        outline: none;
    }
    QPushButton:pressed {
        background: rgba(255, 255, 255, 0.06);
        outline: none;
    }
    QPushButton:focus {
        background: rgba(255, 255, 255, 0.12);
        border: 1px solid rgba(255, 255, 255, 0.25);
        outline: none;
    }
    QPushButton:checked {
        background: rgba(255, 255, 255, 0.15);
        border: 1px solid rgba(255, 255, 255, 0.3);
        outline: none;
    }
"""

MODERN_TABLE_STYLE = """
    QTableWidget {
        background: rgba(30, 30, 30, 0.9);
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 12px;
        color: white;
        gridline-color: rgba(255, 255, 255, 0.08);
        selection-background-color: rgba(96, 165, 250, 0.3);
        alternate-background-color: rgba(255, 255, 255, 0.02);
    }
    QTableWidget::item {
        padding: 8px;
        border: none;
    }
    QTableWidget::item:selected {
        background: rgba(96, 165, 250, 0.3);
    }
    QHeaderView::section {
        background: rgba(255, 255, 255, 0.08);
        color: rgba(255, 255, 255, 0.9);
        padding: 8px;
        border: none;
        border-right: 1px solid rgba(255, 255, 255, 0.08);
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        font-weight: 600;
    }
"""

MODERN_FRAME_STYLE = """
    QFrame {
        background: rgba(255, 255, 255, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 12px;
    }
"""

# Global style to remove all outlines and ensure consistency
GLOBAL_NO_OUTLINE_STYLE = """
/* Remove all outlines from all widgets */
* {
    outline: none;
}

/* Remove outlines from labels */
QLabel {
    outline: none;
    border: none;
}

QLabel:focus {
    outline: none;
    border: none;
}

/* Specific widget styling to ensure no blue outlines */
QPushButton:focus {
    outline: none;
    border: 1px solid rgba(255, 255, 255, 0.25);
}

QComboBox:focus {
    outline: none;
    border: 1px solid rgba(255, 255, 255, 0.25);
}

QLineEdit:focus {
    outline: none;
    border: 1px solid rgba(255, 255, 255, 0.25);
}

QDateEdit:focus {
    outline: none;
    border: 1px solid rgba(255, 255, 255, 0.25);
}

QTableWidget:focus {
    outline: none;
    border: 1px solid rgba(255, 255, 255, 0.12);
}

QSpinBox:focus {
    outline: none;
    border: 1px solid rgba(255, 255, 255, 0.25);
}

QTextEdit:focus {
    outline: none;
    border: 1px solid rgba(255, 255, 255, 0.25);
}

/* Remove system default button focus styling */
QPushButton:default {
    border: 1px solid rgba(255, 255, 255, 0.12);
    outline: none;
}
"""
