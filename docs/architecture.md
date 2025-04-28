# 🧠 AI-Powered Crypto Signal Engine - System Architecture

## 🎯 Goal
Automatically fetch crypto data (market, social, **technical**), analyze it using GPT, rank coins, and output daily signals to Excel and Telegram.

---

## 🔄 High-Level Flow

```mermaid
graph LR
    A[Data Collectors] --> B(Data Formatter);
    subgraph Data Collectors
        C[CoinGecko API<br/>Market Data, Trending]
        D[KuCoin API<br/>OHLC Data (Optional)]
        E[Social APIs/Scrapers<br/>Mentions, Sentiment (Optional)]
    end
    B --> F{GPT Analysis<br/>(GPT-4o Mini)};
    F --> G[Output Layer];
    subgraph Output Layer
        H[Excel Exporter<br/>(cryptos.xlsx)]
        I[Telegram Sender]
    end

    %% Data Flow Details
    C --> A;
    D --> A;
    E --> A;
    A -- Formatted Coin Data<br/>(incl. Market, Social, RSI) --> F;
    F -- Analysis Results<br/>(Score, Reason) --> G;
    G --> H;
    G --> I;

```

---

## 🧩 System Components

### 1. 📥 Data Collection Layer (`app/collectors/`)

-   **`CoinGeckoCollector`**:
    -   Fetches trending coins list.
    -   Fetches market data for top N coins (price, market cap, volume, % change).
    -   *Input:* None (or config limits)
    -   *Output:* Dictionary containing `trending_coins` list and `market_data` list.

-   **`KuCoinCollector` (Optional, controlled by `ENABLE_KUCOIN_TA`)**:
    -   Fetches OHLC (k-line) data for specified coin symbols (e.g., BTC-USDT).
    -   Calculates Technical Indicators (currently **RSI 1d, 7d**) using `pandas-ta`.
    -   *Input:* List of coin symbols (from CoinGecko data).
    *   *Output:* Dictionary mapping symbol to `{rsi_1d: value, rsi_7d: value}`.

-   **`SocialMediaCollector` (Placeholder)**:
    -   *(Intended)* To fetch mentions, sentiment from Reddit, Twitter, etc.
    -   *Input:* List of coin symbols.
    -   *Output:* Dictionary mapping symbol to social metrics.

✅ Outputs: Separate dictionaries/lists from each active collector.

---

### 2. 🧹 Data Formatting Layer (`app/formatters/`)

-   **`DataFormatter`**:
    -   Merges data from all collectors based on coin symbol.
    -   Handles missing data (e.g., if KuCoin doesn't list a coin, or TA is disabled).
    -   Cleans data for AI (e.g., converts `None` to 'N/A').
    -   Selects and formats relevant fields (market data, social metrics, **RSI values**) into a list of dictionaries.
    -   Filters/limits the list of coins to analyze based on `MAX_COINS_TO_ANALYZE`.

✅ Output: List of dictionaries, each representing a coin with all relevant data points ready for the AI prompt.

---

### 3. 🧠 GPT Analysis Layer (`app/analysis/`)

-   **`GPTAnalyzer`**:
    -   Constructs a detailed prompt for the AI model (`gpt-4o-mini`).
        -   System Message: Explains the role, task, scoring, output format, and how to interpret data fields (**including RSI if enabled**).
        -   User Message: Contains the formatted data for the selected coins.
    -   Handles interaction with the OpenAI API.
    -   Manages token limits and basic error handling.
    -   Parses the JSON response from the AI.

✅ Output: Dictionary containing metadata (timestamp, model used) and the `analysis` list (coins with `coin_symbol`, `breakout_score`, `reason`).

---

### 4. 📊 Output Layer (`app/output/`)

-   **`ExcelExporter`**:
    -   Takes the analysis results and the raw collected/formatted data bundle.
    -   Merges analysis scores/reasons with the formatted input data (including **RSI**) for a comprehensive 'Analysis' sheet.
    -   Saves the raw data bundle (serialized) to a 'RawData' sheet.
    -   Writes to `cryptos.xlsx` with timestamped sheet names.

-   **`TelegramSender`**:
    -   Formats the top N analysis results into a concise message.
    -   Sends the message via the configured Telegram bot.

✅ Outputs: Updated `cryptos.xlsx` file and Telegram notification.

---

###  orchestration (`run.py`)

-   Main script that initializes and calls components in sequence.
-   Loads environment variables (`dotenv`).
-   Handles conditional logic (e.g., `SKIP_GPT`, `ENABLE_KUCOIN_TA`).
-   Passes data between components.

---

## 💻 Minimal Tech Stack (Free & Lean)

| Component       | Tool                  | Notes                            |
|----------------|-----------------------|----------------------------------|
| Data Collection| Python + APIs         | CoinGecko, LunarCrush, scrapers |
| AI Processing  | GPT-4o Mini API       | 10M tokens/mo free               |
| Output         | cryptos.xlsx          |                                  |
| Alerts         | Telegram bot          | `python-telegram-bot`            |
| Scheduler      | Github Actions        | Daily runs                       |

---
