# CryptoTrendy - User Manual

This document provides instructions on how to set up and run the CryptoTrendy analysis pipeline locally and understand its configuration.

## Local Setup

### Prerequisites

*   Python 3.x (Refer to `.github/workflows/daily_run.yml` for the version used in CI/CD, e.g., 3.10)
*   Git
*   `uv` (Recommended for environment management) or `pip` with `venv`.
*   Required API Keys (see Configuration section below).

### Installation Steps

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/asadkhalid-softdev/cryptotrendy.git
    cd cryptotrendy
    ```

2.  **Set Up Python Environment (Using UV):**
    ```bash
    # Install uv if needed: pip install uv
    uv venv # Create virtual environment in .venv
    source .venv/bin/activate # Linux/macOS
    # .\.venv\Scripts\activate # Windows PowerShell
    ```
    *(Alternatively, use `python -m venv .venv` and activate)*

3.  **Install Dependencies:**
    ```bash
    uv pip install -r requirements.txt
    # Or: pip install -r requirements.txt
    ```
    *(This installs all necessary packages including `requests`, `pycoingecko`, `praw`, `openai`, `kucoin-python`, `pandas-ta`, `python-telegram-bot`, `python-dotenv`, `pandas`, `openpyxl` etc.)*

4.  **Configure API Keys and Settings:**
    *   Create a `.env` file in the root directory of the project (you can copy `.env.example` and rename it).
    *   Add your API keys and other configuration details to this file.
    *   **Required:**
        *   `OPENAI_API_KEY`: Your key from OpenAI.
        *   `TELEGRAM_BOT_TOKEN`: Token for your Telegram bot.
        *   `TELEGRAM_CHAT_ID`: Chat ID for Telegram notifications.
    *   **Optional (Reddit):**
        *   `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`: Your Reddit API credentials (needed for `SocialMediaCollector`).
    *   **Optional (KuCoin TA Feature):**
        *   `ENABLE_KUCOIN_TA`: Set to `true` to activate RSI calculation using KuCoin data. Defaults to `false`.
        *   `KUCOIN_API_KEY`, `KUCOIN_API_SECRET`, `KUCOIN_API_PASSPHRASE`: Your KuCoin API credentials. **Needed only if `ENABLE_KUCOIN_TA` is set to `true`.**
    *   **Other Settings:**
        *   `MAX_COINS_TO_ANALYZE`: Controls how many top coins (by market cap rank from CoinGecko) are sent to GPT.
        *   `MAX_COINS_TELEGRAM`: (Optional) Controls how many top coins from the analysis are sent via Telegram message (defaults to 3 if not set). Ensure this is an integer.
        *   `SKIP_GPT`: Set to `true` to bypass the GPT analysis call.
        *   `TOP_COINS_LIMIT`: Max coins to fetch from CoinGecko market data.
        *   `CURRENT_ASSET_SHEET_ID`: (Optional) Google Sheet ID to fetch a 'Symbols' list for existing assets RSI alerts.
        *   `TRENDING_COINS_LIMIT`: Max trending coins to fetch from CoinGecko.
    *   **Example `.env` content:**
        ```env
        # Required
        OPENAI_API_KEY=your_openai_key_here
        TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
        TELEGRAM_CHAT_ID=your_telegram_chat_id_here

        # Reddit
        REDDIT_CLIENT_ID=your_reddit_client_id
        REDDIT_CLIENT_SECRET=your_reddit_client_secret

        # Optional KuCoin TA Feature
        ENABLE_KUCOIN_TA=false # Set to true to enable
        KUCOIN_API_KEY=your_kucoin_key_if_enabled
        KUCOIN_API_SECRET=your_kucoin_secret_if_enabled
        KUCOIN_API_PASSPHRASE=your_kucoin_passphrase_if_enabled

        # Other Settings
        MAX_COINS_TO_ANALYZE=10
        MAX_COINS_TELEGRAM=3 # Optional: Max coins in Telegram message
        SKIP_GPT=false
        DEVELOPMENT_MODE=false
        TOP_COINS_LIMIT=100
        # Existing Assets Alerts
        CURRENT_ASSET_SHEET_ID=your_google_sheet_id_here
        ```

### Running the Analysis

1.  **Activate the virtual environment** (if not already active):
    ```bash
    source .venv/bin/activate # Linux/macOS
    # .\.venv\Scripts\activate # Windows PowerShell
    ```

2.  **Execute the main script:**
    ```bash
    python run.py
    ```
    *   The script will print progress messages to the console, including data collection, formatting, analysis, and output steps.
    *   If `CURRENT_ASSET_SHEET_ID` is configured, the script will also run existing assets RSI alert analysis.

3.  **Check Outputs:**
    *   Look for the updated `cryptos.xlsx` file in the project directory. It will contain sheets like `Analysis_YYYYMMDD_HHMMSS` and `RawData_YYYYMMDD_HHMMSS`.
        *   The 'Analysis' sheet includes the GPT score/reason, market data, social mentions, and (if enabled) `rsi_1d` and `rsi_7d` columns.
        *   The 'RawData' sheet contains the raw JSON data collected from sources and the data formatted for GPT.
    *   Check your configured Telegram chat for alerts summarizing the top coins based on the analysis.

## Using GitHub Actions (Automated Workflow)

1.  **Fork/Clone the Repository:** Ensure the repository is in your GitHub account.
2.  **Configure Secrets:**
    *   Go to your repository's `Settings` > `Secrets and variables` > `Actions`.
    *   Add the required API keys as repository secrets. The names must match those expected by the workflow file (`.github/workflows/daily_run.yml`) and your `.env` file:
        *   `OPENAI_API_KEY`
        *   `TELEGRAM_BOT_TOKEN`
        *   `TELEGRAM_CHAT_ID`
        *   **(Optional)** `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`
        *   **(Optional)** `KUCOIN_API_KEY`, `KUCOIN_API_SECRET`, `KUCOIN_API_PASSPHRASE` (only needed if you intend the action to run with `ENABLE_KUCOIN_TA=true` - you might need to modify the workflow file to set this env var). *Note: The current workflow file sets `ENABLE_KUCOIN_TA=false` directly.*
    *   Ensure the secrets contain the correct values.
3.  **Enable Actions:** Ensure GitHub Actions are enabled for your repository (`Settings` > `Actions` > `General`).
4.  **Triggering the Workflow:**
    *   The workflow is configured to run on a schedule (e.g., daily at 07:00 UTC).
    *   You can also trigger it manually from the `Actions` tab in your GitHub repository (select the "Daily Crypto Signal Analysis" workflow and click "Run workflow").
5.  **Check Results:** The workflow should commit the updated `cryptos.xlsx` back to the repository and send Telegram alerts as configured. Check the Actions logs for details if issues occur. 