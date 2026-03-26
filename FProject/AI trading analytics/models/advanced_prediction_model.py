"""
AI prediction storage and performance for AI Trading Analytics.

Saves predictions from the advanced AI predictor, retrieves the latest
prediction per symbol for the dashboard/API, lists a user's predictions,
and computes accuracy/performance. Schema uses an advanced_predictions
table; outcome is updated when actual price is known.

Used by: app.py (dashboard, advanced prediction page, prediction API),
services/advanced_ai_predictor (save after predict).
"""

import json
import logging
from datetime import datetime, timedelta

from models import db

logger = logging.getLogger(__name__)


def save_prediction(user_id: int, symbol: str, timeframe: str, result: dict):
    """
    Persist one prediction from the advanced AI predictor.

    Args:
        user_id: Owner user id.
        symbol: Trading pair (e.g. 'BTC/USDT' or 'BTCUSDT').
        timeframe: e.g. '1h', '4h', '1d'.
        result: Dict with signal, direction, confidence, current_price, target_price,
                pct_change, summary, indicators (optional).

    Returns:
        New prediction id or None on failure.
    """
    try:
        signal = result.get('signal', 'HOLD')
        direction = result.get('direction', 'neutral')
        confidence = result.get('confidence', 0)
        current_price = result.get('current_price', 0)
        target_price = result.get('target_price', 0)
        pct_change = result.get('pct_change', 0)
        summary = result.get('summary', '')
        indicators_json = json.dumps(result.get('indicators', {}))
        target_time = datetime.utcnow() + timedelta(hours=24)

        query = """
            INSERT INTO advanced_predictions
            (user_id, symbol, mode, timeframe, signal, direction, confidence,
             current_price, target_price, pct_change, summary, indicators_snapshot,
             target_time, outcome)
            VALUES (?, ?, 'ai', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')
        """
        prediction_id = db.execute_query(
            query,
            (user_id, symbol, timeframe, signal, direction, confidence,
             current_price, target_price, pct_change, summary, indicators_json,
             target_time.isoformat())
        )
        if prediction_id:
            logger.info("Saved prediction #%s: %s %s", prediction_id, signal, symbol)
        return prediction_id
    except Exception as e:
        logger.error("Error saving prediction: %s", e)
        return None


def get_latest_prediction_for_symbol(user_id: int, symbol: str):
    """
    Return the most recent prediction for a symbol for the dashboard/API.

    Accepts symbol as BTCUSDT or BTC/USDT; matches both in the database.
    Returns a dict with direction (UP/DOWN/neutral), confidence_pct, symbol,
    signal, current_price, target_price, pct_change, created_at, timestamp.
    """
    try:
        symbol_slash = symbol.replace('USDT', '/USDT', 1) if 'USDT' in symbol and '/' not in symbol else symbol
        symbol_noslash = symbol.replace('/', '') if '/' in symbol else symbol
        symbols = [s for s in (symbol, symbol_slash, symbol_noslash) if s]
        placeholders = ','.join(['?'] * len(symbols))
        query = f"""
            SELECT id, symbol, signal, direction, confidence, current_price, target_price, pct_change, created_at
            FROM advanced_predictions
            WHERE user_id = ? AND symbol IN ({placeholders})
            ORDER BY created_at DESC
            LIMIT 1
        """
        row = db.fetch_one(query, (user_id,) + tuple(symbols))
        if not row:
            return None

        direction_raw = (row.get('direction') or 'neutral').lower()
        if direction_raw == 'up':
            direction = 'UP'
        elif direction_raw == 'down':
            direction = 'DOWN'
        else:
            direction = 'neutral'
        raw_conf = float(row.get('confidence') or 0)
        confidence_pct = min(100.0, raw_conf if raw_conf > 1 else raw_conf * 100)
        out_symbol = symbol.replace('/', '') if '/' in symbol else symbol

        return {
            'direction': direction,
            'confidence_pct': round(confidence_pct, 1),
            'symbol': out_symbol,
            'signal': row.get('signal'),
            'current_price': float(row['current_price']) if row.get('current_price') else None,
            'target_price': float(row['target_price']) if row.get('target_price') else None,
            'pct_change': float(row['pct_change']) if row.get('pct_change') else None,
            'created_at': row.get('created_at'),
            'timestamp': row.get('created_at'),
        }
    except Exception as e:
        logger.error("Error fetching latest prediction for symbol: %s", e)
        return None


def get_user_predictions(user_id: int, limit: int = 20):
    """
    Return a user's recent predictions, newest first.

    Returns:
        List of dicts with id, symbol, mode, timeframe, signal, confidence,
        current_price, target_price, pct_change, summary, created_at, outcome, actual_price.
    """
    try:
        query = """
            SELECT id, symbol, mode, timeframe, signal, confidence,
                   current_price, target_price, pct_change, summary,
                   created_at, outcome, actual_price
            FROM advanced_predictions
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """
        rows = db.fetch_all(query, (user_id, limit))
        if not rows:
            return []
        predictions = []
        for row in rows:
            predictions.append({
                'id': row['id'],
                'symbol': row['symbol'],
                'mode': row['mode'],
                'timeframe': row['timeframe'],
                'signal': row['signal'],
                'confidence': float(row['confidence']) if row['confidence'] else 0,
                'current_price': float(row['current_price']) if row['current_price'] else 0,
                'target_price': float(row['target_price']) if row['target_price'] else 0,
                'pct_change': float(row['pct_change']) if row['pct_change'] else 0,
                'summary': row['summary'],
                'created_at': row['created_at'],
                'outcome': row['outcome'],
                'actual_price': float(row['actual_price']) if row['actual_price'] else None,
            })
        return predictions
    except Exception as e:
        logger.error("Error fetching predictions: %s", e)
        return []


def get_prediction_performance(user_id: int):
    """
    Aggregate prediction performance for a user (evaluated predictions only).

    Returns:
        Dict with total_predictions, correct_predictions, accuracy_pct, avg_confidence.
    """
    default = {
        'total_predictions': 0,
        'correct_predictions': 0,
        'accuracy_pct': 0.0,
        'avg_confidence': 0.0,
    }
    try:
        query = """
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN outcome = 'correct' THEN 1 ELSE 0 END) as correct,
                AVG(confidence) as avg_confidence
            FROM advanced_predictions
            WHERE user_id = ? AND outcome IN ('correct', 'incorrect')
        """
        row = db.fetch_one(query, (user_id,))
        if not row or row['total'] == 0:
            return default
        total = row['total']
        correct = row['correct'] or 0
        accuracy = (correct / total * 100) if total > 0 else 0
        avg_conf = float(row['avg_confidence']) if row['avg_confidence'] else 0
        return {
            'total_predictions': total,
            'correct_predictions': correct,
            'accuracy_pct': round(accuracy, 1),
            'avg_confidence': round(avg_conf, 1),
        }
    except Exception as e:
        logger.error("Error fetching performance: %s", e)
        return default


def update_prediction_outcome(prediction_id: int, actual_price: float):
    """
    Mark a prediction with actual price and computed outcome (correct/incorrect).

    Compares actual_price to current_price and signal (BUY/SELL/HOLD) to set outcome
    and an accuracy_score. Call this when the target time has passed and actual price is known.

    Returns:
        True if the row was updated, False otherwise.
    """
    try:
        query = "SELECT signal, target_price, current_price FROM advanced_predictions WHERE id = ?"
        pred = db.fetch_one(query, (prediction_id,))
        if not pred:
            return False

        signal = pred['signal']
        target = float(pred['target_price'])
        current = float(pred['current_price'])
        outcome = 'incorrect'

        if signal == 'BUY' and actual_price > current:
            outcome = 'correct'
        elif signal == 'SELL' and actual_price < current:
            outcome = 'correct'
        elif signal == 'HOLD' and current and abs(actual_price - current) / current < 0.02:
            outcome = 'correct'

        accuracy_score = max(0, 100 - abs((actual_price - target) / target * 100)) if target > 0 else 0

        update_query = """
            UPDATE advanced_predictions
            SET actual_price = ?, outcome = ?, accuracy_score = ?
            WHERE id = ?
        """
        db.execute_query(update_query, (actual_price, outcome, accuracy_score, prediction_id))
        logger.info("Updated prediction #%s: %s", prediction_id, outcome)
        return True
    except Exception as e:
        logger.error("Error updating prediction outcome: %s", e)
        return False


__all__ = [
    'save_prediction',
    'get_latest_prediction_for_symbol',
    'get_user_predictions',
    'get_prediction_performance',
    'update_prediction_outcome',
]
