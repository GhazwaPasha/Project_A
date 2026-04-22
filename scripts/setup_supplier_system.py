#!/usr/bin/env python3
"""
Setup script for the Supplier Management System
Creates the necessary database tables and functions for supplier management
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client

REPO_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(REPO_ROOT / ".env")


def setup_supplier_system():
    """Setup the supplier management system in the database"""

    print("🚀 Setting up Supplier Management System...")

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        print("❌ SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in .env")
        return False

    supabase = create_client(url, key)

    schema_file = REPO_ROOT / "database" / "SUPPLIER_SYSTEM_SCHEMA.sql"

    if not schema_file.exists():
        print(f"❌ Schema file not found: {schema_file}")
        return False

    with open(schema_file, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    print("📄 Reading supplier schema...")

    try:
        print("🔧 Creating supplier tables and functions...")
        result = supabase.rpc("exec_sql", {"sql": schema_sql})

        if result.data:
            print("✅ Supplier system setup completed successfully!")
            print("\n📋 Created tables:")
            print("  - suppliers")
            print("  - supplier_account_mappings")
            print("  - supplier_contacts")
            print("\n🔧 Created functions:")
            print("  - get_supplier_account_mappings()")
            print("  - update_supplier_balance()")
            print("\n🔐 RLS policies enabled for all tables")
            print("\n🎉 Supplier management system is ready to use!")
            return True

        print("❌ Failed to setup supplier system")
        if hasattr(result, "error") and result.error:
            print(f"Error: {result.error}")
        return False

    except Exception as e:
        print(f"❌ Error setting up supplier system: {str(e)}")
        return False


def main():
    print("=" * 60)
    print("SUPPLIER MANAGEMENT SYSTEM SETUP")
    print("=" * 60)

    success = setup_supplier_system()

    if success:
        print("\n" + "=" * 60)
        print("✅ SETUP COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Navigate to the Suppliers page in your web app")
        print("2. Create your first supplier with account mappings")
        print("3. Use suppliers when creating purchase vouchers")
        print("\nThe supplier system is now integrated with your voucher system!")
    else:
        print("\n" + "=" * 60)
        print("❌ SETUP FAILED!")
        print("=" * 60)
        print("Please check the error messages above and try again.")
        sys.exit(1)


if __name__ == "__main__":
    main()
