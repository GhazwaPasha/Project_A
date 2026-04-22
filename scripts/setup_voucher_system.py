#!/usr/bin/env python3
"""
Setup script for the voucher system
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client, Client

REPO_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(REPO_ROOT / ".env")


def get_supabase_client() -> Client:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    if not url or not key:
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY (recommended) or SUPABASE_ANON_KEY must be set in .env"
        )
    return create_client(url, key)


def setup_voucher_system():
    """Setup the voucher system database schema"""

    print("🚀 Setting up Voucher System...")

    schema_file = REPO_ROOT / "database" / "VOUCHER_SYSTEM_SCHEMA.sql"
    if not schema_file.exists():
        print(f"❌ Schema file not found: {schema_file}")
        return False

    with open(schema_file, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    print(f"📖 Read schema file: {len(schema_sql)} characters")

    try:
        supabase = get_supabase_client()
        print("✅ Connected to Supabase")

        print("🔧 Executing schema...")
        result = supabase.rpc("exec_sql", {"sql": schema_sql})

        if result.data:
            print("✅ Voucher system schema executed successfully!")
            print(f"📊 Result: {result.data}")
        else:
            print("⚠️  Schema execution completed (no data returned)")

        print("\n🧪 Testing voucher functions...")

        try:
            test_result = supabase.rpc(
                "generate_voucher_number",
                {
                    "p_voucher_type": "purchase",
                    "p_org_id": "00000000-0000-0000-0000-000000000000",
                },
            )
            print(f"✅ generate_voucher_number test: {test_result.data}")
        except Exception as e:
            print(f"⚠️  generate_voucher_number test failed: {e}")

        try:
            test_result = supabase.rpc(
                "assign_voucher_approver",
                {"org_id": "00000000-0000-0000-0000-000000000000"},
            )
            print(f"✅ assign_voucher_approver test: {test_result.data}")
        except Exception as e:
            print(f"⚠️  assign_voucher_approver test failed: {e}")

        print("\n🎉 Voucher system setup completed successfully!")
        return True

    except Exception as e:
        print(f"❌ Error setting up voucher system: {e}")
        return False


if __name__ == "__main__":
    success = setup_voucher_system()
    sys.exit(0 if success else 1)
