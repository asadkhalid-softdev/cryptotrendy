import os
import asyncio
from telegram import Bot
from datetime import datetime
import pandas as pd

class TelegramSender:
    def __init__(self):
        self.token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.enabled = self.token is not None and self.chat_id is not None
        self.max_coins = int(os.getenv('MAX_COINS_TELEGRAM', '10')) # <-- Wrap with int()

        if not self.enabled:
            print("Telegram bot not configured. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID to enable.")
            
    async def send_message_async(self, message):
        """Send message asynchronously"""
        if not self.enabled:
            return False
            
        try:
            bot = Bot(token=self.token)
            await bot.send_message(chat_id=self.chat_id, text=message, parse_mode='Markdown')
            return True
        except Exception as e:
            print(f"Error sending Telegram message: {e}")
            return False
            
    def send_message(self, message):
        """Send message (synchronous wrapper)"""
        return asyncio.run(self.send_message_async(message))
        
    def format_analysis_for_telegram(self, analysis_result, coingecko_data, social_mentions_data, kucoin_data):
        """Format analysis results for Telegram message"""
        if not analysis_result or 'analysis' not in analysis_result:
            return "No analysis data available to send."
            
        analysis_data = analysis_result['analysis']
            
        # Sort by breakout score (descending)
        if isinstance(analysis_data, list):
            sorted_coins = sorted(analysis_data, key=lambda x: float(x.get('breakout_score', 0)), reverse=True)
            top_coins = sorted_coins[:self.max_coins]
        else:
            # Single coin case
            top_coins = [analysis_data]
        
        top_symbols = [i.get('coin_symbol', '').upper() for i in top_coins]

        coingecko_data = [i for i in coingecko_data['market_data'] if i.get('symbol', '').upper() in top_symbols]
        coingecko_data = {item.get('symbol', '').upper(): item for item in coingecko_data}
        
        if not analysis_data:
            return "Analysis completed but no results found."
            
        # Format message
        date_str = datetime.now().strftime('%Y-%m-%d')
        message = f"*🚀 CRYPTO BREAKOUT POTENTIAL: {date_str} 🚀*\n\n"
        
        for i, coin in enumerate(top_coins, 1):
            symbol = coin.get('coin_symbol', '').upper()
            score = coin.get('breakout_score', 0)
            reason = coin.get('reason', '').replace('\n', ' ')

            coingecko_data_item = coingecko_data.get(symbol, {})
            social_mentions_data_item = social_mentions_data.get(symbol, {})
            kucoin_data_item = kucoin_data.get(symbol, {})

            social_mentions = social_mentions_data_item.get('reddit_mentions', 0)
            current_price = round(coingecko_data_item.get('current_price', 0), 4)
            price_change_24h = round(coingecko_data_item.get('price_change_percentage_24h', 0), 2)
            price_change_7d = round(coingecko_data_item.get('price_change_percentage_7d_in_currency', 0), 2)
            is_trending = coingecko_data_item.get('is_trending', False)
            rsi_1d = kucoin_data_item.get('rsi_1d', 'n/a')
            rsi_7d = kucoin_data_item.get('rsi_7d', 'n/a')

            message += f"*{i}. {symbol} - Score: {score}/10* \
                \n Social Mentions: {social_mentions} | Trending: {'Yes' if is_trending else 'No'} \
                \n Price: ${current_price} | 24H: {price_change_24h}% | 7D: {price_change_7d}% \
                \n RSI 1D: {rsi_1d} | RSI 7D: {rsi_7d} \
                \n _{reason}_\n\n"
            
        message += "\n_This is an automated analysis and not financial advice._"
        
        return message
        
    def send_analysis(self, analysis_result, coingecko_data, social_mentions_data, kucoin_data):
        """Format and send analysis results via Telegram"""
        message = self.format_analysis_for_telegram(analysis_result, coingecko_data, social_mentions_data, kucoin_data)
        return self.send_message(message) 