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

import time
from services.xp_service import add_xp

active_guesses = {}
GUESS_TTL = 120  # بازی بعد از ۲ دقیقه خودکار لغو میشه

async def start_guess(chat_id, user_id):
    """شروع بازی حدس عدد"""
    # اگه کاربر داره بازی میکنه، نذار دوباره شروع کنه
    if user_id in active_guesses and active_guesses[user_id]["chat_id"] == chat_id:
        await send_message(chat_id, "⏳ شما در حال بازی هستید! فقط عدد رو بفرستید.")
        return
        
    target = random.randint(1, 100)
    active_guesses[user_id] = {
        "chat_id": chat_id,
        "target": target,
        "attempts_left": 7,
        "expires_at": time.time() + GUESS_TTL
    }
    
    text = (
        "🎯 <b>بازی حدس عدد شروع شد!</b>\n\n"
        "من یک عدد بین <b>۱ تا ۱۰۰</b> در نظر گرفتم.\n"
        "شما <b>۷ فرصت</b> دارید تا اون رو حدس بزنید.\n\n"
        "✏️ فقط کافیه عدد مورد نظرتون رو همینجا بفرستید!\n"
        "<i>(فرصت‌ها: ۷ از ۷)</i>"
    )
    await send_message(chat_id, text)

async def check_guess(chat_id, user_id, guess):
    """بررسی عدد ارسال شده کاربر در حین بازی"""
    # اگه کاربر بازی نکرده باشه None برمیگرده تا پیام عادی 처리 بشه
    if user_id not in active_guesses or active_guesses[user_id]["chat_id"] != chat_id:
        return None
        
    game = active_guesses[user_id]
    
    # بررسی زمان انقضای بازی
    if time.time() > game["expires_at"]:
        del active_guesses[user_id]
        return "⌛ زمان بازی به پایان رسید! بازی لغو شد."
        
    target = game["target"]
    game["attempts_left"] -= 1
    attempts_left = game["attempts_left"]
    
    # اگه درست حدس زد
    if guess == target:
        del active_guesses[user_id]
        await add_xp(user_id, chat_id, 30)
        return f"🎉 <b>آفرین! درست حدس زدی!</b>\nعدد من <b>{target}</b> بود.\n+30 XP به شما اضافه شد."
        
    # اگه فرصت‌ها تموم شد
    if attempts_left == 0:
        del active_guesses[user_id]
        return f"😢 <b>باختی!</b>\nفرصت‌هات تموم شد.\nعدد من <b>{target}</b> بود."
        
    # راهنمایی (بزرگ‌تر یا کوچیک‌تر)
    hint = "⬆️ عدد من بزرگ‌تره!" if guess < target else "⬇️ عدد من کوچیک‌تره!"
    return f"{hint}\n\n<i>(فرصت‌های باقیمانده: {attempts_left})</i>"