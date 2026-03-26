"""
Exchange accounts and trade logging for AI Trading Analytics.

Manages linked exchange accounts (create, list, get by id, deactivate) and logs
trades executed via those accounts. API secrets are stored encoded (base64);
this is not encryption and is not suitable for production use proper secret
management (e.g. vault, env vars) in production.

Used by: app.py (exchanges page, balance/positions, test connection, place order),
services/exchange_service.py (get client from account).
"""

from datetime import datetime
import base64

from models import db


def simple_encode_secret(secret):
    """
    Encode a string with base64 (reversible, not secure).

    Used only for storing API secrets in this project. In production,
    use proper encryption and secret management.
    """
    return base64.b64encode(secret.encode('utf-8')).decode('utf-8')


def simple_decode_secret(encoded_secret):
    """
    Decode a base64-encoded string (inverse of simple_encode_secret).
    """
    return base64.b64decode(encoded_secret.encode('utf-8')).decode('utf-8')


def create_exchange_account(user_id, exchange_name, account_label, api_key, api_secret, is_testnet=False):
    """
    Create a linked exchange account for a user.

    API secret is stored encoded (base64). Exchange name must be one of:
    binance, bybit, okx, mexc, bingx.

    Args:
        user_id: Owner user id.
        exchange_name: Exchange identifier (e.g. 'binance').
        account_label: Display name for the account.
        api_key: Exchange API key.
        api_secret: Exchange API secret (stored encoded).
        is_testnet: True for testnet/sandbox.

    Returns:
        {'success': True, 'account_id': id} or {'success': False, 'error': str}.
    """
    valid_exchanges = ['binance', 'bybit', 'okx', 'mexc', 'bingx']
    if exchange_name.lower() not in valid_exchanges:
        return {
            'success': False,
            'error': f'Invalid exchange. Must be one of: {", ".join(valid_exchanges)}'
        }
    if not api_key or not api_secret:
        return {'success': False, 'error': 'API key and secret are required'}
    if not account_label:
        account_label = f"{exchange_name.capitalize()} Account"

    is_testnet_int = 1 if is_testnet else 0
    api_secret_encoded = simple_encode_secret(api_secret)

    try:
        query = """
            INSERT INTO exchange_accounts
            (user_id, exchange_name, account_label, api_key, api_secret_encrypted, is_testnet, is_active)
            VALUES (?, ?, ?, ?, ?, ?, 1)
        """
        account_id = db.execute_query(query, (
            user_id, exchange_name, account_label, api_key, api_secret_encoded, is_testnet_int
        ))
        if account_id:
            return {'success': True, 'account_id': account_id}
        return {'success': False, 'error': 'Failed to create account'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def get_exchange_accounts_for_user(user_id, active_only=True):
    """
    List exchange accounts for a user (without API secrets).

    Args:
        user_id: Owner user id.
        active_only: If True, only return accounts with is_active = 1.

    Returns:
        List of dicts (id, user_id, exchange_name, account_label, api_key, is_testnet, is_active, created_at).
        api_key_masked is added for display (first 10 chars + '...').
    """
    if active_only:
        query = """
            SELECT id, user_id, exchange_name, account_label, api_key, is_testnet, is_active, created_at
            FROM exchange_accounts
            WHERE user_id = ? AND is_active = 1
            ORDER BY created_at DESC
        """
    else:
        query = """
            SELECT id, user_id, exchange_name, account_label, api_key, is_testnet, is_active, created_at
            FROM exchange_accounts
            WHERE user_id = ?
            ORDER BY created_at DESC
        """
    accounts = db.fetch_all(query, (user_id,))
    if not accounts:
        return []
    for acc in accounts:
        key = acc.get('api_key')
        if key:
            acc['api_key_masked'] = (key[:10] + '...') if len(key) > 10 else key
    return accounts


def get_exchange_account_by_id(account_id, user_id):
    """
    Fetch one exchange account including decoded API secret (for making API calls).

    Only returns the account if it belongs to user_id and is active.
    Call this only when needed for requests; do not expose the secret to the frontend or logs.
    """
    query = """
        SELECT * FROM exchange_accounts
        WHERE id = ? AND user_id = ? AND is_active = 1
    """
    account = db.fetch_one(query, (account_id, user_id))
    if not account:
        return None
    try:
        account['api_secret'] = simple_decode_secret(account['api_secret_encrypted'])
    except Exception:
        account['api_secret'] = None
    return account


def deactivate_exchange_account(account_id, user_id):
    """
    Set is_active = 0 for an account (soft deactivate).

    Returns:
        True if a row was updated, False otherwise.
    """
    query = """
        UPDATE exchange_accounts
        SET is_active = 0
        WHERE id = ? AND user_id = ?
    """
    result = db.execute_query(query, (account_id, user_id))
    return result is not None


def delete_exchange_account(account_id, user_id):
    """
    Soft-delete an exchange account (sets is_active = 0).

    Preserves the row for audit; trade logs remain. Returns a result dict.
    """
    result = db.execute_query(
        "UPDATE exchange_accounts SET is_active = 0 WHERE id = ? AND user_id = ?",
        (account_id, user_id)
    )
    if result:
        return {'success': True, 'message': 'Account removed successfully'}
    return {'success': False, 'error': 'Account not found or access denied'}


def log_exchange_trade(user_id, exchange_account_id, symbol, side, amount, price,
                       status='NEW', exchange_order_id=None, raw_response=None,
                       trade_source='manual', fee=0, fee_currency=None, error_message=None):
    """
    Insert a trade log for an exchange order (filled, rejected, etc.).

    Args:
        user_id: User id.
        exchange_account_id: Exchange account used.
        symbol: Trading pair (e.g. 'BTCUSDT').
        side: 'BUY' or 'SELL'.
        amount, price: Trade size and price; total_value = amount * price is computed.
        status: e.g. 'NEW', 'FILLED', 'REJECTED'.
        exchange_order_id, raw_response, trade_source, fee, fee_currency, error_message: Optional.

    Returns:
        New log id or None.
    """
    total_value = amount * price
    query = """
        INSERT INTO exchange_trade_logs
        (user_id, exchange_account_id, symbol, side, amount, price, total_value,
         status, exchange_order_id, raw_response, trade_source, fee, fee_currency, error_message)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    return db.execute_query(query, (
        user_id, exchange_account_id, symbol, side, amount, price, total_value,
        status, exchange_order_id, raw_response, trade_source, fee, fee_currency, error_message
    ))


def update_trade_log_status(log_id, status, filled_at=None, error_message=None):
    """
    Update status (and optionally filled_at, error_message) for a trade log.

    Returns:
        True if a row was updated.
    """
    if filled_at is not None:
        result = db.execute_query(
            "UPDATE exchange_trade_logs SET status = ?, filled_at = ?, error_message = ? WHERE id = ?",
            (status, filled_at, error_message, log_id)
        )
    else:
        result = db.execute_query(
            "UPDATE exchange_trade_logs SET status = ?, error_message = ? WHERE id = ?",
            (status, error_message, log_id)
        )
    return result is not None


def get_user_trade_logs(user_id, limit=50):
    """
    Fetch recent trade logs for a user, joined with exchange name and label.

    Returns:
        List of dicts, newest first, up to limit.
    """
    query = """
        SELECT tl.*, ea.exchange_name, ea.account_label
        FROM exchange_trade_logs tl
        JOIN exchange_accounts ea ON tl.exchange_account_id = ea.id
        WHERE tl.user_id = ?
        ORDER BY tl.created_at DESC
        LIMIT ?
    """
    rows = db.fetch_all(query, (user_id, limit))
    return rows if rows else []


def get_trade_statistics(user_id, symbol=None):
    """
    Aggregate trade stats for a user (optionally for one symbol).

    Returns:
        Dict with total_trades, filled_trades, buy_trades, sell_trades, total_volume, total_fees.
    """
    if symbol:
        query = """
            SELECT
                COUNT(*) as total_trades,
                SUM(CASE WHEN status = 'FILLED' THEN 1 ELSE 0 END) as filled_trades,
                SUM(CASE WHEN side = 'BUY' THEN 1 ELSE 0 END) as buy_trades,
                SUM(CASE WHEN side = 'SELL' THEN 1 ELSE 0 END) as sell_trades,
                SUM(total_value) as total_volume,
                SUM(fee) as total_fees
            FROM exchange_trade_logs
            WHERE user_id = ? AND symbol = ?
        """
        return db.fetch_one(query, (user_id, symbol)) or {}
    query = """
        SELECT
            COUNT(*) as total_trades,
            SUM(CASE WHEN status = 'FILLED' THEN 1 ELSE 0 END) as filled_trades,
            SUM(CASE WHEN side = 'BUY' THEN 1 ELSE 0 END) as buy_trades,
            SUM(CASE WHEN side = 'SELL' THEN 1 ELSE 0 END) as sell_trades,
            SUM(total_value) as total_volume,
            SUM(fee) as total_fees
        FROM exchange_trade_logs
        WHERE user_id = ?
    """
    return db.fetch_one(query, (user_id,)) or {}
