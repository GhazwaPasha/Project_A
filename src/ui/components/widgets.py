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
from PyQt6.QtCore import Qt, QStringListModel
from PyQt6.QtWidgets import QCompleter
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
        border_radius = ResponsiveHelper.scale_size(8, 6, 10)
        
        # Use accent color for consistent single-color theming
        accent_rgb = self._hex_to_rgb(self.accent_color)
        
        self.setStyleSheet(f"""
            QFrame {{
                background: rgba({accent_rgb[0]}, {accent_rgb[1]}, {accent_rgb[2]}, 0.1);
                border: 1px solid rgba(0, 0, 0, 0.3);
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
        self.callback = callback or (lambda start_date, end_date: None)
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup the date range selector UI with level filter styling."""
        from ..common import QHBoxLayout, QLabel, QButtonGroup, QPushButton, QDateEdit, QDate, QFrame
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(12)
        
        # Create container frame like level filter
        filter_group = QFrame()
        filter_group.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.03);
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 8px;
                padding: 4px;
            }
        """)
        
        filter_layout = QHBoxLayout(filter_group)
        filter_layout.setSpacing(4)
        filter_layout.setContentsMargins(4, 4, 4, 4)
        
        # Quick filters with level filter styling
        self.quick_buttons = QButtonGroup(self)
        quick_filters = ["This Month", "Last Month", "This Quarter", "This Year", "All Time"]
        
        for i, filter_name in enumerate(quick_filters):
            btn = QPushButton(filter_name)
            btn.setCheckable(True)
            btn.setStyleSheet(self._get_date_filter_button_style())
            btn.clicked.connect(self._quick_filter_selected)
            self.quick_buttons.addButton(btn, i)
            filter_layout.addWidget(btn)
        
        layout.addWidget(filter_group)
        layout.addStretch()  # This pushes the date pickers to the right
        
        # Custom date range on the right with Windows 11 styling
        self.from_date = QDateEdit()
        self.from_date.setDate(QDate.currentDate().addDays(-30))
        self.from_date.setCalendarPopup(True)
        date_picker_style = """
            QDateEdit {
                background: rgba(255, 255, 255, 0.03);
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 6px;
                padding: 4px 16px;
                color: rgba(255, 255, 255, 0.8);
                font-size: 13px;
                font-weight: 500;
                margin: 0;
                min-width: 130px;
                min-height: 40px;
            }
            QDateEdit:hover {
                background: rgba(255, 255, 255, 0.08);
                color: white;
            }
            QDateEdit:focus {
                background: rgba(0, 120, 215, 0.3);
                color: white;
            }
            QDateEdit::drop-down {
                border: none;
                width: 20px;
            }
            QDateEdit::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 4px solid rgba(255, 255, 255, 0.7);
                margin-right: 6px;
            }
            QCalendarWidget {
                background-color: rgb(32, 32, 32);
                color: white;
            }
            QCalendarWidget QToolButton {
                color: white;
                background: transparent;
                border: none;
                border-radius: 4px;
                padding: 4px;
            }
            QCalendarWidget QToolButton:hover {
                background: rgba(255, 255, 255, 0.1);
            }
            QCalendarWidget QMenu {
                background-color: rgb(32, 32, 32);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
            QCalendarWidget QSpinBox {
                color: white;
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 4px;
                padding: 2px;
            }
            QCalendarWidget QAbstractItemView:enabled {
                color: white;
                background: rgb(32, 32, 32);
                selection-background-color: rgba(100, 181, 246, 0.3);
                selection-color: white;
            }
            QCalendarWidget QWidget#qt_calendar_navigationbar {
                background: rgb(32, 32, 32);
            }
        """
        self.from_date.setStyleSheet(date_picker_style)
        self.from_date.dateChanged.connect(self._on_date_changed)
        layout.addWidget(self.from_date)
        
        to_label = QLabel("to")
        to_label.setStyleSheet("color: rgba(255, 255, 255, 0.7); background: transparent; border: none; font-size: 12px; font-weight: 500;")
        layout.addWidget(to_label)
        
        self.to_date = QDateEdit()
        self.to_date.setDate(QDate.currentDate())
        self.to_date.setCalendarPopup(True)
        self.to_date.setStyleSheet(date_picker_style)
        self.to_date.dateChanged.connect(self._on_date_changed)
        layout.addWidget(self.to_date)
        
        # Set default selection
        self.quick_buttons.button(0).setChecked(True)  # This Month
        
    def _on_date_changed(self):
        """Handle date changes - supports both callback and signal patterns."""
        if self.callback:
            # Get current date range and pass to callback
            start_date, end_date = self.get_date_range()
            self.callback(start_date, end_date)
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
        
    def _get_date_filter_button_style(self):
        """Get Windows 11 style date filter button styling to match level filter."""
        return """
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                color: rgba(255, 255, 255, 0.8);
                font-size: 13px;
                font-weight: 500;
                margin: 0;
                min-width: 70px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.08);
                color: white;
            }
            QPushButton:checked {
                background: rgba(0, 120, 215, 0.3);
                color: white;
            }
            QPushButton:checked:hover {
                background: rgba(0, 120, 215, 0.4);
            }
        """
        
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


class EditableAccountComboBox(QComboBox):
    """An editable combo box with smart account suggestions.
    
    Features:
    - Editable text input for typing account names/codes
    - Auto-completion with smart filtering
    - Non-scrollable when not focused (prevents accidents)
    - Smart matching (partial text, codes, account names)
    - Proper placeholder text (not a selectable item)
    - Strict validation: only accepts accounts from chart of accounts    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        
        # Completely disable native dropdown - we only want QCompleter suggestions
        self.setMaxVisibleItems(0)  # Hide native dropdown
        
        self.placeholder_text = "Select or type account..."
        self.valid_accounts = []  # List of valid account strings
        self.valid_account_codes = []  # List of valid account codes
        self.valid_account_names = []  # List of valid account names
        self._setup_completer()
        self._setup_placeholder()
        self._setup_validation()
        
        # Ensure we start with no selection to show placeholder
        self.setCurrentIndex(-1)
    
    def _setup_validation(self):
        """Setup validation to only accept valid accounts."""
        line_edit = self.lineEdit()
        if line_edit:
            # Connect to text editing finished to validate
            line_edit.editingFinished.connect(self._validate_input)
            # Connect to text changed for real-time feedback
            line_edit.textChanged.connect(self._on_text_changed_with_validation)
    
    def _validate_input(self):
        """Validate that the entered text matches a valid account."""
        line_edit = self.lineEdit()
        if not line_edit:
            return
            
        text = line_edit.text().strip()
        if not text:
            # Empty is allowed (placeholder)
            return
            
        # Check if the text matches any valid account format
        if self._is_valid_account(text):
            # Valid account - ensure proper formatting and set selection
            formatted_account = self._format_account_text(text)
            if formatted_account:
                # Find and select the properly formatted account
                index = self.findText(formatted_account, Qt.MatchFlag.MatchExactly)
                if index >= 0:
                    self.setCurrentIndex(index)
                else:
                    # Set the text directly if not found in combo
                    line_edit.setText(formatted_account)
            else:
                # Could not format - reject input
                self._show_validation_error(line_edit)
                line_edit.clear()
        else:
            # Invalid account - clear the input and show error styling
            self._show_validation_error(line_edit)
            line_edit.clear()
    
    def _is_valid_account(self, text):
        """Check if the text represents a valid account - strict validation."""
        text = text.strip()
        if not text:
            return True  # Empty is allowed
            
        # For strict validation: only allow exact matches or partial matches that lead to exact matches
        
        # Check if it's exactly one of our valid account strings
        if text in self.valid_accounts:
            return True
            
        # Check if it's a valid account code (4 digits) that exists in our chart
        if len(text) == 4 and text.isdigit():
            return text in self.valid_account_codes
            
        # Check if it's a valid account name that exists in our chart
        if text in self.valid_account_names:
            return True
              # For partial input during typing: check if it's a valid part of an account
        # But only if it's unique enough (at least 2 characters)
        if len(text) >= 2:
            text_lower = text.lower()
            
            # Check for partial matches in account codes
            if text.isdigit():
                matching_codes = [code for code in self.valid_account_codes if text in code]
                if len(matching_codes) >= 1:  # Allow if there's at least one match
                    return True
            
            # Find matches in full account strings (including code and name)
            matching_accounts = []
            for acc in self.valid_accounts:
                acc_lower = acc.lower()
                # Match if:
                # 1. Input is part of the account string
                # 2. Input matches a word in the account name
                if (text_lower in acc_lower or
                    any(word.startswith(text_lower) for word in acc_lower.split())):
                    matching_accounts.append(acc)
            if matching_accounts:
                return True
                
            # Check for partial matches in account names (more flexible)
            matching_names = []
            for name in self.valid_account_names:
                name_lower = name.lower()
                # Match if the input is part of a word in the name
                if text_lower in name_lower or any(word.startswith(text_lower) for word in name_lower.split()):
                    matching_names.append(name)
            if matching_names:
                return True
        
        return False
    
    def _format_account_text(self, text):
        """Format the text to proper account format (code - name)."""
        text = text.strip()
        if not text:
            return ""
            
        # If it's already in proper format, return as-is
        if text in self.valid_accounts:
            return text
            
        # If it's just a code, find the full account string
        if len(text) == 4 and text.isdigit():
            for account in self.valid_accounts:
                if account.startswith(text + " - "):
                    return account
                    
        # If it's just a name, find the full account string
        for account in self.valid_accounts:
            account_name = account.split(" - ", 1)[1] if " - " in account else ""
            if account_name.lower() == text.lower():
                return account
                  # Try partial matching for the closest account
        text_lower = text.lower()
        best_match = None
        best_score = 0
        
        for account in self.valid_accounts:
            account_lower = account.lower()
            score = 0
            
            # Exact word match
            if text_lower in account_lower.split():
                score = 100
            # Word starts with the text
            elif any(word.startswith(text_lower) for word in account_lower.split()):
                score = 75
            # Contains the text
            elif text_lower in account_lower:
                score = 50
                
            # Prefer shorter matches with equal scores
            if score > best_score or (score == best_score and len(account) < len(best_match or "")):
                best_score = score
                best_match = account
                
        return best_match if best_score > 0 else None
                
        return None
    
    def _show_validation_error(self, line_edit):
        """Show visual feedback for validation error."""
        # Temporarily change styling to indicate error
        original_style = line_edit.styleSheet()
        error_style = original_style + """
            border: 2px solid rgba(255, 100, 100, 0.9) !important;
            background: rgba(255, 100, 100, 0.15) !important;
            color: rgba(255, 255, 255, 0.9) !important;
        """
        line_edit.setStyleSheet(error_style)
        
        # Show tooltip with error message
        line_edit.setToolTip("❌ Invalid account. Please select an account from the chart of accounts.")
        
        # Reset styling after a delay
        from PyQt6.QtCore import QTimer
        def reset_style():
            line_edit.setStyleSheet(original_style)
            line_edit.setToolTip("")
        
        QTimer.singleShot(2000, reset_style)
    
    def _on_text_changed_with_validation(self, text):
        """Handle text changes with validation feedback."""
        # Call original text changed handler        self._on_text_changed(text)
        
        # Prevent styling conflicts - don't apply validation styling while typing
        # The bulk entry page handles validation styling externally
    
    def setAccountList(self, accounts):
        """Set the list of valid accounts for validation and QCompleter only."""
        self.valid_accounts = accounts.copy() if accounts else []
        
        # Extract codes and names for validation
        self.valid_account_codes = []
        self.valid_account_names = []
        
        for account in self.valid_accounts:
            if " - " in account:
                code, name = account.split(" - ", 1)
                self.valid_account_codes.append(code)
                self.valid_account_names.append(name)
        
        # Only update the QCompleter, don't add items to combo box (prevents third dropdown)
        if hasattr(self, 'completer') and self.completer:
            model = QStringListModel(self.valid_accounts)
            self.completer.setModel(model)

    def _setup_placeholder(self):
        """Setup proper placeholder text functionality."""
        # Set placeholder text on the line edit
        line_edit = self.lineEdit()
        if line_edit:
            line_edit.setPlaceholderText(self.placeholder_text)
            # Connect to text changes to handle placeholder behavior
            line_edit.textChanged.connect(self._on_text_changed)
            # Ensure it starts empty to show placeholder
            line_edit.clear()
    
    def _on_text_changed(self, text):
        """Handle text changes to manage placeholder and selection."""
        # If user types something, clear the current selection if it was the placeholder
        if text and self.currentIndex() == 0 and self.count() > 0:
            # Check if the first item was our old placeholder item
            first_item = self.itemText(0)
            if first_item.startswith("--") and "Select" in first_item:
                self.setCurrentIndex(-1)  # Clear selection
    
    def setPlaceholderText(self, text):
        """Set the placeholder text."""
        self.placeholder_text = text
        line_edit = self.lineEdit()
        if line_edit:
            line_edit.setPlaceholderText(text)
    
    def _setup_completer(self):
        """Setup the auto-completer for smart suggestions."""        # Create completer with smart case-insensitive matching
        self.completer = QCompleter()
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        # Match if the text appears anywhere in the account string
        self.completer.setFilterMode(Qt.MatchFlag.MatchContains)
        # Pop up completion as soon as user starts typing
        self.completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        # Set max visible items to show more suggestions
        self.completer.setMaxVisibleItems(10)
        
        # Set the completer on the line edit
        self.setCompleter(self.completer)
        
        # Connect completion selection to combo box selection
        self.completer.activated.connect(self._on_completion_selected)
    
    def _on_completion_selected(self, text):
        """Handle when a completion is selected."""
        # Find the index of the selected item and set it
        index = self.findText(text, Qt.MatchFlag.MatchExactly)
        if index >= 0:
            self.setCurrentIndex(index)    
    def setModel(self, model):
        """Override setModel to also update the completer."""
        super().setModel(model)
        if self.completer:
            self.completer.setModel(model)
    
    def addItems(self, items):
        """Override addItems to prevent dropdown list - only use QCompleter."""
        # Don't call super().addItems(items) to prevent creating dropdown list
        # Only update the QCompleter model for smart suggestions
        if hasattr(self, 'completer') and self.completer:
            model = QStringListModel(items)
            self.completer.setModel(model)
        
        # Ensure no selection and placeholder shows        self.setCurrentIndex(-1)
        line_edit = self.lineEdit()
        if line_edit:
            line_edit.clear()
    
    def addItem(self, text, userData=None):
        """Override addItem to prevent dropdown items - only use QCompleter."""
        # Don't call super().addItem() to prevent creating dropdown items
        # The QCompleter handles all suggestions
        pass
    
    def currentText(self):
        """Override currentText to handle empty selection properly."""
        # If no item is selected (index -1), return empty string to show placeholder
        if self.currentIndex() == -1:
            line_edit = self.lineEdit()
            if line_edit:
                text = line_edit.text()
                # If it's empty or just the placeholder, return empty
                if not text or text == self.placeholder_text:
                    return ""
                return text
            return ""
        
        # Otherwise get the normal current text
        text = super().currentText()
        # If it's a placeholder-like text, return empty string
        if text and (text.startswith("--") and "Select" in text):
            return ""
        return text
    
    def setCurrentText(self, text):
        """Override setCurrentText to handle setting custom text."""
        if not text or (text.startswith("--") and "Select" in text):
            # Clear selection and show placeholder
            self.setCurrentIndex(-1)
            line_edit = self.lineEdit()
            if line_edit:
                line_edit.clear()
                line_edit.setText("")  # Ensure completely empty
        else:            # Try to find the text in the list first
            index = self.findText(text, Qt.MatchFlag.MatchExactly)
            if index >= 0:
                self.setCurrentIndex(index)
            else:
                # Set custom text and clear index to show it's custom
                self.setCurrentIndex(-1)
                line_edit = self.lineEdit()
                if line_edit:
                    line_edit.setText(text)
    
    def clear_selection(self):
        """Clear the selection and show placeholder text."""
        self.setCurrentIndex(-1)
        line_edit = self.lineEdit()
        if line_edit:
            line_edit.clear()
            line_edit.setText("")  # Ensure it's completely empty

    def showPopup(self):
        """Override showPopup to disable native dropdown - only use QCompleter suggestions."""
        # Don't call the parent showPopup to prevent the native dropdown
        # The QCompleter will handle showing suggestions as the user types
        pass
    
    def wheelEvent(self, event):
        """Override wheel event to prevent accidental scrolling.
        
        Same behavior as NonScrollableComboBox:
        - Only allow wheel scrolling when focused and dropdown is open
        - Prevent accidental changes while scrolling through form
        """
        if self.hasFocus() and self.view().isVisible():
            super().wheelEvent(event)
        else:
            event.ignore()
    
    def keyPressEvent(self, event):
        """Enhanced key handling for better user experience."""
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            # On Enter, try to find the best match for the current text
            current_text = self.currentText()
            best_match_index = self._find_best_match(current_text)
            if best_match_index >= 0:
                self.setCurrentIndex(best_match_index)
        
        super().keyPressEvent(event)
    
    def _find_best_match(self, text):
        """Find the best matching item for the given text."""
        if not text:
            return -1
        
        text_lower = text.lower()
        
        # Try exact match first
        for i in range(self.count()):
            item_text = self.itemText(i)
            if item_text.lower() == text_lower:
                return i
        
        # Try partial match (starts with)
        for i in range(self.count()):
            item_text = self.itemText(i)
            if item_text.lower().startswith(text_lower):
                return i
        
        # Try contains match
        for i in range(self.count()):
            item_text = self.itemText(i)
            if text_lower in item_text.lower():
                return i
        
        return -1
    
    def getValidatedAccount(self):
        """Get the current account text only if it's valid, otherwise return empty string."""
        current_text = self.currentText()
        if not current_text:
            return ""
            
        # Final validation check
        if self._is_valid_account(current_text):
            formatted = self._format_account_text(current_text)
            return formatted if formatted else ""
        
        return ""

    def isValidAccount(self):
        """Check if the current account selection/input is valid."""
        current_text = self.currentText()
        if not current_text:
            return True  # Empty is considered valid (will be caught by form validation)
        
        return self._is_valid_account(current_text) and self._format_account_text(current_text) is not None
    
    def setTextWithValidation(self, text):
        """Set text and trigger validation to match against chart of accounts."""
        if not text:
            self.clear_selection()
            return
            
        # First try exact match
        index = self.findText(text, Qt.MatchFlag.MatchExactly)
        if index >= 0:
            self.setCurrentIndex(index)
            return
            
        # Set the text in line edit
        line_edit = self.lineEdit()
        if line_edit:
            line_edit.setText(text)
            # Trigger validation to find matching accounts
            self._validate_input()
            # Ensure UI updates
            line_edit.textChanged.emit(text)
            line_edit.editingFinished.emit()
            
        # Force a repaint to ensure visual update
        self.update()

    def force_refresh(self):
        """Force a complete UI refresh of the combo box."""
        line_edit = self.lineEdit()
        if line_edit:
            # Force the line edit to repaint
            line_edit.update()
            line_edit.repaint()
        # Force the combo box itself to repaint
        self.update()
        self.repaint()
