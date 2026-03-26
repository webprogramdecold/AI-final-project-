"""
Train advanced AI prediction models for AI Trading Analytics.

Fetches OHLCV via AdvancedDataService, engineers features (returns, volatility,
indicators), trains direction (classification) and return (regression) models,
saves scaler and feature_info to services/models/. Run from project root:
  python3 -m services.train_advanced_ai_model
  or: python3 services/train_advanced_ai_model.py
"""

import sys
from pathlib import Path

_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import accuracy_score, mean_absolute_error
import joblib
import os

from services.feature_engineering import compute_simple_indicators


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """Engineer features for machine learning model."""
    df['return_1h'] = df['close'].pct_change(1)
    df['return_3h'] = df['close'].pct_change(3)
    df['return_6h'] = df['close'].pct_change(6)
    df['return_12h'] = df['close'].pct_change(12)
    df['return_24h'] = df['close'].pct_change(24)
    df['volatility_24h'] = df['return_1h'].rolling(window=24).std()
    df = compute_simple_indicators(df)
    df['volume_change'] = df['volume'].pct_change(1)
    df['high_24h'] = df['high'].rolling(window=24).max()
    df['low_24h'] = df['low'].rolling(window=24).min()
    df['price_position'] = (df['close'] - df['low_24h']) / (df['high_24h'] - df['low_24h'])
    return df


def build_targets(df: pd.DataFrame) -> pd.DataFrame:
    """Create target variables (direction and next return)."""
    df['next_close'] = df['close'].shift(-1)
    df['direction'] = (df['next_close'] > df['close']).astype(int)
    df['next_return'] = df['close'].pct_change(-1) * -1
    return df


def train_models():
    """Main function to train ML models."""
    print("\n" + "="*70)
    print("TRAINING ADVANCED AI PREDICTION MODELS")
    print("="*70)

    print("\n[1/6] Fetching historical price data...")
    from services.advanced_data_service import AdvancedDataService
    data_service = AdvancedDataService()
    df = data_service.get_ohlcv('BTC/USDT', timeframe='1h', since_days=90)
    print(f"   ✅ Data loaded (90 days)")

    if len(df) < 200:
        print("   ❌ Not enough data for training (need at least 200 candles)")
        return

    print("\n[2/6] Engineering features...")
    df = build_features(df)
    df = build_targets(df)
    df = df.dropna()
    print(f"   ✅ Created features, {len(df)} valid samples")

    print("\n[3/6] Preparing training data...")
    feature_columns = [
        'return_1h', 'return_3h', 'return_6h', 'return_12h', 'return_24h',
        'volatility_24h',
        'rsi', 'macd', 'ma_ratio',
        'volume_change',
        'price_position'
    ]
    X = df[feature_columns].values
    y_direction = df['direction'].values
    y_return = df['next_return'].values
    X_train, X_test, y_dir_train, y_dir_test, y_ret_train, y_ret_test = train_test_split(
        X, y_direction, y_return,
        test_size=0.2,
        random_state=42
    )
    print(f"   ✅ Train samples: {len(X_train)}")
    print(f"   ✅ Test samples: {len(X_test)}")

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    print(f"   ✅ Features normalized")

    print("\n[4/6] Training direction model (UP/DOWN)...")
    direction_model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        n_jobs=-1
    )
    direction_model.fit(X_train_scaled, y_dir_train)
    y_dir_pred = direction_model.predict(X_test_scaled)
    direction_accuracy = accuracy_score(y_dir_test, y_dir_pred)

    return_model = RandomForestRegressor(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        n_jobs=-1
    )
    return_model.fit(X_train_scaled, y_ret_train)
    y_ret_pred = return_model.predict(X_test_scaled)
    mae = mean_absolute_error(y_ret_test, y_ret_pred)

    print("\n[6/6] Saving models...")
    models_dir = os.path.join(os.path.dirname(__file__), 'models')
    os.makedirs(models_dir, exist_ok=True)
    joblib.dump(direction_model, os.path.join(models_dir, 'adv_direction_model.joblib'))
    joblib.dump(return_model, os.path.join(models_dir, 'adv_return_model.joblib'))
    joblib.dump(scaler, os.path.join(models_dir, 'adv_scaler.joblib'))
    feature_info_path = os.path.join(models_dir, 'feature_info.joblib')
    eval_acc, eval_mae = direction_accuracy, mae
    try:
        if os.path.isfile(feature_info_path):
            existing = joblib.load(feature_info_path)
            if isinstance(existing, dict) and 'direction_accuracy' in existing and 'return_mae' in existing:
                eval_acc = existing['direction_accuracy']
                eval_mae = existing['return_mae']
    except Exception:
        pass
    feature_info = {
        'feature_columns': feature_columns,
        'train_size': len(X_train),
        'test_size': len(X_test),
        'direction_accuracy': eval_acc,
        'return_mae': eval_mae
    }
    joblib.dump(feature_info, feature_info_path)
    print(f"   ✅ Models saved to: {models_dir}")

    print("\n" + "="*70)
    print("TRAINING COMPLETE!")
    print("="*70)
    print(f"Direction Accuracy: {eval_acc*100:.1f}%")
    print(f"Return MAE: {eval_mae*100:.3f}%")
    print("="*70 + "\n")


if __name__ == "__main__":
    print("\n⚠️  DISCLAIMER ⚠️")
    print("This is an educational demo. NOT financial advice.\n")
    try:
        train_models()
        print("\n✅ All done! Models are ready to use.\n")
    except Exception as e:
        print(f"\n❌ Error during training: {e}")
        import traceback
        traceback.print_exc()
