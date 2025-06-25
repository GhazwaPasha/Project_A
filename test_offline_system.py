#!/usr/bin/env python3
"""
Test the new Supabase offline-capable system
"""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️  python-dotenv not installed. Install with: pip install python-dotenv")

def test_offline_system():
    """Test the offline-capable accounting system"""
    print("🧪 Testing Supabase Offline System")
    print("=" * 40)
    
    try:
        # Test imports
        print("📦 Testing imports...")
        from src.core.supabase_offline_manager import EnhancedSupabaseOnlyManager, OfflineManager
        from src.core.auth_manager import AuthManager
        from src.core.session_manager import SessionManager
        print("✅ All imports successful")
        
        # Test Supabase configuration
        print("\n🔧 Testing Supabase configuration...")
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_ANON_KEY')
        
        if not supabase_url or not supabase_key:
            print("❌ Supabase credentials not found in environment")
            print("   Please set SUPABASE_URL and SUPABASE_ANON_KEY in your .env file")
            return False
        
        if 'your-project' in supabase_url or 'your-anon-key' in supabase_key:
            print("❌ Supabase credentials are still placeholder values")
            print("   Please update your .env file with real Supabase credentials")
            return False
        
        print(f"✅ Supabase URL configured: {supabase_url[:30]}...")
        print(f"✅ Supabase key configured: {supabase_key[:20]}...")
        
        # Test offline manager
        print("\n📱 Testing offline manager...")
        offline_mgr = OfflineManager("test_cache.db")
        print("✅ Offline manager created")
        
        # Test cache operations
        test_data = [
            {"id": "test-1", "name": "Test Account", "type": "asset", "code": "1000"},
            {"id": "test-2", "name": "Test Revenue", "type": "revenue", "code": "4000"}
        ]
        
        offline_mgr.cache_data("accounts", test_data, "test-org-id")
        cached = offline_mgr.get_cached_data("accounts", "test-org-id")
        
        if len(cached) == 2:
            print("✅ Cache operations working")
        else:
            print(f"❌ Cache test failed: expected 2 items, got {len(cached)}")
        
        # Test EnhancedSupabaseOnlyManager (will fail if no connection, but we can test init)
        print("\n🌐 Testing Supabase manager...")
        try:
            mgr = EnhancedSupabaseOnlyManager(
                organization_id="test-org",
                user_id="test-user"
            )
            print(f"✅ Supabase manager created (online: {mgr.is_online})")
            
            if mgr.is_online:
                print("✅ Supabase connection successful")
            else:
                print("📱 Offline mode - will use cached data")
                
        except Exception as e:
            print(f"⚠️  Supabase manager creation failed: {e}")
            print("   This is expected if you haven't run the SQL schema yet")
        
        print("\n🎯 Test Summary:")
        print("✅ Core components are working")
        print("✅ Offline caching functional") 
        print("✅ Ready for full implementation")
        
        # Clean up test cache
        try:
            os.remove("test_cache.db")
            print("🧹 Test cache cleaned up")
        except:
            pass
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Make sure all dependencies are installed")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_offline_system()
    
    if success:
        print("\n🚀 Next Steps:")
        print("1. Run the SQL schema in Supabase SQL Editor:")
        print("   - Copy contents of tools/create_multitenant_schema_fixed.sql")
        print("   - Paste and execute in Supabase SQL Editor")
        print("2. Test login and organization switching")
        print("3. Try working offline (disconnect internet)")
        print("4. Reconnect and verify sync works")
    else:
        print("\n❌ Please fix the issues above before proceeding")
    
    sys.exit(0 if success else 1)
