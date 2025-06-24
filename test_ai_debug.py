"""
Debug script to test the enhanced AI processor
"""
import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.ui.components.enhanced_ai_processor import ContextAwareAI

# Set the API key
os.environ.setdefault('MISTRAL_API_KEY', '***REMOVED***')

def test_ai_processor():
    print("🧪 Testing Enhanced AI Processor")
    print("=" * 40)
    
    # Create AI processor
    ai_processor = ContextAwareAI()
    
    # Test context updates
    print("📊 Testing context updates...")
    ai_processor.update_context('page', {'page': 'dashboard', 'data': {'test': 'data'}})
    ai_processor.update_context('application', {'startup_time': '2024-12-27T10:00:00'})
    print("✅ Context updates successful")
    
    # Test command processing (this will make an API call)
    print("\n🤖 Testing command processing...")
    
    # Simple test commands
    test_commands = [
        "show me the dashboard",
        "what is my current balance?",
        "generate a trial balance"
    ]
    
    def on_response(response):
        print(f"✅ AI Response: {response}")
    
    def on_error(error):
        print(f"❌ AI Error: {error}")
    
    def on_navigation(page, params):
        print(f"🧭 Navigation Request: {page} with params {params}")
    
    def on_report(report_type, params):
        print(f"📊 Report Request: {report_type} with params {params}")
    
    # Connect signals for testing
    ai_processor.response_ready.connect(on_response)
    ai_processor.error_occurred.connect(on_error)
    ai_processor.navigation_requested.connect(on_navigation)
    ai_processor.report_requested.connect(on_report)
    
    # Process a simple command
    print("\n🔍 Processing test command: 'show me the dashboard'")
    ai_processor.process_command("show me the dashboard")
    
    # Wait a bit for processing
    import time
    print("⏳ Waiting for AI response...")
    time.sleep(3)
    
    print("\n✅ Test completed!")

if __name__ == "__main__":
    test_ai_processor()
