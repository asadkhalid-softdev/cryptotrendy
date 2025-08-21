import pandas as pd
import numpy as np
from datetime import datetime
import os

class DataFormatter:
    def __init__(self):
        # Define thresholds or scaling factors if needed
        self.max_coins_to_analyze = int(os.getenv('MAX_COINS_TO_ANALYZE', 10))
        pass
        
    def normalize_scores(self, values, min_val=None, max_val=None):
        """Normalize values to 0-1 range"""
        if isinstance(values, pd.Series) and values.empty:
            return values
            
        values = np.array(values)
        if min_val is None:
            min_val = np.min(values)
        if max_val is None:
            max_val = np.max(values)
            
        # Avoid division by zero
        if max_val == min_val:
            return np.ones_like(values)
            
        return (values - min_val) / (max_val - min_val)
        
    def merge_coin_data(self, collected_data):
        """Merge data from different collectors into a unified format"""
        if not collected_data:
            return []
            
        # Extract different data sources
        market_data = collected_data.get('coingecko', {}).get('market_data', [])
        coin_mentions = collected_data.get('social_media', {}).get('coin_mentions', {})
        
        # If no market data, we can't proceed
        if not market_data:
            return []
            
        # Create merged data
        merged_coins = []
        for coin in market_data:
            symbol = coin.get('symbol', '').upper()
            coin_id = coin.get('id', '')
            
            # Base coin data
            coin_data = {
                'id': coin_id,
                'symbol': symbol,
                'name': coin.get('name', ''),
                'price': coin.get('current_price', 0),
                'market_cap': coin.get('market_cap', 0),
                'volume_24h': coin.get('total_volume', 0),
                'price_change_24h': coin.get('price_change_percentage_24h', 0),
                'price_change_7d': coin.get('price_change_percentage_7d_in_currency', 0),
                'is_trending': coin.get('is_trending', False)
            }
            
            # Add default values for previously LunarCrush fields
            coin_data.update({
                'galaxy_score': 0,
                'alt_rank': 0,
                'social_score': 0,
                'social_volume': 0,
                'social_contributors': 0,
                'sentiment': 0,
                'tweet_volume': 0
            })
                
            # Add social media mentions if available
            if symbol in coin_mentions:
                coin_data.update(coin_mentions[symbol])
            else:
                coin_data.update({
                    'reddit_mentions': 0
                })
                
            merged_coins.append(coin_data)
            
        return merged_coins
        
    def normalize_merged_data(self, merged_coins):
        """Normalize all score fields in the merged data"""
        if not merged_coins:
            return []
            
        # Convert to DataFrame for easier manipulation
        df = pd.DataFrame(merged_coins)
        
        # Fields to normalize
        score_fields = [
            'reddit_mentions'
        ]
        
        # Normalize each field
        for field in score_fields:
            if field in df.columns:
                df[f'{field}_normalized'] = self.normalize_scores(df[field])
                
        # Convert back to list of dictionaries
        return df.to_dict('records')
        
    def _normalize(self, value, min_val, max_val):
        """Normalize a value between 0 and 1."""
        if max_val == min_val:
            return 0.5 # Avoid division by zero, return neutral value
        return (value - min_val) / (max_val - min_val)

    def format_for_gpt(self, coingecko_data, social_data, kucoin_data):
        """
        Format combined data into a structure suitable for GPT analysis.
        Includes CoinGecko market data, social mentions, and KuCoin RSI data.
        """
        # print(coingecko_data)

        market_data = coingecko_data.get('market_data', [])
        trending_coins = coingecko_data.get('trending_coins', [])

        # If no market data, we can't proceed
        if not market_data:
            print("  Formatter: No market data found.")
            return []

        # Create merged data
        merged_coins = []
        for coin in market_data:
            coin['symbol'] = coin['symbol'].upper()
            
            symbol = coin.get('symbol', '')
            if not symbol:
                continue
            
            coin_info = coin.copy()

            # Add social data if available
            coin_social = social_data.get(symbol, {})
            coin_info['social_mentions'] = coin_social.get('reddit_mentions', 0)

            # Add KuCoin RSI data if available
            coin_kucoin = kucoin_data.get(symbol, {})

            if coin_kucoin:
                coin_info['rsi_1d'] = coin_kucoin.get('rsi_1d', 'n/a') # Will be None if not found/calculated
                coin_info['rsi_7d'] = coin_kucoin.get('rsi_7d', 'n/a') # Will be None if not found/calculated

            merged_coins.append(coin_info)

        # --- Filtering/Ranking before sending to GPT (Optional) ---
        # Example: Prioritize trending coins or coins with high volume change
        # For now, just limit the number of coins based on market cap rank
        merged_coins.sort(key=lambda x: x.get('social_mentions', 0), reverse=True) # Sort by social mentions in descending order
        
        # Filter out coins with no social mentions
        merged_coins = [coin for coin in merged_coins if coin.get('social_mentions', 0) > 10] # greater than 10 mentions
        print(f"  Formatter: Filtered to {len(merged_coins)} coins with social mentions.")

        limited_coins = merged_coins[:self.max_coins_to_analyze]
        print(f"  Formatter: Limited coins to {len(limited_coins)}.")

        print(f"  Formatter: Prepared data for {len(limited_coins)} coins (out of {len(market_data)}).")
        return limited_coins
        
    def process(self, collected_data):
        """Process all collected data and prepare for GPT analysis"""
        merged_data = self.merge_coin_data(collected_data)
        normalized_data = self.normalize_merged_data(merged_data)
        gpt_prompt = self.format_for_gpt(collected_data['coingecko'], collected_data['social_media'], collected_data['kucoin'])
        
        return {
            'merged_data': merged_data,
            'normalized_data': normalized_data,
            'gpt_prompt': gpt_prompt,
            'timestamp': datetime.now().isoformat()
        } 