"""
Test database connection and basic queries for AI Trading Analytics.

Runs connection test, fetch users, fetch one user, fetch price_history, list tables.
Requires SQLite DB (run scripts/setup_sqlite.py first). Run from project root: python3 tests/test_db_connection.py
"""

import sys
from pathlib import Path

_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from models import db


def main():
    print("=" * 60)
    print("AI Trading Analytics - Database Connection Test")
    print("=" * 60)
    
    print("\n[Test 1] Testing database connection...")
    print("-" * 60)
    if db.test_connection():
        print("✅ Test 1 PASSED: Database connection works!")
    else:
        print("❌ Test 1 FAILED: Cannot connect to database")
        print("\n💡 Make sure:")
        print("   1. You are in the project root (directory containing app.py)")
        print("   2. SQLite database exists (run scripts/setup_sqlite.py or use app)")
        print("   3. For MySQL: run setup_database.py and set config accordingly")
        return
    
    print("\n[Test 2] Fetching all users from database...")
    print("-" * 60)
    query = "SELECT * FROM users"
    users = db.fetch_all(query)
    
    if users is not None:
        print(f"✅ Test 2 PASSED: Found {len(users)} user(s)")
        for user in users:
            print(f"   - User ID: {user['id']}, Username: {user['username']}, Balance: ${user['balance']}")
    else:
        print("❌ Test 2 FAILED: Could not fetch users")
    
    print("\n[Test 3] Fetching one user (ID = 1)...")
    print("-" * 60)
    query = "SELECT * FROM users WHERE id = ?"
    user = db.fetch_one(query, (1,))
    
    if user:
        print("✅ Test 3 PASSED: User found")
        print(f"   Username: {user['username']}")
        print(f"   Email: {user['email']}")
        print(f"   Balance: ${user['balance']}")
    else:
        print("⚠️  Test 3: No user with ID = 1 found (this is OK if no data)")
    
    print("\n[Test 4] Fetching price history...")
    print("-" * 60)
    query = "SELECT * FROM price_history LIMIT 5"
    prices = db.fetch_all(query)
    
    if prices is not None:
        print(f"✅ Test 4 PASSED: Found {len(prices)} price record(s)")
        for price in prices:
            print(f"   - {price['symbol']}: ${price['close_price']} at {price['timestamp']}")
    else:
        print("❌ Test 4 FAILED: Could not fetch price history")
    
    print("\n[Test 5] Checking database tables...")
    print("-" * 60)
    query = "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    tables = db.fetch_all(query)
    
    if tables:
        print(f"✅ Test 5 PASSED: Found {len(tables)} table(s)")
        for table in tables:
            table_name = table.get('name', list(table.values())[0])
            print(f"   - {table_name}")
    else:
        print("❌ Test 5 FAILED: Could not list tables")
    
    print("\n" + "=" * 60)
    print("✅ All basic database tests completed!")
    print("=" * 60)
    print("\n💡 Your database connection is working correctly.")
    print("   You can now use these functions in your Flask app:")
    print("   - db.get_connection()")
    print("   - db.execute_query(query, params)")
    print("   - db.fetch_all(query, params)")
    print("   - db.fetch_one(query, params)")
    print()


if __name__ == "__main__":
    main()

