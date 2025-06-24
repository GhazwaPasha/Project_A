#!/usr/bin/env python3
"""
Script to clear journal entries from the accounting system.

Updated for the new Supabase-based system.
"""

import os
import sys

def main():
    print("🗑️ Clear Journal Tool")
    print("=" * 25)
    print("❌ This tool needs to be updated to work with the new Supabase-based system.")
    print("The old AccountingSystem has been replaced with supabase_offline_manager.")
    print("")
    print("To use this tool:")
    print("1. Update to use EnhancedSupabaseOnlyManager")
    print("2. Add proper authentication and organization context")
    print("3. Use the new data deletion methods with proper RLS")
    print("")
    print("For now, you can delete data directly from Supabase dashboard.")
    print("")
    print("⚠️ Warning: This tool will delete all journal entries in the current organization!")

if __name__ == '__main__':
    main()
