# handlers/fun.py
import random
import time
from core.api_client import send_message, edit_message_text

_active_users = {}
active_votes = {}
VOTE_TTL_SECONDS = 30 * 60  # بعد از ۳۰ دقیقه، رأی‌گیری‌های تمام‌نشده از حافظه پاک می‌شوند


def _prune_expired_votes():
    now = time.time()
    expired_ids = [
        msg_id for msg_id, data in active_votes.items()
        if now - data.get("created_at", now) > VOTE_TTL_SECONDS
    ]
    for msg_id in expired_ids:
        del active_votes[msg_id]

async def track_user(chat_id, user_id, first_name):
    if chat_id not in _active_users:
        _active_users[chat_id] = {}
    _active_users[chat_id][user_id] = first_name

async def handle_who(chat_id):
    users = _active_users.get(chat_id, {})
    if not users:
        await send_message(chat_id, "🤔 هنوز کسی در گروه پیامی نداده است که بتونم انتخابش کنم!")
        return
        
    selected_id = random.choice(list(users.keys()))
    selected_name = users[selected_id]
    
    text = f"🎲 <b>انتخاب تصادفی!</b>\n\nنفر انتخاب شده برای این کار: <b>{selected_name}</b> 🎉"
    await send_message(chat_id, text)

async def handle_vote(chat_id, text, user_id, first_name):
    parts = text.split(" ", 1)
    if len(parts) < 2:
        await send_message(chat_id, "❌ استفاده درست: /vote [موضوع رأی‌گیری]")
        return
        
    subject = parts[1]
    keyboard = {
        "inline_keyboard": [
            [
                {"text": "✅ موافقم", "callback_data": "vote_yes"},
                {"text": "❌ مخالفم", "callback_data": "vote_no"}
            ]
        ]
    }
    
    text = f"📊 <b>رأی‌گیری جدید</b>\n\nسوال: <b>{subject}</b>\n\n👤 ایجاد شده توسط: {first_name}\n\nموافقین: 0 | مخالفین: 0"
    res = await send_message(chat_id, text, reply_markup=keyboard)
    
    if res and res.get("ok"):
        _prune_expired_votes()
        msg_id = res["result"]["message_id"]
        active_votes[msg_id] = {
            "chat_id": chat_id,
            "subject": subject,
            "creator": first_name,
            "yes": 0,
            "no": 0,
            "voters": [],
            "created_at": time.time()
        }

async def process_vote(chat_id, message_id, user_id, vote_choice):
    if message_id not in active_votes:
        return "expired"
        
    vote_data = active_votes[message_id]
    
    if user_id in vote_data["voters"]:
        return "voted"
        
    vote_data["voters"].append(user_id)
    if vote_choice == "yes":
        vote_data["yes"] += 1
    else:
        vote_data["no"] += 1
        
    new_text = f"📊 <b>رأی‌گیری جدید</b>\n\nسوال: <b>{vote_data['subject']}</b>\n\n👤 ایجاد شده توسط: {vote_data['creator']}\n\nموافقین: {vote_data['yes']} | مخالفین: {vote_data['no']}"
    
    keyboard = {
        "inline_keyboard": [
            [
                {"text": "✅ موافقم", "callback_data": "vote_yes"},
                {"text": "❌ مخالفم", "callback_data": "vote_no"}
            ]
        ]
    }
    await edit_message_text(chat_id, message_id, new_text, reply_markup=keyboard)
    return "success"

TRUTHS = [
    "بزرگترین دروغ زندگیت چه بوده؟",
    "کی رو تو گروه دوست داری ولی جرات نمیکنی بگی؟",
    "بدترین خاطره مدرسه‌ت چیه؟",
    "اگه الان یک سوپرپاور داشتی چی میشد؟"
]

DARES = [
    "یک عکس از چهره‌ت بفرست!",
    "همین الان یک پیام عاشقانه تو گروه بفرست!",
    "اسم خودت رو برعکس تایپ کن!",
    "یک آهنگ بخوان و ویسش کن!"
]

async def handle_truth(chat_id):
    truth = random.choice(TRUTHS)
    text = f"🤔 <b>جرئت یا حقیقت؟</b>\n\n🧠 حقیقت:\n<b>{truth}</b>"
    await send_message(chat_id, text)

async def handle_dare(chat_id):
    dare = random.choice(DARES)
    text = f"🤔 <b>جرئت یا حقیقت؟</b>\n\n🔥 جرئت:\n<b>{dare}</b>"
    await send_message(chat_id, text)