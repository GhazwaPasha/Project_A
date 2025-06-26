"""
Reminders & Tasks Page - Manage reminders, tasks, and recurring events
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                            QLineEdit, QTextEdit, QDateTimeEdit, QComboBox, QFrame,
                            QScrollArea, QCheckBox, QGroupBox, QStackedWidget, QButtonGroup, QMessageBox)
from PyQt6.QtCore import Qt, QDateTime, QTimer, pyqtSignal, QDate, QTime
from PyQt6.QtGui import QFont, QIcon
from datetime import datetime, timedelta
import json
import os

from ..components.widgets import PageHeader
from ..components.styles import ModernStyles, GlassmorphismHelper
from ..components.scrollbar_styles import ModernScrollbarStyles
from ..common import ResponsiveHelper


class ReminderItem(QFrame):
    """Individual reminder item widget"""
    
    # Signals
    reminder_completed = pyqtSignal(str)  # reminder_id
    reminder_deleted = pyqtSignal(str)    # reminder_id
    
    def __init__(self, reminder_data: dict, parent=None):
        super().__init__(parent)
        self.reminder_data = reminder_data
        self.reminder_id = reminder_data.get('id', '')
        self._setup_ui()
        self._apply_styling()
        
    def _setup_ui(self):
        """Setup reminder item UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)  # Consistent with journal card margins
        layout.setSpacing(12)  # Consistent spacing
        
        # Complete checkbox
        self.complete_cb = QCheckBox()
        self.complete_cb.setChecked(self.reminder_data.get('completed', False))
        self.complete_cb.toggled.connect(self._on_complete_toggled)
        self.complete_cb.setStyleSheet("""
            QCheckBox {
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid rgba(255, 255, 255, 0.3);
                border-radius: 4px;
                background: rgba(255, 255, 255, 0.08);
            }
            QCheckBox::indicator:hover {
                border: 2px solid rgba(100, 181, 246, 0.5);
                background: rgba(255, 255, 255, 0.12);
            }
            QCheckBox::indicator:checked {
                background: rgba(76, 175, 80, 0.8);
                border: 2px solid rgba(76, 175, 80, 1.0);
            }
            QCheckBox::indicator:checked:hover {
                background: rgba(76, 175, 80, 0.9);
            }
        """)
        layout.addWidget(self.complete_cb)
        
        # Reminder details
        details_layout = QVBoxLayout()
        details_layout.setSpacing(4)
        
        # Title with consistent styling
        title = QLabel(self.reminder_data.get('title', 'Untitled Reminder'))
        title.setStyleSheet("""
            color: rgba(255, 255, 255, 0.9);
            font-weight: 500;
            font-size: 14px;
            background: transparent;
            border: none;
            padding: 0px;
            margin: 0px;
        """)
        details_layout.addWidget(title)
        
        # Description with consistent styling
        if self.reminder_data.get('description'):
            desc = QLabel(self.reminder_data['description'])
            desc.setStyleSheet("""
                color: rgba(255, 255, 255, 0.7);
                font-size: 12px;
                background: transparent;
                border: none;
                padding: 0px;
                margin: 0px;
            """)
            desc.setWordWrap(True)
            details_layout.addWidget(desc)
        
        # Due date and time with consistent styling
        due_datetime = self.reminder_data.get('due_datetime', '')
        if due_datetime:
            due_label = QLabel(f"Due: {due_datetime}")
            due_label.setStyleSheet("""
                color: rgba(100, 181, 246, 0.8);
                font-size: 12px;
                background: transparent;
                border: none;
                padding: 0px;
                margin: 0px;
            """)
            details_layout.addWidget(due_label)
        
        # Recurring info with consistent styling
        recurring = self.reminder_data.get('recurring', 'none')
        if recurring != 'none':
            recurring_label = QLabel(f"Repeats: {recurring}")
            recurring_label.setStyleSheet("""
                color: rgba(255, 193, 7, 0.8);
                font-size: 12px;
                background: transparent;
                border: none;
                padding: 0px;
                margin: 0px;
            """)
            details_layout.addWidget(recurring_label)
        
        layout.addLayout(details_layout, 1)
        
        # Delete button with consistent styling
        delete_btn = QPushButton("×")
        delete_btn.setFixedSize(24, 24)
        delete_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(0, 0, 0, 0.3);
                border-radius: 12px;
                color: rgba(255, 255, 255, 0.6);
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(244, 67, 54, 0.3);
                border: 1px solid rgba(244, 67, 54, 0.5);
                color: white;
            }
            QPushButton:pressed {
                background: rgba(244, 67, 54, 0.4);
            }
        """)
        delete_btn.clicked.connect(self._on_delete_clicked)
        layout.addWidget(delete_btn)
        
    def _apply_styling(self):
        """Apply modern styling to reminder item"""
        completed = self.reminder_data.get('completed', False)
        
        if completed:
            self.setStyleSheet("""
                QFrame {
                    background: rgba(255, 255, 255, 0.05);
                    border: 1px solid rgba(76, 175, 80, 0.3);
                    border-radius: 8px;
                    margin: 4px 0px;
                    min-height: 48px;
                }
                QFrame:hover {
                    background: rgba(255, 255, 255, 0.08);
                    border: 1px solid rgba(76, 175, 80, 0.5);
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    background: rgba(255, 255, 255, 0.08);
                    border: 1px solid rgba(0, 0, 0, 0.3);
                    border-radius: 8px;
                    margin: 4px 0px;
                    min-height: 48px;
                }
                QFrame:hover {
                    background: rgba(255, 255, 255, 0.12);
                    border: 1px solid rgba(100, 181, 246, 0.3);
                }
            """)
    
    def _on_complete_toggled(self, checked):
        """Handle completion toggle"""
        self.reminder_data['completed'] = checked
        self._apply_styling()
        self.reminder_completed.emit(self.reminder_id)
    
    def _on_delete_clicked(self):
        """Handle delete button click"""
        self.reminder_deleted.emit(self.reminder_id)


class RemindersTasksPage(QWidget):
    """Reminders and Tasks management page"""
    
    def __init__(self, accounting_system, notification_manager=None, parent=None):
        super().__init__(parent)
        self.accounting_system = accounting_system
        self.notification_manager = notification_manager
        self.reminders_file = "reminders_data.json"
        self.reminders_data = self._load_reminders()
        
        self._setup_ui()
        self._apply_styling()
        self._load_reminder_items()
        
        # Timer for checking due reminders
        self.check_timer = QTimer()
        self.check_timer.timeout.connect(self._check_due_reminders)
        self.check_timer.start(60000)  # Check every minute
        
    def _apply_styling(self):
        """Apply modern glassmorphism styling."""
        GlassmorphismHelper.apply_main_container_effect(self)
        self.setStyleSheet(ModernStyles.get_complete_stylesheet())
        
    def _setup_ui(self):
        """Setup the reminders page UI"""
        main_layout = QVBoxLayout(self)
        responsive_margin = ResponsiveHelper.scale_size(32, 24, 48)
        main_layout.setContentsMargins(responsive_margin, 0,  # Remove top margin for seamless flow
                                     responsive_margin, responsive_margin)
        main_layout.setSpacing(16)  # Standardized spacing
        
        # Page header
        header = PageHeader(
            title="Reminders & Tasks",
            subtitle="Manage your accounting reminders and recurring tasks"
        )
        main_layout.addWidget(header)
        
        # Create custom tab selector with modern styling (matching journal page)
        self._create_tab_selector(main_layout)
        
        # Create stacked widget for tab content
        self.stacked_widget = QStackedWidget()
        
        # Active reminders tab
        self.active_tab = self._create_active_reminders_tab()
        self.stacked_widget.addWidget(self.active_tab)
        
        # Completed reminders tab
        self.completed_tab = self._create_completed_reminders_tab()
        self.stacked_widget.addWidget(self.completed_tab)
        
        # Add new reminder tab
        self.add_tab = self._create_add_reminder_tab()
        self.stacked_widget.addWidget(self.add_tab)
        
        # Set default tab
        self.stacked_widget.setCurrentIndex(0)
        main_layout.addWidget(self.stacked_widget, 1)  # Use default stretch factor for natural spacing
    
    def _create_tab_selector(self, layout):
        """Create tab selector with modern styling matching journal page."""
        # Container for tab selector
        tab_container_layout = QHBoxLayout()
        tab_container_layout.setContentsMargins(0, 8, 0, 8)  # Match journal tab margins
        tab_container_layout.setSpacing(12)
        
        # Create container frame like level filter
        tab_group = QFrame()
        tab_group.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.03);
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 8px;
                padding: 4px;
            }
        """)
        
        tab_layout = QHBoxLayout(tab_group)
        tab_layout.setSpacing(4)
        tab_layout.setContentsMargins(4, 4, 4, 4)
        
        # Tab buttons with modern styling
        self.tab_buttons = QButtonGroup(self)
        tab_options = [("Active Reminders", 0), ("Completed", 1), ("Add New", 2)]
        
        for i, (tab_name, tab_index) in enumerate(tab_options):
            btn = QPushButton(tab_name)
            btn.setCheckable(True)
            if i == 0:  # Default to first tab
                btn.setChecked(True)
            btn.setStyleSheet(self._get_tab_filter_button_style())
            btn.clicked.connect(lambda checked, idx=tab_index: self._switch_tab(idx))
            self.tab_buttons.addButton(btn, tab_index)
            tab_layout.addWidget(btn)
        
        tab_container_layout.addWidget(tab_group)
        tab_container_layout.addStretch()  # Push tabs to the left
        
        layout.addLayout(tab_container_layout)
        
    def _switch_tab(self, tab_index):
        """Switch to the specified tab."""
        self.stacked_widget.setCurrentIndex(tab_index)
        
    def _get_tab_filter_button_style(self):
        """Get modern tab filter button styling to match journal page."""
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
                min-width: 80px;
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
        
    def _create_active_reminders_tab(self):
        """Create active reminders tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)  # Remove extra margins for seamless flow
        layout.setSpacing(16)  # Standardized spacing
        
        # Scroll area for reminders
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Apply modern scrollbar styling
        scroll_style = """
            QScrollArea {
                background: transparent;
                border: none;
            }
            QWidget#scrollAreaWidgetContents {
                background: transparent;
            }
        """ + ModernScrollbarStyles.get_vertical_scrollbar_style()
        scroll_area.setStyleSheet(scroll_style)
        
        # Content widget
        self.active_content = QWidget()
        self.active_content.setObjectName("scrollAreaWidgetContents")
        self.active_layout = QVBoxLayout(self.active_content)
        self.active_layout.setContentsMargins(8, 8, 8, ResponsiveHelper.scale_size(24, 16, 32))
        self.active_layout.setSpacing(8)
        self.active_layout.addStretch()
        
        scroll_area.setWidget(self.active_content)
        layout.addWidget(scroll_area)
        
        return tab
    
    def _create_completed_reminders_tab(self):
        """Create completed reminders tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)  # Remove extra margins for seamless flow
        layout.setSpacing(16)  # Standardized spacing
        
        # Scroll area for completed reminders
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        # Apply modern scrollbar styling
        scroll_style = """
            QScrollArea {
                background: transparent;
                border: none;
            }
            QWidget#scrollAreaWidgetContents {
                background: transparent;
            }
        """ + ModernScrollbarStyles.get_vertical_scrollbar_style()
        scroll_area.setStyleSheet(scroll_style)
        
        # Content widget
        self.completed_content = QWidget()
        self.completed_content.setObjectName("scrollAreaWidgetContents")
        self.completed_layout = QVBoxLayout(self.completed_content)
        self.completed_layout.setContentsMargins(8, 8, 8, ResponsiveHelper.scale_size(24, 16, 32))
        self.completed_layout.setSpacing(8)
        self.completed_layout.addStretch()
        
        scroll_area.setWidget(self.completed_content)
        layout.addWidget(scroll_area)
        
        return tab
    
    def _create_add_reminder_tab(self):
        """Create add new reminder tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)  # Remove extra margins for seamless flow
        layout.setSpacing(16)  # Standardized spacing
        
        # Form for new reminder with modern styling (matching journal page)
        form_frame = QFrame()
        form_frame.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(0, 0, 0, 0.3);
                border-radius: 8px;
            }
        """)
        form_layout = QVBoxLayout(form_frame)
        form_layout.setContentsMargins(18, 18, 18, 18)  # Match journal form margins
        form_layout.setSpacing(12)  # Match journal form spacing
        
        # Title input
        title_label = QLabel("REMINDER TITLE")
        title_label.setStyleSheet("""
            color: rgba(255, 255, 255, 0.8);
            font-size: 11px;
            font-weight: 600;
            background: transparent;
            border: none;
            padding: 0px;
            margin: 0px;
            letter-spacing: 0.5px;
        """)
        form_layout.addWidget(title_label)
        
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Enter reminder title...")
        self.title_input.setStyleSheet("""
            QLineEdit {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(0, 0, 0, 0.3);
                border-radius: 8px;
                padding: 8px 12px;
                color: white;
                font-size: 12px;
                min-height: 32px;
            }
            QLineEdit:hover {
                background: rgba(255, 255, 255, 0.12);
                border: 1px solid rgba(100, 181, 246, 0.3);
            }
            QLineEdit:focus {
                background: rgba(255, 255, 255, 0.12);
                border: 1px solid rgba(100, 181, 246, 0.5);
            }
            QLineEdit::placeholder {
                color: rgba(255, 255, 255, 0.5);
            }
        """)
        form_layout.addWidget(self.title_input)
        
        # Description input
        desc_label = QLabel("DESCRIPTION (OPTIONAL)")
        desc_label.setStyleSheet("""
            color: rgba(255, 255, 255, 0.8);
            font-size: 11px;
            font-weight: 600;
            background: transparent;
            border: none;
            padding: 0px;
            margin: 0px;
            letter-spacing: 0.5px;
        """)
        form_layout.addWidget(desc_label)
        
        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText("Enter description...")
        self.desc_input.setMaximumHeight(80)
        self.desc_input.setStyleSheet("""
            QTextEdit {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(0, 0, 0, 0.3);
                border-radius: 8px;
                padding: 8px 12px;
                color: white;
                font-size: 12px;
            }
            QTextEdit:hover {
                background: rgba(255, 255, 255, 0.12);
                border: 1px solid rgba(100, 181, 246, 0.3);
            }
            QTextEdit:focus {
                background: rgba(255, 255, 255, 0.12);
                border: 1px solid rgba(100, 181, 246, 0.5);
            }
        """)
        form_layout.addWidget(self.desc_input)
        
        # Date and time section
        date_label = QLabel("DUE DATE & TIME")
        date_label.setStyleSheet("""
            color: rgba(255, 255, 255, 0.8);
            font-size: 11px;
            font-weight: 600;
            background: transparent;
            border: none;
            padding: 0px;
            margin: 0px;
            letter-spacing: 0.5px;
        """)
        form_layout.addWidget(date_label)
        
        self.date_input = QDateTimeEdit()
        self.date_input.setDateTime(QDateTime.currentDateTime().addDays(1))
        self.date_input.setCalendarPopup(True)
        self.date_input.setStyleSheet("""
            QDateTimeEdit {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(0, 0, 0, 0.3);
                border-radius: 8px;
                padding: 8px 12px;
                color: white;
                font-size: 12px;
                min-height: 32px;
            }
            QDateTimeEdit:hover {
                background: rgba(255, 255, 255, 0.12);
                border: 1px solid rgba(100, 181, 246, 0.3);
            }
            QDateTimeEdit:focus {
                background: rgba(255, 255, 255, 0.12);
                border: 1px solid rgba(100, 181, 246, 0.5);
            }
            QDateTimeEdit::drop-down {
                border: none;
                width: 20px;
            }
            QDateTimeEdit::down-arrow {
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
        """)
        form_layout.addWidget(self.date_input)
        
        # Recurring options
        recurring_label = QLabel("RECURRING")
        recurring_label.setStyleSheet("""
            color: rgba(255, 255, 255, 0.8);
            font-size: 11px;
            font-weight: 600;
            background: transparent;
            border: none;
            padding: 0px;
            margin: 0px;
            letter-spacing: 0.5px;
        """)
        form_layout.addWidget(recurring_label)
        
        self.recurring_combo = QComboBox()
        self.recurring_combo.addItems(["None", "Daily", "Weekly", "Monthly"])
        self.recurring_combo.setStyleSheet("""
            QComboBox {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(0, 0, 0, 0.3);
                border-radius: 8px;
                padding: 8px 12px;
                color: white;
                font-size: 12px;
                min-height: 32px;
                min-width: 160px;
            }
            QComboBox:hover {
                background: rgba(255, 255, 255, 0.12);
                border: 1px solid rgba(100, 181, 246, 0.3);
            }
            QComboBox:focus {
                background: rgba(255, 255, 255, 0.12);
                border: 1px solid rgba(100, 181, 246, 0.5);
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 4px solid rgba(255, 255, 255, 0.7);
                margin-right: 6px;
            }
            QComboBox QAbstractItemView {
                background: rgba(40, 40, 40, 0.95);
                border: 1px solid rgba(0, 0, 0, 0.3);
                border-radius: 8px;
                color: white;
                selection-background-color: rgba(100, 181, 246, 0.2);
                selection-color: white;
                padding: 4px;
            }
            QComboBox QAbstractItemView::item {
                padding: 8px 12px;
                border: none;
                border-radius: 4px;
                margin: 2px;
            }
            QComboBox QAbstractItemView::item:hover {
                background: rgba(100, 181, 246, 0.1);
            }
            QComboBox QAbstractItemView::item:selected {
                background: rgba(100, 181, 246, 0.2);
            }
        """)
        form_layout.addWidget(self.recurring_combo)
        
        # Add button with primary styling (matching journal page)
        add_btn = QPushButton("Add Reminder")
        add_btn.setStyleSheet("""
            QPushButton {
                background: rgba(100, 181, 246, 0.2);
                border: 1px solid rgba(100, 181, 246, 0.5);
                border-radius: 8px;
                color: #90CAF9;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: 500;
                min-height: 32px;
            }
            QPushButton:hover {
                background: rgba(100, 181, 246, 0.3);
                border: 1px solid rgba(100, 181, 246, 0.7);
            }
            QPushButton:pressed {
                background: rgba(100, 181, 246, 0.4);
            }
        """)
        add_btn.clicked.connect(self._add_new_reminder)
        form_layout.addWidget(add_btn)
        
        layout.addWidget(form_frame)
        layout.addStretch()
        
        return tab
    
    def _load_reminders(self):
        """Load reminders from file"""
        try:
            if os.path.exists(self.reminders_file):
                with open(self.reminders_file, 'r') as f:
                    return json.load(f)
            return []
        except Exception:
            return []
    
    def _save_reminders(self):
        """Save reminders to file"""
        try:
            with open(self.reminders_file, 'w') as f:
                json.dump(self.reminders_data, f, indent=2)
        except Exception as e:
            print(f"Error saving reminders: {e}")
    
    def _load_reminder_items(self):
        """Load reminder items into UI"""
        # Clear existing items
        self._clear_layout(self.active_layout)
        self._clear_layout(self.completed_layout)
        
        # Add reminder items
        for reminder in self.reminders_data:
            item = ReminderItem(reminder, self)
            item.reminder_completed.connect(self._on_reminder_completed)
            item.reminder_deleted.connect(self._on_reminder_deleted)
            
            if reminder.get('completed', False):
                self.completed_layout.insertWidget(0, item)
            else:
                self.active_layout.insertWidget(0, item)
    
    def _clear_layout(self, layout):
        """Clear all widgets from layout except stretch"""
        while layout.count() > 1:  # Keep the stretch item
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    
    def _add_new_reminder(self):
        """Add new reminder"""
        title = self.title_input.text().strip()
        if not title:
            QMessageBox.warning(self, "Error", "Please enter a reminder title.")
            return
        
        # Create reminder data
        reminder = {
            'id': f"reminder_{len(self.reminders_data)}_{int(datetime.now().timestamp())}",
            'title': title,
            'description': self.desc_input.toPlainText().strip(),
            'due_datetime': self.date_input.dateTime().toString("yyyy-MM-dd hh:mm"),
            'recurring': self.recurring_combo.currentText().lower(),
            'completed': False,
            'created_at': datetime.now().isoformat()
        }
        
        # Add to data
        self.reminders_data.append(reminder)
        self._save_reminders()
        self._load_reminder_items()
        
        # Clear form
        self.title_input.clear()
        self.desc_input.clear()
        self.date_input.setDateTime(QDateTime.currentDateTime().addDays(1))
        self.recurring_combo.setCurrentIndex(0)
        
        # Switch to active tab
        self.stacked_widget.setCurrentIndex(0)
        
        # Notify parent
        if hasattr(self.parent(), 'add_notification'):
            self.parent().add_notification(
                "Reminder Added",
                f"Reminder '{title}' has been created successfully.",
                "success"
            )
    
    def _on_reminder_completed(self, reminder_id):
        """Handle reminder completion"""
        self._save_reminders()
        self._load_reminder_items()
    
    def _on_reminder_deleted(self, reminder_id):
        """Handle reminder deletion"""
        self.reminders_data = [r for r in self.reminders_data if r.get('id') != reminder_id]
        self._save_reminders()
        self._load_reminder_items()
        
    def _check_due_reminders(self):
        """Check for due reminders and notify"""
        current_time = datetime.now()
        
        for reminder in self.reminders_data:
            if reminder.get('completed', False):
                continue
                
            due_str = reminder.get('due_datetime', '')
            if not due_str:
                continue
                
            try:
                due_time = datetime.strptime(due_str, "%Y-%m-%d %H:%M")
                
                # Check if reminder is due (within 1 minute)
                time_diff = (due_time - current_time).total_seconds()
                if 0 <= time_diff <= 60:
                    self._trigger_reminder_notification(reminder)
                    
            except ValueError:
                continue
                
    def _trigger_reminder_notification(self, reminder):
        """Trigger notification for due reminder"""
        title = f"⏰ Reminder: {reminder['title']}"
        description = reminder.get('description', 'You have a pending task.')
        
        # Use notification manager if available
        if self.notification_manager:
            self.notification_manager.add_notification(
                title=title,
                message=description,
                notification_type="warning"
            )
        elif hasattr(self.parent(), 'add_notification'):
            self.parent().add_notification(title, description, "warning")
    
    def add_reminder_from_ai(self, title: str, description: str = "", due_datetime: str = "", recurring: str = "none"):
        """Add reminder from AI command"""
        reminder = {
            'id': f"ai_reminder_{int(datetime.now().timestamp())}",
            'title': title,
            'description': description,
            'due_datetime': due_datetime,
            'recurring': recurring.lower(),
            'completed': False,
            'created_at': datetime.now().isoformat()
        }
        
        self.reminders_data.append(reminder)
        self._save_reminders()
        self._load_reminder_items()
        
        return reminder['id']
