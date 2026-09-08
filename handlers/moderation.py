# handlers/moderation.py
import re
from core.api_client import send_message, delete_message, send_typing_action
from services.group_service import (
    add_warning, get_warnings_count, ban_user, add_filter, get_filters,
    get_filter_count, is_group_premium, is_antilink_enabled, set_antilink
)
from services.permission_service import is_group_admin

MAX_WARNINGS = 3
MAX_FREE_FILTERS = 3

NO_PERMISSION_TEXT = "⛔ این دستور فقط برای ادمین‌های گروه در دسترس است."


async def handle_warn(chat_id, message):
    await send_typing_action(chat_id)
    user_id = message["from"]["id"]

    if not await is_group_admin(chat_id, user_id):
        await send_message(chat_id, NO_PERMISSION_TEXT)
        return

    if not message.get("reply_to_message"):
        await send_message(chat_id, "❌ این دستور باید روی پیام یک کاربر ریپلای شود.")
        return

    target_user = message["reply_to_message"]["from"]
    if target_user.get("id") == user_id:
        await send_message(chat_id, "❌ نمی‌توانید به خودتان اخطار بدهید.")
        return

    await add_warning(target_user["id"], chat_id, "اخطار دستی")
    count = await get_warnings_count(target_user["id"], chat_id)

    if count >= MAX_WARNINGS:
        await ban_user(target_user["id"], chat_id)
        await send_message(chat_id, f"🚫 کاربر <b>{target_user['first_name']}</b> بن مجازی شد!")
    else:
        await send_message(chat_id, f"⚠️ اخطار به <b>{target_user['first_name']}</b> داده شد.\nتعداد: {count}/{MAX_WARNINGS}")


async def handle_ban(chat_id, message):
    """دستور /ban — بن مجازی فوری کاربر (بدون نیاز به رسیدن به سقف اخطار)."""
    await send_typing_action(chat_id)
    user_id = message["from"]["id"]

    if not await is_group_admin(chat_id, user_id):
        await send_message(chat_id, NO_PERMISSION_TEXT)
        return

    if not message.get("reply_to_message"):
        await send_message(chat_id, "❌ این دستور باید روی پیام کاربری که می‌خواهید بن کنید ریپلای شود.")
        return

    target_user = message["reply_to_message"]["from"]
    if target_user.get("id") == user_id:
        await send_message(chat_id, "❌ نمی‌توانید خودتان را بن کنید.")
        return

    await ban_user(target_user["id"], chat_id)
    await send_message(chat_id, f"🚫 کاربر <b>{target_user['first_name']}</b> بن مجازی شد!")


async def handle_filter(chat_id, text, user_id):
    await send_typing_action(chat_id)

    if not await is_group_admin(chat_id, user_id):
        await send_message(chat_id, NO_PERMISSION_TEXT)
        return

    parts = text.split(" ", 1)
    if len(parts) < 2:
        await send_message(chat_id, "❌ استفاده: /filter [word]")
        return

    word = parts[1].strip().lower()

    # بررسی محدودیت Premium
    is_premium = await is_group_premium(chat_id)
    if not is_premium:
        count = await get_filter_count(chat_id)
        if count >= MAX_FREE_FILTERS:
            await send_message(chat_id, f"🔒 در نسخه رایگان فقط می‌توانید {MAX_FREE_FILTERS} کلمه فیلتر کنید.\n\n💳 برای فیلتر نامحدود، گروه را به Premium ارتقا دهید. (/premium)")
            return

    await add_filter(chat_id, word)
    await send_message(chat_id, f"✅ کلمه '{word}' فیلتر شد.")


async def handle_set_antilink(chat_id, text, user_id):
    """دستور: /setantilink on یا /setantilink off"""
    if not await is_group_admin(chat_id, user_id):
        await send_message(chat_id, NO_PERMISSION_TEXT)
        return

    parts = text.split(" ", 1)
    if len(parts) < 2 or parts[1].strip().lower() not in ["on", "off"]:
        await send_message(chat_id, "❌ استفاده: /setantilink [on/off]")
        return

    enabled = parts[1].strip().lower() == "on"
    await set_antilink(chat_id, enabled)
    if enabled:
        await send_message(chat_id, "🛡 آنتی‌لینک فعال شد. از این به بعد لینک‌ها حذف می‌شوند.")
    else:
        await send_message(chat_id, "🔓 آنتی‌لینک غیرفعال شد.")


async def check_message_violations(chat_id, message):
    """بررسی لینک‌ها و کلمات ممنوعه"""
    text = message.get("text", "")
    message_id = message["message_id"]

    # ۱. بررسی ضد لینک (فقط اگر برای این گروه فعال باشد)
    if await is_antilink_enabled(chat_id):
        url_pattern = re.compile(r'(https?://\S+|www\.\S+|t\.me/\S+|splus\.ir/\S+)', re.IGNORECASE)
        if url_pattern.search(text):
            await delete_message(chat_id, message_id)
            await send_message(chat_id, "🛑 ارسال لینک ممنوع است!")
            return True

    # ۲. بررسی فیلتر کلمات
    filters = await get_filters(chat_id)
    text_lower = text.lower()
    for bad_word in filters:
        if bad_word in text_lower:
            await delete_message(chat_id, message_id)
            await send_message(chat_id, "🛑 استفاده از کلمات ممنوعه مجاز نیست!")
            return True

    return False
