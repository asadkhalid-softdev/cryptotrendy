# CryptoTrendy 🚀

## 🎯 Goal
Automatically fetch crypto data, analyze it using GPT-4o Mini, rank coins by breakout potential, and output daily signals to an Excel file (`cryptos.xlsx`) and Telegram — all designed to run efficiently, potentially at **$0 cost** using free tiers and optimized API usage.

---

## ✨ Features
- **Data Collection:** Fetches trending coins and market data from CoinGecko. *(Optional: Scrapes Reddit/Twitter for social buzz)*.
- **AI Analysis:** Uses GPT-4o Mini to analyze coin data (market info, social buzz) and rank them by breakout potential (0-10 score with justification).
- **Output:** Saves results to `cryptos.xlsx` and sends top 3 alerts via Telegram.
- **Automation:** Daily runs via GitHub Actions.
- **Cost-Effective:** Leverages free API tiers (CoinGecko, GPT-4o Mini free tier) and efficient processing.

---

## 🛠️ Tech Stack
| Component       | Tool                  | Notes                            |
|----------------|-----------------------|----------------------------------|
| Data Collection| Python + APIs         | CoinGecko, *(Optional: scrapers)* |
| AI Processing  | GPT-4o Mini API       | OpenAI API Key needed            |
| Output         | `cryptos.xlsx`        | `openpyxl` library               |
| Alerts         | Telegram Bot          | `python-telegram-bot`            |
| Environment    | Python 3.x, UV (recommended) | `python-dotenv` for keys     |
| Scheduler      | GitHub Actions        | Daily runs                       |

---

## 🚀 Getting Started

### Prerequisites
- Python 3.x
- Git
- OpenAI API Key
- Telegram Bot Token & Chat ID (for alerts)

### Local Setup & Run
1.  **Clone:**
    ```bash
    git clone https://github.com/asadkhalid-softdev/cryptotrendy.git
    cd cryptotrendy
    ```
2.  **Environment (UV Recommended):**
    ```bash
    # Install UV if you haven't: https://github.com/astral-sh/uv
    uv venv
    source .venv/bin/activate  # Linux/macOS
    # .venv\Scripts\activate  # Windows
    ```
    *Alternatively, use standard `python -m venv .venv`*
3.  **Install Dependencies:**
    ```bash
    uv pip install -r requirements.txt
    # or: pip install -r requirements.txt
    ```
4.  **Configure API Keys:**
    - Create a `.env` file in the root directory.
    - Add your keys:
      ```env
      OPENAI_API_KEY=your_openai_key
      TELEGRAM_BOT_TOKEN=your_telegram_token
      TELEGRAM_CHAT_ID=your_telegram_chat_id
      ```
5.  **Run:**
    ```bash
    python main.py
    ```
    - Check `cryptos.xlsx` and your Telegram for results.

### GitHub Actions Automation
1.  **Fork** the repository.
2.  Go to `Settings` > `Secrets and variables` > `Actions`.
3.  Add Repository Secrets:
    - `OPENAI_API_KEY`
    - `TELEGRAM_BOT_TOKEN`
    - `TELEGRAM_CHAT_ID`
4.  The workflow in `.github/workflows/` will run automatically (usually daily) or can be triggered manually from the Actions tab. It will commit the updated `cryptos.xlsx` back to the repo.

---

## 🏗️ Architecture Overview
(See `docs/architecture.md` for more details)

1.  **Data Collectors (Python):** Fetch data from CoinGecko.
2.  **Data Formatter:** Clean and prepare data for GPT.
3.  **GPT Processing:** Send data to GPT-4o Mini for analysis and ranking.
4.  **Output Formatter:** Save to Excel and send Telegram alerts.

---

## 🤝 Contributing
Contributions, issues, and feature requests are welcome!

---

## 📄 License
[Specify your license, e.g., MIT] 