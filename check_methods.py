#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.unified_accounting_system import UnifiedAccountingSystem

# List all methods
methods = [m for m in dir(UnifiedAccountingSystem) if not m.startswith('_')]
print("UnifiedAccountingSystem methods:")
for method in sorted(methods):
    print(f"  {method}")

# Check if it has chart of accounts method
if hasattr(UnifiedAccountingSystem, 'get_chart_of_accounts'):
    print("\n✅ get_chart_of_accounts exists")
else:
    print("\n❌ get_chart_of_accounts does not exist")

if hasattr(UnifiedAccountingSystem, 'get_all_accounts'):
    print("✅ get_all_accounts exists")
else:
    print("❌ get_all_accounts does not exist")
