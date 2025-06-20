from src.core.accounting_system_postgresql import AccountingSystem
import traceback

try:
    print("Creating system...")
    system = AccountingSystem()
    print("System created successfully")
    
    print("Testing get_statistics...")
    stats = system.get_statistics()
    print("Statistics retrieved successfully:", stats)
    print("Stats type:", type(stats))
    
    # Test cursor directly
    print("\nTesting cursor directly...")
    with system.db_manager.get_db_cursor() as cursor:
        cursor.execute("SELECT COUNT(*) as count FROM accounts")
        result = cursor.fetchone()
        print("Direct cursor result:", result)
        print("Result type:", type(result))
        print("Result['count']:", result['count'])
        
except Exception as e:
    print(f"Error: {e}")
    traceback.print_exc()
