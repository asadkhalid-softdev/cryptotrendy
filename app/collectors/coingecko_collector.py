import os
import time
from pycoingecko import CoinGeckoAPI

class CoinGeckoCollector:
    def __init__(self):
        self.cg = CoinGeckoAPI()
        self.top_coins_limit = int(os.getenv('TOP_COINS_LIMIT', 100))
    
    def get_trending_coins(self):
        """Fetch trending coins from CoinGecko"""
        try:
            trending = self.cg.get_search_trending()
            return [coin['item'] for coin in trending['coins']]
        except Exception as e:
            print(f"Error fetching trending coins: {e}")
            return []
    
    def get_market_data(self):
        """Fetch market data for top coins by market cap"""
        try:
            market_data = self.cg.get_coins_markets(
                vs_currency='usd',
                order='market_cap_desc',
                per_page=self.top_coins_limit,
                page=1,
                sparkline=False,
                price_change_percentage='24h,7d'
            )
            
            # Add a small delay to avoid API rate limiting
            time.sleep(0.5)

            print(f"Fetched market data for {len(market_data)} coins")
            
            return market_data
        except Exception as e:
            print(f"Error fetching market data: {e}")
            return []
    
    def collect(self):
        """Collect all data from CoinGecko"""
        trending_coins = self.get_trending_coins()
        market_data = self.get_market_data()
        
        # Create an identifier for trending coins
        trending_ids = [coin['id'] for coin in trending_coins]
        
        # Add trending flag to market data
        for coin in market_data:
            coin['is_trending'] = coin['id'] in trending_ids
            
        return {
            'trending_coins': trending_coins,
            'market_data': market_data
        } 
    
if __name__ == "__main__":
    import pandas as pd
    coingecko = CoinGeckoCollector()
    coingecko_data = coingecko.collect()
    coin_symbols = [coin.get('symbol', '').upper() for coin in coingecko_data['market_data']]
    print(coin_symbols)
    market_coins = pd.DataFrame(coingecko_data['market_data'])
    print(market_coins)
    print(market_coins.columns)