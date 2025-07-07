#!/usr/bin/env python3
"""
Simple script to fix organization owner policies for journal_entry_lines table.
Runs SQL statements directly without using RPC.
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.supabase_manager import SupabaseManager

def main():
    """Run the organization owner policies fix."""
    print("🔧 Fixing organization owner policies for journal_entry_lines...")
    
    try:
        # Initialize database manager
        db_manager = SupabaseManager()
        print("✅ Connected to database")
        
        # Step 1: Add policy for organization owners
        print("📝 Adding organization owner policy...")
        create_owner_policy = """
        CREATE POLICY "journal_entry_lines_modify_owners" ON public.journal_entry_lines
            FOR ALL USING (
                EXISTS (
                    SELECT 1 FROM public.journal_entries je
                    WHERE je.id = journal_entry_id
                    AND public.get_user_organization_role(je.organization_id) = 'organization_owner'
                )
            );
        """
        
        try:
            db_manager.supabase.rpc('exec', {'sql': create_owner_policy}).execute()
            print("✅ Organization owner policy added")
        except Exception as e:
            if "already exists" in str(e).lower():
                print("ℹ️  Organization owner policy already exists")
            else:
                print(f"⚠️  Could not add owner policy: {e}")
        
        # Step 2: Drop old member-only policies
        print("📝 Removing restrictive member-only policies...")
        drop_policies = [
            "DROP POLICY IF EXISTS \"journal_entry_lines_insert_members\" ON public.journal_entry_lines;",
            "DROP POLICY IF EXISTS \"journal_entry_lines_update_members\" ON public.journal_entry_lines;",
            "DROP POLICY IF EXISTS \"journal_entry_lines_delete_members\" ON public.journal_entry_lines;"
        ]
        
        for drop_sql in drop_policies:
            try:
                db_manager.supabase.rpc('exec', {'sql': drop_sql}).execute()
            except Exception as e:
                print(f"ℹ️  Policy drop: {e}")
        
        # Step 3: Create comprehensive policies for owners and accountants
        print("📝 Creating comprehensive policies for owners and accountants...")
        
        new_policies = [
            """
            CREATE POLICY "journal_entry_lines_insert_owners_accountants" ON public.journal_entry_lines
                FOR INSERT WITH CHECK (
                    EXISTS (
                        SELECT 1 FROM public.journal_entries je
                        WHERE je.id = journal_entry_id
                        AND public.get_user_organization_role(je.organization_id) IN ('organization_owner', 'accountant')
                    )
                );
            """,
            """
            CREATE POLICY "journal_entry_lines_update_owners_accountants" ON public.journal_entry_lines
                FOR UPDATE USING (
                    EXISTS (
                        SELECT 1 FROM public.journal_entries je
                        WHERE je.id = journal_entry_id
                        AND public.get_user_organization_role(je.organization_id) IN ('organization_owner', 'accountant')
                    )
                );
            """,
            """
            CREATE POLICY "journal_entry_lines_delete_owners_accountants" ON public.journal_entry_lines
                FOR DELETE USING (
                    EXISTS (
                        SELECT 1 FROM public.journal_entries je
                        WHERE je.id = journal_entry_id
                        AND public.get_user_organization_role(je.organization_id) IN ('organization_owner', 'accountant')
                    )
                );
            """
        ]
        
        for policy_sql in new_policies:
            try:
                db_manager.supabase.rpc('exec', {'sql': policy_sql}).execute()
                print("✅ Policy created successfully")
            except Exception as e:
                if "already exists" in str(e).lower():
                    print("ℹ️  Policy already exists")
                else:
                    print(f"⚠️  Could not create policy: {e}")
        
        print("\n🎉 Migration completed!")
        print("📊 Organization owners should now have proper access to journal entry lines.")
        
        # Verify policies exist
        print("\n📋 Verifying policies...")
        try:
            result = db_manager.supabase.rpc('exec', {
                'sql': """
                SELECT policyname, cmd 
                FROM pg_policies 
                WHERE tablename = 'journal_entry_lines'
                ORDER BY policyname;
                """
            }).execute()
            
            if result.data:
                print("Current policies on journal_entry_lines:")
                for policy in result.data:
                    print(f"  - {policy.get('policyname')} ({policy.get('cmd')})")
            else:
                print("ℹ️  Could not retrieve policy information")
                
        except Exception as e:
            print(f"ℹ️  Could not verify policies: {e}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n💡 Manual fix:")
        print("1. Go to your Supabase SQL editor")
        print("2. Run the SQL from 'add_organization_owner_policies.sql' manually")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1) 