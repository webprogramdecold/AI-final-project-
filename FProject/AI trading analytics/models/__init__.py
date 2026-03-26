"""
Database layer for AI Trading Analytics.

This package exposes:
- db: Low-level SQLite helpers (get_connection, execute_query, fetch_all, fetch_one, test_connection).
  Used by all other modules in this package and by several services.
- user_model: User registration, login, and profile (used by app.py for auth and profile routes).
- exchange_account_model: Linked exchange accounts and trade logs (used by app.py exchanges/trading).
- advanced_prediction_model: Save and retrieve AI predictions and performance (used by app.py and services/advanced_ai_predictor).
"""

from . import db
from .db import (
    get_connection,
    execute_query,
    fetch_all,
    fetch_one,
    test_connection,
)
from . import user_model
from . import exchange_account_model
from . import advanced_prediction_model
