"""
Database diagnostics for AI Trading Analytics.

Provides table record counts, table metadata (columns, sample rows), DB file size,
and a health check (status, issues, recommendations). Used by app.py diagnostics
endpoint. Uses models/db (fetch_one, fetch_all for reads).
"""

import os

from models import db

TABLES = [
    'users',
    'exchange_accounts',
    'advanced_predictions',
    'price_history',
    'predictions',
    'exchange_trade_logs',
]


def get_db_overview():
    """
    Return record counts for each app table.

    Returns dict mapping table name to count (or -1 if table missing/error).
    """
    overview = {}
    for table in TABLES:
        try:
            row = db.fetch_one(f"SELECT COUNT(*) as count FROM {table}")
            count = row['count'] if row else 0
            overview[table] = count
        except Exception:
            overview[table] = -1
    return overview


def get_table_info(table_name):
    """
    Return record count, column names, and first 5 rows for a table.

    Returns dict with table_name, record_count, columns, sample_data, exists; or exists=False and error on failure.
    """
    try:
        count_row = db.fetch_one(f"SELECT COUNT(*) as count FROM {table_name}")
        record_count = count_row['count'] if count_row else 0

        pragma_rows = db.fetch_all(f"PRAGMA table_info({table_name})")
        columns = [r['name'] for r in pragma_rows] if pragma_rows else []

        sample_data = db.fetch_all(f"SELECT * FROM {table_name} LIMIT 5") or []

        return {
            'table_name': table_name,
            'record_count': record_count,
            'columns': columns,
            'sample_data': sample_data,
            'exists': True,
        }
    except Exception as e:
        return {
            'table_name': table_name,
            'record_count': -1,
            'columns': [],
            'sample_data': [],
            'exists': False,
            'error': str(e),
        }


def get_database_size_info():
    """
    Return DB file size (bytes, MB, human-readable string).

    Assumes ai_trading.db in project root (one level up from services/).
    """
    try:
        db_path = os.path.join(os.path.dirname(__file__), '..', 'ai_trading.db')
        if not os.path.exists(db_path):
            return {
                'database_file': 'ai_trading.db',
                'total_size_bytes': 0,
                'total_size_mb': 0,
                'total_size_readable': '0 KB',
                'exists': False,
                'error': 'Database file not found',
            }
        size_bytes = os.path.getsize(db_path)
        size_mb = size_bytes / (1024 * 1024)
        if size_mb < 1:
            size_readable = f"{size_bytes / 1024:.2f} KB"
        elif size_mb < 1024:
            size_readable = f"{size_mb:.2f} MB"
        else:
            size_readable = f"{size_mb / 1024:.2f} GB"
        return {
            'database_file': 'ai_trading.db',
            'total_size_bytes': size_bytes,
            'total_size_mb': round(size_mb, 2),
            'total_size_readable': size_readable,
            'exists': True,
        }
    except Exception as e:
        return {
            'database_file': 'ai_trading.db',
            'total_size_bytes': 0,
            'total_size_mb': 0,
            'total_size_readable': 'Unknown',
            'exists': False,
            'error': str(e),
        }


def check_database_health():
    """
    Run overview and size check; derive status (healthy/warning/critical), issues, and recommendations.

    Returns dict with status, overview, size_info, issues, recommendations, total_records.
    """
    overview = get_db_overview()
    size_info = get_database_size_info()
    issues = []
    recommendations = []

    missing = [t for t, c in overview.items() if c == -1]
    if missing:
        issues.append(f"Missing tables: {', '.join(missing)}")
        recommendations.append("Run database setup script or migrations")

    if overview.get('users', 0) == 0:
        issues.append("No users registered")
        recommendations.append("Create a demo user for testing")

    if overview.get('price_history', 0) < 100:
        issues.append("Limited price history (< 100 records)")
        recommendations.append("Sync price history from exchange")

    status = "critical" if missing else ("warning" if issues else "healthy")
    return {
        'status': status,
        'overview': overview,
        'size_info': size_info,
        'issues': issues,
        'recommendations': recommendations,
        'total_records': sum(c for c in overview.values() if c > 0),
    }


if __name__ == '__main__':
    overview = get_db_overview()
    print("Overview:", overview)
    size_info = get_database_size_info()
    print("Size:", size_info.get('total_size_readable', 'Unknown'))
    health = check_database_health()
    print("Status:", health['status'])
