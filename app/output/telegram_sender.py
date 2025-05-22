import os
import asyncio
import logging
from telegram import Bot
from datetime import datetime

logger = logging.getLogger(__name__)

class TelegramSender:
    def __init__(self):
        self.token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.enabled = self.token is not None and self.chat_id is not None
        self.max_coins = int(os.getenv('MAX_COINS_TELEGRAM', '10'))
        self.bot = None
        self.TELEGRAM_MAX_MESSAGE_LENGTH = 4096

        if self.enabled:
            self.bot = Bot(token=self.token)
            logger.info("TelegramSender initialized and enabled.")
        else:
            logger.warning("Telegram bot not configured. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID to enable. TelegramSender disabled.")
            
    async def _send_single_message_async(self, message_part):
        """Helper to send a single part of a potentially split message."""
        if not self.enabled or not self.bot:
            logger.warning("TelegramSender not enabled or bot not initialized. Cannot send message part.")
            return False
        try:
            await self.bot.send_message(chat_id=self.chat_id, text=message_part, parse_mode='Markdown')
            logger.debug(f"Telegram message part sent successfully (length: {len(message_part)}).")
            return True
        except Exception as e:
            logger.error(f"Error sending Telegram message part: {e}", exc_info=True)
            return False

    def send_message(self, message_text):
        """
        Send a message, splitting it into multiple parts if it exceeds Telegram's character limit.
        (Synchronous wrapper)
        """
        if not self.enabled or not self.bot:
            logger.warning("TelegramSender not enabled or bot not initialized. Cannot send message.")
            return False

        if len(message_text) <= self.TELEGRAM_MAX_MESSAGE_LENGTH:
            return asyncio.run(self._send_single_message_async(message_text))
        
        logger.info(f"Message length ({len(message_text)}) exceeds max length ({self.TELEGRAM_MAX_MESSAGE_LENGTH}). Splitting message.")
        parts = []
        current_part = ""
        # Split by lines first to maintain readability
        lines = message_text.split('\n')
        
        for line in lines:
            # If a single line itself is too long, it needs hard splitting.
            # This simple splitter doesn't handle hard splitting a single overlong line yet.
            # For now, we assume lines are not individually longer than MAX_LENGTH.
            if len(line) > self.TELEGRAM_MAX_MESSAGE_LENGTH:
                logger.warning(f"A single line is too long to send: {line[:100]}...")
                # Attempt to send what we have and then this long line separately (it will likely fail if too long)
                if current_part:
                    parts.append(current_part)
                    current_part = ""
                parts.append(line) # Add the problematic line as its own part
                continue

            if len(current_part) + len(line) + 1 <= self.TELEGRAM_MAX_MESSAGE_LENGTH: # +1 for newline
                if current_part:
                    current_part += "\n" + line
                else:
                    current_part = line
            else:
                parts.append(current_part)
                current_part = line
        
        if current_part: # Add the last part
            parts.append(current_part)

        all_sent_successfully = True
        for i, part in enumerate(parts):
            logger.info(f"Sending part {i+1}/{len(parts)} (length: {len(part)})")
            if not asyncio.run(self._send_single_message_async(part)):
                all_sent_successfully = False
                # Optionally break here or try to send all parts
                # For now, try to send all parts and report overall success/failure
        
        return all_sent_successfully
        
    def format_analysis_for_telegram(self, analysis_result):
        """Format analysis results for Telegram message"""
        if not analysis_result or 'analysis' not in analysis_result:
            logger.warning("No analysis data available to format for Telegram.")
            return "No analysis data available to send." # Return a string to be sent as a message
            
        analysis_data = analysis_result.get('analysis', []) # analysis_result['analysis'] is already checked
        
        if not analysis_data:
            logger.info("Analysis completed but no results found to format for Telegram.")
            return "Analysis completed but no results found." # Return a string
            
        # Sort by breakout score (descending)
        if isinstance(analysis_data, list):
            sorted_coins = sorted(analysis_data, key=lambda x: float(x.get('breakout_score', 0)), reverse=True)
            top_coins = sorted_coins[:self.max_coins]
        else:
            # Single coin case (though analysis_result['analysis'] is expected to be a list)
            logger.warning("analysis_data is not a list, treating as a single coin case.")
            top_coins = [analysis_data]
            
        # Format message
        date_str = datetime.now().strftime('%Y-%m-%d')
        # Using a slightly different header to reflect it might be for top N coins
        message_header = f"*🏆 Top {len(top_coins)} Crypto Breakout Potentials ({date_str}) 🏆*\n\n"
        
        message_body_parts = []
        for i, coin in enumerate(top_coins, 1):
            symbol = coin.get('coin_symbol', 'N/A')
            score_val = coin.get('breakout_score', 0)
            try:
                score = float(score_val) # Ensure score is float for formatting if needed
            except ValueError:
                score = 0.0 # Default if conversion fails
            reason = coin.get('reason', 'N/A').replace('\n', ' ') # Replace newlines in reason
            
            rsi_1d = coin.get('rsi_1d', 'N/A')
            rsi_7d = coin.get('rsi_7d', 'N/A')
            
            coin_entry = f"*{i}. {symbol}* - Score: {score:.1f}/10\n" \
                         f"RSI 1D: {rsi_1d}, 7D: {rsi_7d}\n" \
                         f"_{reason}_\n\n"
            message_body_parts.append(coin_entry)
            
        disclaimer = "\n_This is an automated analysis and not financial advice._"
        
        # Construct the full message string
        # The splitting logic in send_message will handle this.
        full_message_string = message_header + "".join(message_body_parts) + disclaimer
        
        return full_message_string # Return the full string to be handled by send_message
        
    def send_analysis(self, analysis_result):
        """Format and send analysis results via Telegram"""
        # Get the formatted message string (which might be very long)
        full_message_string = self.format_analysis_for_telegram(analysis_result)
        
        # The send_message method will now handle potential splitting
        return self.send_message(message) 