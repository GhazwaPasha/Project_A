from src.core.accounting_system import AccountingSystem

def test_fuzzy_account_matching():
    system = AccountingSystem()
    print("=== Testing Fuzzy Account Matching ===")
    
    # Test cases with partial matches
    test_cases = [
        "cash",              # Should match "Cash in Hand", "Cash at Bank", or "Petty Cash"
        "bank",              # Should match "Cash at Bank"
        "hand",              # Should match "Cash in Hand"
        "petty",            # Should match "Petty Cash"
        "goods",            # Should match "Cost of Goods Sold"
        "cogs",             # Should match "Cost of Goods Sold" by code
        "5101",             # Should match by code
        "5101 - COGS",      # Should match by code-name format
        "sold"              # Should match "Cost of Goods Sold"
    ]
    
    for search_term in test_cases:
        print(f"\nTesting search term: '{search_term}'")
        name, acc_type, code = system.resolve_account(search_term)
        if name:
            print(f"✓ Found match: {name} (Type: {acc_type}, Code: {code})")
        else:
            print(f"✗ No match found")

if __name__ == "__main__":
    test_fuzzy_account_matching()
