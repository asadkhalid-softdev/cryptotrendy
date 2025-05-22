#!/usr/bin/env python
import os
import time
import sys
import logging
from datetime import datetime
from dotenv import load_dotenv
import pandas as pd
from concurrent.futures import ThreadPoolExecutor

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

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
RSI_SELL_1D_THRESHOLD = int(os.getenv('RSI_SELL_1D_THRESHOLD', '80'))
RSI_SELL_7D_THRESHOLD = int(os.getenv('RSI_SELL_7D_THRESHOLD', '70'))

def main():
    """Main function to orchestrate the crypto analysis pipeline"""
    start_time = time.time()
    logging.info(f"🔍 Starting crypto signal analysis - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check for development mode and feature flags
    dev_mode = os.getenv('DEVELOPMENT_MODE', 'false').lower() == 'true'
    skip_gpt = os.getenv('SKIP_GPT', 'false').lower() == 'true'
    enable_kucoin_ta = os.getenv('ENABLE_KUCOIN_TA', 'false').lower() == 'true'
    
    if dev_mode:
        logging.info("ℹ️ Running in development mode")
    
    if skip_gpt:
        logging.info("ℹ️ GPT analysis will be skipped")
    
    # 1. Collect data from various sources
    logging.info("\n📥 Collecting data from sources...")
    
    # CoinGecko data
    logging.info("  - Fetching CoinGecko market data...")
    coingecko_data = coingecko.collect()
    
    # Check if CoinGecko data was successfully retrieved
    if not coingecko_data or 'market_data' not in coingecko_data or not coingecko_data['market_data']:
        logging.error("  ❌ Error: Failed to collect CoinGecko market data. Exiting.")
        sys.exit(1)
    
    # Extract coin symbols from CoinGecko data for other collectors
    coin_symbols = [coin.get('symbol', '').upper() for coin in coingecko_data['market_data']]
    logging.info(f"  ✓ Found {len(coin_symbols)} coins in market data for potential KuCoin and Social Media collection.")

    kucoin_data = {}
    social_data_full = {}

    if enable_kucoin_ta:
        logging.info("  - Starting concurrent fetching for KuCoin TA data and Social Media mentions...")
        with ThreadPoolExecutor(max_workers=2) as executor:
            # Submit KuCoin collection task
            kucoin_future = executor.submit(kucoin_collector.collect, coin_symbols)
            # Submit Social Media collection task (uses the original coin_symbols from CoinGecko)
            social_future = executor.submit(social_media.collect, coin_symbols)

            # Retrieve results
            # Future.result() will re-raise exceptions from the threads, caught by main try-except
            kucoin_data = kucoin_future.result()
            social_data_full = social_future.result()
        
        logging.info("  ✓ Concurrent fetching for KuCoin and Social Media complete.")

        # Filter coin_symbols and coingecko_data['market_data'] based on results from kucoin_data
        # This is done after both collections are complete.
        original_coingecko_market_data_count = len(coingecko_data['market_data'])
        original_coin_symbols_count = len(coin_symbols)

        # Filter coin_symbols to only those for which KuCoin returned data (i.e., keys in kucoin_data)
        # and for which RSI values were actually calculated (not None and not filtered by KuCoin's internal logic)
        filtered_symbols_from_kucoin = set(kucoin_data.keys())
        
        coin_symbols = [s for s in coin_symbols if s in filtered_symbols_from_kucoin]
        logging.info(f"  ✓ {len(coin_symbols)} coins remain after filtering based on KuCoin data presence (from {original_coin_symbols_count}).")

        coingecko_data['market_data'] = [
            entry for entry in coingecko_data['market_data']
            if entry.get('symbol', '').upper() in coin_symbols
        ]
        logging.info(f"  ✓ {len(coingecko_data['market_data'])} CoinGecko entries remain after filtering based on KuCoin data presence (from {original_coingecko_market_data_count}).")

        if not coin_symbols:
            logging.warning("All coins were filtered out after KuCoin data processing or KuCoin returned no data. No coins left for further processing.")
    else:
        logging.info("  - KuCoin TA is disabled. Fetching Social Media mentions only...")
        social_data_full = social_media.collect(coin_symbols)
        logging.info("  - KuCoin TA is disabled via environment variable.") # Kept for consistency if needed, or remove

    # Extract the actual mentions dictionary
    social_mentions_data = social_data_full.get('coin_mentions', {})

    # Fix the log message to report based on the mentions dictionary
    logging.info(f"  ✓ Social media data collection complete (found mentions for {len(social_mentions_data)} coins)")
    
    # 2. Format data for analysis
    logging.info("\n🧹 Formatting data...")
    formatter = DataFormatter()
    formatted_data = formatter.format_for_gpt(coingecko_data, social_mentions_data, kucoin_data)
    
    if not formatted_data:
        logging.error("  ❌ Error: No data available after formatting. Exiting.")
        sys.exit(1)
    
    logging.info(f"  ✓ Formatted data for {len(formatted_data)} coins")
    
    # 3. Analyze data using GPT (Conditional)
    analysis_result = {}
    if not skip_gpt:
        logging.info("\n🧠 Analyzing data with GPT...")
        analyzer = GPTAnalyzer()
        analysis_result = analyzer.analyze(formatted_data)
        if analysis_result and 'analysis' in analysis_result and analysis_result.get('analysis'):
            logging.info(f"  ✓ GPT analysis complete. Found potential breakouts for {len(analysis_result.get('analysis', []))} coins.")
        elif analysis_result and 'error' in analysis_result:
            logging.error(f"  GPT analysis returned an error: {analysis_result['error']}")
        else:
            logging.warning("  ✓ GPT analysis complete. No specific breakouts identified or an unexpected response structure was received.")
    else:
        logging.info("\n🧠 Skipping GPT analysis...")
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
    logging.info("\n📤 Exporting results...")
    
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
        logging.info(f"  ✓ Results saved to {exporter.output_file}")
    else:
        logging.error(f"  ❌ Failed to save results to Excel.")
    
    # Send to Telegram
    send_status = telegram_sender.send_analysis(analysis_result)
    if send_status:
        logging.info("  ✓ Telegram notification sent successfully.")
    else:
        logging.error("  ❌ Failed to send Telegram notification.")
    
    end_time = time.time()
    logging.info(f"\n✅ Crypto signal analysis finished in {end_time - start_time:.2f} seconds.")

def current_asset_analysis():
    """Fetch symbols from Google Sheet, fetch KuCoin RSI data, and send alerts for overbought symbols."""
    sheet_id = os.getenv('CURRENT_ASSET_SHEET_ID')
    if not sheet_id:
        logging.warning("Environment variable CURRENT_ASSET_SHEET_ID is not set. Skipping current asset analysis.")
        return
    csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    try:
        df_sheet = pd.read_csv(csv_url)
    except Exception as e:
        logging.error(f"Error fetching Google Sheet: {e}")
        return
    # Locate 'Symbols' column
    col_symbols = next((col for col in df_sheet.columns if col.lower() == 'symbols'), None)
    if col_symbols is None:
        logging.warning("No 'Symbols' column found in Google Sheet. Skipping current asset analysis.")
        return
    symbols = df_sheet[col_symbols].dropna().astype(str).str.upper().tolist()
    logging.info(f"Fetched {len(symbols)} symbols from Google Sheet for current asset analysis.")
    # Fetch RSI data from KuCoin
    ku_data = kucoin_collector.collect(symbols) # This will use KuCoinCollector's own logging
    # Build notification list for symbols with both RSIs > thresholds
    notification_list = []
    for sym, metrics in ku_data.items():
        r1 = metrics.get('rsi_1d')
        r7 = metrics.get('rsi_7d')
        if r1 is not None and r7 is not None and r1 > RSI_SELL_1D_THRESHOLD and r7 > RSI_SELL_7D_THRESHOLD: # Ensure thresholds are used
            notification_list.append({'symbol': sym, 'rsi_1d': r1, 'rsi_7d': r7})

    if not notification_list:
        logging.info("No symbols with both RSI_1d and RSI_7d > sell thresholds found in current assets.")
        return
    # Build notification message
    message = "*🚨 RSI Alert: KuCoin Overbought Signals (Current Assets) 🚨*\n\n"
    for item in notification_list:
        message += f"*{item['symbol']}* - RSI 1D: {item['rsi_1d']}, RSI 7D: {item['rsi_7d']}\n"
    message += "\n_This is an automated alert by your script._"
    # Send via Telegram
    sent = telegram_sender.send_message(message) # This will use TelegramSender's own logging
    if sent:
        logging.info("Current asset overbought notification sent via Telegram.")
    else:
        logging.error("Failed to send current asset overbought Telegram notification.") 
    
if __name__ == "__main__":
    # Wrap main execution in a try-except block for overarching error capture
    try:
        main()
    except SystemExit: # Let SystemExit propagate to exit the script with the intended code
        raise
    except Exception as e:
        logging.error("An unexpected error occurred in the main analysis pipeline:", exc_info=True)
        sys.exit(1) # Exit with a general error code
    
    # Separate try-except for current_asset_analysis as it's a distinct task
    try:
        current_asset_analysis()
    except Exception as e:
        logging.error("An unexpected error occurred in the current asset analysis:", exc_info=True)
        # Do not necessarily exit here, as main analysis might have succeeded.
    # current_asset_analysis() # This is now called within the try-except block above