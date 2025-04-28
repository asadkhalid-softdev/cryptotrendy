import os
import asyncio
from telegram import Bot
from datetime import datetime

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
        
    def format_analysis_for_telegram(self, analysis_result):
        """Format analysis results for Telegram message"""
        if not analysis_result or 'analysis' not in analysis_result:
            return "No analysis data available to send."
            
        analysis_data = analysis_result['analysis']
        
        if not analysis_data:
            return "Analysis completed but no results found."
            
        # Sort by breakout score (descending)
        if isinstance(analysis_data, list):
            sorted_coins = sorted(analysis_data, key=lambda x: float(x.get('breakout_score', 0)), reverse=True)
            top_coins = sorted_coins[:self.max_coins]
        else:
            # Single coin case
            top_coins = [analysis_data]
            
        # Format message
        date_str = datetime.now().strftime('%Y-%m-%d')
        message = f"*🚀 CRYPTO BREAKOUT POTENTIAL: {date_str} 🚀*\n\n"
        
        for i, coin in enumerate(top_coins, 1):
            symbol = coin.get('coin_symbol', '')
            score = coin.get('breakout_score', 0)
            reason = coin.get('reason', '').replace('\n', ' ')
            
            message += f"*{i}. {symbol}* - Score: {score}/10\n"
            message += f"_{reason}_\n\n"
            
        message += "\n_This is an automated analysis and not financial advice._"
        
        return message
        
    def send_analysis(self, analysis_result):
        """Format and send analysis results via Telegram"""
        message = self.format_analysis_for_telegram(analysis_result)
        return self.send_message(message) 