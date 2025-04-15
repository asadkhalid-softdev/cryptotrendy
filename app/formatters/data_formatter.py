import pandas as pd
import numpy as np
from datetime import datetime

class DataFormatter:
    def __init__(self):
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
        
    def format_for_gpt(self, normalized_data):
        """Format data into a prompt for GPT analysis"""
        if not normalized_data:
            return "No data available for analysis."
            
        prompt = """Based on the data below, rank coins by breakout potential. Justify each score.

COIN DATA:
"""
        
        # Add data for each coin
        for coin in normalized_data:
            prompt += f"\n--- {coin['name']} ({coin['symbol']}) ---\n"
            prompt += f"• Price: ${coin['price']:.4f}\n"
            prompt += f"• Market Cap: ${coin['market_cap']:,}\n"
            prompt += f"• 24h Volume: ${coin['volume_24h']:,}\n"
            prompt += f"• 24h Price Change: {coin['price_change_24h']:.2f}%\n"
            prompt += f"• 7d Price Change: {coin['price_change_7d']:.2f}%\n"
            
            # Add social data
            prompt += f"• Reddit Mentions: {coin.get('reddit_mentions', 0)}\n"
            
            # Add trending flag if applicable
            if coin.get('is_trending', False):
                prompt += "• TRENDING ON COINGECKO\n"
                
        prompt += """
Output JSON with:
- coin_symbol: Symbol of the cryptocurrency
- breakout_score: Score from 0-10 based on breakout potential
- reason: Brief explanation for the score
- timestamp: Current analysis timestamp

IMPORTANT: Provide a rating for ALL coins that have ANY Reddit mentions, even if they have low breakout potential.
For coins with low potential, you may assign a low score (0-3), but still include them in the results.

Format the output as a valid JSON array.
"""
        
        return prompt
        
    def process(self, collected_data):
        """Process all collected data and prepare for GPT analysis"""
        merged_data = self.merge_coin_data(collected_data)
        normalized_data = self.normalize_merged_data(merged_data)
        gpt_prompt = self.format_for_gpt(normalized_data)
        
        return {
            'merged_data': merged_data,
            'normalized_data': normalized_data,
            'gpt_prompt': gpt_prompt,
            'timestamp': datetime.now().isoformat()
        } 