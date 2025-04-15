# 🚀 CryptoTrendy - AI-Powered Crypto Signal Engine

An automated system that collects cryptocurrency data from various sources, analyzes it using GPT, and provides daily breakout potential signals at zero cost.

## 🎯 Overview

CryptoTrendy fetches data from:
- CoinGecko API (market data, trending coins)
- Social media (Reddit posts and mentions)

It then processes this data, formats it for GPT analysis, and outputs the results to:
- Local Excel file (`cryptos.xlsx`)
- Telegram alerts (optional)

## 🔧 Setup

1. Create a virtual environment (Python 3.10+ recommended):
   ```
   uv venv --python 3.10
   ```

2. Install dependencies:
   ```
   .venv\Scripts\activate
   uv pip install -r requirements.txt
   ```

3. Create a `.env` file with your API keys (see `.env.example`):
   ```
   OPENAI_API_KEY=your_openai_api_key
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token
   TELEGRAM_CHAT_ID=your_chat_id
   REDDIT_CLIENT_ID=your_reddit_client_id
   REDDIT_CLIENT_SECRET=your_reddit_client_secret
   TOP_COINS_LIMIT=100
   TRENDING_COINS_LIMIT=20
   DEVELOPMENT_MODE=false
   SKIP_GPT=false
   ```

## 🏃‍♂️ Usage

Run the analysis:
```
python run.py
```

The results will be saved to `cryptos.xlsx` in the project root directory and sent to your Telegram chat if configured.

## 🧩 System Components

### 1. Data Collection Layer
- `app/collectors/coingecko_collector.py`: Fetches market data and trending coins
- `app/collectors/social_collector.py`: Collects Reddit posts and mentions

### 2. Data Formatting Layer
- `app/formatters/data_formatter.py`: Normalizes data and prepares it for GPT analysis

### 3. Analysis Layer
- `app/analysis/gpt_analyzer.py`: Processes data with OpenAI GPT models and extracts insights

### 4. Output Layer
- `app/output/excel_exporter.py`: Saves results to Excel
- `app/output/telegram_sender.py`: Sends alerts to Telegram

## 📅 Automation

The project includes a GitHub Actions workflow that runs the analysis daily at 01:00 UTC. You can also trigger the workflow manually via the GitHub interface, or set up a local scheduler.

## 🛠️ Configuration Options

- `TOP_COINS_LIMIT`: Number of top coins to analyze (default: 100)
- `TRENDING_COINS_LIMIT`: Number of trending coins to include (default: 20)
- `DEVELOPMENT_MODE`: Enable development mode for testing (default: false)
- `SKIP_GPT`: Skip GPT analysis when testing (default: false)

## 🔄 Disclaimer

This tool is for informational purposes only and should not be considered financial advice. Always do your own research before making investment decisions. 