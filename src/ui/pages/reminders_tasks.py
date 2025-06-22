"""
Reminders & Tasks Page - Manage reminders, tasks, and recurring events
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                            QLineEdit, QTextEdit, QDateTimeEdit, QComboBox, QFrame,
                            QScrollArea, QCheckBox, QGroupBox, QTabWidget, QMessageBox)
from PyQt6.QtCore import Qt, QDateTime, QTimer, pyqtSignal, QDate, QTime
from PyQt6.QtGui import QFont, QIcon
from datetime import datetime, timedelta
import json
import os

from ..components.widgets import PageHeader
from ..components.styles import ModernStyles


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
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)
        
        # Complete checkbox
        self.complete_cb = QCheckBox()
        self.complete_cb.setChecked(self.reminder_data.get('completed', False))
        self.complete_cb.toggled.connect(self._on_complete_toggled)
        layout.addWidget(self.complete_cb)
        
        # Reminder details
        details_layout = QVBoxLayout()
        details_layout.setSpacing(4)
        
        # Title
        title = QLabel(self.reminder_data.get('title', 'Untitled Reminder'))
        title.setFont(QFont("Segoe UI", 11, QFont.Weight.Medium))
        details_layout.addWidget(title)
        
        # Description
        if self.reminder_data.get('description'):
            desc = QLabel(self.reminder_data['description'])
            desc.setStyleSheet("color: rgba(255, 255, 255, 0.7); font-size: 10px;")
            details_layout.addWidget(desc)
        
        # Due date and time
        due_datetime = self.reminder_data.get('due_datetime', '')
        if due_datetime:
            due_label = QLabel(f"Due: {due_datetime}")
            due_label.setStyleSheet("color: rgba(100, 181, 246, 0.8); font-size: 10px;")
            details_layout.addWidget(due_label)
        
        # Recurring info
        recurring = self.reminder_data.get('recurring', 'none')
        if recurring != 'none':
            recurring_label = QLabel(f"Repeats: {recurring}")
            recurring_label.setStyleSheet("color: rgba(255, 193, 7, 0.8); font-size: 10px;")
            details_layout.addWidget(recurring_label)
        
        layout.addLayout(details_layout, 1)
        
        # Delete button
        delete_btn = QPushButton("×")
        delete_btn.setFixedSize(24, 24)
        delete_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.1);
                border: none;
                border-radius: 12px;
                color: rgba(255, 255, 255, 0.6);
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(244, 67, 54, 0.3);
                color: white;
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
                    margin: 2px 0;
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    background: rgba(255, 255, 255, 0.08);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 8px;
                    margin: 2px 0;
                }
                QFrame:hover {
                    border-color: rgba(100, 181, 246, 0.3);
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
        self._load_reminder_items()
        
        # Timer for checking due reminders
        self.check_timer = QTimer()
        self.check_timer.timeout.connect(self._check_due_reminders)
        self.check_timer.start(60000)  # Check every minute
        
    def _setup_ui(self):
        """Setup the reminders page UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Page header
        header = PageHeader(
            title="Reminders & Tasks",
            subtitle="Manage your accounting reminders and recurring tasks"
        )
        layout.addWidget(header)
          # Tab widget for different views
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                background: rgba(255, 255, 255, 0.05);
            }
            QTabBar::tab {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-bottom: none;
                border-radius: 6px 6px 0 0;
                padding: 8px 16px;
                margin-right: 2px;
                color: rgba(255, 255, 255, 0.7);
                font-weight: 500;
            }
            QTabBar::tab:selected {
                background: rgba(33, 150, 243, 0.3);
                color: white;
                border-color: rgba(33, 150, 243, 0.5);
            }
            QTabBar::tab:hover:!selected {
                background: rgba(255, 255, 255, 0.12);
                color: rgba(255, 255, 255, 0.9);
            }
        """)
        
        # Active reminders tab
        self.active_tab = self._create_active_reminders_tab()
        self.tab_widget.addTab(self.active_tab, "Active Reminders")
        
        # Completed reminders tab
        self.completed_tab = self._create_completed_reminders_tab()
        self.tab_widget.addTab(self.completed_tab, "Completed")
        
        # Add new reminder tab
        self.add_tab = self._create_add_reminder_tab()
        self.tab_widget.addTab(self.add_tab, "Add New")
        
        layout.addWidget(self.tab_widget)
        
    def _create_active_reminders_tab(self):
        """Create active reminders tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Scroll area for reminders
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Content widget
        self.active_content = QWidget()
        self.active_layout = QVBoxLayout(self.active_content)
        self.active_layout.setSpacing(8)
        self.active_layout.addStretch()
        
        scroll_area.setWidget(self.active_content)
        layout.addWidget(scroll_area)
        
        return tab
    
    def _create_completed_reminders_tab(self):
        """Create completed reminders tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Scroll area for completed reminders
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        # Content widget
        self.completed_content = QWidget()
        self.completed_layout = QVBoxLayout(self.completed_content)
        self.completed_layout.setSpacing(8)
        self.completed_layout.addStretch()
        
        scroll_area.setWidget(self.completed_content)
        layout.addWidget(scroll_area)
        
        return tab
    
    def _create_add_reminder_tab(self):
        """Create add new reminder tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Form for new reminder
        form_frame = QFrame()
        form_frame.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                padding: 20px;
            }
        """)
        form_layout = QVBoxLayout(form_frame)
        form_layout.setSpacing(15)
        
        # Title input
        title_label = QLabel("Reminder Title:")
        title_label.setStyleSheet("color: white; font-weight: 500;")
        form_layout.addWidget(title_label)
        
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Enter reminder title...")
        self.title_input.setStyleSheet(ModernStyles.get_input_style())
        form_layout.addWidget(self.title_input)
        
        # Description input
        desc_label = QLabel("Description (Optional):")
        desc_label.setStyleSheet("color: white; font-weight: 500;")
        form_layout.addWidget(desc_label)
        
        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText("Enter description...")
        self.desc_input.setMaximumHeight(80)
        self.desc_input.setStyleSheet(ModernStyles.get_input_style())
        form_layout.addWidget(self.desc_input)
        
        # Date and time
        datetime_layout = QHBoxLayout()
        
        date_label = QLabel("Due Date:")
        date_label.setStyleSheet("color: white; font-weight: 500;")
        datetime_layout.addWidget(date_label)
        
        self.date_input = QDateTimeEdit()
        self.date_input.setDateTime(QDateTime.currentDateTime().addDays(1))
        self.date_input.setCalendarPopup(True)
        self.date_input.setStyleSheet(ModernStyles.get_input_style())
        datetime_layout.addWidget(self.date_input)
        
        form_layout.addLayout(datetime_layout)
        
        # Recurring options
        recurring_label = QLabel("Recurring:")
        recurring_label.setStyleSheet("color: white; font-weight: 500;")
        form_layout.addWidget(recurring_label)
        
        self.recurring_combo = QComboBox()
        self.recurring_combo.addItems(["None", "Daily", "Weekly", "Monthly"])
        self.recurring_combo.setStyleSheet(ModernStyles.get_input_style())
        form_layout.addWidget(self.recurring_combo)
        
        # Add button
        add_btn = QPushButton("Add Reminder")
        add_btn.setStyleSheet(ModernStyles.get_button_style())
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
        self.tab_widget.setCurrentIndex(0)
        
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
