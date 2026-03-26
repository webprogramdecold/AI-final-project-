"""
Shared feature engineering for AI Trading Analytics.

Computes technical indicators (RSI, MACD, MA ratio) used by both the training
pipeline (train_advanced_ai_model) and the predictor (advanced_ai_predictor).
Must stay in sync so training and inference use the same formulas.
"""

import pandas as pd


def compute_simple_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Compute RSI (14), MACD (12,26), and MA ratio (20/50). Modifies df in place and returns it."""
    prices = df['close']
    delta = prices.diff()
    gain = delta.where(delta > 0, 0).rolling(window=14).mean()
    loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    ema12 = prices.ewm(span=12, adjust=False).mean()
    ema26 = prices.ewm(span=26, adjust=False).mean()
    df['macd'] = ema12 - ema26
    ma20 = prices.rolling(window=20).mean()
    ma50 = prices.rolling(window=50).mean()
    df['ma_ratio'] = ma20 / ma50
    return df
