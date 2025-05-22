import os
import praw
import time
import ssl
import logging
# import requests # Not used directly
from datetime import datetime, timedelta # Not used directly
import urllib3

logger = logging.getLogger(__name__)

class SocialMediaCollector:
    def __init__(self):
        # Initialize Reddit client if credentials are available
        try:
            self.reddit = praw.Reddit(
                client_id=os.getenv('REDDIT_CLIENT_ID'),
                client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
                user_agent="CryptoTrendyApp/1.0" # TODO: Consider making user_agent configurable or more specific
            )
            self.reddit_enabled = True
            logger.info("Reddit client initialized successfully.")
        except Exception as e: # Catching a more specific exception is better if possible
            self.reddit_enabled = False
            logger.error("Reddit API credentials not found or invalid, Reddit collection disabled.", exc_info=True)
            
        # Disable SSL certificate verification if in development mode
        self.dev_mode = os.getenv('DEVELOPMENT_MODE', 'false').lower() == 'true'
        if self.dev_mode:
            # Disable SSL verification warnings
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            # Create unverified SSL context
            # Note: Modifying ssl._create_default_https_context is a global change and might affect other parts of the application
            # or other libraries. Consider if this is the desired scope.
            ssl._create_default_https_context = ssl._create_unverified_context
            logger.warning("Development mode: SSL certificate verification disabled. This is a global change.")
        
    def get_reddit_posts(self, subreddits=['CryptoCurrency', 'CryptoMarkets', 'Altcoin', 'Solana', 'DeFi', 'CryptoMoonShots', 'Cardano'], limit=100):
        """Collect top posts from cryptocurrency subreddits"""
        if not self.reddit_enabled:
            return []
            
        posts = []
        try:
            for subreddit_name in subreddits:
                subreddit = self.reddit.subreddit(subreddit_name)
                
                # Get hot posts
                for post in subreddit.hot(limit=limit):
                    posts.append({
                        'title': post.title,
                        'score': post.score,
                        'url': post.url,
                        'created_utc': post.created_utc,
                        'num_comments': post.num_comments,
                        'subreddit': subreddit_name
                    })
                    
                # Add a small delay
                time.sleep(0.5) # PRAW usually handles rate limits, but this adds politeness.
                
            if posts:
                logger.info(f"✓ Successfully collected {len(posts)} Reddit posts from {', '.join(subreddits)}")
            return posts
        except Exception as e:
            logger.error(f"Error collecting Reddit posts: {e}", exc_info=True)
            return []
            
    def extract_coin_mentions(self, posts, coin_symbols):
        """Extract mentions of specific coins from social media content"""
        mentions = {symbol: {'reddit_mentions': 0} for symbol in coin_symbols}
        
        # Convert symbols to lowercase for case-insensitive matching
        symbols_lower = [s.lower() for s in coin_symbols]
        
        # Count Reddit mentions
        for post in posts:
            title_lower = post['title'].lower()
            for i, symbol in enumerate(symbols_lower):
                if symbol in title_lower or f"${symbol}" in title_lower:
                    mentions[coin_symbols[i]]['reddit_mentions'] += 1
        
        # Count mentions with at least one occurrence
        mentioned_coins = sum(1 for symbol in mentions if mentions[symbol]['reddit_mentions'] > 0)
        if mentioned_coins > 0:
            logger.info(f"✓ Found mentions of {mentioned_coins} different coins in Reddit posts")
            
            # Display the top mentioned coins for debugging
            mentioned_list = [(symbol, mentions[symbol]['reddit_mentions']) 
                             for symbol in mentions if mentions[symbol]['reddit_mentions'] > 0]
            mentioned_list.sort(key=lambda x: x[1], reverse=True)
            
            # Show top 10 or all if less than 10
            display_count = min(10, len(mentioned_list))
            if display_count > 0:
                logger.debug("  Top mentioned coins:")
                for i in range(display_count):
                    symbol, count = mentioned_list[i]
                    logger.debug(f"  - {symbol}: {count} mentions")
                    
                # If more than 10, show how many more
                if len(mentioned_list) > 10:
                    logger.debug(f"  ... and {len(mentioned_list) - 10} more coins with mentions")
                    
        return mentions
        
    def collect(self, coin_symbols):
        """Collect all social media data and extract relevant mentions"""
        if not coin_symbols:
            logger.warning("No coin symbols provided to SocialMediaCollector, skipping collection.")
            return {} # Return empty structure consistent with expected output
            
        reddit_posts = self.get_reddit_posts()
        
        mentions = self.extract_coin_mentions(reddit_posts, coin_symbols)
        
        result = {
            'reddit_posts': reddit_posts, # This can be large, consider if it's always needed in the result
            'coin_mentions': mentions
        }
        
        if reddit_posts:
            logger.info(f"✓ Social media collection completed successfully with {len(reddit_posts)} posts and {len(mentions)} tracked coins for mentions.")
        else:
            logger.info("Social media collection resulted in no posts.")
        
        # --- DEBUG PRINTS ---
        # These are now logged as DEBUG level
        mentions_to_return = result.get('coin_mentions', {})
        logger.debug(f"DEBUG (SocialCollector): Returning social_data keys: {list(mentions_to_return.keys())}")
        # Avoid logging potentially very large structures unless necessary, or summarize them.
        # For instance, log the number of items or a few examples if the content is large.
        # For now, this will log the full content at DEBUG level.
        logger.debug(f"DEBUG (SocialCollector): Returning social_data content: {mentions_to_return}")
        # --- END DEBUG PRINTS ---

        return result 