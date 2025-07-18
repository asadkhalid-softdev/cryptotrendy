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

# At top of run.py or in a config module
RSI_BUY_1D_THRESHOLD = int(os.getenv('RSI_BUY_1D_THRESHOLD', '50'))
RSI_BUY_7D_THRESHOLD = int(os.getenv('RSI_BUY_7D_THRESHOLD', '50'))

print(f"RSI_BUY_1D_THRESHOLD: {RSI_BUY_1D_THRESHOLD}")
print(f"RSI_BUY_7D_THRESHOLD: {RSI_BUY_7D_THRESHOLD}")

def buy_analysis():
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

    original_count = len(coin_symbols)
    coins_filtered = []
    for sym, metrics in kucoin_data.items():
        r1 = metrics.get('rsi_1d')
        r7 = metrics.get('rsi_7d')
        if r1 < RSI_BUY_1D_THRESHOLD and r7 < RSI_BUY_7D_THRESHOLD:
            coins_filtered.append(sym)
    
    coin_symbols = [symbol for symbol in coin_symbols if symbol in coins_filtered]
    print(f"  ✓ {len(coin_symbols)} coins remain after KuCoin filter (from {original_count})")
    
    # Filter coin_symbols to only those present in kucoin_data if KuCoin TA is enabled
    if enable_kucoin_ta:
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
    
    # Enrich analysis results with RSI data
    for entry in analysis_result.get('analysis', []):
        symbol = entry.get('coin_symbol')
        metrics = kucoin_data.get(symbol, {})
        entry['rsi_1d'] = metrics.get('rsi_1d')
        entry['rsi_7d'] = metrics.get('rsi_7d')
    
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

if __name__ == "__main__":
    buy_analysis()