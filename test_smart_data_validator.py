#!/usr/bin/env python3
"""
Test script for Smart Data Validator
Verifies that expensive operations are prevented when there's no data.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.smart_data_validator import SmartDataValidator

class MockSystem:
    """Mock system for testing"""
    def __init__(self, has_data=True):
        self.current_organization_id = "test-org-123"
        self.has_data = has_data
        self.supabase = MockSupabase(has_data)
    
    def _test_connectivity(self):
        return True

class MockSupabase:
    """Mock Supabase client"""
    def __init__(self, has_data=True):
        self.has_data = has_data
    
    def table(self, table_name):
        return MockTable(self.has_data)

class MockTable:
    """Mock table"""
    def __init__(self, has_data=True):
        self.has_data = has_data
    
    def select(self, *args, **kwargs):
        return self
    
    def eq(self, *args, **kwargs):
        return self
    
    def limit(self, *args, **kwargs):
        return self
    
    def execute(self):
        class MockResult:
            def __init__(self, has_data):
                self.count = 5 if has_data else 0
                self.data = [{"id": 1}] if has_data else []
        
        return MockResult(self.has_data)

def test_smart_data_validator():
    """Test the smart data validator"""
    print("🧪 Testing Smart Data Validator...")
    
    # Test with data
    print("\n📊 Test 1: System with data")
    system_with_data = MockSystem(has_data=True)
    validator_with_data = SmartDataValidator(system_with_data)
    
    has_data_result = validator_with_data.has_any_data()
    print(f"   has_any_data(): {has_data_result}")
    assert has_data_result == True, "Should return True when data exists"
    
    # Test without data
    print("\n📊 Test 2: System without data")
    system_without_data = MockSystem(has_data=False)
    validator_without_data = SmartDataValidator(system_without_data)
    
    has_data_result = validator_without_data.has_any_data()
    print(f"   has_any_data(): {has_data_result}")
    assert has_data_result == False, "Should return False when no data exists"
    
    # Test validation before expensive operation
    print("\n📊 Test 3: Validation before expensive operation")
    should_proceed = validator_with_data.validate_before_expensive_operation("test_operation")
    print(f"   validate_before_expensive_operation(): {should_proceed}")
    assert should_proceed == True, "Should proceed when data exists"
    
    should_proceed = validator_without_data.validate_before_expensive_operation("test_operation")
    print(f"   validate_before_expensive_operation(): {should_proceed}")
    assert should_proceed == False, "Should not proceed when no data exists"
    
    # Test safe empty results
    print("\n📊 Test 4: Safe empty results")
    empty_ledger = validator_without_data.get_safe_empty_result('ledger')
    print(f"   get_safe_empty_result('ledger'): {empty_ledger}")
    assert empty_ledger == [], "Should return empty list for ledger"
    
    empty_ratios = validator_without_data.get_safe_empty_result('ratios')
    print(f"   get_safe_empty_result('ratios'): {empty_ratios}")
    assert 'error' in empty_ratios, "Should return error for ratios"
    
    print("\n✅ All tests passed! Smart Data Validator is working correctly.")

if __name__ == "__main__":
    test_smart_data_validator() 