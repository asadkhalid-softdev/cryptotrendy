#!/usr/bin/env python
import os
import time
import sys
from datetime import datetime
from dotenv import load_dotenv
import pandas as pd

# Load environment variables from .env file
load_dotenv()

# Import components
from app.collectors.kucoin_collector import KuCoinCollector
from app.output.telegram_sender import TelegramSender

kucoin_collector = KuCoinCollector()
telegram_sender = TelegramSender()

# At top of run.py or in a config module
RSI_SELL_1D_THRESHOLD = int(os.getenv('RSI_SELL_1D_THRESHOLD', '80'))
RSI_SELL_7D_THRESHOLD = int(os.getenv('RSI_SELL_7D_THRESHOLD', '70'))

print(f"RSI_SELL_1D_THRESHOLD: {RSI_SELL_1D_THRESHOLD}")
print(f"RSI_SELL_7D_THRESHOLD: {RSI_SELL_7D_THRESHOLD}")

def current_asset_analysis():
    """Fetch symbols from Google Sheet, fetch KuCoin RSI data, and send alerts for overbought symbols."""
    sheet_id = os.getenv('CURRENT_ASSET_SHEET_ID')
    if not sheet_id:
        print("Environment variable CURRENT_ASSET_SHEET_ID is not set.")
        return
    csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    try:
        df_sheet = pd.read_csv(csv_url)
    except Exception as e:
        print(f"Error fetching Google Sheet: {e}")
        return
    # Locate 'Symbols' column
    col_symbols = next((col for col in df_sheet.columns if col.lower() == 'symbols'), None)
    if col_symbols is None:
        print("No 'Symbols' column found in Google Sheet.")
        return
    symbols = df_sheet[col_symbols].dropna().astype(str).str.upper().tolist()
    print(f"Fetched {len(symbols)} symbols from Google Sheet.")
    # Fetch RSI data from KuCoin
    ku_data = kucoin_collector.collect(symbols)
    # Build notification list for symbols with both RSIs >70
    notification_list = []
    for sym, metrics in ku_data.items():
        r1 = metrics.get('rsi_1d')
        r7 = metrics.get('rsi_7d')
        if r1 is not None and r7 is not None and r1 > RSI_SELL_1D_THRESHOLD and r7 > RSI_SELL_7D_THRESHOLD:
            notification_list.append({'symbol': sym, 'rsi_1d': r1, 'rsi_7d': r7})

    if not notification_list:
        print("No symbols with both RSI_1d and RSI_7d > thresholds found.")
        return
    # Build notification message
    message = "*🚨 RSI Alert: KuCoin Overbought Signals 🚨*\n\n"
    for item in notification_list:
        message += f"*{item['symbol']}* - RSI 1D: {item['rsi_1d']}, RSI 7D: {item['rsi_7d']}\n"
    message += "\n_This is an automated alert by your script._"
    # Send via Telegram
    sent = telegram_sender.send_message(message)
    if sent:
        print("Notification sent via Telegram.")
    else:
        print("Failed to send Telegram notification.") 
    
if __name__ == "__main__":
    current_asset_analysis()