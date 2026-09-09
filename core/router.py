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
import re
from core.api_client import join_chat, get_chat_member_count, send_message
from handlers.admin import handle_install

MENU_BUTTONS = ["🎮 بازی‌ها", "🏆 رتبه من", "😂 فان", "🛡 مدیریت", "⚙️ تنظیمات", "❓ راهنما"]

async def route_message(message):
    chat_id = message["chat"]["id"]
    chat_type = message["chat"]["type"]
    text = message.get("text", "")
    user_id = message["from"]["id"]
    first_name = message["from"].get("first_name", "کاربر")

    # --- قابلیت جوین شدن به گروه از طریق لینک در پی‌وی ---
    if chat_type == "private":
        # تشخیص لینک‌های سروش پلاس یا لینک‌های دعوت
        link_pattern = re.compile(r'(https?://splus\.ir/\S+|splus\.ir/\S+|@[\w_]+)', re.IGNORECASE)
        if link_pattern.search(text):
            link = text.strip()
            
            await send_message(chat_id, "⏳ در حال تلاش برای ورود به گروه...")
            res = await join_chat(link)
            
            if res and res.get("ok"):
                group_id = res["result"]["id"]
                group_name = res["result"].get("title", "گروه")
                
                # بررسی تعداد اعضای گروه (مثلا حداقل ۹۰ نفر مثل دیجی آنتی)
                count_res = await get_chat_member_count(group_id)
                member_count = count_res["result"] if count_res and count_res.get("ok") else 0
                
                if member_count < 10: # برای تست روی ۱۰ گذاشتیم، بعدا ببر روی ۹۰
                    await send_message(chat_id, f"⚠️ گروه شما (<b>{group_name}</b>) فقط {member_count} عضو دارد.\nحداقل تعداد اعضا برای فعال‌سازی ربات ۱۰ نفر است.")
                else:
                    await send_message(chat_id, f"✅ ربات با موفقیت وارد گروه <b>{group_name}</b> شد!\n\n🎯 مرحله بعد:\n۱. ربات را در گروه ادمین کنید.\n۲. در گروه دستور /install را بزنید.")
                    
                    # ارسال پیام در خود گروه
                    await send_message(group_id, f"👋 سلام به گروه <b>{group_name}</b>!\nمن RafiBot هستم و اضافه شدم. لطفاً من را ادمین کنید و دستور /install را بزنید.")
            else:
                await send_message(chat_id, "❌ متأسفانه نتوانستم وارد گروه شوم. لطفاً بررسی کنید که لینک درست باشد یا ربات قبلاً عضو نشده باشد.")
            return
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
        "/setantilink": handle_set_antilink, "/setwelcome": handle_set_welcome, 
        "/setrules": handle_set_rules, "/install": handle_install
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