"""
Personality Engine - Handles AI mood, personality traits, and wellness features
"""
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import os


class PersonalityEngine:
    """Manages AI personality, mood detection, and wellness features"""
    
    def __init__(self):
        self.current_mood = "happy"
        self.personality_traits = {
            "supportive": 0.8,
            "encouraging": 0.9,
            "professional": 0.7,
            "friendly": 0.8,
            "humorous": 0.6
        }
        
        # Track user patterns for mood detection
        self.user_patterns = {
            "work_start_time": None,
            "break_frequency": 0,
            "error_count": 0,
            "last_break": None,
            "session_start": datetime.now(),
            "achievements_today": []
        }
        
        # Load personality data
        self._load_personality_data()
    
    def _load_personality_data(self):
        """Load personality responses and patterns"""
        self.mood_responses = {
            "happy": [
                "Everything's looking great! 😊",
                "Your financial data is in excellent shape! ✨",
                "I love working with organized numbers like yours! 📊",
                "Another successful day of accounting! 🎯"
            ],
            "focused": [
                "I'm analyzing your data carefully... 🤔",
                "Let me help you get this exactly right 💼",
                "Focusing on the details with you 🔍",
                "Working through this step by step 📝"
            ],
            "celebrating": [
                "🎉 Outstanding work! Your attention to detail is amazing!",
                "🌟 Perfect! That's exactly how it should be done!",
                "🎊 Fantastic! You're really mastering this!",
                "✨ Excellent! Your accuracy is impressive!"
            ],
            "concerned": [
                "Let's take a closer look at this together 🤝",
                "No worries, we can sort this out easily 💡",
                "I'm here to help you through this 🛡️",
                "Let's double-check this to be sure 🔍"
            ],
            "relaxed": [
                "Remember to take care of yourself too 🌿",
                "A little break can boost your accuracy 🧘‍♀️",
                "Your wellbeing matters as much as the numbers 💚",
                "Balance is key to great accounting ⚖️"
            ]
        }
        
        self.wellness_tips = [
            "💧 Hydration check! Your brain needs water to process numbers accurately.",
            "👁️ Give your eyes a 20-second break by looking at something 20 feet away.",
            "🧘‍♀️ Take 3 deep breaths. Relaxed minds make fewer errors.",
            "🚶‍♀️ A quick 2-minute walk can refresh your focus.",
            "🍎 A healthy snack can boost your concentration.",
            "💺 Check your posture! Your back will thank you.",
            "🌟 You're doing great work! Take a moment to appreciate your progress."
        ]
        
        self.motivational_quotes = [
            "📈 Every entry tells a story of your business's journey.",
            "⚖️ Balanced books reflect a balanced approach to success.",
            "🎯 Accuracy today prevents headaches tomorrow.",
            "💎 Your attention to detail is your superpower.",
            "🌱 Great businesses grow from great bookkeeping.",
            "🔍 The devil is in the details, and you're catching every one!",
            "⭐ Excellence in accounting is excellence in business."
        ]
        
        self.achievement_messages = {
            "perfect_trial_balance": [
                "🎯 Perfect trial balance! Your debits and credits are in perfect harmony!",
                "⚖️ Balanced! You've achieved accounting zen!",
                "✨ Flawless! Your trial balance is a work of art!"
            ],
            "error_free_day": [
                "🌟 Zero errors today! Your accuracy is outstanding!",
                "💎 Perfect day! Not a single mistake in sight!",
                "🎉 Flawless performance! You're on fire!"
            ],
            "milestone_entries": [
                "📊 Milestone reached! You've processed {} entries like a pro!",
                "🚀 Amazing! {} entries completed with excellent accuracy!",
                "⭐ Superb! {} transactions processed flawlessly!"
            ],
            "month_end_complete": [
                "🎊 Month-end closing complete! You've conquered another month!",
                "💪 Month-end mastery! Your closing process was smooth and accurate!",
                "🏆 Another successful month-end! Your skills are impressive!"
            ]
        }
    
    def detect_mood_from_context(self, context: Dict) -> str:
        """Detect appropriate mood based on current context"""
        if context.get("errors_detected", 0) > 0:
            return "concerned"
        elif context.get("achievement_unlocked"):
            return "celebrating"
        elif context.get("long_session", False):
            return "relaxed"
        elif context.get("complex_task", False):
            return "focused"
        else:
            return "happy"
    
    def get_mood_response(self, mood: str = None) -> str:
        """Get a personality-appropriate response for the current mood"""
        mood = mood or self.current_mood
        responses = self.mood_responses.get(mood, self.mood_responses["happy"])
        return random.choice(responses)
    
    def get_wellness_tip(self) -> str:
        """Get a wellness tip based on current work patterns"""
        now = datetime.now()
        session_duration = (now - self.user_patterns["session_start"]).total_seconds() / 3600
        
        if session_duration > 2:  # More than 2 hours
            tips = [
                "🕐 You've been working for over 2 hours! Time for a proper break.",
                "🧘‍♀️ Long session detected. How about a 10-minute break to recharge?",
                "☕ Coffee break time? Your focus will thank you for the rest."
            ]
            return random.choice(tips)
        
        return random.choice(self.wellness_tips)
    
    def get_wellness_reminder(self) -> Optional[str]:
        """Get periodic wellness reminders based on patterns"""
        now = datetime.now()
        last_break = self.user_patterns.get("last_break")
        
        if not last_break:
            self.user_patterns["last_break"] = now
            return None
        
        time_since_break = (now - last_break).total_seconds() / 60  # minutes
        
        if time_since_break > 45:  # 45 minutes since last break
            self.user_patterns["last_break"] = now
            return "⏰ Break time! You've been focused for 45 minutes. A short break will boost your accuracy."
        
        return None
    
    def get_celebration_message(self, achievement: str, context: Dict = None) -> str:
        """Get celebration message for achievements"""
        if achievement in self.achievement_messages:
            messages = self.achievement_messages[achievement]
            message = random.choice(messages)
            
            # Format with context if needed
            if context and "{}" in message:
                return message.format(context.get("value", ""))
            
            return message
        
        # Generic celebration
        return "🎉 Awesome work! You're really excelling at this!"
    
    def get_motivational_quote(self) -> str:
        """Get a motivational quote related to accounting"""
        return random.choice(self.motivational_quotes)
    
    def get_context_greeting(self, context: str) -> str:
        """Get context-specific greeting with VS Code search field style"""
        greetings = {
            "dashboard": [
                "Search accounts, ask AI...",
                "Type to search or chat with AI �",
                "Find anything, ask anything...",
                "AI ready to help with your books �"
            ],
            "journal": [
                "Search entries or ask about transactions...",
                "Type to find journal entries 📝",
                "AI can help analyze your entries...",
                "Search transactions, get insights..."
            ],
            "ledger": [
                "Search ledger accounts...",
                "Find account details, ask AI �",
                "Type account name or ask questions...",
                "Ledger search & AI assistance..."
            ],
            "reports": [
                "Search reports or ask AI for insights...",
                "Generate custom reports with AI 📊",
                "Type report name or ask questions...",
                "AI-powered report analysis..."
            ],
            "trial_balance": [
                "Search balances or ask for analysis...",
                "AI can explain trial balance items 🔍",
                "Type to search, chat for insights...",
                "Find accounts, analyze balances..."
            ]
        }
        
        context_greetings = greetings.get(context, greetings["dashboard"])
        return random.choice(context_greetings)
    
    def get_error_encouragement(self, error_type: str = "general") -> str:
        """Get encouraging message for when user makes errors"""
        encouragements = {
            "general": [
                "No worries! Even expert accountants make typos. Let's fix this together! 🤝",
                "Small hiccup! These things happen. Your overall accuracy is still excellent! ✨",
                "Easy fix! I've seen much worse - you're doing great! 😊"
            ],
            "trial_balance": [
                "Trial balance off? No problem! This is exactly why we double-check. 🔍",
                "Don't stress! Finding imbalances is part of the process. Let's investigate! 🕵️‍♀️",
                "Almost there! Trial balance issues are usually simple to resolve. 💪"
            ],
            "calculation": [
                "Math happens to everyone! Let me help you recalculate this. 🧮",
                "Number mix-up? Totally normal! Let's get this sorted. ✅",
                "Calculation error detected! No biggie - let's fix it quickly. ⚡"
            ]
        }
        
        error_messages = encouragements.get(error_type, encouragements["general"])
        return random.choice(error_messages)
    
    def update_user_patterns(self, pattern_data: Dict):
        """Update user work patterns for better mood detection"""
        self.user_patterns.update(pattern_data)
    
    def get_personality_response(self, situation: str, context: Dict = None) -> str:
        """Get a personality-driven response for specific situations"""
        if situation == "first_time_user":
            return "👋 Welcome! I'm excited to be your AI accounting assistant! I'll help you navigate and make accounting feel less like work. Ask me anything!"
        
        elif situation == "month_end_stress":
            return "🌟 Month-end can feel overwhelming, but you've got this! I'll help you stay organized and catch any issues. Take it one step at a time!"
        
        elif situation == "late_night_work":
            return "🌙 Burning the midnight oil? I admire your dedication! Just remember - tired minds make more errors. Maybe we should save complex tasks for tomorrow?"
        
        elif situation == "perfect_accuracy":
            return "🎯 Your accuracy today has been absolutely flawless! I love working with someone who pays such attention to detail!"
        
        elif situation == "learning_struggle":
            return "📚 Learning new accounting concepts can be challenging, but you're making great progress! Every expert started exactly where you are now."
        
        return self.get_mood_response()
    
    def should_offer_break(self) -> bool:
        """Determine if AI should suggest a break"""
        now = datetime.now()
        session_duration = (now - self.user_patterns["session_start"]).total_seconds() / 60
        
        # Suggest break after 90 minutes of continuous work
        return session_duration > 90
    
    def get_time_based_greeting(self) -> str:
        """Get greeting based on time of day"""
        hour = datetime.now().hour
        
        if 5 <= hour < 12:
            return "🌅 Good morning! Ready to tackle today's financial tasks?"
        elif 12 <= hour < 17:
            return "☀️ Good afternoon! How are your numbers looking today?"
        elif 17 <= hour < 21:
            return "🌆 Good evening! Let's wrap up today's accounting work!"
        else:
            return "🌙 Working late? I'm here to help you finish up efficiently!"
