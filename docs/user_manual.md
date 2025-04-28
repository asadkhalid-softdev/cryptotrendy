# User Manual - CryptoTrendy

This guide explains how to set up and run the CryptoTrendy project locally or utilize the automated workflow.

## Goal

Automatically fetch crypto data, analyze it using GPT-4o Mini, rank coins by breakout potential, and output daily signals to an Excel file and Telegram.

## Running Locally

### Prerequisites

1.  **Python:** Ensure you have Python 3.x installed.
2.  **Git:** Required for cloning the repository.
3.  **API Keys:**
    *   OpenAI API Key (for GPT-4o Mini)
    *   Telegram Bot Token & Chat ID (if using Telegram alerts)
4.  **(Optional) UV:** A fast Python package installer and virtual environment manager (recommended).

### Setup Steps

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/asadkhalid-softdev/cryptotrendy.git # Replace with your repo URL
    cd cryptotrendy
    ```

2.  **Set up Virtual Environment (Recommended):**
    *   **Using UV:**
        ```bash
        uv venv # Creates .venv
        source .venv/bin/activate # Linux/macOS
        .venv\Scripts\activate # Windows
        ```
    *   **Using venv (standard Python):**
        ```bash
        python -m venv .venv
        source .venv/bin/activate # Linux/macOS
        .venv\Scripts\activate # Windows
        ```

3.  **Install Dependencies:**
    *   **Using UV:**
        ```bash
        uv pip install -r requirements.txt
        ```
    *   **Using pip:**
        ```bash
        pip install -r requirements.txt
        ```

4.  **Configure API Keys:**
    *   Create a `.env` file in the root directory of the project.
    *   Add your API keys and other configuration details to this file. Refer to `.env.example` (if available) or the script configurations for the required variable names (e.g., `OPENAI_API_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`).
    *   **Example `.env` content:**
        ```env
        OPENAI_API_KEY=your_openai_key_here
        TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
        TELEGRAM_CHAT_ID=your_telegram_chat_id_here
        ```

### Running the Analysis

1.  **Activate the virtual environment** (if not already active):
    ```bash
    source .venv/bin/activate # Linux/macOS
    .venv\Scripts\activate # Windows
    ```

2.  **Execute the main script:** (Assuming the main script is `main.py` - adjust if needed)
    ```bash
    python main.py
    ```

3.  **Check Outputs:**
    *   Look for the updated `cryptos.xlsx` file in the project directory.
    *   Check your configured Telegram chat for alerts (if enabled).

## Using GitHub Actions (Automated Workflow)

1.  **Fork/Clone the Repository:** Ensure the repository is in your GitHub account.
2.  **Configure Secrets:**
    *   Go to your repository's `Settings` > `Secrets and variables` > `Actions`.
    *   Add the required API keys (`OPENAI_API_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`) as repository secrets. The names must match those expected by the workflow file (usually found in `.github/workflows/`).
3.  **Enable Actions:** Ensure GitHub Actions are enabled for your repository (`Settings` > `Actions` > `General`).
4.  **Triggering the Workflow:**
    *   The workflow is typically configured to run on a schedule (e.g., daily).
    *   You might also be able to trigger it manually from the `Actions` tab in your GitHub repository.
5.  **Check Results:** The workflow should commit the updated `cryptos.xlsx` back to the repository, and send Telegram alerts as configured. 