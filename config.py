import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("SOUROUSH_BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
DB_PATH = os.getenv("DATABASE_PATH", "rafibot.db")
API_BASE_URL = f"https://api.splus.ir/bot{BOT_TOKEN}/"
AVALAI_API_KEY = os.getenv("AVALAI_API_KEY", "")

# تنظیمات جدید
MIN_GROUP_MEMBERS = int(os.getenv("MIN_GROUP_MEMBERS", "10"))
AI_RATE_LIMIT = int(os.getenv("AI_RATE_LIMIT", "5"))  # تعداد درخواست در دقیقه
MAX_AI_PROMPT_LENGTH = int(os.getenv("MAX_AI_PROMPT_LENGTH", "1000"))
OWNER_USERNAME = "Iambrrr"  # یوزرنیم شما بدون @
AVALAI_API_KEY = os.getenv("AVALAI_API_KEY", "")
MIN_GROUP_MEMBERS = int(os.getenv("MIN_GROUP_MEMBERS", "10"))