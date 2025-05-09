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
from app.collectors.coingecko_collector import CoinGeckoCollector
from app.collectors.social_collector import SocialMediaCollector
from app.collectors.kucoin_collector import KuCoinCollector
from app.formatters.data_formatter import DataFormatter
from app.analysis.gpt_analyzer import GPTAnalyzer
from app.output.excel_exporter import ExcelExporter
from app.output.telegram_sender import TelegramSender

coingecko = CoinGeckoCollector()
social_media = SocialMediaCollector()
kucoin_collector = KuCoinCollector()
telegram_sender = TelegramSender()

def main():
    """Main function to orchestrate the crypto analysis pipeline"""
    start_time = time.time()
    print(f"🔍 Starting crypto signal analysis - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check for development mode and feature flags
    dev_mode = os.getenv('DEVELOPMENT_MODE', 'false').lower() == 'true'
    skip_gpt = os.getenv('SKIP_GPT', 'false').lower() == 'true'
    enable_kucoin_ta = os.getenv('ENABLE_KUCOIN_TA', 'false').lower() == 'true'
    
    if dev_mode:
        print("ℹ️ Running in development mode")
    
    if skip_gpt:
        print("ℹ️ GPT analysis will be skipped")
    
    # 1. Collect data from various sources
    print("\n📥 Collecting data from sources...")
    
    # CoinGecko data
    print("  - Fetching CoinGecko market data...")
    coingecko_data = coingecko.collect()
    
    # Check if CoinGecko data was successfully retrieved
    if not coingecko_data or 'market_data' not in coingecko_data or not coingecko_data['market_data']:
        print("  ❌ Error: Failed to collect CoinGecko market data. Exiting.")
        sys.exit(1)
    
    # Extract coin symbols from CoinGecko data for other collectors
    coin_symbols = [coin.get('symbol', '').upper() for coin in coingecko_data['market_data']]
    print(f"  ✓ Found {len(coin_symbols)} coins in market data")
    
    # KuCoin TA data (Conditional)
    kucoin_data = {}
    if enable_kucoin_ta:
        kucoin_data = kucoin_collector.collect(coin_symbols)
    else:
        print("  - KuCoin TA is disabled via environment variable.")
    
    # Filter coin_symbols to only those present in kucoin_data if KuCoin TA is enabled
    if enable_kucoin_ta:
        original_count = len(coin_symbols)
        coin_symbols = [symbol for symbol in coin_symbols if symbol in kucoin_data]
        print(f"  ✓ {len(coin_symbols)} coins remain after KuCoin filter (from {original_count})")
        # Filter CoinGecko market_data to include only symbols present in KuCoin data
        coingecko_data['market_data'] = [entry for entry in coingecko_data['market_data'] if entry.get('symbol', '').upper() in coin_symbols]
        print(f"  ✓ {len(coingecko_data['market_data'])} CoinGecko entries remain after KuCoin filter")
    
    # Social media data
    print("  - Fetching social media mentions...")
    social_data_full = social_media.collect(coin_symbols)

    # Extract the actual mentions dictionary
    social_mentions_data = social_data_full.get('coin_mentions', {})

    # Fix the log message to report based on the mentions dictionary
    print(f"  ✓ Social media data collection complete (found mentions for {len(social_mentions_data)} coins)")
    
    # 2. Format data for analysis
    print("\n🧹 Formatting data...")
    formatter = DataFormatter()
    formatted_data = formatter.format_for_gpt(coingecko_data, social_mentions_data, kucoin_data)
    
    if not formatted_data:
        print("  ❌ Error: No data available after formatting. Exiting.")
        sys.exit(1)
    
    print(f"  ✓ Formatted data for {len(formatted_data)} coins")
    
    # 3. Analyze data using GPT (Conditional)
    analysis_result = {}
    if not skip_gpt:
        print("\n🧠 Analyzing data with GPT...")
        analyzer = GPTAnalyzer()
        analysis_result = analyzer.analyze(formatted_data)
        if analysis_result and 'analysis' in analysis_result:
            print(f"  ✓ GPT analysis complete. Found potential breakouts for {len(analysis_result.get('analysis', []))} coins.")
        else:
            print("  ✓ GPT analysis complete. No specific breakouts identified or error occurred.")
    else:
        print("\n🧠 Skipping GPT analysis...")
        # Prepare a structure similar to GPT output for downstream processing if skipped
        analysis_result = {
            'timestamp': datetime.now().isoformat(),
            'model_used': 'skipped',
            'analysis': [{'coin_symbol': coin.get('symbol'), 'breakout_score': '0', 'reason': 'GPT analysis skipped'} for coin in formatted_data]
        }
    
    # 4. Output results
    print("\n📤 Exporting results...")
    
    # Prepare raw data bundle for Excel export
    raw_data_bundle = {
        'coingecko': coingecko_data,
        'social': social_data_full,
        'kucoin': kucoin_data,
        'formatted_for_gpt': formatted_data
    }
    
    # Save to Excel
    exporter = ExcelExporter()
    save_status = exporter.save_analysis(analysis_result, raw_data=raw_data_bundle)
    if save_status:
        print(f"  ✓ Results saved to {exporter.output_file}")
    else:
        print(f"  ❌ Failed to save results to Excel.")
    
    # Send to Telegram
    send_status = telegram_sender.send_analysis(analysis_result)
    if send_status:
        print("  ✓ Telegram notification sent successfully.")
    else:
        print("  ❌ Failed to send Telegram notification.")
    
    end_time = time.time()
    print(f"\n✅ Crypto signal analysis finished in {end_time - start_time:.2f} seconds.")

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
        if r1 is not None and r7 is not None and r1 > 70 and r7 > 70:
            notification_list.append({'symbol': sym, 'rsi_1d': r1, 'rsi_7d': r7})

    if not notification_list:
        print("No symbols with both RSI_1d and RSI_7d >70 found.")
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
    main()
    current_asset_analysis()