"""
Low-level database access for AI Trading Analytics.

This module provides SQLite connection and query helpers used by all other
models (user_model, exchange_account_model, advanced_prediction_model) and by
services that touch the database (e.g. price_sync_service, realtime_price_service).
It does not define tables; schema is created by setup_database.py / scripts/setup_sqlite.py.

Used by: app.py (via models), models/*.py, services/price_sync_service.py,
services/realtime_price_service.py, services/db_diagnostics.py, scripts.
"""

import os
import sqlite3

# SQLite is used for the default setup (no separate DB server required).
USE_SQLITE = True

# Project root = directory containing app.py (parent of this file's parent).
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Default database file path: always under project root so it's the same from any cwd.
DEFAULT_DB_PATH = os.path.join(_PROJECT_ROOT, 'ai_trading.db')


def get_connection(db_path=None):
    """
    Open a connection to the SQLite database.

    Returns:
        sqlite3.Connection with row_factory set to Row (dict-like access), or None on failure.
    """
    path = db_path or DEFAULT_DB_PATH
    try:
        conn = sqlite3.connect(path)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None


def execute_query(query, params=None):
    """
    Run an INSERT, UPDATE, or DELETE; commits and closes the connection.

    Args:
        query: SQL string with ? placeholders.
        params: Optional tuple of values.

    Returns:
        Last inserted row id for INSERT, or number of affected rows; None on failure.
    """
    conn = get_connection()
    if conn is None:
        return None
    try:
        cur = conn.cursor()
        if params:
            cur.execute(query, params)
        else:
            cur.execute(query)
        conn.commit()
        return cur.lastrowid if cur.lastrowid else cur.rowcount
    except Exception as e:
        print(f"Query execution error: {e}")
        conn.rollback()
        return None
    finally:
        if 'cur' in locals() and cur:
            cur.close()
        if conn:
            conn.close()


def fetch_all(query, params=None):
    """
    Run a SELECT and return all rows as a list of dicts.

    Args:
        query: SQL string with ? placeholders.
        params: Optional tuple of values.

    Returns:
        List of dicts (one per row), or None on failure.
    """
    conn = get_connection()
    if conn is None:
        return None
    try:
        cur = conn.cursor()
        if params:
            cur.execute(query, params)
        else:
            cur.execute(query)
        rows = cur.fetchall()
        return [dict(row) for row in rows]
    except Exception as e:
        print(f"Query error: {e}")
        return None
    finally:
        if 'cur' in locals() and cur:
            cur.close()
        if conn:
            conn.close()


def fetch_one(query, params=None):
    """
    Run a SELECT and return the first row as a dict, or None.

    Args:
        query: SQL string with ? placeholders.
        params: Optional tuple of values.

    Returns:
        One row as a dict, or None if no row or on failure.
    """
    conn = get_connection()
    if conn is None:
        return None
    try:
        cur = conn.cursor()
        if params:
            cur.execute(query, params)
        else:
            cur.execute(query)
        row = cur.fetchone()
        return dict(row) if row else None
    except Exception as e:
        print(f"Query error: {e}")
        return None
    finally:
        if 'cur' in locals() and cur:
            cur.close()
        if conn:
            conn.close()


def test_connection():
    """
    Verify that the database file can be opened.

    Returns:
        True if connection succeeds, False otherwise.
    """
    conn = get_connection()
    if conn:
        conn.close()
        return True
    return False
