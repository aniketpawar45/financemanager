# Finance OS (Finance Manager Telegram Bot)

Finance OS is a feature-rich, automated Telegram Bot designed to act as your personal finance manager. It allows you to seamlessly track, categorize, and analyze your daily expenses directly through Telegram using text or voice messages. It securely syncs all your financial data to a Google Sheet hosted on Google Drive.

## 🌟 Features

* **Smart Text Entry:** Log expenses quickly using natural language (e.g., `Milk 40`). The bot uses intelligent parsing to extract the item name, amount, and custom dates.
* **Voice Logging:** Send a voice note (e.g., "I spent 500 on groceries today"), and the bot will transcribe the audio to text and log the expense.
* **Google Sheets Syncing:** All expenses are saved to an Excel (`.xlsx`) file hosted on Google Drive, ensuring you always have access to your raw data and can edit it manually if needed.
* **Intelligent Auto-Categorization:** Uses fuzzy matching against your historical expenses to automatically assign categories to new purchases, saving you time.
* **Interactive Keyboards:** Features easy-to-use Telegram inline buttons for category selection and an interactive UI for confirming expense deletions.
* **Comprehensive Reporting:** Use the `/report` command to get spending summaries for specific timeframes (e.g., `/report today`, `/report June`, `/report yesterday`).
* **Visual Analytics:** Use `/chart` to instantly generate and receive a doughnut chart visualizing your spending breakdown by category.
* **Nightly Reminders (Nags):** Sends an automated reminder at 10:00 PM IST if you haven't logged any expenses for the day.
* **Security & Authorization:** The bot is restricted to pre-authorized Telegram User IDs, ensuring your personal financial data remains completely private.
* **Background Health Server:** Runs a Waitress/Flask web service to keep the bot alive and provide health checks for deployment platforms.

## 🛠️ Technical Specifications

* **Runtime:** Python 3.14 (Pre-release execution via `run.py`)
* **Architecture:** Asynchronous operations heavily utilizing `asyncio` and `httpx` for non-blocking API calls.
* **Deployment Ready:** Configured for seamless deployment on Render (includes `render.yaml`).
* **Timezone Handling:** Hardcoded to `Asia/Kolkata` (IST) using `pytz` for accurate date parsing and scheduling.

### 📦 Major Python Dependencies

* **`python-telegram-bot[job-queue]`**: Core framework for interfacing with the Telegram API and handling scheduled jobs.
* **`openpyxl`**: For reading, writing, and updating `.xlsx` files in memory.
* **`google-api-python-client` & `google-auth`**: For authentication and secure interaction with Google Drive.
* **`httpx`**: Modern, fast asynchronous HTTP client.
* **`dateparser`**: For intelligently parsing human-readable custom dates.
* **`rapidfuzz`**: For rapid string matching to predict categories based on previous entries.
* **`Flask` & `waitress`**: To serve the application's health check web endpoint.

### 🔌 External APIs Used

1.  **Telegram Bot API:** Handles messaging, inline keyboards, callbacks, and voice file retrieval.
2.  **Google Drive API (v3):** Fetches the Excel database, updates it, and pushes the new version back to the cloud. Requires a Google Cloud Service Account.
3.  **Groq API (`whisper-large-v3` model):** Used for highly accurate audio-to-text transcription for voice expense logging.
4.  **QuickChart.io API:** An open-source chart generation API used to create doughnut charts from JSON payloads.

## ⚙️ Environment Variables

To run the project, configure your deployment environment with the following variables:

| Variable | Description |
| :--- | :--- |
| `BOT_TOKEN` | Your Telegram Bot Token obtained from BotFather. |
| `EXCEL_FILE_ID` | The Google Drive File ID of your expense tracking spreadsheet. |
| `SHEET_NAME` | (Optional) The specific sheet tab name. Defaults to `Daily Expense Log`. |
| `GROQ_API_KEY` | Your Groq API key for voice transcription functionality. |
| `ADMIN_CHAT_ID` | Your personal Telegram Chat ID for receiving the nightly reminders. |
| `AUTHORIZED_USER_IDS`| Comma-separated list of Telegram Chat IDs authorized to use the bot. |
| `PORT` | (Optional) Port for the Flask health check web server. Defaults to `10000`. |

*⚠️ **Important**: You must also provide a `credentials.json` file in the root directory for Google Drive Service Account authentication. Ensure this Service Account has "Editor" access to your Excel file.*

## 🚀 Running the Project Locally

1.  Clone the repository.
2.  Add your `credentials.json` to the root directory.
3.  Ensure your environment variables are set (you can use a `.env` file).
4.  Run the application using the automated startup script:

```bash
python run.py
