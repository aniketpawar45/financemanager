import os
import pytz
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

IST = pytz.timezone('Asia/Kolkata')

def get_ist_now():
    return datetime.now(IST)

BOT_TOKEN = os.getenv("BOT_TOKEN")
EXCEL_FILE_ID = os.getenv("EXCEL_FILE_ID")
SHEET_NAME = os.getenv("SHEET_NAME", "Daily Expense Log")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")
