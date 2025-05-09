# CryptoTrendy - AI-Powered Crypto Breakout Analysis

CryptoTrendy is a Python-based pipeline designed to identify cryptocurrencies with potential breakout opportunities. It aggregates data from various sources, leverages AI for analysis, and delivers insights through Excel reports and Telegram alerts.

## Key Features

*   **Multi-Source Data Aggregation:**
    *   **CoinGecko:** Fetches trending coins, market capitalization, price changes (24h, 7d), and trading volume.
    *   **Reddit (PRAW):** Collects posts from relevant subreddits to gauge social mentions for specific coins.
    *   **(Optional) KuCoin:** Fetches historical OHLC data to calculate technical indicators like RSI (1-day, 1-week).
*   **AI-Driven Analysis:**
    *   Uses **GPT-4o Mini** (via OpenAI API) to analyze the combined data (market stats, social mentions, optional TA).
    *   Assigns a "breakout potential" score (0-10) with reasoning for each analyzed coin.
    *   Ensures analysis is provided for *all* coins included in the input data.
*   **Configurable Analysis:**
    *   Control the number of top coins to analyze (`MAX_COINS_TO_ANALYZE`).
    *   Enable/disable KuCoin Technical Analysis (`ENABLE_KUCOIN_TA`).
    *   Optionally skip the GPT analysis step (`SKIP_GPT`).
    *   Existing Assets Alerts (`CURRENT_ASSET_SHEET_ID`): Pulls a 'Symbols' list from a Google Sheet, detects overbought assets (1-day & 1-week RSI > 70), and sends Telegram alerts.
*   **Structured Outputs:**
    *   **Excel Reports:** Generates timestamped sheets in `cryptos.xlsx` containing:
        *   Detailed analysis results (scores, reasons, market data, social mentions, RSI if enabled).
        *   Raw data collected from all sources for transparency and debugging.
    *   **Telegram Alerts:** Sends notifications for the top N analyzed coins to a specified chat.
*   **Automation:**
    *   Includes a **GitHub Actions** workflow (`.github/workflows/daily_run.yml`) for automated daily execution, results generation, and committing back to the repository.

## Quick Start

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/asadkhalid-softdev/cryptotrendy.git
    cd cryptotrendy
    ```

2.  **Set up environment and install dependencies:** (Using `uv` is recommended)
    ```bash
    # Install uv if needed: pip install uv
    uv venv
    source .venv/bin/activate # Linux/macOS or .\.venv\Scripts\activate for Windows PowerShell
    uv pip install -r requirements.txt
    ```

3.  **Configure:**
    *   Copy `.env.example` to `.env`.
    *   Fill in your API keys (`OPENAI_API_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, optional `REDDIT_*`, optional `KUCOIN_*`) and adjust settings as needed in the `.env` file.
    *   (Optional) Set `CURRENT_ASSET_SHEET_ID` to enable custom assets overbought alerts from a Google Sheet.

4.  **Run:**
    ```bash
    python run.py
    ```
    This executes the main breakout analysis and, if `CURRENT_ASSET_SHEET_ID` is configured, also runs the existing assets overbought alerts via Google Sheets.

5.  **Check Outputs:**
    *   `cryptos.xlsx` file in the root directory.
    *   Telegram messages in your configured chat.

## Detailed Documentation

For comprehensive setup instructions, configuration details, and information on the automated workflow, please refer to the **[User Manual](docs/user_manual.md)**.

To track the latest implemented features and development progress, see **[Current Progress](docs/current_progress.md)**.

## Contributing

Contributions, issues, and feature requests are welcome. Please feel free to open an issue or submit a pull request. 