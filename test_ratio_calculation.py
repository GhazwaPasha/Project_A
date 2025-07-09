#!/usr/bin/env python3
"""
Test script to verify ratio calculation functionality
"""

import sys
import os
from datetime import date

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core.financial_ratios import FinancialRatioCalculator
from core.config import DatabaseConfig
from supabase import create_client

def test_ratio_calculation():
    """Test the ratio calculation functionality."""
    
    print("🧪 Testing Ratio Calculation...")
    
    try:
        # Initialize Supabase client
        DatabaseConfig.validate_config()
        supabase_client = create_client(
            DatabaseConfig.SUPABASE_URL,
            DatabaseConfig.SUPABASE_ANON_KEY
        )
        
        # Create ratio calculator
        ratio_calculator = FinancialRatioCalculator(supabase_client)
        
        # Test with a specific organization ID (you may need to update this)
        org_id = "0946405f-3b8a-4fe5-8c29-125b39d9ca8e"  # From the debug logs
        
        # Set the organization ID manually for testing
        ratio_calculator.accounting_system = type('MockSystem', (), {
            'current_organization_id': org_id
        })()
        
        # Calculate ratios
        print(f"📊 Calculating ratios for organization: {org_id}")
        ratios_data = ratio_calculator.calculate_all_ratios(
            as_of_date=date(2025, 7, 10),
            from_date=date(2025, 1, 1),
            to_date=date(2025, 7, 10)
        )
        
        if 'error' in ratios_data:
            print(f"❌ Error calculating ratios: {ratios_data['error']}")
            return False
        
        print("✅ Ratio calculation successful!")
        print(f"📋 Available data keys: {list(ratios_data.keys())}")
        
        # Check if ratios are present
        ratios = ratios_data.get('ratios', {})
        print(f"📊 Available ratio categories: {list(ratios.keys())}")
        
        for category, category_ratios in ratios.items():
            print(f"   {category}: {list(category_ratios.keys())}")
            for ratio_name, ratio_data in category_ratios.items():
                value = ratio_data.get('value', 0)
                label = ratio_data.get('label', ratio_name)
                print(f"     {label}: {value}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during ratio calculation test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_ratio_calculation()
    if success:
        print("✅ Ratio calculation test completed successfully!")
    else:
        print("❌ Ratio calculation test failed!")
        sys.exit(1) 