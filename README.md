# CryptoTrendy 🚀

## 🎯 Goal
Automatically fetch crypto data, analyze it using GPT-4o Mini (considering market data, social buzz, and **optional technical indicators like RSI**), rank coins by breakout potential, and output daily signals to an Excel file (`cryptos.xlsx`) and Telegram — all designed to run efficiently, potentially at **$0 cost** using free tiers and optimized API usage.

---

## ✨ Features
- **Data Collection:**
    - Fetches trending coins and market data from CoinGecko.
    - *(Optional)* Fetches OHLC data from KuCoin to calculate technical indicators (RSI 1d, 7d). Controlled via `ENABLE_KUCOIN_TA` flag.
    - *(Optional: Placeholder)* Scrapes Reddit/Twitter for social buzz.
- **AI Analysis:** Uses GPT-4o Mini to analyze coin data (market info, social buzz, **RSI**) and rank them by breakout potential (0-10 score with justification).
- **Output:** Saves results (including RSI if enabled) to `cryptos.xlsx` and sends top alerts via Telegram.
- **Automation:** Daily runs via GitHub Actions.
- **Cost-Effective:** Leverages free API tiers (CoinGecko, GPT-4o Mini free tier) and efficient processing.

---

## 🛠️ Tech Stack
| Component       | Tool                  | Notes                            |
|----------------|-----------------------|----------------------------------|
| Data Collection| Python + APIs         | CoinGecko, **KuCoin (Optional)**, *(Optional: scrapers)* |
| TA Calculation | `pandas-ta`           | Used if KuCoin TA is enabled     |
| AI Processing  | GPT-4o Mini API       | OpenAI API Key needed            |
| Output         | `cryptos.xlsx`        | `openpyxl` library               |
| Alerts         | Telegram Bot          | `python-telegram-bot`            |
| Environment    | Python 3.x, UV (recommended) | `python-dotenv` for keys     |
| Dependencies   | `requests`, `pandas`, `openai`, `kucoin-python`, `pandas-ta`, etc. | See `requirements.txt` |
| Scheduler      | GitHub Actions        | Daily runs                       |

---

## 🚀 Getting Started

### Prerequisites
- Python 3.x (check `.github/workflows/daily_run.yml` for version used in Actions)
- Git
- OpenAI API Key
- Telegram Bot Token & Chat ID (for alerts)
- **(Optional)** KuCoin API Key, Secret, and Passphrase (only needed if `ENABLE_KUCOIN_TA=true`)

### Local Setup & Run
1.  **Clone:**
    ```bash
    git clone https://github.com/asadkhalid-softdev/cryptotrendy.git
    cd cryptotrendy
    ```
2.  **Environment Setup (UV Recommended):**
    ```bash
    # Install uv if you haven't already
    # pip install uv

    # Create and activate virtual environment
    uv venv
    source .venv/bin/activate  # Linux/macOS
    # .\.venv\Scripts\activate # Windows PowerShell
    # .venv\Scripts\activate.bat # Windows CMD

    # Install dependencies
    uv pip install -r requirements.txt
    ```
3.  **Configure API Keys & Settings:**
    *   Create a `.env` file in the root directory (copy from `.env.example`).
    *   Add your API keys: `OPENAI_API_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`.
    *   **(Optional)** If using the KuCoin TA feature, add `KUCOIN_API_KEY`, `KUCOIN_API_SECRET`, `KUCOIN_API_PASSPHRASE`.
    *   Set `ENABLE_KUCOIN_TA=true` or `false`.
    *   Adjust other settings like `MAX_COINS_TO_ANALYZE` if needed.
    *   **Example `.env`:**
        ```env
        OPENAI_API_KEY=your_openai_key_here
        TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
        TELEGRAM_CHAT_ID=your_telegram_chat_id_here

        # Optional KuCoin Keys (only needed if ENABLE_KUCOIN_TA=true)
        # KUCOIN_API_KEY=your_kucoin_key
        # KUCOIN_API_SECRET=your_kucoin_secret
        # KUCOIN_API_PASSPHRASE=your_kucoin_passphrase

        # Feature Flags & Settings
        ENABLE_KUCOIN_TA=false
        MAX_COINS_TO_ANALYZE=10
        # ... other settings ...
        ```
4.  **Run the Analysis:**
    ```bash
    python run.py
    ```
5.  **Check Outputs:**
    *   `cryptos.xlsx` file in the project root.
    *   Telegram messages in your configured chat.

---

## ⚙️ Configuration (.env)

*   `OPENAI_API_KEY`: Your OpenAI API key.
*   `TELEGRAM_BOT_TOKEN`: Your Telegram bot token.
*   `TELEGRAM_CHAT_ID`: The chat ID where the bot should send messages.
*   `ENABLE_KUCOIN_TA`: Set to `true` to enable fetching OHLC data from KuCoin and calculating RSI. Defaults to `false`.
*   `KUCOIN_API_KEY`, `KUCOIN_API_SECRET`, `KUCOIN_API_PASSPHRASE`: Required only if `ENABLE_KUCOIN_TA=true`. Public market data fetching might work without keys, but using keys is recommended practice for potential future private endpoint usage.
*   `MAX_COINS_TO_ANALYZE`: Limits the number of coins sent to GPT for analysis (helps manage cost/tokens). Default: 10.
*   `SKIP_GPT`: Set to `true` to skip the actual GPT analysis step (useful for testing data collection/formatting). Default: `false`.
*   `DEVELOPMENT_MODE`: Set to `true` for potential development-specific logic (currently unused). Default: `false`.
*   *(Other collector-specific limits like `TOP_COINS_LIMIT` might exist)*

---

## 🤖 Automation (GitHub Actions)

*   The workflow in `.github/workflows/daily_run.yml` runs the analysis daily.
*   **Secrets:** You need to configure `OPENAI_API_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, and optionally `KUCOIN_API_KEY`, `KUCOIN_API_SECRET`, `KUCOIN_API_PASSPHRASE` as GitHub repository secrets for the action to work.
*   The action checks out the code, installs dependencies, runs `run.py` with environment variables populated from secrets, and commits the updated `cryptos.xlsx` back to the repository.

---

## 🤝 Contributing
Contributions, issues, and feature requests are welcome!

---

## 📄 License
[Specify your license, e.g., MIT] 