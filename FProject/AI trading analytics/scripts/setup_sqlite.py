"""
Create SQLite database and all tables for AI Trading Analytics.

Creates the DB file and tables: users, price_history, predictions, portfolio,
trades, exchange_accounts, exchange_trade_logs, advanced_predictions. Inserts
a few sample price_history rows. If the DB file already exists, it is removed
and recreated. Run from project root so the DB is created in the current directory.

Used by: run manually for initial setup (no other code depends on this script).
"""

import os
import sqlite3

# Create DB in project root (same location models/db.py uses) so it works from any cwd.
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_SCRIPT_DIR)
DB_PATH = os.path.join(_PROJECT_ROOT, 'ai_trading.db')


def setup_sqlite_database():
    if os.path.exists(DB_PATH):
        print(f"Removing existing database: {DB_PATH}")
        os.remove(DB_PATH)

    print(f"Creating SQLite database: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            balance REAL DEFAULT 10000.00,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cur.execute("""
        CREATE TABLE price_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            open_price REAL NOT NULL,
            high_price REAL NOT NULL,
            low_price REAL NOT NULL,
            close_price REAL NOT NULL,
            volume REAL DEFAULT 0
        )
    """)
    cur.execute("""
        CREATE TABLE predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            prediction_class INTEGER NOT NULL,
            confidence REAL NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE portfolio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            symbol TEXT NOT NULL,
            quantity REAL NOT NULL,
            average_price REAL NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            UNIQUE (user_id, symbol)
        )
    """)
    cur.execute("""
        CREATE TABLE trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            symbol TEXT NOT NULL,
            side TEXT NOT NULL,
            quantity REAL NOT NULL,
            price REAL NOT NULL,
            total_amount REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    cur.execute("""
        CREATE TABLE exchange_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            exchange_name TEXT NOT NULL,
            account_label TEXT DEFAULT 'My Account',
            api_key TEXT NOT NULL,
            api_secret_encrypted TEXT NOT NULL,
            is_testnet INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_used_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    cur.execute("""
        CREATE TABLE exchange_trade_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            exchange_account_id INTEGER NOT NULL,
            symbol TEXT NOT NULL,
            side TEXT NOT NULL,
            amount REAL NOT NULL,
            price REAL NOT NULL,
            total_value REAL,
            status TEXT DEFAULT 'NEW',
            exchange_order_id TEXT,
            raw_response TEXT,
            trade_source TEXT DEFAULT 'manual',
            fee REAL DEFAULT 0,
            fee_currency TEXT,
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            filled_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (exchange_account_id) REFERENCES exchange_accounts(id) ON DELETE CASCADE
        )
    """)
    cur.execute("""
        CREATE TABLE advanced_predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            symbol TEXT NOT NULL,
            mode TEXT NOT NULL,
            timeframe TEXT NOT NULL,
            signal TEXT NOT NULL,
            direction TEXT,
            confidence REAL,
            current_price REAL NOT NULL,
            target_price REAL,
            pct_change REAL,
            summary TEXT,
            indicators_snapshot TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            target_time TIMESTAMP,
            actual_price REAL,
            outcome TEXT,
            accuracy_score REAL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Sample price rows for quick testing
    sample_prices = [
        ('BTCUSDT', '2025-11-13 09:00:00', 45000.00, 45500.00, 44800.00, 45200.00, 1250.50),
        ('BTCUSDT', '2025-11-13 10:00:00', 45200.00, 45800.00, 45100.00, 45600.00, 1380.75),
        ('BTCUSDT', '2025-11-13 11:00:00', 45600.00, 46000.00, 45400.00, 45900.00, 1520.25),
    ]
    for row in sample_prices:
        cur.execute(
            "INSERT INTO price_history (symbol, timestamp, open_price, high_price, low_price, close_price, volume) VALUES (?, ?, ?, ?, ?, ?, ?)",
            row
        )

    conn.commit()
    conn.close()

    print("Database created successfully.")
    print("Tables: users, price_history, predictions, portfolio, trades, exchange_accounts, exchange_trade_logs, advanced_predictions")

    # Create demo user so login works immediately (username: testuser, password: password123)
    import sys
    if _PROJECT_ROOT not in sys.path:
        sys.path.insert(0, _PROJECT_ROOT)
    try:
        from models import user_model
        if not user_model.get_user_by_username("testuser"):
            user_model.create_user("testuser", "test@example.com", "password123")
            print("Demo user created: username=testuser, password=password123")
        else:
            print("Demo user already exists: username=testuser, password=password123")
    except Exception as e:
        print(f"Could not create demo user: {e}. Run: python scripts/create_demo_user.py")

    print("Next: python app.py")


if __name__ == "__main__":
    setup_sqlite_database()
