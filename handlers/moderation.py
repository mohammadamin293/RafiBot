# handlers/moderation.py
import re
import time
from collections import defaultdict
from core.api_client import send_message, delete_message, send_typing_action
from services.group_service import (
    add_warning, get_warnings_count, ban_user, add_filter, get_filters,
    get_filter_count, is_group_premium, set_antilink,
    mute_user, unmute_user, is_user_muted, add_mod_log, get_mod_logs,
    get_group_settings
)
from services.permission_service import is_group_admin
from core.normalizer import normalize_text
from core.api_client import send_message, delete_message, send_typing_action, join_chat

MAX_WARNINGS = 3
MAX_FREE_FILTERS = 3
NO_PERMISSION_TEXT = "⛔ این دستور فقط برای ادمین‌های گروه در دسترس است."

# دیتابیس موقت برای ضد اسپم
_flood_cache = defaultdict(list)
FLOOD_LIMIT = 5
FLOOD_WINDOW = 5

async def handle_warn(chat_id, message):
    user_id = message["from"]["id"]
    if not await is_group_admin(chat_id, user_id):
        await send_message(chat_id, NO_PERMISSION_TEXT)
        return

    if not message.get("reply_to_message"):
        await send_message(chat_id, "❌ این دستور باید روی پیام یک کاربر ریپلای شود.")
        return

    target_user = message["reply_to_message"]["from"]
    parts = message.get("text", "").split(" ", 1)
    reason = parts[1] if len(parts) > 1 else "اخطار دستی ادمین"

    await add_warning(target_user["id"], chat_id, reason)
    count = await get_warnings_count(target_user["id"], chat_id)
    await add_mod_log(chat_id, user_id, "WARN", target_user["id"], reason)

    if count >= MAX_WARNINGS:
        await mute_user(target_user["id"], chat_id, 3600)
        await send_message(
            chat_id, 
            f"🔇 کاربر <b>{target_user['first_name']}</b> به دلیل رسیدن به سقف اخطارها، برای ۱ ساعت میوت شد!"
        )
    else:
        await send_message(
            chat_id, 
            f"⚠️ اخطار به <b>{target_user['first_name']}</b> داده شد.\n"
            f"دلیل: {reason}\n"
            f"تعداد: {count}/{MAX_WARNINGS}"
        )

async def handle_ban(chat_id, message):
    user_id = message["from"]["id"]
    if not await is_group_admin(chat_id, user_id):
        await send_message(chat_id, NO_PERMISSION_TEXT)
        return
        
    if not message.get("reply_to_message"):
        await send_message(chat_id, "❌ این دستور باید روی پیام کاربر ریپلای شود.")
        return
        
    target_user = message["reply_to_message"]["from"]
    await ban_user(target_user["id"], chat_id)
    await add_mod_log(chat_id, user_id, "BAN", target_user["id"], "Permanent Ban")
    await send_message(chat_id, f"🚫 کاربر <b>{target_user['first_name']}</b> بن مجازی شد!")

async def handle_filter(chat_id, text, user_id):
    if not await is_group_admin(chat_id, user_id):
        await send_message(chat_id, NO_PERMISSION_TEXT)
        return
        
    parts = text.split(" ", 1)
    if len(parts) < 2:
        await send_message(chat_id, "❌ استفاده: /filter [word]")
        return
        
    word = normalize_text(parts[1].strip())
    if len(word) < 2:
        await send_message(chat_id, "⚠️ کلمه باید حداقل ۲ کاراکتر باشد.")
        return
    
    is_premium = await is_group_premium(chat_id)
    if not is_premium:
        count = await get_filter_count(chat_id)
        if count >= MAX_FREE_FILTERS:
            await send_message(
                chat_id, 
                f"🔒 در نسخه رایگان فقط {MAX_FREE_FILTERS} کلمه فیلتر می‌شود.\n"
                f"برای فیلتر نامحدود، گروه را به Premium ارتقا دهید."
            )
            return
            
    await add_filter(chat_id, word)
    await send_message(chat_id, f"✅ کلمه '{word}' فیلتر شد.")

async def handle_set_antilink(chat_id, text, user_id):
    if not await is_group_admin(chat_id, user_id):
        await send_message(chat_id, NO_PERMISSION_TEXT)
        return
        
    parts = text.split(" ", 1)
    if len(parts) < 2 or parts[1].strip().lower() not in ["on", "off"]:
        await send_message(chat_id, "❌ استفاده: /setantilink [on/off]")
        return
        
    enabled = parts[1].strip().lower() == "on"
    await set_antilink(chat_id, enabled)
    await send_message(
        chat_id, 
        "🛡 آنتی‌لینک فعال شد." if enabled else "🔓 آنتی‌لینک غیرفعال شد."
    )

async def handle_mute(chat_id, message, admin_id):
    if not await is_group_admin(chat_id, admin_id):
        await send_message(chat_id, NO_PERMISSION_TEXT)
        return
        
    if not message.get("reply_to_message"):
        await send_message(chat_id, "❌ این دستور باید روی پیام یک کاربر ریپلای شود.")
        return
        
    target_user = message["reply_to_message"]["from"]
    parts = message.get("text", "").split()
    
    duration_min = 10
    if len(parts) > 1:
        try:
            duration_min = int(parts[1])
        except ValueError:
            pass
            
    reason = " ".join(parts[2:]) if len(parts) > 2 else "بدون دلیل مشخص"
    duration_sec = duration_min * 60
    
    await mute_user(target_user["id"], chat_id, duration_sec)
    await add_mod_log(chat_id, admin_id, "MUTE", target_user["id"], reason)
    
    text = (
        f"🔇 کاربر <b>{target_user['first_name']}</b> برای <b>{duration_min} دقیقه</b> میوت شد.\n"
        f"دلیل: {reason}"
    )
    await send_message(chat_id, text)

async def handle_unmute(chat_id, message, admin_id):
    if not await is_group_admin(chat_id, admin_id):
        await send_message(chat_id, NO_PERMISSION_TEXT)
        return
        
    if not message.get("reply_to_message"):
        await send_message(chat_id, "❌ این دستور باید روی پیام یک کاربر ریپلای شود.")
        return
        
    target_user = message["reply_to_message"]["from"]
    await unmute_user(target_user["id"], chat_id)
    await add_mod_log(chat_id, admin_id, "UNMUTE", target_user["id"], "Manual unmute")
    await send_message(chat_id, f"🔊 کاربر <b>{target_user['first_name']}</b> آنمیوت شد.")

async def handle_kick(chat_id, message, admin_id):
    from core.api_client import kick_chat_member
    
    if not await is_group_admin(chat_id, admin_id):
        await send_message(chat_id, NO_PERMISSION_TEXT)
        return
        
    if not message.get("reply_to_message"):
        await send_message(chat_id, "❌ این دستور باید روی پیام یک کاربر ریپلای شود.")
        return
        
    target_user = message["reply_to_message"]["from"]
    res = await kick_chat_member(chat_id, target_user["id"])
    
    if res and res.get("ok"):
        await add_mod_log(chat_id, admin_id, "KICK", target_user["id"], "Manual kick")
        await send_message(chat_id, f"👢 کاربر <b>{target_user['first_name']}</b> از گروه اخراج شد!")
    else:
        await send_message(chat_id, "❌ اخراج ناموفق بود. مطمئن شوید ربات ادمین است.")

async def handle_logs(chat_id, admin_id):
    if not await is_group_admin(chat_id, admin_id):
        await send_message(chat_id, NO_PERMISSION_TEXT)
        return
        
    logs = await get_mod_logs(chat_id)
    if not logs:
        await send_message(chat_id, "📜 هنوز هیچ اقدام مدیریتی ثبت نشده است.")
        return
        
    text = "📜 <b>آخرین اقدامات مدیریتی گروه:</b>\n\n"
    for log in logs:
        text += (
            f"👤 ادمین: <code>{log['admin_id']}</code> | 🎯 هدف: <code>{log['target_id']}</code>\n"
            f"اقدام: <b>{log['action']}</b> - دلیل: {log['reason']}\n"
            f"⏱ {log['date']}\n"
            f"➖➖➖➖➖➖\n"
        )
        
    await send_message(chat_id, text)

# در انتهای فایل handlers/moderation.py این تابع را اصلاح کنید:

async def handle_end_vote(chat_id, admin_id):
    if not await is_group_admin(chat_id, admin_id):
        await send_message(chat_id, NO_PERMISSION_TEXT)
        return
        
    from handlers.fun import end_vote
    ended = await end_vote(chat_id)
    
    if ended:
        await send_message(chat_id, "✅ نظرسنجی فعال با موفقیت پایان داده شد.")
    else:
        await send_message(chat_id, "⚠️ هیچ نظرسنجی فعالی در این گروه وجود ندارد.")

async def check_message_violations(chat_id, message):
    text = message.get("text", "")
    message_id = message["message_id"]
    user_id = message["from"]["id"]
    first_name = message["from"].get("first_name", "کاربر")
    
    settings = await get_group_settings(chat_id)

    # ۱. بررسی ضد لینک (برگشت به حالت عادی - پاک کردن لینک‌ها)
    if settings.get("antilink", 1) or settings.get("lock_links", 0):
        url_pattern = re.compile(r'(https?://\S+|www\.\S+|t\.me/\S+|telegram\.me/\S+|splus\.ir/\S+)', re.IGNORECASE)
        if url_pattern.search(text):
            await delete_message(chat_id, message_id)
            if settings.get("antilink", 1):
                await send_message(chat_id, "🛑 ارسال لینک ممنوع است!")
            return True

    # ۲. بررسی فیلتر کلمات
    if settings.get("filter_enabled", 1):
        filters = await get_filters(chat_id)
        normalized_text = normalize_text(text)
        for bad_word in filters:
            if bad_word in normalized_text:
                await delete_message(chat_id, message_id)
                await send_message(chat_id, "🛑 استفاده از کلمات ممنوعه مجاز نیست!")
                return True

    # ۳. بررسی قفل‌های رسانه‌ای
    if settings.get("lock_photos", 0) and message.get("photo"):
        await delete_message(chat_id, message_id)
        return True
    if settings.get("lock_videos", 0) and message.get("video"):
        await delete_message(chat_id, message_id)
        return True
    if settings.get("lock_stickers", 0) and message.get("sticker"):
        await delete_message(chat_id, message_id)
        return True
    if settings.get("lock_forward", 0) and (message.get("forward_from") or message.get("forward_from_chat")):
        await delete_message(chat_id, message_id)
        return True

    # ۴. بررسی اسپم و فلود
    if settings.get("antispam", 1):
        now = time.time()
        cache_key = (chat_id, user_id)
        
        _flood_cache[cache_key] = [t for t in _flood_cache[cache_key] if now - t < FLOOD_WINDOW]
        _flood_cache[cache_key].append(now)
        
        if len(_flood_cache[cache_key]) > FLOOD_LIMIT:
            await delete_message(chat_id, message_id)
            await send_message(chat_id, f"⚠️ کاربر <b>{first_name}</b> به دلیل اسپم محدود شد!")
            _flood_cache[cache_key] = [] 
            
            await add_warning(user_id, chat_id, "اسپم و فلود")
            count = await get_warnings_count(user_id, chat_id)
            
            if count >= MAX_WARNINGS:
                await mute_user(user_id, chat_id, 1800)
                await send_message(
                    chat_id, 
                    f"🔇 کاربر <b>{first_name}</b> به دلیل تکرار اسپم، برای ۳۰ دقیقه میوت شد!"
                )
            return True

    return False

    # ۲. بررسی فیلتر کلمات
    if settings.get("filter_enabled", 1):
        filters = await get_filters(chat_id)
        normalized_text = normalize_text(text)
        for bad_word in filters:
            if bad_word in normalized_text:
                await delete_message(chat_id, message_id)
                await send_message(chat_id, "🛑 استفاده از کلمات ممنوعه مجاز نیست!")
                return True

    # ۳. بررسی قفل‌های رسانه‌ای
    if settings.get("lock_photos", 0) and message.get("photo"):
        await delete_message(chat_id, message_id)
        return True
    if settings.get("lock_videos", 0) and message.get("video"):
        await delete_message(chat_id, message_id)
        return True
    if settings.get("lock_stickers", 0) and message.get("sticker"):
        await delete_message(chat_id, message_id)
        return True
    if settings.get("lock_forward", 0) and (message.get("forward_from") or message.get("forward_from_chat")):
        await delete_message(chat_id, message_id)
        return True

    # ۴. بررسی اسپم و فلود
    if settings.get("antispam", 1):
        now = time.time()
        cache_key = (chat_id, user_id)
        
        _flood_cache[cache_key] = [t for t in _flood_cache[cache_key] if now - t < FLOOD_WINDOW]
        _flood_cache[cache_key].append(now)
        
        if len(_flood_cache[cache_key]) > FLOOD_LIMIT:
            await delete_message(chat_id, message_id)
            await send_message(chat_id, f"⚠️ کاربر <b>{first_name}</b> به دلیل اسپم محدود شد!")
            _flood_cache[cache_key] = [] 
            
            await add_warning(user_id, chat_id, "اسپم و فلود")
            count = await get_warnings_count(user_id, chat_id)
            
            if count >= MAX_WARNINGS:
                await mute_user(user_id, chat_id, 1800)
                await send_message(
                    chat_id, 
                    f"🔇 کاربر <b>{first_name}</b> به دلیل تکرار اسپم، برای ۳۰ دقیقه میوت شد!"
                )
            return True

    return False