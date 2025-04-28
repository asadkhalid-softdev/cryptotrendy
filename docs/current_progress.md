# Current Progress - CryptoTrendy

**Status:** Core components implemented, including optional technical analysis integration.

## Implemented Features:

1.  **Data Collection:**
    *   Fetching trending coins, market data (market cap, price %, volume) from **CoinGecko API**.
    *   **(New/Optional)** Fetching OHLC data from **KuCoin API** for selected coins.
    *   *(Placeholder)* Social media data collection structure exists but needs specific implementation/APIs.

2.  **Technical Analysis (Optional):**
    *   **(New)** Calculation of **RSI (14-period)** on **1-day** and **1-week** timeframes using KuCoin data.
    *   Feature is controlled by the `ENABLE_KUCOIN_TA` environment variable.

3.  **Data Preprocessing/Formatting:**
    *   Data from various sources (CoinGecko, Social, KuCoin TA) is merged per coin.
    *   Data is cleaned (handling missing values) and formatted into a structure suitable for the AI model.
    *   Limits the number of coins sent for analysis based on `MAX_COINS_TO_ANALYZE`.

4.  **AI Analysis (GPT):**
    *   Utilizes **GPT-4o Mini** via API key.
    *   Analyzes provided coin data (market info, social buzz, **and RSI if enabled**).
    *   Ranks coins based on breakout potential (score 0-10) with reasoning.
    *   Outputs results in a structured JSON format.

5.  **Output Layer:**
    *   Saves analysis results (including price, market data, **RSI if enabled**, score, reason) to a timestamped sheet in `cryptos.xlsx`.
    *   Saves raw collected data (CoinGecko, Social, KuCoin, Formatted) to a separate timestamped sheet in `cryptos.xlsx`.
    *   Sends daily alerts for the top coins via a **Telegram Bot**.

6.  **Automation:**
    *   A **GitHub Actions** workflow (`.github/workflows/daily_run.yml`) is configured for daily automated runs and commits results back to the repo.

## Next Steps / Potential Improvements:

*   Refinement of GPT prompts for potentially better analysis, especially incorporating RSI interpretation.
*   Implementation of actual social media data collection (Reddit/Twitter).
*   Adding more technical indicators (e.g., MACD, Moving Averages) to the KuCoin collector.
*   More sophisticated error handling and rate limiting for API calls.
*   Adding unit and integration tests.
*   Improving configuration management (e.g., using a dedicated config file). 