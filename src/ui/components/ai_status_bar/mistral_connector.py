"""
Mistral API Connector - Handles AI responses and natural language processing
"""
import os
import json
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
from PyQt6.QtCore import QObject, pyqtSignal, QThread
import requests


class MistralConnector(QObject):
    """Handles communication with Mistral AI API for intelligent responses"""
    
    # Signals
    response_ready = pyqtSignal(str, dict)  # Response text and metadata
    error_occurred = pyqtSignal(str)  # Error message
    
    def __init__(self):
        super().__init__()
        
        # API Configuration
        self.api_key = os.getenv('MISTRAL_API_KEY')
        self.api_url = "https://api.mistral.ai/v1/chat/completions"
        self.model = "mistral-small"  # Using smaller model for faster responses
        
        # Context management
        self.conversation_history = []
        self.system_context = self._build_system_context()
        
        # Response templates for fallback
        self.fallback_responses = self._load_fallback_responses()
    
    def _build_system_context(self) -> str:
        """Build system context for AI assistant"""
        return """You are an AI accounting assistant with a friendly, supportive personality. 
        You help users with:
        - Accounting questions and explanations
        - Financial data analysis and insights
        - Productivity tips and reminders
        - Wellness advice for accounting professionals
        - Motivation and encouragement
        
        Guidelines:
        - Be concise but helpful (keep responses under 100 words usually)
        - Use accounting terminology appropriately
        - Be encouraging when users make mistakes
        - Offer specific, actionable advice
        - Use appropriate emojis to convey personality
        - Focus on accuracy and best practices
        - Suggest breaks and wellness when appropriate
        
        Current date: {date}
        
        Remember: You're not just answering questions - you're a supportive colleague who cares about the user's success and wellbeing.""".format(
            date=datetime.now().strftime("%Y-%m-%d")
        )
    
    def _load_fallback_responses(self) -> Dict[str, List[str]]:
        """Load fallback responses for when API is unavailable"""
        return {
            "general": [
                "I'm here to help! What accounting question can I assist you with? 😊",
                "Let's work on this together! What do you need help with? 💼",
                "I'm ready to help you with your accounting tasks! What's on your mind? 📊"
            ],
            "cash_flow": [
                "Cash flow is the lifeblood of business! Let me help you analyze your cash position. 💰",
                "Understanding cash flow trends helps you make better business decisions. 📈",
                "I can help you track where your money comes from and where it goes! 💸"
            ],
            "trial_balance": [
                "A balanced trial balance means your debits equal your credits - the foundation of accurate accounting! ⚖️",
                "Trial balance issues are common but fixable! Let's find what's causing the imbalance. 🔍",
                "Perfect trial balance = peace of mind! Let's make sure everything adds up correctly. ✅"
            ],
            "journal_entries": [
                "Every transaction tells a story! Let me help you record it properly. ✍️",
                "Remember: Debits on the left, credits on the right, and always balance! 📝",
                "Journal entries are the building blocks of financial statements. Let's get them right! 🏗️"
            ],
            "reports": [
                "Financial reports turn raw data into business insights! Which report interests you? 📊",
                "Reports help you understand your business performance. What would you like to analyze? 📈",
                "From profit & loss to balance sheets, I can help you interpret your financial story! 📋"
            ],
            "motivation": [
                "You're doing great work! Attention to detail in accounting really matters. 🌟",
                "Every number you enter contributes to a clear financial picture. Keep it up! 💪",
                "Accounting excellence comes from consistent, careful work - and you're nailing it! 🎯"
            ],
            "wellness": [
                "Remember to take breaks! Your accuracy improves when you're well-rested. 🧘‍♀️",
                "Hydration check! Your brain needs water to process all those numbers. 💧",
                "Stretch those shoulders! Accounting involves a lot of computer work. 🤸‍♀️"
            ],
            "error_help": [
                "No worries! Even expert accountants make errors. Let's fix this together! 🤝",
                "Mistakes happen! The important thing is catching and correcting them. 🔧",
                "Error detected? Perfect! That means our checks are working. Let's resolve it! ✨"
            ]
        }
    
    def get_ai_response(self, user_input: str, context: Dict[str, Any] = None) -> None:
        """Get AI response for user input (async)"""
        # Start processing in background thread
        self.thread = MistralWorkerThread(
            user_input, 
            context or {}, 
            self.api_key, 
            self.conversation_history.copy(),
            self.system_context
        )
        self.thread.response_ready.connect(self._handle_api_response)
        self.thread.error_occurred.connect(self._handle_api_error)
        self.thread.start()
    
    def _handle_api_response(self, response: str, metadata: dict):
        """Handle successful API response"""
        # Add to conversation history
        self.conversation_history.append({
            "role": "assistant",
            "content": response,
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep conversation history manageable
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-15:]
        
        self.response_ready.emit(response, metadata)
    
    def _handle_api_error(self, error_message: str):
        """Handle API error with fallback response"""
        # Try to provide contextual fallback
        fallback = self._get_fallback_response(error_message)
        
        self.response_ready.emit(fallback, {"fallback": True, "error": error_message})
    
    def _get_fallback_response(self, context_hint: str = "") -> str:
        """Get appropriate fallback response"""
        # Determine context from hint
        context_hint = context_hint.lower()
        
        if any(word in context_hint for word in ["cash", "flow", "money"]):
            category = "cash_flow"
        elif any(word in context_hint for word in ["trial", "balance", "debit", "credit"]):
            category = "trial_balance"
        elif any(word in context_hint for word in ["journal", "entry", "transaction"]):
            category = "journal_entries"
        elif any(word in context_hint for word in ["report", "statement", "analysis"]):
            category = "reports"
        elif any(word in context_hint for word in ["error", "mistake", "wrong"]):
            category = "error_help"
        elif any(word in context_hint for word in ["break", "tired", "stress"]):
            category = "wellness"
        elif any(word in context_hint for word in ["good", "great", "perfect"]):
            category = "motivation"
        else:
            category = "general"
        
        responses = self.fallback_responses.get(category, self.fallback_responses["general"])
        return responses[0]  # Return first response for consistency
    
    def parse_accounting_command(self, command: str) -> Dict[str, Any]:
        """Parse accounting-specific commands"""
        command = command.lower().strip()
        
        # Command patterns
        if "cash" in command and ("position" in command or "flow" in command):
            return {"type": "cash_analysis", "action": "show_cash_position"}
        
        elif "trial balance" in command:
            return {"type": "trial_balance", "action": "show_trial_balance"}
        
        elif "remind" in command:
            return {"type": "reminder", "action": "create_reminder", "text": command}
        
        elif any(word in command for word in ["create", "add", "record"]) and "entry" in command:
            return {"type": "journal_entry", "action": "create_entry"}
        
        elif "report" in command or "statement" in command:
            return {"type": "report", "action": "generate_report"}
        
        elif any(word in command for word in ["break", "rest", "tired"]):
            return {"type": "wellness", "action": "suggest_break"}
        
        elif "help" in command:
            return {"type": "help", "action": "provide_help"}
        
        else:
            return {"type": "general", "action": "chat", "text": command}
    
    def get_contextual_prompt(self, user_input: str, context: Dict[str, Any]) -> str:
        """Build contextual prompt for AI"""
        # Base user input
        prompt_parts = [f"User says: {user_input}"]
        
        # Add context information
        if context.get("current_page"):
            prompt_parts.append(f"Current page: {context['current_page']}")
        
        if context.get("trial_balance_balanced") is not None:
            status = "balanced" if context["trial_balance_balanced"] else "NOT balanced"
            prompt_parts.append(f"Trial balance status: {status}")
        
        if context.get("session_duration"):
            duration = context["session_duration"]
            prompt_parts.append(f"User has been working for {duration:.1f} hours")
        
        if context.get("stress_indicators"):
            indicators = ", ".join(context["stress_indicators"])
            prompt_parts.append(f"Stress indicators: {indicators}")
        
        if context.get("recent_errors"):
            prompt_parts.append(f"Recent errors detected: {context['recent_errors']}")
        
        # Add user behavior context
        if context.get("user_pattern"):
            prompt_parts.append(f"User behavior pattern: {context['user_pattern']}")
        
        return " | ".join(prompt_parts)
    
    def add_user_message(self, message: str):
        """Add user message to conversation history"""
        self.conversation_history.append({
            "role": "user",
            "content": message,
            "timestamp": datetime.now().isoformat()
        })
    
    def clear_conversation(self):
        """Clear conversation history"""
        self.conversation_history = []
    
    def get_conversation_summary(self) -> str:
        """Get summary of recent conversation"""
        if not self.conversation_history:
            return "No recent conversation"
        
        recent_messages = self.conversation_history[-6:]  # Last 6 messages
        summary_parts = []
        
        for msg in recent_messages:
            role = "You" if msg["role"] == "user" else "AI"
            content = msg["content"][:50] + "..." if len(msg["content"]) > 50 else msg["content"]
            summary_parts.append(f"{role}: {content}")
        
        return " | ".join(summary_parts)


class MistralWorkerThread(QThread):
    """Worker thread for Mistral API calls"""
    
    response_ready = pyqtSignal(str, dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, user_input, context, api_key, conversation_history, system_context):
        super().__init__()
        self.user_input = user_input
        self.context = context
        self.api_key = api_key
        self.conversation_history = conversation_history
        self.system_context = system_context
    
    def run(self):
        """Run API call in background thread"""
        try:
            if not self.api_key:
                raise Exception("Mistral API key not found")
            
            # Build messages for API
            messages = [
                {"role": "system", "content": self.system_context}
            ]
            
            # Add recent conversation history (last 10 messages)
            recent_history = self.conversation_history[-10:] if self.conversation_history else []
            for msg in recent_history:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
            
            # Add current user input with context
            contextual_input = self._build_contextual_input()
            messages.append({
                "role": "user", 
                "content": contextual_input
            })
            
            # Make API call
            response = self._call_mistral_api(messages)
            
            if response:
                content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
                if content:
                    metadata = {
                        "model": response.get("model"),
                        "tokens_used": response.get("usage", {}).get("total_tokens", 0),
                        "timestamp": datetime.now().isoformat()
                    }
                    self.response_ready.emit(content.strip(), metadata)
                else:
                    self.error_occurred.emit("Empty response from API")
            else:
                self.error_occurred.emit("No response from API")
                
        except Exception as e:
            self.error_occurred.emit(str(e))
    
    def _build_contextual_input(self) -> str:
        """Build contextual input with user message and context"""
        parts = [self.user_input]
        
        # Add relevant context
        if self.context.get("current_page"):
            parts.append(f"[User is currently on {self.context['current_page']} page]")
        
        if self.context.get("trial_balance_balanced") is False:
            parts.append("[Trial balance is currently unbalanced]")
        
        if self.context.get("session_duration", 0) > 2:
            parts.append("[User has been working for over 2 hours]")
        
        return " ".join(parts)
    
    def _call_mistral_api(self, messages: List[Dict]) -> Optional[Dict]:
        """Make actual API call to Mistral"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "mistral-small",
            "messages": messages,
            "max_tokens": 150,  # Keep responses concise
            "temperature": 0.7,  # Balanced creativity
            "stream": False
        }
        
        try:
            response = requests.post(
                "https://api.mistral.ai/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=10  # 10 second timeout
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"API error: {response.status_code} - {response.text}")
                
        except requests.exceptions.Timeout:
            raise Exception("API request timed out")
        except requests.exceptions.ConnectionError:
            raise Exception("Connection error - check internet connection")
        except Exception as e:
            raise Exception(f"API call failed: {str(e)}")
