import os
import time
import pandas as pd
import pandas_ta as ta
from datetime import datetime, timedelta
from kucoin.client import Market

# At top of run.py or in a config module
RSI_BUY_1D_THRESHOLD = int(os.getenv('RSI_BUY_1D_THRESHOLD', '50'))
RSI_BUY_7D_THRESHOLD = int(os.getenv('RSI_BUY_7D_THRESHOLD', '50'))

class KuCoinCollector:
    def __init__(self):
        """Initialize KuCoin client and settings."""
        self.api_key = os.getenv('KUCOIN_API_KEY')
        self.api_secret = os.getenv('KUCOIN_API_SECRET')
        self.api_passphrase = os.getenv('KUCOIN_API_PASSPHRASE')
        self.enabled = os.getenv('ENABLE_KUCOIN_TA', 'false').lower() == 'true'

        if self.enabled:
            # Initialize Market client (doesn't require authentication for public endpoints)
            self.client = Market(url='https://api.kucoin.com') # Use Market for public data
            print("  - KuCoin TA enabled. Market client initialized.")
        else:
            self.client = None
            print("  - KuCoin TA disabled.")

    def _get_ohlc(self, symbol_pair, interval='1day', limit=30):
        """
        Fetch OHLC data for a given symbol pair and interval.
        KuCoin API returns data in reverse chronological order (newest first).
        [
            "1583942400",             //Start time of the candle cycle
            "3800",                   //opening price
            "3800.5",                 //closing price
            "3801",                   //highest price
            "3799.5",                 //lowest price
            "1000",                   //Transaction volume
            "3800000"                 //Transaction amount
        ]
        """
        try:
            # KuCoin API expects timestamps in seconds
            # Fetch slightly more data to ensure calculations are stable
            klines = self.client.get_kline(symbol_pair, interval) # Default limit might be large enough

            if not klines:
                print(f"    - No OHLC data found for {symbol_pair} ({interval})")
                return None

            # Convert to DataFrame
            df = pd.DataFrame(klines, columns=['timestamp', 'open', 'close', 'high', 'low', 'amount', 'volume'])
            # Convert timestamp to datetime
            # Convert strings to numeric first
            df['timestamp'] = pd.to_numeric(df['timestamp'])
            # Then apply to_datetime with unit
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
            
            df.set_index('timestamp', inplace=True)
            df = df[['open', 'high', 'low', 'close', 'volume']].astype(float)

            # Sort by timestamp ascending (oldest first) as required by pandas_ta
            df.sort_index(inplace=True)

            # Limit data points after sorting
            df = df.tail(limit + 14) # Keep enough for RSI calculation buffer

            return df

        except Exception as e:
            print(f"    - Error fetching KuCoin OHLC for {symbol_pair} ({interval}): {e}")
            # Handle specific KuCoin errors if needed, e.g., invalid symbol
            return None

    def _calculate_rsi(self, df, period=14):
        """Calculate RSI using pandas_ta."""
        if df is None or len(df) < period:
            return None
        try:
            # Calculate RSI
            df.ta.rsi(length=period, append=True)
            # Return the latest RSI value
            latest_rsi = df[f'RSI_{period}'].iloc[-1]
            return round(latest_rsi, 2) if pd.notna(latest_rsi) else None
        except Exception as e:
            print(f"    - Error calculating RSI: {e}")
            return None

    def collect(self, coin_symbols):
        """
        Fetch OHLC data and calculate RSI for a list of coin symbols.
        Returns a dictionary: {'SYMBOL': {'rsi_1d': value, 'rsi_7d': value}, ...}
        """
        if not self.enabled or not self.client:
            return {}

        results = {}
        print("  - Fetching KuCoin TA data...")

        # Assume USDT pairing for simplicity. This might need refinement.
        # Consider adding error handling or logic for different base pairs if needed.
        for symbol in coin_symbols:
            symbol_pair = f"{symbol.upper()}-USDT"
            print(f"    - Processing {symbol_pair}...")
            results[symbol] = {'rsi_1d': None, 'rsi_7d': None}

            # --- Daily RSI ---
            # Fetch ~30 days of data for 14-day RSI
            df_1d = self._get_ohlc(symbol_pair, interval='1day', limit=30)
            if df_1d is not None:
                rsi_1d = self._calculate_rsi(df_1d, period=14)
                results[symbol]['rsi_1d'] = rsi_1d
                print(f"      - Daily RSI: {rsi_1d}")
            else:
                 print(f"      - Could not fetch daily data or calculate RSI.")
            time.sleep(0.2) # Basic rate limiting

            # --- Weekly RSI ---
            # Fetch ~30 weeks of data for 14-week RSI
            df_1w = self._get_ohlc(symbol_pair, interval='1week', limit=30)
            if df_1w is not None:
                rsi_7d = self._calculate_rsi(df_1w, period=14)
                results[symbol]['rsi_7d'] = rsi_7d
                print(f"      - Weekly RSI: {rsi_7d}")
            else:
                print(f"      - Could not fetch weekly data or calculate RSI.")
            time.sleep(0.2) # Basic rate limiting

        print("  ✓ KuCoin TA data collection complete.")
        # Filter out symbols with RSI values greater than 70
        filtered_results = {}
        for symbol, metrics in results.items():
            rsi_1d = metrics.get('rsi_1d')
            rsi_7d = metrics.get('rsi_7d')
            if (rsi_1d is None or rsi_1d <= RSI_BUY_1D_THRESHOLD) and (rsi_7d is None or rsi_7d <= RSI_BUY_7D_THRESHOLD):
                filtered_results[symbol] = metrics
        return filtered_results 