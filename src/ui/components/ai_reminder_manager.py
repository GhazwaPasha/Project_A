"""
AI Reminder Manager - Integrates natural language reminder creation with the existing reminder system
"""
import json
import os
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging


class AIReminderManager:
    """Manages AI-powered reminder creation and integration"""
    
    def __init__(self, reminders_file_path: str = None):
        self.logger = logging.getLogger(__name__)
        
        # Set default path if not provided
        if reminders_file_path is None:
            # Assume we're in the components directory, go up to project root
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            self.reminders_file = os.path.join(project_root, 'reminders_data.json')
        else:
            self.reminders_file = reminders_file_path
        
        # Natural language patterns for reminder processing
        self.reminder_patterns = {
            'create': [
                r'(?:remind|reminder|alert)\s+(?:me\s+)?(?:to\s+)?(.+?)\s+(?:at|on|in|every|tomorrow|next|today)',
                r'(?:set|create|add)\s+(?:a\s+)?reminder\s+(?:to\s+)?(.+)',
                r'(?:notify|alert)\s+me\s+(?:to\s+)?(.+)',
            ],
            'time_expressions': {
                'relative': {
                    r'(?:in\s+)?(\d+)\s*(?:minute|min)s?': lambda m: timedelta(minutes=int(m.group(1))),
                    r'(?:in\s+)?(\d+)\s*(?:hour|hr)s?': lambda m: timedelta(hours=int(m.group(1))),
                    r'(?:in\s+)?(\d+)\s*(?:day)s?': lambda m: timedelta(days=int(m.group(1))),
                    r'(?:in\s+)?(\d+)\s*(?:week)s?': lambda m: timedelta(weeks=int(m.group(1))),
                    r'(?:in\s+)?(\d+)\s*(?:month)s?': lambda m: timedelta(days=int(m.group(1))*30),
                    r'tomorrow': lambda m: timedelta(days=1),
                    r'next\s+week': lambda m: timedelta(weeks=1),
                    r'next\s+month': lambda m: timedelta(days=30),
                },
                'absolute': {
                    r'(?:at\s+)?(\d{1,2}):(\d{2})\s*(?:am|pm)?': 'time',
                    r'(?:on\s+)?(\d{1,2})/(\d{1,2})/(\d{4})': 'date',
                    r'(?:on\s+)?(monday|tuesday|wednesday|thursday|friday|saturday|sunday)': 'weekday',
                },
                'recurring': {
                    r'every\s+(day|daily)': 'daily',
                    r'every\s+(week|weekly)': 'weekly', 
                    r'every\s+(month|monthly)': 'monthly',
                    r'every\s+(year|yearly|annually)': 'yearly',
                    r'every\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)': 'weekly_day',
                }
            }
        }
    
    def process_reminder_command(self, user_input: str) -> Dict[str, Any]:
        """Process natural language reminder command"""
        try:
            # Extract reminder intent and content
            reminder_match = self._extract_reminder_content(user_input)
            if not reminder_match:
                return {
                    'success': False,
                    'message': 'Could not understand the reminder request. Try: "Remind me to review invoices tomorrow"'
                }
            
            task_description = reminder_match['task']
            
            # Extract timing information
            timing_info = self._extract_timing(user_input)
            
            # Create reminder data
            reminder_data = self._create_reminder_data(task_description, timing_info, user_input)
            
            # Save to reminders file
            result = self._save_reminder(reminder_data)
            
            if result['success']:
                response_text = self._generate_confirmation_message(reminder_data)
                return {
                    'success': True,
                    'message': response_text,
                    'reminder_data': reminder_data
                }
            else:
                return {
                    'success': False,
                    'message': f"Failed to save reminder: {result['error']}"
                }
                
        except Exception as e:
            self.logger.error(f"Error processing reminder command: {e}")
            return {
                'success': False,
                'message': f"Error creating reminder: {str(e)}"
            }
    
    def _extract_reminder_content(self, user_input: str) -> Optional[Dict[str, str]]:
        """Extract the main task from reminder command"""
        user_input_lower = user_input.lower().strip()
        
        for pattern in self.reminder_patterns['create']:
            match = re.search(pattern, user_input_lower)
            if match:
                task = match.group(1).strip()
                # Clean up common words that might be captured
                task = re.sub(r'^(to\s+|me\s+to\s+)', '', task)
                return {'task': task}
        
        return None
    
    def _extract_timing(self, user_input: str) -> Dict[str, Any]:
        """Extract timing information from user input"""
        user_input_lower = user_input.lower().strip()
        timing_info = {
            'type': 'relative',  # relative, absolute, recurring
            'datetime': None,
            'recurring': None,
            'original_text': user_input
        }
        
        # Check for recurring patterns first
        for pattern, recurrence_type in self.reminder_patterns['time_expressions']['recurring'].items():
            if re.search(pattern, user_input_lower):
                timing_info['type'] = 'recurring'
                timing_info['recurring'] = recurrence_type
                # For recurring reminders, set initial date to tomorrow
                timing_info['datetime'] = datetime.now() + timedelta(days=1)
                return timing_info
        
        # Check for relative time patterns
        base_time = datetime.now()
        for pattern, time_func in self.reminder_patterns['time_expressions']['relative'].items():
            match = re.search(pattern, user_input_lower)
            if match:
                if callable(time_func):
                    time_delta = time_func(match)
                    timing_info['datetime'] = base_time + time_delta
                else:
                    timing_info['datetime'] = base_time + timedelta(days=1)  # Default to tomorrow
                return timing_info
        
        # Check for absolute time patterns
        for pattern, time_type in self.reminder_patterns['time_expressions']['absolute'].items():
            match = re.search(pattern, user_input_lower)
            if match:
                timing_info['type'] = 'absolute'
                if time_type == 'time':
                    # Handle time parsing (basic implementation)
                    hour = int(match.group(1))
                    minute = int(match.group(2))
                    target_time = datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
                    if target_time <= datetime.now():
                        target_time += timedelta(days=1)  # Next day if time has passed
                    timing_info['datetime'] = target_time
                elif time_type == 'weekday':
                    # Handle weekday parsing (basic implementation)
                    weekday = match.group(1)
                    timing_info['datetime'] = self._get_next_weekday(weekday)
                return timing_info
        
        # Default: tomorrow at 9 AM
        default_time = (datetime.now() + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
        timing_info['datetime'] = default_time
        
        return timing_info
    
    def _get_next_weekday(self, weekday_name: str) -> datetime:
        """Get the next occurrence of a specific weekday"""
        weekdays = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6
        }
        
        target_weekday = weekdays.get(weekday_name.lower(), 0)
        current_weekday = datetime.now().weekday()
        days_ahead = target_weekday - current_weekday
        
        if days_ahead <= 0:  # Target day already happened this week
            days_ahead += 7
        
        target_date = datetime.now() + timedelta(days=days_ahead)
        return target_date.replace(hour=9, minute=0, second=0, microsecond=0)
    
    def _create_reminder_data(self, task: str, timing_info: Dict[str, Any], original_input: str) -> Dict[str, Any]:
        """Create reminder data structure"""
        reminder_id = f"ai_reminder_{int(datetime.now().timestamp())}"
        
        reminder_data = {
            'id': reminder_id,
            'title': task.title(),
            'description': f"AI-created reminder: {original_input}",
            'due_date': timing_info['datetime'].isoformat() if timing_info['datetime'] else None,
            'status': 'active',
            'priority': 'medium',
            'created_at': datetime.now().isoformat(),
            'created_by': 'ai_assistant',
            'type': 'ai_reminder',
            'acknowledged': False,
            'recurring': timing_info.get('recurring'),
            'original_command': original_input
        }
        
        return reminder_data
    
    def _save_reminder(self, reminder_data: Dict[str, Any]) -> Dict[str, Any]:
        """Save reminder to the reminders file"""
        try:
            # Load existing reminders
            if os.path.exists(self.reminders_file):
                with open(self.reminders_file, 'r') as f:
                    reminders_db = json.load(f)
            else:
                reminders_db = {'reminders': []}
            
            # Add new reminder
            reminders_db['reminders'].append(reminder_data)
            
            # Save back to file
            with open(self.reminders_file, 'w') as f:
                json.dump(reminders_db, f, indent=2)
            
            return {'success': True}
            
        except Exception as e:
            self.logger.error(f"Error saving reminder: {e}")
            return {'success': False, 'error': str(e)}
    
    def _generate_confirmation_message(self, reminder_data: Dict[str, Any]) -> str:
        """Generate a confirmation message for the created reminder"""
        task = reminder_data['title']
        due_date = reminder_data.get('due_date')
        recurring = reminder_data.get('recurring')
        
        if recurring:
            if recurring == 'daily':
                return f"✅ Daily reminder set: '{task}'"
            elif recurring == 'weekly':
                return f"✅ Weekly reminder set: '{task}'"
            elif recurring == 'monthly':
                return f"✅ Monthly reminder set: '{task}'"
            else:
                return f"✅ Recurring reminder set: '{task}'"
        elif due_date:
            try:
                due_dt = datetime.fromisoformat(due_date)
                if due_dt.date() == datetime.now().date():
                    time_str = due_dt.strftime('%I:%M %p')
                    return f"✅ Reminder set for today at {time_str}: '{task}'"
                elif due_dt.date() == (datetime.now() + timedelta(days=1)).date():
                    time_str = due_dt.strftime('%I:%M %p')
                    return f"✅ Reminder set for tomorrow at {time_str}: '{task}'"
                else:
                    date_str = due_dt.strftime('%B %d, %Y at %I:%M %p')
                    return f"✅ Reminder set for {date_str}: '{task}'"
            except:
                return f"✅ Reminder created: '{task}'"
        else:
            return f"✅ Reminder created: '{task}'"
    
    def get_unread_reminders_count(self) -> int:
        """Get count of unread/unacknowledged reminders"""
        try:
            if not os.path.exists(self.reminders_file):
                return 0
                
            with open(self.reminders_file, 'r') as f:
                reminders_db = json.load(f)
            
            unread_count = 0
            for reminder in reminders_db.get('reminders', []):
                if reminder.get('status') == 'active' and not reminder.get('acknowledged', False):
                    # Check if reminder is due
                    due_date = reminder.get('due_date')
                    if due_date:
                        due_dt = datetime.fromisoformat(due_date)
                        if due_dt <= datetime.now():
                            unread_count += 1
                    
            return unread_count
            
        except Exception as e:
            self.logger.error(f"Error getting unread reminders count: {e}")
            return 0
    
    def get_due_reminders(self) -> List[Dict[str, Any]]:
        """Get list of due reminders"""
        try:
            if not os.path.exists(self.reminders_file):
                return []
                
            with open(self.reminders_file, 'r') as f:
                reminders_db = json.load(f)
            
            due_reminders = []
            for reminder in reminders_db.get('reminders', []):
                if reminder.get('status') == 'active':
                    due_date = reminder.get('due_date')
                    if due_date:
                        due_dt = datetime.fromisoformat(due_date)
                        if due_dt <= datetime.now():
                            due_reminders.append(reminder)
                            
            return due_reminders
            
        except Exception as e:
            self.logger.error(f"Error getting due reminders: {e}")
            return []
