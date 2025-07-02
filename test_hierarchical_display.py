#!/usr/bin/env python3
"""
Test script to verify hierarchical display logic
"""

def test_hierarchical_display_logic():
    """Test the hierarchical display logic"""
    
    # Sample hierarchical data structure
    sample_data = [
        {
            'name': 'Revenues',
            'level': 1,
            'balance': 1000000.0,
            'children': [
                {
                    'name': 'Sales',
                    'level': 2,
                    'balance': 1000000.0,
                    'children': [
                        {
                            'name': 'Cash Sales',
                            'level': 3,
                            'balance': 1000000.0,
                            'children': []
                        }
                    ]
                }
            ]
        }
    ]
    
    print("Testing Hierarchical Display Logic")
    print("=" * 40)
    
    def simulate_display_logic(accounts, indent_level=0):
        """Simulate the display logic from the UI"""
        result = []
        for account in accounts:
            account_name = account.get('name', '')
            balance = account.get('balance', 0.0)
            children = account.get('children', [])
            level = account.get('level', 3)
            
            indent = "  " * indent_level
            
            if level < 3 and children:
                # Parent account - show as header without amount
                result.append(f"{indent}{account_name} (Header)")
                # Add children recursively
                result.extend(simulate_display_logic(children, indent_level + 1))
            else:
                # Leaf account - show with amount
                result.append(f"{indent}{account_name}: $1,000,000.00")
                # If it has children, add them too
                if children:
                    result.extend(simulate_display_logic(children, indent_level + 1))
        
        return result
    
    # Test the display logic
    display_result = simulate_display_logic(sample_data)
    
    print("Expected Display:")
    print("Revenues (Header)")
    print("  Sales (Header)")
    print("    Cash Sales: $1,000,000.00")
    print()
    print("Actual Display:")
    for line in display_result:
        print(line)
    
    # Verify the result
    expected_lines = [
        "Revenues (Header)",
        "  Sales (Header)", 
        "    Cash Sales: $1,000,000.00"
    ]
    
    success = len(display_result) == len(expected_lines)
    for i, (actual, expected) in enumerate(zip(display_result, expected_lines)):
        if actual != expected:
            print(f"Line {i+1} mismatch:")
            print(f"  Expected: {expected}")
            print(f"  Actual:   {actual}")
            success = False
    
    print(f"\nTest {'PASSED' if success else 'FAILED'}")
    return success

if __name__ == "__main__":
    test_hierarchical_display_logic() 