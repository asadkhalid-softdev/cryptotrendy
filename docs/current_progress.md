# Current Progress - CryptoTrendy

**Status:** Core components implemented, including optional technical analysis (RSI) via KuCoin. Recent bug fixes applied.

## Implemented Features:

1.  **Data Collection:**
    *   Fetching trending coins, market data (market cap, price %, volume) from **CoinGecko API**.
    *   **(Optional)** Fetching OHLC data from **KuCoin API** for selected coins.
    *   Fetching posts from Reddit via **PRAW** (`SocialMediaCollector`).

2.  **Technical Analysis (Optional):**
    *   Calculation of **RSI (14-period)** on **1-day** and **1-week** timeframes using KuCoin data.
    *   Feature is controlled by the `ENABLE_KUCOIN_TA` environment variable.

3.  **Social Mentions:**
    *   Extraction of coin symbol mentions from collected Reddit post titles.

4.  **Data Preprocessing/Formatting:**
    *   Data from various sources (CoinGecko, Social Mentions, KuCoin TA) is merged per coin.
    *   Data is cleaned (handling missing values) and formatted into a structure suitable for the AI model.
    *   Limits the number of coins sent for analysis based on `MAX_COINS_TO_ANALYZE`.
    *   **Fixed:** Correctly handles the nested structure returned by `SocialMediaCollector` when passing data to the formatter.

5.  **AI Analysis (GPT):**
    *   Utilizes **GPT-4o Mini** via API key.
    *   Analyzes provided coin data (market info, social mentions, **and RSI if enabled**).
    *   Ranks coins based on breakout potential (score 0-10) with reasoning.
    *   **Updated:** Prompt explicitly instructs the AI to provide an analysis for **all** coins included in the input data.
    *   Outputs results in a structured JSON format.

6.  **Output Layer:**
    *   Saves analysis results (including price, market data, social mentions, **RSI if enabled**, score, reason) to a timestamped sheet in `cryptos.xlsx`.
    *   Saves raw collected data (CoinGecko, Social, KuCoin, Formatted) to a separate timestamped sheet in `cryptos.xlsx`.
    *   Sends daily alerts for the top N coins via a **Telegram Bot**.
    *   **Fixed:** Correctly converts `max_coins` setting to an integer in `TelegramSender` to prevent slicing errors.

7.  **Automation:**
    *   A **GitHub Actions** workflow (`.github/workflows/daily_run.yml`) is configured for daily automated runs and commits results back to the repo. Workflow environment variables aligned with `.env.example`.

## Next Steps / Potential Improvements:

*   Refinement of GPT prompts for potentially better analysis quality and consistency.
*   Enhance social media analysis (e.g., sentiment analysis on post content/comments, Twitter integration).
*   Adding more technical indicators (e.g., MACD, Moving Averages) to the KuCoin collector.
*   More sophisticated error handling and rate limiting for API calls.
*   Adding unit and integration tests.
*   Improving configuration management (e.g., using a dedicated config file instead of only `.env`). 