#!/usr/bin/env python3
"""
Test script to check ratio calculation with group-based data
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.unified_accounting_system import UnifiedAccountingSystem
from src.core.financial_ratios import FinancialRatioCalculator
from src.core.supabase_manager import SupabaseManager
from src.core.auth_manager import AuthManager
from src.core.session_manager import SessionManager
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def test_ratio_calculation():
    """Test the ratio calculation with group-based data."""
    try:
        print("🔧 Setting up test environment...")
        
        # Initialize components
        supabase_manager = SupabaseManager()
        auth_manager = AuthManager()
        session_manager = SessionManager(auth_manager)
        
        # Create accounting system
        system = UnifiedAccountingSystem(auth_manager)
        
        # Set organization (you may need to adjust this)
        # system.set_organization("your-org-id")
        
        print("\n📊 Testing Group-Based Balance Sheet...")
        try:
            balance_data = system.generate_group_based_balance_sheet("2025-01-01")
            print(f"✅ Balance Sheet generated successfully")
            print(f"   - Structure: {balance_data.get('structure', 'unknown')}")
            print(f"   - Is group-based: {balance_data.get('is_group_based', False)}")
            print(f"   - Asset sections: {len(balance_data.get('asset_sections', []))}")
            print(f"   - Liability sections: {len(balance_data.get('liability_sections', []))}")
            print(f"   - Equity sections: {len(balance_data.get('equity_sections', []))}")
            print(f"   - Total Assets: {balance_data.get('total_assets', 0)}")
            print(f"   - Total Liabilities: {balance_data.get('total_liabilities', 0)}")
            print(f"   - Total Equity: {balance_data.get('total_equity', 0)}")
            
            # Show asset sections
            print("\n   Asset Sections:")
            for section in balance_data.get('asset_sections', []):
                print(f"     - {section['name']} ({section['group']}): {section['total']} ({len(section['accounts'])} accounts)")
                
            # Show liability sections
            print("\n   Liability Sections:")
            for section in balance_data.get('liability_sections', []):
                print(f"     - {section['name']} ({section['group']}): {section['total']} ({len(section['accounts'])} accounts)")
                
        except Exception as e:
            print(f"❌ Balance Sheet generation failed: {e}")
            import traceback
            traceback.print_exc()
            return
        
        print("\n📈 Testing Ratio Calculation...")
        try:
            # Create ratio calculator
            ratio_calculator = FinancialRatioCalculator(supabase_manager, system)
            
            # Calculate ratios
            from datetime import date
            ratio_data = ratio_calculator.calculate_all_ratios(date.today())
            
            print(f"✅ Ratio calculation completed")
            
            if 'error' in ratio_data:
                print(f"❌ Error in ratio calculation: {ratio_data['error']}")
                return
            
            # Show liquidity ratios
            liquidity_ratios = ratio_data.get('ratios', {}).get('liquidity', {})
            print(f"\n   Liquidity Ratios ({len(liquidity_ratios)} calculated):")
            for ratio_name, ratio_data in liquidity_ratios.items():
                print(f"     - {ratio_name}: {ratio_data.get('value', 0):.2f} ({ratio_data.get('unit', 'unknown')})")
                print(f"       Description: {ratio_data.get('description', 'N/A')}")
                print(f"       Interpretation: {ratio_data.get('interpretation', 'N/A')}")
            
            # Show other ratios
            for category, ratios in ratio_data.get('ratios', {}).items():
                if category != 'liquidity':
                    print(f"\n   {category.capitalize()} Ratios ({len(ratios)} calculated):")
                    for ratio_name, ratio_data in ratios.items():
                        print(f"     - {ratio_name}: {ratio_data.get('value', 0):.2f} ({ratio_data.get('unit', 'unknown')})")
            
        except Exception as e:
            print(f"❌ Ratio calculation failed: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n🎯 Test completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ratio_calculation() 