# handlers/moderation.py
import re
import time
from collections import defaultdict
from core.api_client import send_message, delete_message, send_typing_action
from services.group_service import (
    add_warning, get_warnings_count, ban_user, add_filter, get_filters,
    get_filter_count, is_group_premium, is_antilink_enabled, set_antilink
)
from services.permission_service import is_group_admin
from core.normalizer import normalize_text

MAX_WARNINGS = 3
MAX_FREE_FILTERS = 3
NO_PERMISSION_TEXT = "⛔ این دستور فقط برای ادمین‌های گروه در دسترس است."

# دیتابیس موقت برای ضد اسپم (Flood Detection)
# ساختار: {user_id: [timestamp1, timestamp2, ...]}
_flood_cache = defaultdict(list)
FLOOD_LIMIT = 5  # حداکثر 5 پیام
FLOOD_WINDOW = 5  # در 5 ثانیه

async def handle_warn(chat_id, message):
    await send_typing_action(chat_id)
    user_id = message["from"]["id"]
    if not await is_group_admin(chat_id, user_id):
        await send_message(chat_id, NO_PERMISSION_TEXT); return

    if not message.get("reply_to_message"):
        await send_message(chat_id, "❌ این دستور باید روی پیام یک کاربر ریپلای شود."); return

    target_user = message["reply_to_message"]["from"]
    parts = message.get("text", "").split(" ", 1)
    reason = parts[1] if len(parts) > 1 else "اخطار دستی ادمین"

    await add_warning(target_user["id"], chat_id, reason)
    count = await get_warnings_count(target_user["id"], chat_id)

    if count >= MAX_WARNINGS:
        await ban_user(target_user["id"], chat_id)
        await send_message(chat_id, f"🚫 کاربر <b>{target_user['first_name']}</b> به دلیل رسیدن به سقف اخطارها بن مجازی شد!")
    else:
        await send_message(chat_id, f"⚠️ اخطار به <b>{target_user['first_name']}</b> داده شد.\nدلیل: {reason}\nتعداد: {count}/{MAX_WARNINGS}")

# ... (handle_ban, handle_filter, handle_set_antilink دقیقا مثل قبل می‌مانند) ...

async def handle_ban(chat_id, message):
    await send_typing_action(chat_id)
    user_id = message["from"]["id"]
    if not await is_group_admin(chat_id, user_id):
        await send_message(chat_id, NO_PERMISSION_TEXT); return
    if not message.get("reply_to_message"):
        await send_message(chat_id, "❌ این دستور باید روی پیام کاربر ریپلای شود."); return
    target_user = message["reply_to_message"]["from"]
    await ban_user(target_user["id"], chat_id)
    await send_message(chat_id, f"🚫 کاربر <b>{target_user['first_name']}</b> بن مجازی شد!")

async def handle_filter(chat_id, text, user_id):
    await send_typing_action(chat_id)
    if not await is_group_admin(chat_id, user_id):
        await send_message(chat_id, NO_PERMISSION_TEXT); return
    parts = text.split(" ", 1)
    if len(parts) < 2:
        await send_message(chat_id, "❌ استفاده: /filter [word]"); return
    word = normalize_text(parts[1].strip()) # استفاده از نرمالایزر
    
    is_premium = await is_group_premium(chat_id)
    if not is_premium:
        count = await get_filter_count(chat_id)
        if count >= MAX_FREE_FILTERS:
            await send_message(chat_id, f"🔒 در نسخه رایگان فقط {MAX_FREE_FILTERS} کلمه فیلتر می‌شود."); return
    await add_filter(chat_id, word)
    await send_message(chat_id, f"✅ کلمه '{word}' فیلتر شد.")

async def handle_set_antilink(chat_id, text, user_id):
    if not await is_group_admin(chat_id, user_id):
        await send_message(chat_id, NO_PERMISSION_TEXT); return
    parts = text.split(" ", 1)
    if len(parts) < 2 or parts[1].strip().lower() not in ["on", "off"]:
        await send_message(chat_id, "❌ استفاده: /setantilink [on/off]"); return
    enabled = parts[1].strip().lower() == "on"
    await set_antilink(chat_id, enabled)
    await send_message(chat_id, "🛡 آنتی‌لینک فعال شد." if enabled else "🔓 آنتی‌لینک غیرفعال شد.")

async def check_message_violations(chat_id, message):
    """بررسی لینک‌ها، فیلتر کلمات و اسپم"""
    text = message.get("text", "")
    message_id = message["message_id"]
    user_id = message["from"]["id"]

    # ۱. بررسی ضد لینک
    if await is_antilink_enabled(chat_id):
        # رجکس قوی‌تر برای انواع لینک‌ها
        url_pattern = re.compile(r'(https?://\S+|www\.\S+|t\.me/\S+|telegram\.me/\S+|splus\.ir/\S+)', re.IGNORECASE)
        if url_pattern.search(text):
            await delete_message(chat_id, message_id)
            await send_message(chat_id, "🛑 ارسال لینک ممنوع است!")
            return True

    # ۲. بررسی فیلتر کلمات با متن نرمالایز شده
    filters = await get_filters(chat_id)
    normalized_text = normalize_text(text)
    for bad_word in filters:
        if bad_word in normalized_text:
            await delete_message(chat_id, message_id)
            await send_message(chat_id, "🛑 استفاده از کلمات ممنوعه مجاز نیست!")
            return True

    # ۳. بررسی اسپم و فلود (Flood Detection)
    now = time.time()
    # پاکسازی پیام‌های قدیمی‌تر از ۵ ثانیه
    _flood_cache[user_id] = [t for t in _flood_cache[user_id] if now - t < FLOOD_WINDOW]
    _flood_cache[user_id].append(now)
    
    if len(_flood_cache[user_id]) > FLOOD_LIMIT:
        await delete_message(chat_id, message_id)
        await send_message(chat_id, f"⚠️ کاربر <b>{message['from'].get('first_name', '')}</b> به دلیل اسپم کردن محدود شد!")
        # پاک کردن کش برای جلوگیری از لوپ اخطار
        _flood_cache[user_id] = [] 
        # اخطار خودکار برای اسپم
        await add_warning(user_id, chat_id, "اسپم و فلود")
        return True

    return False