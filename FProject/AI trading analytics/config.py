"""
Config for AI Trading Analytics.

DB (MySQL): DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, DB_PORT. models/db.py uses SQLite by default; use scripts/setup_sqlite.py for SQLite. App: SECRET_KEY, INITIAL_BALANCE, DEBUG. Live trading: LIVE_TRADING_ENABLED, REQUIRE_TRADE_CONFIRMATION. Market: CMC_API_KEY, CMC_BASE_URL, FEAR_GREED_API_URL, API_TIMEOUT. Used by app.py and services.
"""

import os

# Database (MySQL; SQLite used by models/db.py via setup_sqlite.py)
DB_HOST = 'localhost'
DB_USER = 'root'
DB_PASSWORD = 'your_password_here'
DB_NAME = 'ai_trading_db'
DB_PORT = 3306

# Application
SECRET_KEY = 'your-secret-key-change-this-in-production'
INITIAL_BALANCE = 10000.0
DEBUG = True

# Live trading: False = simulated; True = real exchange orders
LIVE_TRADING_ENABLED = False
REQUIRE_TRADE_CONFIRMATION = True

# CoinMarketCap (set CMC_API_KEY via env in production)
CMC_API_KEY = os.environ.get('CMC_API_KEY', '1d903b5d08d540aa8e7c8d8e36e68106')
CMC_BASE_URL = "https://pro-api.coinmarketcap.com/v1"

# Fear & Greed Index (Alternative.me; no key)
FEAR_GREED_API_URL = "https://api.alternative.me/fng/"
API_TIMEOUT = 10

