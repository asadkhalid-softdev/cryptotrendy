#!/usr/bin/env python
import os
import time
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import components
from app.collectors.coingecko_collector import CoinGeckoCollector
from app.collectors.social_collector import SocialMediaCollector
from app.formatters.data_formatter import DataFormatter
from app.analysis.gpt_analyzer import GPTAnalyzer
from app.output.excel_exporter import ExcelExporter
from app.output.telegram_sender import TelegramSender

def main():
    """Main function to orchestrate the crypto analysis pipeline"""
    start_time = time.time()
    print(f"🔍 Starting crypto signal analysis - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check for development mode
    dev_mode = os.getenv('DEVELOPMENT_MODE', 'false').lower() == 'true'
    skip_gpt = os.getenv('SKIP_GPT', 'false').lower() == 'true'
    
    if dev_mode:
        print("ℹ️ Running in development mode")
    
    if skip_gpt:
        print("ℹ️ GPT analysis will be skipped")
    
    # 1. Collect data from various sources
    print("\n📥 Collecting data from sources...")
    
    # CoinGecko data
    print("  - Fetching CoinGecko market data...")
    coingecko = CoinGeckoCollector()
    coingecko_data = coingecko.collect()
    
    # Check if CoinGecko data was successfully retrieved
    if not coingecko_data or 'market_data' not in coingecko_data or not coingecko_data['market_data']:
        print("  ❌ Error: Failed to collect CoinGecko market data. Exiting.")
        sys.exit(1)
    
    # Extract coin symbols from CoinGecko data for other collectors
    coin_symbols = [coin.get('symbol', '').upper() for coin in coingecko_data['market_data']]
    print(f"  ✓ Found {len(coin_symbols)} coins in market data")
    
    # Social media data
    print("  - Fetching social media mentions...")
    social_media = SocialMediaCollector()
    social_media_data = social_media.collect(coin_symbols)
    
    # Continue even if social media fails, but log a warning
    if not social_media_data:
        print("  ⚠️ Warning: No social media data collected. Continuing with market data only.")
    
    # Combine all collected data
    collected_data = {
        'coingecko': coingecko_data,
        'social_media': social_media_data
    }
    
    # 2. Format and process data
    print("\n🧹 Formatting and normalizing data...")
    formatter = DataFormatter()
    processed_data = formatter.process(collected_data)
    
    # Check if data processing was successful
    if not processed_data or not processed_data.get('merged_data'):
        print("  ❌ Error: Data formatting failed. Exiting.")
        sys.exit(1)
    
    # Check if we have a valid GPT prompt
    gpt_prompt = processed_data.get('gpt_prompt', '')
    if not gpt_prompt or gpt_prompt == "No data available for analysis.":
        print("  ❌ Error: No valid data available for GPT analysis. Exiting.")
        sys.exit(1)

    # 3. Analyze with GPT
    if skip_gpt:
        print("\n🧠 Skipping GPT analysis as requested.")
        # Create a dummy analysis result for testing
        if dev_mode:
            print("  ℹ️ Creating dummy analysis result for development")
            analysis_result = {
                'analysis': [
                    {
                        'coin_symbol': 'BTC',
                        'breakout_score': 8.5,
                        'reason': 'Dummy development analysis for Bitcoin',
                        'timestamp': datetime.now().isoformat()
                    },
                    {
                        'coin_symbol': 'ETH',
                        'breakout_score': 7.8,
                        'reason': 'Dummy development analysis for Ethereum',
                        'timestamp': datetime.now().isoformat()
                    }
                ],
                'timestamp': datetime.now().isoformat()
            }
            print(f"  ✓ Dummy analysis created")
        else:
            print("  ❌ Error: Skipping GPT but not in development mode. Exiting.")
            sys.exit(1)
    else:
        print("\n🧠 Analyzing data with GPT...")
        analyzer = GPTAnalyzer()
        analysis_result = analyzer.analyze(gpt_prompt)
        
        # Check if analysis was successful
        if 'error' in analysis_result:
            print(f"  ❌ Analysis error: {analysis_result['error']}. Exiting.")
            sys.exit(1)
        
        if not analysis_result.get('analysis'):
            print("  ❌ Error: GPT analysis returned no results. Exiting.")
            sys.exit(1)
        
        print(f"  ✓ GPT analysis completed successfully")
    
    # 4. Export results
    print("\n📊 Exporting results...")
    
    # Sort the analysis results by breakout_score in descending order
    if analysis_result and 'analysis' in analysis_result and isinstance(analysis_result['analysis'], list):
        analysis_result['analysis'] = sorted(
            analysis_result['analysis'], 
            key=lambda x: x.get('breakout_score', 0), 
            reverse=True
        )
    
    # Save to Excel
    exporter = ExcelExporter()
    excel_saved = exporter.save_analysis(analysis_result, processed_data)
    
    if not excel_saved:
        print("  ⚠️ Warning: Failed to save Excel file.")
    else:
        print("  ✓ Results exported to Excel")
    
    # Send to Telegram
    telegram = TelegramSender()
    if telegram.enabled:
        print("  - Sending top results to Telegram...")
        telegram_sent = telegram.send_analysis(analysis_result, max_coins=int(os.getenv('MAX_COINS', 10)))
        if telegram_sent:
            print("  ✓ Telegram alert sent successfully")
        else:
            print("  ⚠️ Failed to send Telegram alert")
    
    # Execution summary
    execution_time = time.time() - start_time
    print(f"\n✅ Analysis completed in {execution_time:.2f} seconds")
    
if __name__ == "__main__":
    main() 