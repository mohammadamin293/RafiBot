# main.py
import asyncio
import logging
from core.api_client import api_call, delete_message
from core.database import init_db
from services.group_service import is_user_banned, increment_message_count
from services.xp_service import add_xp
from handlers.base import (
    handle_start, handle_help, handle_rank_menu, handle_games_menu,
    handle_fun_menu, handle_admin_menu, handle_settings_menu,
    handle_profile, handle_leaderboard
)
from handlers.moderation import handle_warn, handle_ban, handle_filter, handle_set_antilink, check_message_violations
from handlers.fun import track_user, handle_who, handle_vote, handle_truth, handle_dare
from handlers.games import handle_trivia
from handlers.admin import (
    handle_set_welcome, handle_set_rules, handle_rules,
    handle_new_member, handle_left_member, handle_set_premium,
    handle_group_stats, handle_premium_info
)
from handlers.ai import handle_ask, handle_suggest, handle_challenge
from handlers.callbacks import handle_callback_query

logging.basicConfig(level=logging.INFO)

MENU_BUTTON_TEXTS = ["🎮 بازی‌ها", "🏆 رتبه من", "😂 فان", "🛡 مدیریت", "⚙️ تنظیمات", "❓ راهنما"]

async def process_message(message):
    chat_id = message["chat"]["id"]
    text = message.get("text", "")
    user_id = message["from"]["id"]
    first_name = message["from"].get("first_name", "کاربر")

    # ۱. بررسی ورود و خروج اعضای جدید (مرحله ۴)
    if "new_chat_members" in message:
        for new_member in message["new_chat_members"]:
            if not new_member.get("is_bot"):
                member_name = new_member.get("first_name", "کاربر")
                await handle_new_member(chat_id, member_name)
        return

    if "left_chat_member" in message:
        left_member = message["left_chat_member"]
        if not left_member.get("is_bot"):
            member_name = left_member.get("first_name", "کاربر")
            await handle_left_member(chat_id, member_name)
        return

    # ۲. بررسی Ban مجازی — این باید قبل از هر مسیر دیگری (از جمله دستورات AI) چک شود
    if await is_user_banned(user_id, chat_id):
        await delete_message(chat_id, message["message_id"])
        return

    # --- مسیر سریع برای هوش مصنوعی (بدون بررسی فیلتر/لینک برای سرعت بالا) ---
    if text.startswith("/ask"):
        await handle_ask(chat_id, text)
        return
    elif text.startswith("/suggest"):
        await handle_suggest(chat_id, text)
        return
    elif text == "/challenge":
        await handle_challenge(chat_id)
        return

    # ۳. بررسی تخلفات (لینک و فیلتر کلمات)
    if await check_message_violations(chat_id, message):
        return

    # ۴. سیستم XP: اگر پیام دستور نبود و از منو هم نیامده بود، 5 امتیاز بده
    if not text.startswith("/") and text not in MENU_BUTTON_TEXTS:
        await add_xp(user_id, chat_id, 5)

    # شمارش واقعی تعداد پیام‌ها برای آمار گروه (Premium)
    await increment_message_count(chat_id)

    # ۵. ثبت کاربران فعال برای دستور /who
    await track_user(chat_id, user_id, first_name)

    # ۶. پردازش دستورات و دکمه‌های منو
    if text.startswith("/start"):
        await handle_start(chat_id)
    elif text.startswith("/help") or text == "❓ راهنما":
        await handle_help(chat_id)

    # پروفایل و رتبه‌بندی
    elif text == "🏆 رتبه من" or text == "/profile":
        await handle_profile(chat_id, user_id, first_name)
    elif text == "/top":
        await handle_leaderboard(chat_id)

    # منوها
    elif text == "🎮 بازی‌ها":
        await handle_games_menu(chat_id)
    elif text == "😂 فان":
        await handle_fun_menu(chat_id)
    elif text == "🛡 مدیریت":
        await handle_admin_menu(chat_id)
    elif text == "⚙️ تنظیمات":
        await handle_settings_menu(chat_id)

    # دستورات مدیریتی (فقط ادمین گروه)
    elif text.startswith("/warn"):
        await handle_warn(chat_id, message)
    elif text.startswith("/ban"):
        await handle_ban(chat_id, message)
    elif text.startswith("/filter"):
        await handle_filter(chat_id, text, user_id)
    elif text.startswith("/setantilink"):
        await handle_set_antilink(chat_id, text, user_id)

    # قابلیت‌های فان
    elif text == "/who":
        await handle_who(chat_id)
    elif text.startswith("/vote"):
        await handle_vote(chat_id, text, user_id, first_name)
    elif text == "/truth":
        await handle_truth(chat_id)
    elif text == "/dare":
        await handle_dare(chat_id)

    # بازی‌ها
    elif text == "/trivia":
        await handle_trivia(chat_id)

    # قوانین و خوش‌آمدگویی (مرحله ۴) — فقط ادمین گروه
    elif text.startswith("/setwelcome"):
        await handle_set_welcome(chat_id, text, user_id)
    elif text.startswith("/setrules"):
        await handle_set_rules(chat_id, text, user_id)
    elif text == "/rules":
        await handle_rules(chat_id)

    # --- قابلیت‌های Premium (مرحله ۵) — /setpremium فقط برای مالک ربات ---
    elif text.startswith("/setpremium"):
        await handle_set_premium(chat_id, text, user_id)
    elif text == "/groupstats":
        await handle_group_stats(chat_id)
    elif text == "/premium":
        await handle_premium_info(chat_id)

async def main():
    logging.info("Initializing Database...")
    await init_db()
    logging.info("RafiBot Async is starting...")
    offset = 0
    while True:
        try:
            payload = {"offset": offset, "timeout": 30, "allowed_updates": ["message", "callback_query"]}
            updates = await api_call("getUpdates", payload)
            if updates and updates.get("ok"):
                for update in updates["result"]:
                    offset = update["update_id"] + 1
                    if "message" in update:
                        asyncio.create_task(process_message(update["message"]))
                    elif "callback_query" in update:
                        asyncio.create_task(handle_callback_query(update["callback_query"]))
        except Exception as e:
            logging.error(f"Error in main loop: {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())
