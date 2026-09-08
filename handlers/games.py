# handlers/games.py
import random
import time
from core.api_client import send_message

# دیتابیس موقت برای نگهداری سوالات در حال بازی
active_trivias = {}
TRIVIA_TTL_SECONDS = 10 * 60  # بعد از ۱۰ دقیقه، سوالات بی‌پاسخ از حافظه پاک می‌شوند


def _prune_expired_trivias():
    now = time.time()
    expired_ids = [
        msg_id for msg_id, data in active_trivias.items()
        if now - data.get("created_at", now) > TRIVIA_TTL_SECONDS
    ]
    for msg_id in expired_ids:
        del active_trivias[msg_id]

TRIVIA_QUESTIONS = [
    {"q": "پایتخت ایران کجاست؟", "options": ["تهران", "شیراز", "اصفهان", "مشهد"], "answer": 0},
    {"q": "بزرگترین سیاره منظومه شمسی کدام است؟", "options": ["زمین", "مریخ", "مشتری", "زهره"], "answer": 2},
    {"q": "نویسنده کتاب شاهنامه کیست؟", "options": ["سعدی", "فردوسی", "حافظ", "مولوی"], "answer": 1},
    {"q": "چند قاره در زمین وجود دارد؟", "options": ["۵", "۶", "۷", "۸"], "answer": 2}
]

async def handle_trivia(chat_id):
    """شروع یک مسابقه عمومی"""
    _prune_expired_trivias()

    # چک درست: آیا مسابقه‌ی فعالی (بر اساس chat_id، نه message_id) در این گروه هست؟
    if any(data["chat_id"] == chat_id for data in active_trivias.values()):
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
    text = f"🧠 <b>مسابقه عمومی!</b>\n\n❓ {q['q']}\n\nبرای پاسخ روی یک گزینه کلیک کنید:"
    
    res = await send_message(chat_id, text, reply_markup=keyboard)
    
    if res and res.get("ok"):
        msg_id = res["result"]["message_id"]
        # ذخیره اطلاعات بازی (جواب درست و کسانی که جواب داده‌اند)
        active_trivias[msg_id] = {
            "chat_id": chat_id,
            "answer": q["answer"],
            "answered_by": [],
            "created_at": time.time()
        }