"""
Advanced AI predictor for AI Trading Analytics.

Loads pre-trained scikit-learn models (direction and return) from services/models/,
fetches OHLCV via AdvancedDataService, engineers features, and returns a prediction
(signal BUY/SELL/HOLD, direction, target price, confidence). Used by app.py
prediction routes and by models/advanced_prediction_model when saving predictions.
Train models first with: python -m services.train_advanced_ai_model
"""

import pandas as pd
import numpy as np
import joblib
import os
from datetime import timedelta


# ============================================
# MODEL LOADING
# ============================================

# Global variables to hold loaded models
# These are loaded once when module is imported
DIRECTION_MODEL = None
RETURN_MODEL = None
SCALER = None
FEATURE_INFO = None


def load_models():
    """
    Load direction model, return model, scaler, and feature_info from services/models/.
    Called on import; stores in module globals. Returns True if all loaded, False otherwise.
    """
    global DIRECTION_MODEL, RETURN_MODEL, SCALER, FEATURE_INFO
    
    # Path to models directory
    models_dir = os.path.join(os.path.dirname(__file__), 'models')
    
    direction_path = os.path.join(models_dir, 'adv_direction_model.joblib')
    return_path = os.path.join(models_dir, 'adv_return_model.joblib')
    scaler_path = os.path.join(models_dir, 'adv_scaler.joblib')
    feature_info_path = os.path.join(models_dir, 'feature_info.joblib')
    
    # Check if models exist
    if not os.path.exists(direction_path):
        print(f"⚠️  Models not found in {models_dir}")
        print(f"   Please run: python services/train_advanced_ai_model.py")
        return False
    
    # Load models
    try:
        DIRECTION_MODEL = joblib.load(direction_path)
        RETURN_MODEL = joblib.load(return_path)
        SCALER = joblib.load(scaler_path)
        FEATURE_INFO = joblib.load(feature_info_path)
        print(f"✅ AI models loaded successfully")
        print(f"   Direction accuracy: {FEATURE_INFO.get('direction_accuracy', 0)*100:.1f}%")
        print(f"   Return MAE: {FEATURE_INFO.get('return_mae', 0)*100:.2f}%")
        return True
    except Exception as e:
        print(f"❌ Error loading models: {e}")
        return False


# Try to load models on import
# If models don't exist, user needs to train them first
load_models()

from services.feature_engineering import compute_simple_indicators


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """Engineer features (returns, volatility, indicators, volume, price position); must match training."""
    # Price Returns
    df['return_1h'] = df['close'].pct_change(1)
    df['return_3h'] = df['close'].pct_change(3)
    df['return_6h'] = df['close'].pct_change(6)
    df['return_12h'] = df['close'].pct_change(12)
    df['return_24h'] = df['close'].pct_change(24)
    
    # Volatility
    df['volatility_24h'] = df['return_1h'].rolling(window=24).std()
    
    # Technical Indicators
    df = compute_simple_indicators(df)
    
    # Volume Features
    df['volume_change'] = df['volume'].pct_change(1)
    
    # Price Position
    df['high_24h'] = df['high'].rolling(window=24).max()
    df['low_24h'] = df['low'].rolling(window=24).min()
    df['price_position'] = (df['close'] - df['low_24h']) / (df['high_24h'] - df['low_24h'])
    
    return df


# ============================================
# PREDICTION FUNCTION
# ============================================

def advanced_ai_predict(symbol: str, timeframe: str = "1h") -> dict:
    """
    Run AI prediction for a symbol: fetch OHLCV, build features, run direction and return models, return signal and target.

    Returns dict with signal (BUY/SELL/HOLD), direction, target_price, confidence, summary, chart, etc.
    If models are not loaded or data is insufficient, returns a result with error/summary and signal HOLD.
    """
    
    # Check if models are loaded
    if DIRECTION_MODEL is None or RETURN_MODEL is None:
        return {
            'mode': 'ai',
            'symbol': symbol,
            'timeframe': timeframe,
            'signal': 'HOLD',
            'direction': 'neutral',
            'error': 'Models not loaded. Please train models first.',
            'summary': 'AI models not available. Run train_advanced_ai_model.py to train them.'
        }
    
    print(f"\n{'='*70}")
    print(f"ADVANCED AI PREDICTION")
    print(f"{'='*70}")
    print(f"Symbol: {symbol}")
    print(f"Timeframe: {timeframe}")
    print(f"{'='*70}\n")
    
    # ========================================
    # Step 1: Fetch Price Data
    # ========================================
    print(f"[1/6] Fetching price data...")
    
    from services.advanced_data_service import AdvancedDataService
    
    data_service = AdvancedDataService()
    df = data_service.get_ohlcv(symbol, timeframe, since_days=30)
    
    if len(df) < 50:
        return {
            'mode': 'ai',
            'symbol': symbol,
            'timeframe': timeframe,
            'signal': 'HOLD',
            'direction': 'neutral',
            'error': 'Insufficient data',
            'summary': 'Insufficient data. Need at least 50 candles.'
        }
    
    print(f"   ✅ Data loaded")
    
    # ========================================
    # Step 2: Engineer Features
    # ========================================
    print(f"[2/6] Engineering features...")
    
    df = build_features(df)
    df = df.dropna()  # Remove rows with NaN
    
    if len(df) == 0:
        return {
            'mode': 'ai',
            'symbol': symbol,
            'signal': 'HOLD',
            'direction': 'neutral',
            'error': 'No valid data after feature engineering',
            'summary': 'Unable to compute features from data.'
        }
    
    print(f"   ✅ Features computed")
    
    # ========================================
    # Step 3: Extract Latest Features
    # ========================================
    print(f"[3/6] Preparing features for prediction...")
    
    # Get feature columns from training
    feature_columns = FEATURE_INFO['feature_columns']
    
    # Extract latest row features
    latest_features = df[feature_columns].iloc[-1].values.reshape(1, -1)
    
    # Normalize using saved scaler
    # IMPORTANT: Must use same scaler as training!
    latest_features_scaled = SCALER.transform(latest_features)
    
    # Get current price
    current_price = float(df['close'].iloc[-1])
    
    print(f"   ✅ Current price: ${current_price:.2f}")
    
    # ========================================
    # Step 4: Make Predictions
    # ========================================
    print(f"[4/6] Running AI models...")
    
    # Direction prediction (probability of UP)
    # Returns array like [[prob_down, prob_up]]
    prob_direction = DIRECTION_MODEL.predict_proba(latest_features_scaled)[0]
    prob_down = prob_direction[0]
    prob_up = prob_direction[1]
    
    # Return magnitude prediction (expected % change)
    predicted_return = RETURN_MODEL.predict(latest_features_scaled)[0]
    
    print(f"   ✅ Probability UP: {prob_up*100:.1f}%")
    print(f"   ✅ Probability DOWN: {prob_down*100:.1f}%")
    print(f"   ✅ Expected return: {predicted_return*100:+.2f}%")
    
    # ========================================
    # Step 5: Generate Signal
    # ========================================
    print(f"[5/6] Generating trading signal...")
    
    # Determine signal based on probability
    # High confidence = probability far from 50%
    if prob_up > 0.55:
        signal = "BUY"
        direction = "up"
        # Use predicted return, but clip to reasonable range
        expected_change_pct = max(min(abs(predicted_return) * 100, 10), 1)
    elif prob_up < 0.45:
        signal = "SELL"
        direction = "down"
        expected_change_pct = -max(min(abs(predicted_return) * 100, 10), 1)
    else:
        signal = "HOLD"
        direction = "neutral"
        expected_change_pct = 0
    
    # Calculate target price
    target_price = current_price * (1 + expected_change_pct / 100)
    
    # Confidence = how far probability is from 50% (uncertain)
    confidence = max(prob_up, prob_down) * 100
    
    # Time horizon based on timeframe
    if timeframe == '1h':
        horizon = "next 1-4 hours"
    elif timeframe == '4h':
        horizon = "next 4-12 hours"
    else:
        horizon = "next 1-2 days"
    
    print(f"   ✅ Signal: {signal}")
    print(f"   ✅ Target: ${target_price:.2f} ({expected_change_pct:+.1f}%)")
    print(f"   ✅ Confidence: {confidence:.1f}%")
    
    # ========================================
    # Step 6: Build Summary
    # ========================================
    
    if signal == "BUY":
        summary = (
            f"AI model predicts ~{expected_change_pct:+.1f}% move up in {horizon} "
            f"(probability {prob_up*100:.0f}%). "
            f"Suggestion: BUY near current levels (${current_price:.2f}) "
            f"and target ${target_price:.2f}. "
            f"Confidence: {confidence:.0f}%."
        )
    elif signal == "SELL":
        summary = (
            f"AI model predicts ~{expected_change_pct:.1f}% move down in {horizon} "
            f"(probability {prob_down*100:.0f}%). "
            f"Suggestion: SELL near current levels (${current_price:.2f}) "
            f"and target ${target_price:.2f}. "
            f"Confidence: {confidence:.0f}%."
        )
    else:
        summary = (
            f"AI model is uncertain (probability split {prob_up*100:.0f}%/{prob_down*100:.0f}%). "
            f"Suggestion: HOLD and wait for clearer signals. "
            f"Current price: ${current_price:.2f}."
        )
    
    # ========================================
    # Step 7: Prepare Chart Data
    # ========================================
    
    chart_df = df.tail(50)
    timestamps = [ts.isoformat() for ts in chart_df.index]
    prices = [float(p) for p in chart_df['close'].values]
    future_timestamp = chart_df.index[-1] + timedelta(hours=24)
    timestamps.append(future_timestamp.isoformat())
    prediction_line = [None] * len(prices)
    prediction_line.append(target_price)
    
    # ========================================
    # Step 8: Build Result Dictionary
    # ========================================
    result = {
        'mode': 'ai',
        'symbol': symbol,
        'timeframe': timeframe,
        'signal': signal,
        'direction': direction,
        'target_price': round(target_price, 2),
        'expected_change_pct': round(expected_change_pct, 2),
        'pct_change': round(expected_change_pct, 2),
        'confidence': round(confidence, 1),
        'horizon': horizon,
        'current_price': round(current_price, 2),
        'probabilities': {
            'up': round(prob_up * 100, 1),
            'down': round(prob_down * 100, 1)
        },
        'predicted_return': round(predicted_return * 100, 2),
        'summary': summary,
        'chart': {
            'timestamps': timestamps,
            'prices': prices,
            'prediction': prediction_line
        },
        'model_info': {
            'direction_accuracy': round(FEATURE_INFO.get('direction_accuracy', 0) * 100, 1),
            'return_mae': round(FEATURE_INFO.get('return_mae', 0) * 100, 2)
        }
    }
    
    print(f"\n{'='*70}")
    print(f"✅ AI PREDICTION COMPLETE")
    print(f"{'='*70}\n")
    
    return result


def print_prediction_summary(result: dict):
    """Pretty-print prediction result."""
    print(f"\n{'='*70}")
    print(f"AI PREDICTION SUMMARY")
    print(f"{'='*70}")
    print(f"Symbol: {result['symbol']}")
    print(f"Timeframe: {result['timeframe']}")
    print(f"🤖 SIGNAL: {result['signal']}")
    print(f"💰 Current Price: ${result['current_price']:.2f}")
    print(f"🎯 Target Price: ${result['target_price']:.2f}")
    print(f"📈 Expected Change: {result.get('expected_change_pct', result.get('pct_change', 0)):+.1f}%")
    print(f"✅ Confidence: {result['confidence']:.1f}%")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    print("\n⚠️  Make sure you've trained the models first!")
    print("   Run: python services/train_advanced_ai_model.py\n")
    print("\n🤖 Testing Bitcoin (BTC/USDT) - 1 hour timeframe\n")
    btc_result = advanced_ai_predict('BTC/USDT', '1h')
    if 'error' not in btc_result:
        print_prediction_summary(btc_result)
    else:
        print(f"❌ Error: {btc_result['error']}")
    print("\n✅ Test complete!")
