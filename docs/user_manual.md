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

4.  **Configure API Keys and Settings:**
    *   Create a `.env` file in the root directory of the project (you can copy `.env.example` and rename it).
    *   Add your API keys and other configuration details to this file.
    *   **Required:**
        *   `OPENAI_API_KEY`: Your key from OpenAI.
        *   `TELEGRAM_BOT_TOKEN`: Token for your Telegram bot.
        *   `TELEGRAM_CHAT_ID`: Chat ID for Telegram notifications.
    *   **Optional (for KuCoin TA Feature):**
        *   `ENABLE_KUCOIN_TA`: Set to `true` to activate RSI calculation using KuCoin data. Defaults to `false`.
        *   `KUCOIN_API_KEY`, `KUCOIN_API_SECRET`, `KUCOIN_API_PASSPHRASE`: Your KuCoin API credentials. **Needed only if `ENABLE_KUCOIN_TA` is set to `true`.**
    *   **Other Settings:**
        *   `MAX_COINS_TO_ANALYZE`: Controls how many top coins (by market cap rank) are sent to GPT.
        *   `SKIP_GPT`: Set to `true` to bypass the GPT analysis call.
    *   **Example `.env` content:**
        ```env
        # Required
        OPENAI_API_KEY=your_openai_key_here
        TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
        TELEGRAM_CHAT_ID=your_telegram_chat_id_here

        # Optional KuCoin TA Feature
        ENABLE_KUCOIN_TA=false # Set to true to enable
        # KUCOIN_API_KEY=your_kucoin_key_if_enabled
        # KUCOIN_API_SECRET=your_kucoin_secret_if_enabled
        # KUCOIN_API_PASSPHRASE=your_kucoin_passphrase_if_enabled

        # Other Settings
        MAX_COINS_TO_ANALYZE=10
        SKIP_GPT=false
        DEVELOPMENT_MODE=false
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
    *   The script will print progress messages to the console.

3.  **Check Outputs:**
    *   Look for the updated `cryptos.xlsx` file in the project directory. It will contain sheets like `Analysis_YYYYMMDD_HHMMSS` and `RawData_YYYYMMDD_HHMMSS`. If KuCoin TA is enabled, the 'Analysis' sheet will include `rsi_1d` and `rsi_7d` columns.
    *   Check your configured Telegram chat for alerts summarizing the top coins.

## Using GitHub Actions (Automated Workflow)

1.  **Fork/Clone the Repository:** Ensure the repository is in your GitHub account.
2.  **Configure Secrets:**
    *   Go to your repository's `Settings` > `Secrets and variables` > `Actions`.
    *   Add the required API keys as repository secrets. The names must match those expected by the workflow file (`.github/workflows/daily_run.yml`) and your `.env` file:
        *   `OPENAI_API_KEY`
        *   `TELEGRAM_BOT_TOKEN`
        *   `TELEGRAM_CHAT_ID`
        *   **(Optional)** `KUCOIN_API_KEY`, `KUCOIN_API_SECRET`, `KUCOIN_API_PASSPHRASE` (only needed if you intend the action to run with `ENABLE_KUCOIN_TA=true` - you might need to modify the workflow file to set this env var based on a secret or input). *Note: The current workflow file sets `ENABLE_KUCOIN_TA=false` directly.*
    *   Ensure the secrets contain the correct values.
3.  **Enable Actions:** Ensure GitHub Actions are enabled for your repository (`Settings` > `Actions` > `General`).
4.  **Triggering the Workflow:**
    *   The workflow is configured to run on a schedule (e.g., daily at 07:00 UTC).
    *   You can also trigger it manually from the `Actions` tab in your GitHub repository (select the "Daily Crypto Signal Analysis" workflow and click "Run workflow").
5.  **Check Results:** The workflow should commit the updated `cryptos.xlsx` back to the repository and send Telegram alerts as configured. Check the Actions logs for details if issues occur. 