"""
Reminder Manager - Handles todos, reminders, and notifications
"""
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from enum import Enum
from dataclasses import dataclass, asdict
from PyQt6.QtCore import QObject, pyqtSignal, QTimer


class ReminderPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class ReminderType(Enum):
    GENERAL = "general"
    ACCOUNTING = "accounting"
    WELLNESS = "wellness"
    DEADLINE = "deadline"
    RECURRING = "recurring"


@dataclass
class Reminder:
    """Data class for reminders"""
    id: str
    title: str
    description: str
    due_date: datetime
    priority: ReminderPriority
    reminder_type: ReminderType
    is_completed: bool = False
    created_date: datetime = None
    completed_date: datetime = None
    recurrence: Optional[str] = None  # "daily", "weekly", "monthly"
    tags: List[str] = None
    
    def __post_init__(self):
        if self.created_date is None:
            self.created_date = datetime.now()
        if self.tags is None:
            self.tags = []
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        # Convert datetime objects to ISO strings
        data['due_date'] = self.due_date.isoformat()
        data['created_date'] = self.created_date.isoformat()
        if self.completed_date:
            data['completed_date'] = self.completed_date.isoformat()
        # Convert enums to strings
        data['priority'] = self.priority.value
        data['reminder_type'] = self.reminder_type.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Reminder':
        """Create from dictionary"""
        # Convert ISO strings back to datetime objects
        data['due_date'] = datetime.fromisoformat(data['due_date'])
        data['created_date'] = datetime.fromisoformat(data['created_date'])
        if data.get('completed_date'):
            data['completed_date'] = datetime.fromisoformat(data['completed_date'])
        # Convert strings back to enums
        data['priority'] = ReminderPriority(data['priority'])
        data['reminder_type'] = ReminderType(data['reminder_type'])
        return cls(**data)


class ReminderManager(QObject):
    """Manages reminders, todos, and notifications"""
    
    # Signals
    reminder_due = pyqtSignal(Reminder)
    reminder_added = pyqtSignal(Reminder)
    reminder_completed = pyqtSignal(Reminder)
    
    def __init__(self, data_dir: str = None):
        super().__init__()
        
        # Data storage
        self.data_dir = data_dir or os.path.join(os.path.expanduser("~"), ".ai_accountant")
        self.reminders_file = os.path.join(self.data_dir, "reminders.json")
        
        # In-memory storage
        self.reminders: Dict[str, Reminder] = {}
        self.next_id = 1
        
        # Ensure data directory exists
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Load existing reminders
        self._load_reminders()
        
        # Setup check timer
        self.check_timer = QTimer()
        self.check_timer.timeout.connect(self._check_due_reminders)
        self.check_timer.start(60000)  # Check every minute
        
        # Load default accounting reminders
        self._setup_default_accounting_reminders()
    
    def _load_reminders(self):
        """Load reminders from persistent storage"""
        try:
            if os.path.exists(self.reminders_file):
                with open(self.reminders_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                for reminder_data in data.get('reminders', []):
                    reminder = Reminder.from_dict(reminder_data)
                    self.reminders[reminder.id] = reminder
                
                self.next_id = data.get('next_id', 1)
        except Exception as e:
            print(f"Error loading reminders: {e}")
    
    def _save_reminders(self):
        """Save reminders to persistent storage"""
        try:
            data = {
                'reminders': [reminder.to_dict() for reminder in self.reminders.values()],
                'next_id': self.next_id
            }
            
            with open(self.reminders_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving reminders: {e}")
    
    def _generate_id(self) -> str:
        """Generate unique reminder ID"""
        reminder_id = f"reminder_{self.next_id}"
        self.next_id += 1
        return reminder_id
    
    def add_reminder(self, 
                    title: str,
                    description: str,
                    due_date: datetime,
                    priority: ReminderPriority = ReminderPriority.MEDIUM,
                    reminder_type: ReminderType = ReminderType.GENERAL,
                    recurrence: Optional[str] = None,
                    tags: List[str] = None) -> Reminder:
        """Add a new reminder"""
        
        reminder = Reminder(
            id=self._generate_id(),
            title=title,
            description=description,
            due_date=due_date,
            priority=priority,
            reminder_type=reminder_type,
            recurrence=recurrence,
            tags=tags or []
        )
        
        self.reminders[reminder.id] = reminder
        self._save_reminders()
        
        self.reminder_added.emit(reminder)
        return reminder
    
    def complete_reminder(self, reminder_id: str) -> bool:
        """Mark reminder as completed"""
        if reminder_id in self.reminders:
            reminder = self.reminders[reminder_id]
            reminder.is_completed = True
            reminder.completed_date = datetime.now()
            
            # Handle recurring reminders
            if reminder.recurrence:
                self._create_next_recurrence(reminder)
            
            self._save_reminders()
            self.reminder_completed.emit(reminder)
            return True
        
        return False
    
    def _create_next_recurrence(self, reminder: Reminder):
        """Create next occurrence for recurring reminders"""
        if reminder.recurrence == "daily":
            next_due = reminder.due_date + timedelta(days=1)
        elif reminder.recurrence == "weekly":
            next_due = reminder.due_date + timedelta(weeks=1)
        elif reminder.recurrence == "monthly":
            # Approximate monthly recurrence
            next_due = reminder.due_date + timedelta(days=30)
        else:
            return
        
        # Create new reminder for next occurrence
        self.add_reminder(
            title=reminder.title,
            description=reminder.description,
            due_date=next_due,
            priority=reminder.priority,
            reminder_type=reminder.reminder_type,
            recurrence=reminder.recurrence,
            tags=reminder.tags
        )
    
    def delete_reminder(self, reminder_id: str) -> bool:
        """Delete a reminder"""
        if reminder_id in self.reminders:
            del self.reminders[reminder_id]
            self._save_reminders()
            return True
        return False
    
    def get_active_reminders(self) -> List[Reminder]:
        """Get all active (non-completed) reminders"""
        return [r for r in self.reminders.values() if not r.is_completed]
    
    def get_due_reminders(self) -> List[Reminder]:
        """Get reminders that are currently due"""
        now = datetime.now()
        return [r for r in self.get_active_reminders() if r.due_date <= now]
    
    def get_upcoming_reminders(self, hours: int = 24) -> List[Reminder]:
        """Get reminders due within specified hours"""
        now = datetime.now()
        cutoff = now + timedelta(hours=hours)
        return [r for r in self.get_active_reminders() 
                if now <= r.due_date <= cutoff]
    
    def get_reminders_by_type(self, reminder_type: ReminderType) -> List[Reminder]:
        """Get reminders of specific type"""
        return [r for r in self.get_active_reminders() 
                if r.reminder_type == reminder_type]
    
    def get_reminders_by_priority(self, priority: ReminderPriority) -> List[Reminder]:
        """Get reminders of specific priority"""
        return [r for r in self.get_active_reminders() 
                if r.priority == priority]
    
    def _check_due_reminders(self):
        """Check for due reminders and emit signals"""
        due_reminders = self.get_due_reminders()
        for reminder in due_reminders:
            self.reminder_due.emit(reminder)
    
    def _setup_default_accounting_reminders(self):
        """Setup default accounting-related reminders"""
        now = datetime.now()
        
        # Only add if no accounting reminders exist
        if not self.get_reminders_by_type(ReminderType.ACCOUNTING):
            
            # Month-end reminders
            if now.day < 25:  # Add for this month
                month_end = datetime(now.year, now.month, 25, 9, 0)
                self.add_reminder(
                    title="Month-End Preparation",
                    description="Start preparing for month-end closing procedures",
                    due_date=month_end,
                    priority=ReminderPriority.HIGH,
                    reminder_type=ReminderType.ACCOUNTING,
                    recurrence="monthly",
                    tags=["month-end", "closing"]
                )
            
            # Weekly backup reminder
            next_friday = now + timedelta(days=(4 - now.weekday()) % 7)
            backup_time = datetime(next_friday.year, next_friday.month, next_friday.day, 17, 0)
            
            self.add_reminder(
                title="Weekly Backup",
                description="Create backup of accounting data",
                due_date=backup_time,
                priority=ReminderPriority.MEDIUM,
                reminder_type=ReminderType.ACCOUNTING,
                recurrence="weekly",
                tags=["backup", "data-safety"]
            )
    
    def add_accounting_reminder(self, task: str, due_in_hours: int = 24) -> Reminder:
        """Quick method to add accounting-specific reminders"""
        due_date = datetime.now() + timedelta(hours=due_in_hours)
        
        # Determine priority based on task
        priority = ReminderPriority.MEDIUM
        if any(word in task.lower() for word in ['urgent', 'asap', 'critical']):
            priority = ReminderPriority.URGENT
        elif any(word in task.lower() for word in ['month-end', 'tax', 'audit']):
            priority = ReminderPriority.HIGH
        
        return self.add_reminder(
            title=f"Accounting Task: {task}",
            description=f"Complete: {task}",
            due_date=due_date,
            priority=priority,
            reminder_type=ReminderType.ACCOUNTING,
            tags=["accounting"]
        )
    
    def add_wellness_reminder(self, message: str, due_in_minutes: int = 30) -> Reminder:
        """Add wellness/break reminder"""
        due_date = datetime.now() + timedelta(minutes=due_in_minutes)
        
        return self.add_reminder(
            title="Wellness Break",
            description=message,
            due_date=due_date,
            priority=ReminderPriority.LOW,
            reminder_type=ReminderType.WELLNESS,
            tags=["wellness", "break"]
        )
    
    def parse_natural_language_reminder(self, text: str) -> Optional[Reminder]:
        """Parse natural language to create reminders"""
        text = text.lower().strip()
        
        # Simple parsing - can be enhanced with NLP
        if "remind me" in text:
            # Extract time information
            due_date = self._extract_time_from_text(text)
            
            # Extract task
            task = self._extract_task_from_text(text)
            
            if task and due_date:
                return self.add_reminder(
                    title=task,
                    description=f"Reminder: {task}",
                    due_date=due_date,
                    priority=ReminderPriority.MEDIUM,
                    reminder_type=ReminderType.GENERAL
                )
        
        return None
    
    def _extract_time_from_text(self, text: str) -> Optional[datetime]:
        """Extract time from natural language text"""
        now = datetime.now()
        
        if "tomorrow" in text:
            if "morning" in text:
                return datetime(now.year, now.month, now.day + 1, 9, 0)
            elif "afternoon" in text:
                return datetime(now.year, now.month, now.day + 1, 14, 0)
            else:
                return datetime(now.year, now.month, now.day + 1, 10, 0)
        
        elif "in 1 hour" in text or "in an hour" in text:
            return now + timedelta(hours=1)
        
        elif "in 2 hours" in text:
            return now + timedelta(hours=2)
        
        elif "next week" in text:
            return now + timedelta(weeks=1)
        
        elif "friday" in text:
            days_ahead = 4 - now.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            return now + timedelta(days=days_ahead)
        
        # Default to 1 hour from now
        return now + timedelta(hours=1)
    
    def _extract_task_from_text(self, text: str) -> Optional[str]:
        """Extract task description from text"""
        # Remove common reminder phrases
        task = text.replace("remind me to", "").replace("remind me", "")
        task = task.replace("set reminder", "").replace("set a reminder", "")
        
        # Remove time references
        time_words = ["tomorrow", "next week", "in 1 hour", "in 2 hours", "friday", "morning", "afternoon"]
        for word in time_words:
            task = task.replace(word, "")
        
        # Clean up
        task = task.strip(" ,.-")
        
        return task if len(task) > 2 else None
    
    def get_reminder_summary(self) -> Dict[str, Any]:
        """Get summary of reminders for display"""
        active_reminders = self.get_active_reminders()
        due_reminders = self.get_due_reminders()
        upcoming_reminders = self.get_upcoming_reminders()
        
        return {
            "total_active": len(active_reminders),
            "due_now": len(due_reminders),
            "due_today": len([r for r in upcoming_reminders 
                            if r.due_date.date() == datetime.now().date()]),
            "high_priority": len(self.get_reminders_by_priority(ReminderPriority.HIGH)),
            "urgent": len(self.get_reminders_by_priority(ReminderPriority.URGENT)),
            "accounting_tasks": len(self.get_reminders_by_type(ReminderType.ACCOUNTING)),
            "wellness_reminders": len(self.get_reminders_by_type(ReminderType.WELLNESS))
        }
    
    def get_formatted_reminder_list(self, limit: int = 5) -> List[str]:
        """Get formatted list of upcoming reminders for display"""
        reminders = sorted(
            self.get_active_reminders(), 
            key=lambda r: (r.priority.value, r.due_date)
        )[:limit]
        
        formatted = []
        for reminder in reminders:
            priority_emoji = {
                ReminderPriority.LOW: "🔵",
                ReminderPriority.MEDIUM: "🟡", 
                ReminderPriority.HIGH: "🟠",
                ReminderPriority.URGENT: "🔴"
            }
            
            emoji = priority_emoji.get(reminder.priority, "⚪")
            due_str = self._format_due_date(reminder.due_date)
            
            formatted.append(f"{emoji} {reminder.title} - {due_str}")
        
        return formatted
    
    def _format_due_date(self, due_date: datetime) -> str:
        """Format due date for display"""
        now = datetime.now()
        diff = due_date - now
        
        if diff.days < 0:
            return "Overdue"
        elif diff.days == 0:
            if diff.seconds < 3600:  # Less than 1 hour
                minutes = diff.seconds // 60
                return f"{minutes}m"
            else:
                hours = diff.seconds // 3600
                return f"{hours}h"
        elif diff.days == 1:
            return "Tomorrow"
        elif diff.days < 7:
            return f"{diff.days} days"
        else:
            return due_date.strftime("%m/%d")
    
    def cleanup_completed_reminders(self, days_old: int = 30):
        """Remove completed reminders older than specified days"""
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        to_remove = []
        for reminder_id, reminder in self.reminders.items():
            if (reminder.is_completed and 
                reminder.completed_date and 
                reminder.completed_date < cutoff_date):
                to_remove.append(reminder_id)
        
        for reminder_id in to_remove:
            del self.reminders[reminder_id]
        
        if to_remove:
            self._save_reminders()
        
        return len(to_remove)
