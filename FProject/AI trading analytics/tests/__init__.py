"""
Tests for AI Trading Analytics.

- test_api_basic.py: Health, auth, public routes, 404 (unittest).
- test_api.py: Prediction API via requests (requires running app and demo user).
- test_api_endpoints.py: All API endpoints via requests (requires running app).
- test_db_connection.py: DB connection and basic queries (requires SQLite DB).
- test_exchange_client.py: CCXT exchange client (Binance, Bybit, OKX) public data.
- test_validation.py: utils.validators (username, email, password).
Run from project root: python -m pytest tests/ or python tests/test_*.py
"""
