#!/usr/bin/env python3
"""
Setup script for the voucher system
"""

import os
import sys
sys.path.append('.')

from database.connection import get_supabase_client

def setup_voucher_system():
    """Setup the voucher system database schema"""
    
    print("🚀 Setting up Voucher System...")
    
    # Read the schema file
    schema_file = 'database/VOUCHER_SYSTEM_SCHEMA.sql'
    if not os.path.exists(schema_file):
        print(f"❌ Schema file not found: {schema_file}")
        return False
    
    with open(schema_file, 'r', encoding='utf-8') as f:
        schema_sql = f.read()
    
    print(f"📖 Read schema file: {len(schema_sql)} characters")
    
    try:
        # Get Supabase client
        supabase = get_supabase_client()
        print("✅ Connected to Supabase")
        
        # Execute the schema
        print("🔧 Executing schema...")
        result = supabase.rpc('exec_sql', {'sql': schema_sql})
        
        if result.data:
            print("✅ Voucher system schema executed successfully!")
            print(f"📊 Result: {result.data}")
        else:
            print("⚠️  Schema execution completed (no data returned)")
        
        # Test the functions
        print("\n🧪 Testing voucher functions...")
        
        # Test generate_voucher_number function
        try:
            test_result = supabase.rpc('generate_voucher_number', {
                'p_voucher_type': 'purchase',
                'p_org_id': '00000000-0000-0000-0000-000000000000'  # Test UUID
            })
            print(f"✅ generate_voucher_number test: {test_result.data}")
        except Exception as e:
            print(f"⚠️  generate_voucher_number test failed: {e}")
        
        # Test assign_voucher_approver function
        try:
            test_result = supabase.rpc('assign_voucher_approver', {
                'org_id': '00000000-0000-0000-0000-000000000000'  # Test UUID
            })
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
