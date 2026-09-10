# handlers/games.py
import random
import time
from core.api_client import send_message, edit_message_text
from services.ai_service import generate_trivia_question

active_trivias = {}
TRIVIA_TTL_SECONDS = 10 * 60

# سوالات پیش‌فرض برای زمانی که هوش مصنوعی قطع باشه یا ارور بده
FALLBACK_QUESTIONS = [
    {"q": "پایتخت ایران کجاست؟", "options": ["تهران", "شیراز", "اصفهان", "مشهد"], "answer": 0},
    {"q": "بزرگترین سیاره منظومه شمسی کدام است؟", "options": ["زمین", "مریخ", "مشتری", "زهره"], "answer": 2},
    {"q": "نویسنده کتاب شاهنامه کیست؟", "options": ["سعدی", "فردوسی", "حافظ", "مولوی"], "answer": 1}
]

def _prune_expired_trivias():
    now = time.time()
    expired_ids = [
        msg_id for msg_id, data in active_trivias.items()
        if now - data.get("created_at", now) > TRIVIA_TTL_SECONDS
    ]
    for msg_id in expired_ids:
        del active_trivias[msg_id]

async def handle_trivia(chat_id):
    """شروع یک مسابقه عمومی با سوال هوش مصنوعی"""
    _prune_expired_trivias()

    # جلوگیری از شروع دو مسابقه همزمان
    if any(data["chat_id"] == chat_id for data in active_trivias.values()):
        await send_message(chat_id, "⏳ یک مسابقه در حال انجام است! لطفاً منتظر بمانید.")
        return False

    # ارسال پیام اولیه برای جلوگیری از احساس هنگی بات
    msg_res = await send_message(chat_id, "🧠 <b>مسابقه عمومی!</b>\n\n⏳ هوش مصنوعی در حال طرح سوال است...")
    
    # گرفتن سوال از هوش مصنوعی
    ai_question = await generate_trivia_question()
    
    # اگه هوش مصنوعی جواب درست نداد، از سوالات پیش‌فرض استفاده کن
    if not ai_question:
        fallback = random.choice(FALLBACK_QUESTIONS)
        q = fallback["q"]
        options = fallback["options"]
        answer_idx = fallback["answer"]
    else:
        q = ai_question["question"]
        options = ai_question["options"]
        answer_idx = ai_question["answer"]

    keyboard = {
        "inline_keyboard": [
            [
                {"text": f"A) {options[0]}", "callback_data": "trivia_0"},
                {"text": f"B) {options[1]}", "callback_data": "trivia_1"}
            ],
            [
                {"text": f"C) {options[2]}", "callback_data": "trivia_2"},
                {"text": f"D) {options[3]}", "callback_data": "trivia_3"}
            ],
            [{"text": "🔚 پایان مسابقه", "callback_data": "trivia_end"}]
        ]
    }
    text = f"🧠 <b>مسابقه عمومی!</b>\n\n❓ {q}\n\nبرای پاسخ روی یک گزینه کلیک کنید:"
    
    # ویرایش پیام اولیه و قرار دادن سوال و دکمه‌ها
    if msg_res and msg_res.get("ok"):
        msg_id = msg_res["result"]["message_id"]
        await edit_message_text(chat_id, msg_id, text, reply_markup=keyboard)
        
        active_trivias[msg_id] = {
            "chat_id": chat_id,
            "answer": answer_idx,
            "answered_by": [],
            "created_at": time.time()
        }
        return True
    return False

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
    """بازی حدس عدد"""
    await send_message(chat_id, "🎯 <b>حدس عدد</b>\n\nاین بخش به‌زودی اضافه خواهد شد!")