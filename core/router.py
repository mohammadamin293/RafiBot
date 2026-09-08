# core/router.py
from core.api_client import send_message
from services.permission_service import is_group_admin, is_super_admin

# ایمپورت تمام هندلرها
from handlers.base import (
    handle_start, handle_help, handle_profile, handle_leaderboard,
    handle_games_menu, handle_fun_menu, handle_admin_menu, handle_settings_menu
)
from handlers.moderation import handle_warn, handle_ban, handle_filter, handle_set_antilink
from handlers.fun import handle_who, handle_vote, handle_truth, handle_dare
from handlers.games import handle_trivia
from handlers.admin import (
    handle_set_welcome, handle_set_rules, handle_rules, 
    handle_set_premium, handle_group_stats, handle_premium_info
)
from handlers.ai import handle_ask, handle_suggest, handle_challenge
from handlers.economy import handle_balance, handle_daily, handle_coinflip
from handlers.admin import handle_admin_panel

MENU_BUTTONS = ["🎮 بازی‌ها", "🏆 رتبه من", "😂 فان", "🛡 مدیریت", "⚙️ تنظیمات", "❓ راهنما"]

async def route_message(message):
    chat_id = message["chat"]["id"]
    text = message.get("text", "")
    user_id = message["from"]["id"]
    first_name = message["from"].get("first_name", "کاربر")

    # --- مسیر سریع برای هوش مصنوعی ---
    if text.startswith("/ask"):
        await handle_ask(chat_id, text); return
    if text.startswith("/suggest"):
        await handle_suggest(chat_id, text); return
    if text == "/challenge":
        await handle_challenge(chat_id); return

    # --- دکمه‌های کیبورد پایین صفحه ---
    if text == "❓ راهنما" or text.startswith("/help"):
        await handle_help(chat_id); return
    if text == "🏆 رتبه من" or text == "/profile":
        await handle_profile(chat_id, user_id, first_name); return
    if text == "🎮 بازی‌ها":
        await handle_games_menu(chat_id); return
    if text == "😂 فان":
        await handle_fun_menu(chat_id); return
    if text == "🛡 مدیریت":
        await handle_admin_panel(chat_id); return
    if text == "⚙️ تنظیمات":
        await handle_settings_menu(chat_id); return

    # --- دستورات ادمین گروه (نیاز به چک ادمین) ---
    admin_cmds = {
        "/warn": handle_warn, "/ban": handle_ban, "/filter": handle_filter,
        "/setantilink": handle_set_antilink, "/setwelcome": handle_set_welcome, "/setrules": handle_set_rules
    }
    for cmd, handler in admin_cmds.items():
        if text.startswith(cmd):
            if await is_group_admin(chat_id, user_id):
                # هندلرهای warn و ban به message نیاز دارند، بقیه به text
                if cmd in ["/warn", "/ban"]:
                    await handler(chat_id, message)
                else:
                    await handler(chat_id, text, user_id)
            else:
                await send_message(chat_id, "⛔ این دستور فقط برای ادمین‌های گروه در دسترس است.")
            return

    # --- دستورات مالک ربات (Super Admin) ---
    if text.startswith("/setpremium"):
        if is_super_admin(user_id):
            await handle_set_premium(chat_id, text, user_id)
        else:
            await send_message(chat_id, "⛔ این دستور فقط برای مالک ربات در دسترس است.")
        return

    # --- دستورات عادی کاربران ---
    if text.startswith("/start"):
        await handle_start(chat_id); return
    if text == "/top":
        await handle_leaderboard(chat_id); return
    if text == "/rules":
        await handle_rules(chat_id); return
    if text == "/who":
        await handle_who(chat_id); return
    if text.startswith("/vote"):
        await handle_vote(chat_id, text, user_id, first_name); return
    if text == "/truth":
        await handle_truth(chat_id); return
    if text == "/dare":
        await handle_dare(chat_id); return
    if text == "/trivia":
        await handle_trivia(chat_id); return
    if text == "/groupstats":
        await handle_group_stats(chat_id); return
    if text == "/premium":
        await handle_premium_info(chat_id); return
        # --- دستورات اقتصاد ---
    if text == "/balance":
        await handle_balance(chat_id, user_id, first_name); return
    if text == "/daily":
        await handle_daily(chat_id, user_id, first_name); return
    if text.startswith("/coinflip"):
        await handle_coinflip(chat_id, text, user_id, first_name); return