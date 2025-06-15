"""
Shared widget components for the accounting application.
This module contains reusable widget classes used across different pages.
"""

from ..common import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QLineEdit,
    ResponsiveHelper, MODERN_BUTTON_STYLE, MODERN_FRAME_STYLE, Qt, QColor
)
from PyQt6.QtWidgets import QGraphicsDropShadowEffect, QSizePolicy, QComboBox
from PyQt6.QtGui import QPixmap
from .styles import ModernStyles, GlassmorphismHelper


class MetricCard(QFrame):
    """Modern styled metric card widget for displaying financial data."""
    
    def __init__(self, title, value="", subtitle="", icon_path="", clickable=True, parent=None):
        super().__init__(parent)
        self.title = title
        self.value = value
        self.subtitle = subtitle
        self.icon_path = icon_path
        self.clickable = clickable
        
        self._setup_ui()
        self._apply_styling()
        
    def _setup_ui(self):
        """Setup the card UI with improved text visibility and sizing."""
        layout = QVBoxLayout(self)
        margins = ResponsiveHelper.scale_size(16, 12, 20)
        layout.setContentsMargins(margins, margins, margins, margins)
        layout.setSpacing(ResponsiveHelper.scale_size(8, 6, 12))
        
        # Header with icon and title
        header_layout = QHBoxLayout()
        header_layout.setSpacing(ResponsiveHelper.scale_size(8, 6, 12))
        
        # Icon (if provided)
        if self.icon_path:
            icon_label = QLabel()
            icon_label.setPixmap(QPixmap(self.icon_path).scaled(28, 28, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            header_layout.addWidget(icon_label)
          # Title with improved sizing and consistent height
        self.title_label = QLabel(self.title)
        self.title_label.setWordWrap(True)
        self.title_label.setFixedHeight(ResponsiveHelper.scale_size(32, 28, 40))  # Fixed height for alignment
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.title_label.setStyleSheet(f"""
            QLabel {{
                color: rgba(255, 255, 255, 0.8);
                font-size: {ResponsiveHelper.scale_size(13, 11, 16)}px;
                font-weight: 600;
                background: transparent;
                margin: 0px;
                padding: 0px;
            }}
        """)
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Value with improved sizing and visibility
        self.value_label = QLabel(self.value)
        self.value_label.setWordWrap(True)
        self.value_label.setStyleSheet(f"""
            QLabel {{
                color: white;
                font-size: {ResponsiveHelper.scale_size(22, 18, 28)}px;
                font-weight: 700;
                background: transparent;
                margin: {ResponsiveHelper.scale_size(4, 2, 6)}px 0;
                padding: 0px;
            }}
        """)
        self.value_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout.addWidget(self.value_label)
        
        # Subtitle/ticker with improved visibility
        self.subtitle_label = QLabel(self.subtitle)
        self.subtitle_label.setWordWrap(True)
        self.subtitle_label.setStyleSheet(f"""
            QLabel {{
                color: rgba(255, 255, 255, 0.7);
                font-size: {ResponsiveHelper.scale_size(11, 9, 13)}px;
                font-weight: 400;
                background: transparent;
                margin: 0px;
                padding: 0px;
            }}
        """)
        self.subtitle_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout.addWidget(self.subtitle_label)
        
        if not self.subtitle:
            self.subtitle_label.hide()
            
        layout.addStretch()
        
    def set_value(self, value, prefix=""):
        """Update the card's main value."""
        display_value = f"{prefix}{value}" if prefix else value
        self.value_label.setText(display_value)
        
    def set_subtitle(self, subtitle):
        """Update the card's subtitle and manage visibility."""
        self.subtitle_label.setText(subtitle)
        self.subtitle_label.setVisible(bool(subtitle))
        
    def set_ticker(self, text, color="#4CAF50"):
        """Update the trend indicator with improved styling for better visibility."""
        self.subtitle_label.setText(text)
        self.subtitle_label.setStyleSheet(f"""
            QLabel {{
                color: {color};
                font-size: {ResponsiveHelper.scale_size(12, 10, 14)}px;
                font-weight: 600;
                background: rgba(255, 255, 255, 0.05);
                border-radius: 4px;
                padding: 4px 8px;
            }}
        """)
        self.subtitle_label.setVisible(True)
        
    def _apply_styling(self):
        """Apply card styling with enhanced glassmorphism effects."""
        # Apply glassmorphism effect
        GlassmorphismHelper.apply_metric_card_effect(self)
        
        # Add drop shadow effect for depth
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(ResponsiveHelper.scale_size(25, 20, 35))
        shadow.setXOffset(0)
        shadow.setYOffset(ResponsiveHelper.scale_size(6, 4, 8))
        shadow.setColor(QColor(0, 0, 0, 120))
        self.setGraphicsEffect(shadow)
        
        # Set improved size policy and constraints for better text visibility
        self.setMinimumHeight(ResponsiveHelper.scale_size(140, 120, 160))
        self.setMaximumHeight(ResponsiveHelper.scale_size(220, 180, 260))
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)


class ActionCard(QFrame):
    """Action card widget for dashboard quick actions."""
    
    def __init__(self, title, description, icon_path="", accent_color="#0078D4", parent=None):
        super().__init__(parent)
        self.title = title
        self.description = description
        self.icon_path = icon_path
        self.accent_color = accent_color
        self.clicked = lambda: None  # Default no-op callback
        
        self._setup_ui()
        self._apply_styling()
        
    def _setup_ui(self):
        """Setup the action card UI."""
        layout = QVBoxLayout(self)
        margins = ResponsiveHelper.scale_size(24, 20, 32)
        layout.setContentsMargins(margins, margins, margins, margins)
        layout.setSpacing(ResponsiveHelper.scale_size(12, 8, 16))
        
        # Icon (if provided)
        if self.icon_path:
            icon_label = QLabel()
            # Set icon logic here if needed
            layout.addWidget(icon_label)
          # Title
        title_label = QLabel(self.title)
        title_label.setStyleSheet(f"""
            QLabel {{
                color: white;
                font-size: {ResponsiveHelper.scale_size(16, 14, 18)}px;
                font-weight: 600;
                background: transparent;
                border: none;
                outline: none;
                margin: 0px;
                padding: 0px;
            }}
        """)
        title_label.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        layout.addWidget(title_label)
        
        # Description
        desc_label = QLabel(self.description)
        desc_label.setStyleSheet(f"""
            QLabel {{
                color: rgba(255, 255, 255, 0.7);
                font-size: {ResponsiveHelper.scale_size(13, 11, 15)}px;
                font-weight: 400;
                background: transparent;
                border: none;
                outline: none;
                margin: 0px;
                padding: 0px;
                margin-top: {ResponsiveHelper.scale_size(4, 2, 6)}px;
            }}
        """)
        desc_label.setWordWrap(True)
        desc_label.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        layout.addWidget(desc_label)
        layout.addStretch()
        
    def _apply_styling(self):
        """Apply action card styling with modern glassmorphism and single accent color."""
        border_radius = ResponsiveHelper.scale_size(12, 10, 16)
        
        # Use accent color for consistent single-color theming
        accent_rgb = self._hex_to_rgb(self.accent_color)
        
        self.setStyleSheet(f"""
            QFrame {{
                background: rgba({accent_rgb[0]}, {accent_rgb[1]}, {accent_rgb[2]}, 0.1);
                border: 1px solid rgba({accent_rgb[0]}, {accent_rgb[1]}, {accent_rgb[2]}, 0.2);
                border-radius: {border_radius}px;
                margin: 4px;
            }}
            QFrame:hover {{
                background: rgba({accent_rgb[0]}, {accent_rgb[1]}, {accent_rgb[2]}, 0.15);
                border: 1px solid rgba({accent_rgb[0]}, {accent_rgb[1]}, {accent_rgb[2]}, 0.4);
            }}
            QFrame:pressed {{
                background: rgba({accent_rgb[0]}, {accent_rgb[1]}, {accent_rgb[2]}, 0.2);
                border: 1px solid rgba({accent_rgb[0]}, {accent_rgb[1]}, {accent_rgb[2]}, 0.5);
            }}
        """)
        
        # Set minimum height instead of fixed height to accommodate text
        self.setMinimumHeight(ResponsiveHelper.scale_size(140, 120, 160))
        self.setMaximumHeight(ResponsiveHelper.scale_size(200, 180, 220))
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Add drop shadow for better depth
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(ResponsiveHelper.scale_size(20, 15, 30))
        shadow.setXOffset(0)
        shadow.setYOffset(ResponsiveHelper.scale_size(4, 2, 6))
        shadow.setColor(QColor(0, 0, 0, 80))
        self.setGraphicsEffect(shadow)
    
    def _hex_to_rgb(self, hex_color):
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        
    def mousePressEvent(self, event):
        """Handle mouse press events."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked()
        super().mousePressEvent(event)


class PageHeader(QWidget):
    """Reusable page header widget."""
    
    def __init__(self, title, subtitle="", parent=None):
        super().__init__(parent)
        self.title = title
        self.subtitle = subtitle
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup the header UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(ResponsiveHelper.scale_size(8, 6, 12))
        
        # Title
        title_label = QLabel(self.title)
        title_label.setStyleSheet(f"""
            QLabel {{
                color: white;
                font-size: {ResponsiveHelper.scale_size(28, 22, 36)}px;
                font-weight: 700;
                background: transparent;
            }}
        """)
        layout.addWidget(title_label)
        
        # Subtitle (if provided)
        if self.subtitle:
            subtitle_label = QLabel(self.subtitle)
            subtitle_label.setStyleSheet(f"""
                QLabel {{
                    color: rgba(255, 255, 255, 0.7);
                    font-size: {ResponsiveHelper.scale_size(14, 12, 16)}px;
                    font-weight: 400;
                    background: transparent;
                }}
            """)
            layout.addWidget(subtitle_label)


class DateRangeSelector(QWidget):
    """Professional date range selector with quick filter buttons and custom range."""
    
    # Signal for compatibility with ledger
    from PyQt6.QtCore import pyqtSignal
    dateRangeChanged = pyqtSignal()
    
    def __init__(self, parent=None, callback=None):
        super().__init__(parent)
        self.callback = callback or (lambda: None)
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup the date range selector UI."""
        from ..common import QHBoxLayout, QLabel, QButtonGroup, QPushButton, QDateEdit, QDate
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(12)
        
        # Quick filters
        quick_label = QLabel("Quick Filter:")
        quick_label.setStyleSheet("color: rgba(255, 255, 255, 0.7); font-weight: 500; background: transparent; border: none;")
        layout.addWidget(quick_label)
        
        self.quick_buttons = QButtonGroup(self)
        quick_filters = ["This Month", "Last Month", "This Quarter", "This Year", "All Time"]
        
        for i, filter_name in enumerate(quick_filters):
            btn = QPushButton(filter_name)
            btn.setCheckable(True)
            btn.setStyleSheet("""
                QPushButton {
                    background: rgba(255, 255, 255, 0.1);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    color: white;
                    border-radius: 6px;
                    padding: 6px 12px;
                    font-weight: 500;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background: rgba(255, 255, 255, 0.2);
                    border-color: rgba(255, 255, 255, 0.3);
                }
                QPushButton:checked {
                    background: rgba(100, 181, 246, 0.3);
                    border-color: #64B5F6;
                    color: #64B5F6;
                }
            """)
            btn.clicked.connect(self._quick_filter_selected)
            self.quick_buttons.addButton(btn, i)
            layout.addWidget(btn)
            
        layout.addStretch()
        
        # Custom date range
        range_label = QLabel("Custom Range:")
        range_label.setStyleSheet("color: rgba(255, 255, 255, 0.7); font-weight: 500; background: transparent; border: none;")
        layout.addWidget(range_label)
        
        self.from_date = QDateEdit()
        self.from_date.setDate(QDate.currentDate().addDays(-30))
        self.from_date.setCalendarPopup(True)
        self.from_date.setStyleSheet("""
            QDateEdit {
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 6px;
                padding: 6px 8px;
                color: white;
                font-size: 12px;
            }
            QDateEdit:focus {
                border-color: #64B5F6;
                background: rgba(255, 255, 255, 0.15);
            }
        """)
        self.from_date.dateChanged.connect(self._on_date_changed)
        layout.addWidget(self.from_date)
        
        to_label = QLabel("to")
        to_label.setStyleSheet("color: rgba(255, 255, 255, 0.5); background: transparent; border: none;")
        layout.addWidget(to_label)
        
        self.to_date = QDateEdit()
        self.to_date.setDate(QDate.currentDate())
        self.to_date.setCalendarPopup(True)
        self.to_date.setStyleSheet(self.from_date.styleSheet())
        self.to_date.dateChanged.connect(self._on_date_changed)
        layout.addWidget(self.to_date)
          # Set default selection
        self.quick_buttons.button(0).setChecked(True)  # This Month
        
    def _on_date_changed(self):
        """Handle date changes - supports both callback and signal patterns."""
        self.callback()
        self.dateRangeChanged.emit()
        
    def _quick_filter_selected(self):
        """Handle quick filter selection."""
        from ..common import QDate
        
        button = self.sender()
        button_id = self.quick_buttons.id(button)
        
        today = QDate.currentDate()
        
        if button_id == 0:  # This Month
            self.from_date.setDate(QDate(today.year(), today.month(), 1))
            self.to_date.setDate(today)
        elif button_id == 1:  # Last Month
            last_month = today.addMonths(-1)
            self.from_date.setDate(QDate(last_month.year(), last_month.month(), 1))
            self.to_date.setDate(QDate(today.year(), today.month(), 1).addDays(-1))
        elif button_id == 2:  # This Quarter
            quarter = ((today.month() - 1) // 3) * 3 + 1
            self.from_date.setDate(QDate(today.year(), quarter, 1))
            self.to_date.setDate(today)
        elif button_id == 3:  # This Year
            self.from_date.setDate(QDate(today.year(), 1, 1))
            self.to_date.setDate(today)
        elif button_id == 4:  # All Time
            self.from_date.setDate(QDate(2020, 1, 1))
            self.to_date.setDate(today)
            
        self._on_date_changed()
        
    def get_date_range(self):
        """Get the selected date range."""
        return self.from_date.date(), self.to_date.date()


class ReportCard(QFrame):
    """A modern card widget for displaying report options."""
    
    def __init__(self, title, description, icon="📊", parent=None):
        super().__init__(parent)
        self.title = title
        self.description = description
        self.icon = icon
        self.clicked = None
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup the report card UI."""
        self.setObjectName("ReportCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            ResponsiveHelper.scale_size(20, 16, 28),
            ResponsiveHelper.scale_size(20, 16, 28),
            ResponsiveHelper.scale_size(20, 16, 28),
            ResponsiveHelper.scale_size(20, 16, 28)
        )
        layout.setSpacing(ResponsiveHelper.scale_size(12, 10, 16))
        
        # Icon
        icon_label = QLabel(self.icon)
        icon_label.setStyleSheet(f"""
            QLabel {{
                color: white;
                font-size: {ResponsiveHelper.scale_size(32, 24, 40)}px;
                background: transparent;
            }}
        """)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)
        
        # Title
        title_label = QLabel(self.title)
        title_label.setObjectName("ReportCardTitle")
        title_label.setStyleSheet(f"""
            QLabel#ReportCardTitle {{
                color: white;
                font-size: {ResponsiveHelper.scale_size(18, 16, 20)}px;
                font-weight: 600;
                background: transparent;
                margin-bottom: {ResponsiveHelper.scale_size(8, 6, 10)}px;
            }}
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Description
        desc_label = QLabel(self.description)
        desc_label.setStyleSheet(f"""
            QLabel {{
                color: rgba(255, 255, 255, 0.8);
                font-size: {ResponsiveHelper.scale_size(12, 10, 14)}px;
                background: transparent;
                text-align: center;
            }}
        """)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # Apply styling
        self.setStyleSheet("""
            QFrame#ReportCard {
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 16px;                margin: 4px;
            }
            QFrame#ReportCard:hover {
                background: rgba(255, 255, 255, 0.12);
                border-color: rgba(255, 255, 255, 0.2);
            }
        """)
        
    def mousePressEvent(self, event):
        """Handle mouse press events."""
        if event.button() == Qt.MouseButton.LeftButton and self.clicked:
            self.clicked()
        super().mousePressEvent(event)


class SettingsCard(QFrame):
    """A card widget for organizing settings sections."""
    
    def __init__(self, title, description, parent=None):
        super().__init__(parent)
        self.title = title
        self.description = description
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup the settings card UI."""
        self.setObjectName("SettingsCard")
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(
            ResponsiveHelper.scale_size(20, 16, 28),
            ResponsiveHelper.scale_size(20, 16, 28),
            ResponsiveHelper.scale_size(20, 16, 28),
            ResponsiveHelper.scale_size(20, 16, 28)
        )
        main_layout.setSpacing(ResponsiveHelper.scale_size(16, 12, 20))
        
        # Header section
        header_layout = QVBoxLayout()
        header_layout.setSpacing(ResponsiveHelper.scale_size(8, 6, 10))
        
        # Title
        title_label = QLabel(self.title)
        title_label.setStyleSheet(f"""
            QLabel {{
                color: white;
                font-size: {ResponsiveHelper.scale_size(18, 16, 20)}px;
                font-weight: 600;
                background: transparent;
            }}
        """)
        header_layout.addWidget(title_label)
        
        # Description
        desc_label = QLabel(self.description)
        desc_label.setStyleSheet(f"""
            QLabel {{
                color: rgba(255, 255, 255, 0.8);
                font-size: {ResponsiveHelper.scale_size(12, 10, 14)}px;
                background: transparent;
            }}
        """)
        header_layout.addWidget(desc_label)
        
        main_layout.addLayout(header_layout)
        
        # Content layout for child widgets
        self.content_layout = QVBoxLayout()
        self.content_layout.setSpacing(ResponsiveHelper.scale_size(12, 10, 16))
        main_layout.addLayout(self.content_layout)
        
        # Apply styling
        self.setStyleSheet("""
            QFrame#SettingsCard {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 12px;
                margin: 2px;
            }
            QLineEdit {
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                padding: 8px 12px;
                color: white;
                font-size: 14px;
            }
            QLineEdit:focus {
                background: rgba(255, 255, 255, 0.15);
                border-color: rgba(0, 120, 215, 0.6);
            }
            QComboBox {
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                padding: 8px 12px;
                color: white;
                font-size: 14px;
            }
            QComboBox:hover {
                background: rgba(255, 255, 255, 0.15);
                border-color: rgba(255, 255, 255, 0.3);
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox QAbstractItemView {
                background: rgba(32, 32, 32, 0.95);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                color: white;
                selection-background-color: rgba(0, 120, 215, 0.3);
            }
            QCheckBox {
                color: white;
                font-size: 14px;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 2px solid rgba(255, 255, 255, 0.3);
                border-radius: 3px;
                background: transparent;
            }
            QCheckBox::indicator:checked {
                background: rgba(0, 120, 215, 0.8);
                border-color: rgba(0, 120, 215, 1.0);
            }
            QSpinBox {
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                padding: 8px 12px;
                color: white;
                font-size: 14px;
            }
            QSpinBox:focus {
                background: rgba(255, 255, 255, 0.15);                border-color: rgba(0, 120, 215, 0.6);
            }
            QLabel {
                color: rgba(255, 255, 255, 0.9);
                font-size: 14px;
                font-weight: 500;
                background: transparent;
                margin-bottom: 4px;
            }
        """)


class SearchBar(QLineEdit):
    """A modern search input widget."""
    
    def __init__(self, placeholder_text="Search...", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder_text)
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup the search bar UI."""
        self.setStyleSheet(f"""
            QLineEdit {{
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                padding: {ResponsiveHelper.scale_size(12, 10, 16)}px {ResponsiveHelper.scale_size(16, 12, 20)}px;
                color: white;
                font-size: {ResponsiveHelper.scale_size(14, 12, 16)}px;
                min-width: {ResponsiveHelper.scale_size(200, 160, 240)}px;
            }}
            QLineEdit:focus {{
                background: rgba(255, 255, 255, 0.15);
                border-color: rgba(0, 120, 215, 0.6);
            }}
            QLineEdit::placeholder {{
                color: rgba(255, 255, 255, 0.5);
            }}
        """)


class NonScrollableComboBox(QComboBox):
    """A QComboBox that ignores wheel events to prevent accidental scrolling.
    
    This is especially useful for account selection fields where users might
    accidentally change the selected account while scrolling through a form.
    The combo box will only respond to wheel events when it has focus AND
    its dropdown list is open, preventing accidental changes.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
    
    def wheelEvent(self, event):
        """Override wheel event to prevent accidental scrolling.
        
        Args:
            event: The wheel event from mouse scrolling
            
        Behavior:
        - Ignores wheel events when combo box doesn't have focus
        - Ignores wheel events when dropdown is closed
        - Allows normal wheel scrolling only when focused AND dropdown is open
        """
        # Only allow wheel scrolling when the combo box has focus
        # and the dropdown list is visible (open)
        if self.hasFocus() and self.view().isVisible():
            # Allow normal wheel behavior when dropdown is open and focused
            super().wheelEvent(event)
        else:
            # Ignore wheel events to prevent accidental changes
            event.ignore()
