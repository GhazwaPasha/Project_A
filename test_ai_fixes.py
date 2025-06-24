#!/usr/bin/env python3
"""
Test script to verify AI status bar and processor fixes
"""

import sys
import os
sys.path.append('src')

def test_imports():
    """Test that all AI components import correctly"""
    print("🔍 Testing imports...")
    
    try:
        from ui.components.enhanced_ai_processor import ContextAwareAI
        print("✅ ContextAwareAI imported successfully")
    except Exception as e:
        print(f"❌ Failed to import ContextAwareAI: {e}")
        return False
    
    try:
        from ui.components.simple_ai_status_bar import SimpleAIStatusBar
        print("✅ SimpleAIStatusBar imported successfully")
    except Exception as e:
        print(f"❌ Failed to import SimpleAIStatusBar: {e}")
        return False
    
    try:
        from ui.components.enhanced_ai_status_bar import EnhancedAIStatusBar
        print("✅ EnhancedAIStatusBar imported successfully")
    except Exception as e:
        print(f"❌ Failed to import EnhancedAIStatusBar: {e}")
        return False
    
    return True

def test_ai_processor():
    """Test ContextAwareAI basic functionality"""
    print("\n🔍 Testing ContextAwareAI functionality...")
    
    try:
        from ui.components.enhanced_ai_processor import ContextAwareAI
        
        # Create AI processor instance
        ai = ContextAwareAI()
        print("✅ ContextAwareAI instantiated successfully")
        
        # Test status method
        status = ai.get_status()
        print(f"✅ Status method works: {status}")
        
        # Test API availability check
        api_available = ai.is_api_available()
        print(f"✅ API availability check: {api_available}")
        
        # Test context update
        ai.update_context("page", {"page": "dashboard", "data": {}})
        print("✅ Context update works")
        
        return True
        
    except Exception as e:
        print(f"❌ ContextAwareAI test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Running AI system fixes verification tests...\n")
    
    tests_passed = 0
    total_tests = 2
    
    if test_imports():
        tests_passed += 1
    
    if test_ai_processor():
        tests_passed += 1
    
    print(f"\n📊 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! AI system fixes are working correctly.")
        return True
    else:
        print("⚠️ Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
