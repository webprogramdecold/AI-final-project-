"""
Business logic and external integrations for AI Trading Analytics.

This package provides:
- advanced_ai_predictor: Loads trained ML models and runs predictions (direction, target price). Used by app.py prediction routes.
- advanced_data_service: Fetches OHLCV from exchanges (CCXT), optional on-chain/sentiment/macro. Used by advanced_ai_predictor and train_advanced_ai_model.
- price_sync_service: Syncs OHLCV from exchange into price_history table. Used by app.py sync endpoint.
- realtime_price_service: Current price and recent OHLCV from exchange or DB fallback. Used by app.py and health check.
- exchange_service: Creates CCXT clients from user accounts and tests connections. Used by app.py exchanges and trading.
- exchange_client: Low-level CCXT client creation and balance/order methods. Used by app.py and tests.
- market_data_service: Fear & Greed Index and top-coins/live prices from external APIs. Used by app.py market endpoints.
- db_diagnostics: DB table counts, size, health. Used by app.py diagnostics endpoint.
- train_advanced_ai_model: Trains direction and return models, saves to services/models/. Run as script.
- feature_engineering: Shared compute_simple_indicators (RSI, MACD, MA ratio) for training and predictor.
"""
