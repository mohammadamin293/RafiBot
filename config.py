import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("SOUROUSH_BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
DB_PATH = os.getenv("DATABASE_PATH", "rafibot.db")
API_BASE_URL = f"https://api.splus.ir/bot{BOT_TOKEN}/"
MAJID_API_TOKEN = os.getenv("MAJID_API_TOKEN", "")