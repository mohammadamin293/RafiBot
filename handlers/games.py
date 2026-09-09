# handlers/games.py
import random
import time
import json
from core.api_client import send_message
from core.database import execute_query

# کش موقت برای سرعت بیشتر
active_trivias = {}
TRIVIA_TTL_SECONDS = 10 * 60

TRIVIA_QUESTIONS = [
    {"q": "پایتخت ایران کجاست؟", "options": ["تهران", "شیراز", "اصفهان", "مشهد"], "answer": 0},
    {"q": "بزرگترین سیاره منظومه شمسی کدام است؟", "options": ["زمین", "مریخ", "مشتری", "زهره"], "answer": 2},
    {"q": "نویسنده کتاب شاهنامه کیست؟", "options": ["سعدی", "فردوسی", "حافظ", "مولوی"], "answer": 1},
    {"q": "چند قاره در زمین وجود دارد؟", "options": ["۵", "۶", "۷", "۸"], "answer": 2},
]

async def handle_trivia(chat_id):
    """شروع مسابقه عمومی"""
    q = random.choice(TRIVIA_QUESTIONS)
    keyboard = {
        "inline_keyboard": [
            [
                {"text": f"A) {q['options'][0]}", "callback_data": "trivia_0"},
                {"text": f"B) {q['options'][1]}", "callback_data": "trivia_1"}
            ],
            [
                {"text": f"C) {q['options'][2]}", "callback_data": "trivia_2"},
                {"text": f"D) {q['options'][3]}", "callback_data": "trivia_3"}
            ]
        ]
    }
    text = f"🧠 <b>مسابقه عمومی!</b>\n\n❓ {q['q']}\n\nبرای پاسخ روی یک گزینه کلیک کن:"
    
    res = await send_message(chat_id, text, reply_markup=keyboard)
    
    if res and res.get("ok"):
        msg_id = res["result"]["message_id"]
        active_trivias[msg_id] = {
            "chat_id": chat_id,
            "answer": q["answer"],
            "answered_by": [],
            "created_at": time.time()
        }

async def handle_rps(chat_id):
    """بازی سنگ کاغذ قیچی - نسخه گروهی"""
    keyboard = {
        "inline_keyboard": [
            [
                {"text": "🪨 سنگ", "callback_data": "rps_rock"},
                {"text": "📄 کاغذ", "callback_data": "rps_paper"},
                {"text": "✂️ قیچی", "callback_data": "rps_scissors"}
            ]
        ]
    }
    text = "✂️ <b>سنگ، کاغذ، قیچی</b>\n\nانتخاب کن:"
    await send_message(chat_id, text, reply_markup=keyboard)

async def handle_guess(chat_id):
    """بازی حدس عدد - نسخه گروهی"""
    number = random.randint(1, 100)
    # ذخیره در کش موقت
    # TODO: پیاده‌سازی کامل
    await send_message(chat_id, f"🎯 یک عدد بین ۱ تا ۱۰۰ حدس بزن!")