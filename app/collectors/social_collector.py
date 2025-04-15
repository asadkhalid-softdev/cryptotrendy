import os
import praw
import time
import ssl
import requests
from datetime import datetime, timedelta
import urllib3

class SocialMediaCollector:
    def __init__(self):
        # Initialize Reddit client if credentials are available
        try:
            self.reddit = praw.Reddit(
                client_id=os.getenv('REDDIT_CLIENT_ID'),
                client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
                user_agent="CryptoTrendyApp/1.0"
            )
            self.reddit_enabled = True
        except:
            self.reddit_enabled = False
            print("Reddit API credentials not found or invalid, Reddit collection disabled")
            
        # Disable SSL certificate verification if in development mode
        self.dev_mode = os.getenv('DEVELOPMENT_MODE', 'false').lower() == 'true'
        if self.dev_mode:
            # Disable SSL verification warnings
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            # Create unverified SSL context
            ssl._create_default_https_context = ssl._create_unverified_context
            print("Development mode: SSL certificate verification disabled")
        
    def get_reddit_posts(self, subreddits=['CryptoCurrency', 'CryptoMarkets'], limit=100):
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
                time.sleep(0.5)
                
            if posts:
                print(f"✓ Successfully collected {len(posts)} Reddit posts from {', '.join(subreddits)}")
            return posts
        except Exception as e:
            print(f"Error collecting Reddit posts: {e}")
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
            print(f"✓ Found mentions of {mentioned_coins} different coins in Reddit posts")
            
            # Display the top mentioned coins for debugging
            mentioned_list = [(symbol, mentions[symbol]['reddit_mentions']) 
                             for symbol in mentions if mentions[symbol]['reddit_mentions'] > 0]
            mentioned_list.sort(key=lambda x: x[1], reverse=True)
            
            # Show top 10 or all if less than 10
            display_count = min(10, len(mentioned_list))
            if display_count > 0:
                print("  Top mentioned coins:")
                for i in range(display_count):
                    symbol, count = mentioned_list[i]
                    print(f"  - {symbol}: {count} mentions")
                    
                # If more than 10, show how many more
                if len(mentioned_list) > 10:
                    print(f"  ... and {len(mentioned_list) - 10} more coins with mentions")
                    
        return mentions
        
    def collect(self, coin_symbols):
        """Collect all social media data and extract relevant mentions"""
        if not coin_symbols:
            return {}
            
        reddit_posts = self.get_reddit_posts()
        
        mentions = self.extract_coin_mentions(reddit_posts, coin_symbols)
        
        result = {
            'reddit_posts': reddit_posts,
            'coin_mentions': mentions
        }
        
        if reddit_posts:
            print(f"✓ Social media collection completed successfully with {len(reddit_posts)} posts and {len(mentions)} tracked coins")
        
        return result 