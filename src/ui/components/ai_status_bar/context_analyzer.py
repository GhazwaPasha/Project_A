"""
Context Analyzer - Analyzes current application state and user behavior
"""
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from enum import Enum


class ApplicationContext(Enum):
    DASHBOARD = "dashboard"
    JOURNAL = "journal"
    LEDGER = "ledger"
    TRIAL_BALANCE = "trial_balance"
    REPORTS = "reports"
    ACCOUNTS = "accounts"
    SETTINGS = "settings"
    UNKNOWN = "unknown"


class UserBehaviorPattern(Enum):
    FOCUSED_WORK = "focused_work"
    EXPLORING = "exploring"
    STRUGGLING = "struggling"
    EFFICIENT = "efficient"
    TAKING_BREAKS = "taking_breaks"
    LONG_SESSION = "long_session"


class ContextAnalyzer:
    """Analyzes application context and user behavior patterns"""
    
    def __init__(self, accounting_system):
        self.accounting_system = accounting_system
        
        # Current state
        self.current_context = ApplicationContext.DASHBOARD
        self.current_page_data = {}
        self.session_start = datetime.now()
        
        # Behavior tracking
        self.page_visit_history = []
        self.error_count = 0
        self.last_activity = datetime.now()
        self.action_count = 0
        self.successful_actions = 0
        
        # Pattern detection
        self.user_patterns = {
            "average_session_length": 0,
            "preferred_work_hours": [],
            "common_error_types": [],
            "efficiency_score": 0,
            "break_frequency": 0
        }
    
    def update_context(self, context: str, data: Dict[str, Any] = None):
        """Update current application context"""
        # Map string context to enum
        context_map = {
            "dashboard": ApplicationContext.DASHBOARD,
            "journal": ApplicationContext.JOURNAL,
            "ledger": ApplicationContext.LEDGER,
            "trial_balance": ApplicationContext.TRIAL_BALANCE,
            "reports": ApplicationContext.REPORTS,
            "accounts": ApplicationContext.ACCOUNTS,
            "settings": ApplicationContext.SETTINGS
        }
        
        new_context = context_map.get(context.lower(), ApplicationContext.UNKNOWN)
        
        # Track page visit
        if new_context != self.current_context:
            self._record_page_visit(self.current_context, new_context)
            self.current_context = new_context
        
        # Update page data
        self.current_page_data = data or {}
        self.last_activity = datetime.now()
        
        # Analyze patterns
        self._analyze_behavior_patterns()
    
    def _record_page_visit(self, from_context: ApplicationContext, to_context: ApplicationContext):
        """Record page navigation for pattern analysis"""
        visit_record = {
            "from": from_context.value,
            "to": to_context.value,
            "timestamp": datetime.now(),
            "duration": (datetime.now() - self.last_activity).total_seconds()
        }
        
        self.page_visit_history.append(visit_record)
        
        # Keep only last 100 visits
        if len(self.page_visit_history) > 100:
            self.page_visit_history = self.page_visit_history[-100:]
    
    def get_current_context(self) -> str:
        """Get current application context"""
        return self.current_context.value
    
    def get_context_insights(self) -> Dict[str, Any]:
        """Get insights about current context"""
        insights = {
            "context": self.current_context.value,
            "session_duration": self._get_session_duration(),
            "page_data": self.current_page_data,
            "user_pattern": self._detect_current_pattern().value,
            "suggestions": self._get_context_suggestions(),
            "stress_indicators": self._detect_stress_indicators(),
            "efficiency_score": self._calculate_efficiency_score()
        }
        
        return insights
    
    def _get_session_duration(self) -> float:
        """Get current session duration in hours"""
        return (datetime.now() - self.session_start).total_seconds() / 3600
    
    def _detect_current_pattern(self) -> UserBehaviorPattern:
        """Detect current user behavior pattern"""
        session_duration = self._get_session_duration()
        recent_actions = self._get_recent_actions()
        error_rate = self._get_recent_error_rate()
        
        # Long session detection
        if session_duration > 3:
            return UserBehaviorPattern.LONG_SESSION
        
        # High error rate indicates struggling
        if error_rate > 0.3:
            return UserBehaviorPattern.STRUGGLING
        
        # Many quick page switches indicate exploring
        if len(recent_actions) > 10 and session_duration < 0.5:
            return UserBehaviorPattern.EXPLORING
        
        # High success rate with steady pace indicates focused work
        if error_rate < 0.1 and len(recent_actions) > 5:
            return UserBehaviorPattern.FOCUSED_WORK
        
        # High success rate with many actions indicates efficiency
        if self._calculate_efficiency_score() > 0.8:
            return UserBehaviorPattern.EFFICIENT
        
        return UserBehaviorPattern.FOCUSED_WORK
    
    def _get_recent_actions(self, minutes: int = 30) -> List[Dict]:
        """Get recent user actions"""
        cutoff = datetime.now() - timedelta(minutes=minutes)
        return [visit for visit in self.page_visit_history 
                if visit["timestamp"] > cutoff]
    
    def _get_recent_error_rate(self, minutes: int = 30) -> float:
        """Calculate recent error rate"""
        if self.action_count == 0:
            return 0
        
        return self.error_count / max(self.action_count, 1)
    
    def _calculate_efficiency_score(self) -> float:
        """Calculate user efficiency score (0-1)"""
        if self.action_count == 0:
            return 0.5
        
        success_rate = self.successful_actions / self.action_count
        speed_factor = min(self.action_count / self._get_session_duration(), 1.0)
        
        return (success_rate * 0.7) + (speed_factor * 0.3)
    
    def _get_context_suggestions(self) -> List[str]:
        """Get context-specific suggestions"""
        suggestions = []
        
        if self.current_context == ApplicationContext.DASHBOARD:
            suggestions = [
                "Check your cash flow trends",
                "Review recent transactions",
                "Generate monthly summary report",
                "Set up accounting reminders"
            ]
        
        elif self.current_context == ApplicationContext.JOURNAL:
            suggestions = [
                "Add a new journal entry",
                "Review unbalanced entries",
                "Import transactions from bank",
                "Search previous entries"
            ]
        
        elif self.current_context == ApplicationContext.LEDGER:
            suggestions = [
                "Analyze account balances",
                "View transaction history",
                "Reconcile accounts",
                "Generate account aging report"
            ]
        
        elif self.current_context == ApplicationContext.TRIAL_BALANCE:
            suggestions = [
                "Check for balance discrepancies",
                "Verify account totals",
                "Export trial balance",
                "Review adjusting entries"
            ]
        
        elif self.current_context == ApplicationContext.REPORTS:
            suggestions = [
                "Generate income statement",
                "Create balance sheet",
                "Analyze cash flow",
                "Compare period performance"
            ]
        
        return suggestions
    
    def _detect_stress_indicators(self) -> List[str]:
        """Detect potential stress indicators"""
        indicators = []
        
        # Long session without breaks
        if self._get_session_duration() > 2:
            indicators.append("long_session")
        
        # High error rate
        if self._get_recent_error_rate() > 0.2:
            indicators.append("high_errors")
        
        # Rapid page switching
        recent_switches = len(self._get_recent_actions(15))
        if recent_switches > 8:
            indicators.append("rapid_navigation")
        
        # Working late hours
        hour = datetime.now().hour
        if hour > 20 or hour < 6:
            indicators.append("late_hours")
        
        return indicators
    
    def _analyze_behavior_patterns(self):
        """Analyze and update user behavior patterns"""
        # Update session statistics
        session_duration = self._get_session_duration()
        
        # Update average session length (simple moving average)
        if self.user_patterns["average_session_length"] == 0:
            self.user_patterns["average_session_length"] = session_duration
        else:
            self.user_patterns["average_session_length"] = (
                self.user_patterns["average_session_length"] * 0.8 + 
                session_duration * 0.2
            )
        
        # Track preferred work hours
        current_hour = datetime.now().hour
        if current_hour not in self.user_patterns["preferred_work_hours"]:
            self.user_patterns["preferred_work_hours"].append(current_hour)
        
        # Update efficiency score
        self.user_patterns["efficiency_score"] = self._calculate_efficiency_score()
    
    def record_user_action(self, action_type: str, success: bool = True, error_details: Dict = None):
        """Record user action for pattern analysis"""
        self.action_count += 1
        self.last_activity = datetime.now()
        
        if success:
            self.successful_actions += 1
        else:
            self.error_count += 1
            if error_details:
                error_type = error_details.get("type", "unknown")
                if error_type not in self.user_patterns["common_error_types"]:
                    self.user_patterns["common_error_types"].append(error_type)
    
    def get_accounting_context(self) -> Dict[str, Any]:
        """Get accounting-specific context information"""
        context = {}
        
        try:
            # Get basic accounting metrics
            if hasattr(self.accounting_system, 'get_trial_balance'):
                trial_balance = self.accounting_system.get_trial_balance()
                context["trial_balance_balanced"] = self._check_trial_balance(trial_balance)
            
            if hasattr(self.accounting_system, 'get_recent_entries'):
                recent_entries = self.accounting_system.get_recent_entries(limit=10)
                context["recent_entry_count"] = len(recent_entries) if recent_entries else 0
                context["has_unbalanced_entries"] = self._check_unbalanced_entries(recent_entries)
            
            # Add current page specific context
            if self.current_context == ApplicationContext.TRIAL_BALANCE:
                context["focus"] = "trial_balance_verification"
            elif self.current_context == ApplicationContext.JOURNAL:
                context["focus"] = "transaction_entry"
            elif self.current_context == ApplicationContext.REPORTS:
                context["focus"] = "financial_analysis"
            
        except Exception as e:
            print(f"Error getting accounting context: {e}")
        
        return context
    
    def _check_trial_balance(self, trial_balance) -> bool:
        """Check if trial balance is balanced"""
        if not trial_balance:
            return False
        
        try:
            total_debits = sum(float(row.get('debit', 0) or 0) for row in trial_balance)
            total_credits = sum(float(row.get('credit', 0) or 0) for row in trial_balance)
            return abs(total_debits - total_credits) < 0.01
        except:
            return False
    
    def _check_unbalanced_entries(self, entries) -> bool:
        """Check if there are any unbalanced journal entries"""
        if not entries:
            return False
        
        try:
            for entry in entries:
                if hasattr(entry, 'debit_amount') and hasattr(entry, 'credit_amount'):
                    if abs(float(entry.debit_amount or 0) - float(entry.credit_amount or 0)) > 0.01:
                        return True
            return False
        except:
            return False
    
    def get_wellness_context(self) -> Dict[str, Any]:
        """Get wellness-related context"""
        return {
            "session_duration": self._get_session_duration(),
            "stress_indicators": self._detect_stress_indicators(),
            "suggested_break": self._should_suggest_break(),
            "productivity_level": self._assess_productivity_level(),
            "time_of_day": datetime.now().hour
        }
    
    def _should_suggest_break(self) -> bool:
        """Determine if break should be suggested"""
        # Suggest break after 90 minutes or if stress indicators present
        return (self._get_session_duration() > 1.5 or 
                len(self._detect_stress_indicators()) > 1)
    
    def _assess_productivity_level(self) -> str:
        """Assess current productivity level"""
        efficiency = self._calculate_efficiency_score()
        stress_count = len(self._detect_stress_indicators())
        
        if efficiency > 0.8 and stress_count == 0:
            return "high"
        elif efficiency > 0.6 and stress_count <= 1:
            return "good"
        elif efficiency > 0.4 or stress_count <= 2:
            return "moderate"
        else:
            return "low"
    
    def get_smart_suggestions(self) -> List[str]:
        """Get AI-powered smart suggestions based on context"""
        suggestions = []
        
        # Add context-specific suggestions
        suggestions.extend(self._get_context_suggestions())
        
        # Add behavior-based suggestions
        pattern = self._detect_current_pattern()
        if pattern == UserBehaviorPattern.STRUGGLING:
            suggestions.extend([
                "Take a short break to refocus",
                "Review the help documentation",
                "Try a simpler task first"
            ])
        elif pattern == UserBehaviorPattern.LONG_SESSION:
            suggestions.extend([
                "Take a 10-minute break",
                "Save your work and stretch",
                "Consider continuing tomorrow"
            ])
        
        # Add accounting-specific suggestions
        accounting_context = self.get_accounting_context()
        if not accounting_context.get("trial_balance_balanced", True):
            suggestions.append("Your trial balance needs attention")
        
        if accounting_context.get("has_unbalanced_entries", False):
            suggestions.append("Some journal entries may need review")
        
        return suggestions[:5]  # Limit to top 5 suggestions
