# handlers/games.py
import random
import time
import json
from core.api_client import send_message
from core.database import execute_query

# کش موقت برای سرعت بیشتر (با پشتیبان دیتابیس)
active_trivias = {}
TRIVIA_TTL_SECONDS = 10 * 60

async def save_game_to_db(game_id, chat_id, game_type, data):
    """ذخیره بازی در دیتابیس"""
    await execute_query(
        "INSERT OR REPLACE INTO active_games (game_id, chat_id, game_type, data) VALUES (?, ?, ?, ?)",
        (game_id, chat_id, game_type, json.dumps(data))
    )

async def load_game_from_db(game_id):
    """بارگذاری بازی از دیتابیس"""
    row = await execute_query(
        "SELECT data FROM active_games WHERE game_id=? AND created_at > datetime('now', '-10 minutes')",
        (game_id,), fetch=True
    )
    if row:
        return json.loads(row[0]["data"])
    return None

async def delete_game_from_db(game_id):
    """حذف بازی از دیتابیس"""
    await execute_query("DELETE FROM active_games WHERE game_id=?", (game_id,))

async def cleanup_expired_games():
    """پاک کردن بازی‌های منقضی شده"""
    await execute_query("DELETE FROM active_games WHERE created_at < datetime('now', '-10 minutes')")

TRIVIA_QUESTIONS = [
    {"q": "پایتخت ایران کجاست؟", "options": ["تهران", "شیراز", "اصفهان", "مشهد"], "answer": 0},
    {"q": "بزرگترین سیاره منظومه شمسی کدام است؟", "options": ["زمین", "مریخ", "مشتری", "زهره"], "answer": 2},
    {"q": "نویسنده کتاب شاهنامه کیست؟", "options": ["سعدی", "فردوسی", "حافظ", "مولوی"], "answer": 1},
    {"q": "چند قاره در زمین وجود دارد؟", "options": ["۵", "۶", "۷", "۸"], "answer": 2},
    {"q": "سریع‌ترین حیوان روی زمین کدام است؟", "options": ["یوزپلنگ", "شیر", "پلنگ", "خرگوش"], "answer": 0}
]

async def handle_trivia(chat_id):
    """شروع یک مسابقه عمومی با ذخیره در دیتابیس"""
    await cleanup_expired_games()
    
    # بررسی بازی فعال در این گروه
    existing = await execute_query(
        "SELECT game_id FROM active_games WHERE chat_id=? AND game_type='trivia'",
        (chat_id,), fetch=True
    )
    if existing:
        await send_message(chat_id, "⏳ یک مسابقه در حال انجام است! لطفاً منتظر بمانید.")
        return

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
        game_data = {
            "chat_id": chat_id,
            "answer": q["answer"],
            "answered_by": [],
            "created_at": time.time()
        }
        active_trivias[msg_id] = game_data
        # ذخیره در دیتابیس
        await save_game_to_db(str(msg_id), chat_id, "trivia", game_data)