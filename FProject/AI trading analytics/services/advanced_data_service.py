"""
Multi-source market data for AI Trading Analytics.

Fetches OHLCV from exchanges (CCXT), optional on-chain metrics, social sentiment, and macro indicators.
Used by advanced_ai_predictor for prediction input and by train_advanced_ai_model for training data.
On-chain, sentiment, and macro are demo/simulated unless real APIs are wired in.
"""

import ccxt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AdvancedDataService:
    """Fetches OHLCV (CCXT), on-chain, sentiment, and macro data for predictions and training."""

    def __init__(self):
        self.exchange = ccxt.binance({
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'}
        })
        logger.info("✅ Advanced Data Service initialized")
    
    # ========================================
    # 1. EXCHANGE OHLCV DATA
    # ========================================
    
    def get_ohlcv(self, symbol: str, timeframe: str = '1h', since_days: int = 30) -> pd.DataFrame:
        """Fetch OHLCV from exchange (CCXT). Returns DataFrame with open, high, low, close, volume; index is timestamp."""
        try:
            logger.info(f"📊 Fetching OHLCV: {symbol} ({timeframe}, {since_days}d)")
            
            # Calculate 'since' timestamp for CCXT
            since_dt = datetime.utcnow() - timedelta(days=since_days)
            since_ts = self.exchange.parse8601(since_dt.strftime('%Y-%m-%dT%H:%M:%SZ'))
            
            # Fetch OHLCV data
            ohlcv = self.exchange.fetch_ohlcv(
                symbol, 
                timeframe=timeframe, 
                since=since_ts, 
                limit=1000
            )
            
            # Convert to DataFrame
            df = pd.DataFrame(
                ohlcv, 
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            logger.info(f"✅ OHLCV loaded for {symbol}")
            return df
            
        except Exception as e:
            logger.error(f"❌ Error fetching OHLCV: {e}")
            # Return empty DataFrame as fallback
            return pd.DataFrame(columns=['open', 'high', 'low', 'close', 'volume'])
    
    # ========================================
    # 2. ON-CHAIN METRICS
    # ========================================
    
    def get_onchain_metrics(self, symbol: str) -> Dict[str, float]:
        """Fetch on-chain metrics (e.g. active addresses, NVT, hash rate). Demo returns simulated data."""
        try:
            base_asset = symbol.split('/')[0].upper()  # Extract BTC from BTC/USDT
            logger.info(f"🔗 Fetching on-chain metrics for {base_asset}")
            
            # ========================================
            # DEMO DATA (Replace with real API calls)
            # ========================================
            # In production, you would call:
            # response = requests.get(f'https://api.glassnode.com/v1/metrics/addresses/active_count',
            #                         params={'a': base_asset, 'api_key': YOUR_KEY})
            # data = response.json()
            
            if base_asset == 'BTC':
                metrics = {
                    'active_addresses': 950000,      # ~950k daily active addresses
                    'nvt_ratio': 75.3,               # NVT ratio (lower = undervalued)
                    'hash_rate': 400_000_000,        # 400 EH/s
                    'miner_revenue_usd': 28_000_000, # $28M daily
                    'exchange_inflow': 2500,         # BTC flowing to exchanges
                    'exchange_outflow': 2800,        # BTC leaving exchanges (bullish if > inflow)
                }
                logger.info(f"✅ On-chain data: NVT={metrics['nvt_ratio']}, Active={metrics['active_addresses']:,}")
                
            elif base_asset == 'ETH':
                metrics = {
                    'active_addresses': 550000,
                    'nvt_ratio': 62.8,
                    'gas_price_gwei': 25,
                    'staking_ratio': 22.5,  # % of ETH staked
                }
                logger.info(f"✅ On-chain data: NVT={metrics['nvt_ratio']}, Gas={metrics['gas_price_gwei']} gwei")
                
            else:
                # For other coins, return basic placeholder
                metrics = {
                    'active_addresses': None,
                    'nvt_ratio': None,
                    'note': 'On-chain data not available for this asset'
                }
                logger.warning(f"⚠️  No on-chain data for {base_asset}")
            
            return metrics
            
        except Exception as e:
            logger.error(f"❌ Error fetching on-chain metrics: {e}")
            return {}
    
    # ========================================
    # 3. SOCIAL SENTIMENT ANALYSIS
    # ========================================
    
    def get_social_sentiment(self, symbol: str) -> Dict[str, float]:
        """Return sentiment metrics (polarity, volume, trend). Demo returns simulated data."""
        try:
            base_asset = symbol.split('/')[0].upper()
            logger.info(f"💬 Analyzing social sentiment for {base_asset}")
            
            # ========================================
            # DEMO DATA (Replace with real sentiment analysis)
            # ========================================
            # In production, you would:
            # 1. Fetch tweets: tweets = api.search_tweets(q=f'${base_asset}', count=100)
            # 2. Analyze each: from nltk.sentiment import SentimentIntensityAnalyzer
            #    sia = SentimentIntensityAnalyzer()
            #    scores = [sia.polarity_scores(tweet.text)['compound'] for tweet in tweets]
            # 3. Aggregate: avg_sentiment = np.mean(scores)
            
            # Simulate sentiment scores
            import random
            random.seed(hash(base_asset) % 100)  # Deterministic for demo
            
            sentiment = {
                'polarity': random.uniform(-0.3, 0.5),  # -1 (negative) to +1 (positive)
                'mention_volume': random.randint(5000, 50000),  # Daily mentions
                'trend_7d': random.choice(['rising', 'falling', 'stable']),
                'fear_greed_index': random.randint(20, 75),  # 0-100 scale
            }
            
            # Interpret sentiment
            if sentiment['polarity'] > 0.3:
                interpretation = "Very Positive (possible euphoria)"
            elif sentiment['polarity'] > 0.1:
                interpretation = "Moderately Positive"
            elif sentiment['polarity'] > -0.1:
                interpretation = "Neutral"
            elif sentiment['polarity'] > -0.3:
                interpretation = "Moderately Negative"
            else:
                interpretation = "Very Negative (possible capitulation)"
            
            sentiment['interpretation'] = interpretation
            
            logger.info(f"✅ Sentiment: {sentiment['polarity']:.2f} ({interpretation})")
            return sentiment
            
        except Exception as e:
            logger.error(f"❌ Error analyzing sentiment: {e}")
            return {'polarity': 0, 'mention_volume': 0, 'interpretation': 'Unknown'}
    
    # ========================================
    # 4. MACROECONOMIC INDICATORS
    # ========================================
    
    def get_macro_indicators(self) -> Dict[str, float]:
        """Return macro indicators (e.g. fed funds rate, VIX, DXY). Demo returns simulated data."""
        try:
            logger.info(f"🌐 Fetching macroeconomic indicators")
            
            # ========================================
            # DEMO DATA (Replace with real API calls)
            # ========================================
            # In production:
            # import yfinance as yf
            # vix = yf.Ticker('^VIX').history(period='1d')['Close'].iloc[-1]
            # dxy = yf.Ticker('DX-Y.NYB').history(period='1d')['Close'].iloc[-1]
            
            # Simulated current macro environment
            macro = {
                'fed_funds_rate': 5.25,      # Federal Reserve interest rate (%)
                'vix': 18.5,                 # CBOE Volatility Index
                'dxy': 104.2,                # US Dollar Index
                'sp500_change_1d': -0.3,     # S&P 500 daily % change
                'us_10yr_yield': 4.45,       # 10-year Treasury yield (%)
            }
            
            # Interpret macro environment
            risk_sentiment = "Neutral"
            if macro['vix'] > 30:
                risk_sentiment = "High Fear (Risk-Off)"
            elif macro['vix'] < 15:
                risk_sentiment = "Low Fear (Risk-On)"
            
            rate_pressure = "Bearish for crypto" if macro['fed_funds_rate'] > 4.5 else "Neutral"
            
            macro['risk_sentiment'] = risk_sentiment
            macro['rate_pressure'] = rate_pressure
            
            logger.info(f"✅ Macro: VIX={macro['vix']}, Rates={macro['fed_funds_rate']}% ({rate_pressure})")
            return macro
            
        except Exception as e:
            logger.error(f"❌ Error fetching macro data: {e}")
            return {'fed_funds_rate': 0, 'vix': 0}
    
    # ========================================
    # UNIFIED DATA AGGREGATION
    # ========================================
    
    def get_all_data(self, symbol: str, timeframe: str = '1h', since_days: int = 30) -> Dict:
        """Aggregate OHLCV, on-chain, sentiment, and macro into one dict for predictions."""
        logger.info(f"\n{'='*70}")
        logger.info(f"📦 FETCHING COMPLETE DATASET FOR {symbol}")
        logger.info(f"{'='*70}\n")
        
        # Fetch all data sources
        ohlcv = self.get_ohlcv(symbol, timeframe, since_days)
        onchain = self.get_onchain_metrics(symbol)
        sentiment = self.get_social_sentiment(symbol)
        macro = self.get_macro_indicators()
        
        # Package everything
        complete_data = {
            'ohlcv': ohlcv,
            'onchain': onchain,
            'sentiment': sentiment,
            'macro': macro,
            'metadata': {
                'symbol': symbol,
                'timeframe': timeframe,
                'fetched_at': datetime.utcnow().isoformat(),
                'data_points': len(ohlcv)
            }
        }
        
        logger.info(f"\n✅ COMPLETE DATASET READY")
        logger.info(f"   OHLCV loaded")
        logger.info(f"   On-chain: {len(onchain)} metrics")
        logger.info(f"   Sentiment: {sentiment.get('interpretation', 'N/A')}")
        logger.info(f"   Macro: VIX={macro.get('vix', 'N/A')}\n")
        
        return complete_data


# ========================================
# HELPER FUNCTIONS
# ========================================

def calculate_returns(prices: pd.Series) -> pd.Series:
    """Calculate percentage returns from price series"""
    return prices.pct_change()


def normalize_features(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize features to 0-1 range for ML models"""
    from sklearn.preprocessing import MinMaxScaler
    scaler = MinMaxScaler()
    normalized = pd.DataFrame(
        scaler.fit_transform(df),
        columns=df.columns,
        index=df.index
    )
    return normalized


# ========================================
# MODULE EXPORTS
# ========================================

__all__ = ['AdvancedDataService', 'calculate_returns', 'normalize_features']

