
# 🧠 AI-Powered Crypto Signal Engine - System Architecture

## 🎯 Goal
Automatically fetch crypto data, analyze it using GPT (free tier), rank coins, and output daily signals to Google Sheets or Telegram — all for **$0 cost**.

---

## 🔄 High-Level Flow

```
1. Data Collectors ─┐
                    │
2. Data Formatter ──┼─> 3. GPT Processing ──> 4. Output Formatter ──┐
                    │                                              │
   (APIs, Scrapers) ┘                                              │
                                                                   ├─> Locally stored cryptos.xlsx
                                                                   ├─> Telegram Alerts
```

---

## 🧩 System Components

### 1. 📥 Data Collection Layer (Python Scripts)

- **CoinGecko API**
  - Trending coins
  - Market cap, price %, volume, etc.

- **LunarCrush API (Free Tier)**
  - Sentiment scores
  - Galaxy score
  - Social engagement

- **Reddit/Twitter Scraper (optional but powerful)**
  - Use `snscrape` or `Twint` for Twitter
  - Use `PRAW` for Reddit top posts/comments

✅ Outputs: structured JSON with all data merged per coin.

---

### 2. 🧹 Data Preprocessing / Formatter

- Normalize scores: scale sentiment/volume between 0–1
- Format Reddit/Twitter comments into bullet points or top phrases
- Merge everything into a GPT-ready prompt template

✅ Output: clean input string or dictionary to send to GPT.

---

### 3. 🧠 GPT Analysis Layer

- Use **GPT-4o Mini (almost free via API key)**

**Prompt Example:**
```
You're a crypto analyst. Based on the data below, rank coins by breakout potential. Justify each score.

[COIN DATA HERE - sentiment, market info, social buzz]

Output JSON with:
- coin name
- score (0-10)
- reason
```

✅ Output: JSON or list of coins with score + rationale.

---

### 4. 📊 Output Layer

Route output to one or more of the following:

- **Locally stored XLSX**
  - history
- **Telegram Bot (Python)**
  - Daily top 3 alerts

---

### 5. 🔁 Scheduler / Automation

- Use **Github actions**

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
