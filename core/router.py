# core/router.py
import re
from core.api_client import send_message, join_chat, get_chat_member_count
from services.permission_service import is_group_admin, is_super_admin

from handlers.base import (
    handle_start, handle_help, handle_profile, handle_leaderboard,
    handle_games_menu, handle_fun_menu, handle_settings_menu, handle_economy_menu,
    get_main_menu_keyboard
)
from handlers.admin import (
    handle_admin_panel, handle_set_welcome, handle_set_rules, handle_rules, 
    handle_set_premium, handle_group_stats, handle_premium_info, handle_install
)
from handlers.moderation import (
    handle_warn, handle_ban, handle_filter, handle_set_antilink,
    handle_mute, handle_unmute, handle_logs, handle_kick, handle_end_vote
)
from handlers.fun import handle_who, handle_vote, handle_truth, handle_dare
from handlers.games import handle_trivia, handle_rps, handle_guess
from handlers.ai import handle_ask, handle_suggest, handle_challenge, handle_direct_chat
from handlers.economy import (
    handle_balance, handle_daily, handle_coinflip, 
    handle_work, handle_rob, handle_give, handle_shop, handle_buy
)
from config import MIN_GROUP_MEMBERS
# core/router.py
import re
from core.api_client import send_message, join_chat, get_chat_member_count
from services.permission_service import is_group_admin, is_super_admin
from handlers.admin import (
    handle_admin_panel, handle_set_welcome, handle_set_rules, handle_rules, 
    handle_set_premium, handle_group_stats, handle_premium_info, handle_install, 
    handle_bot_stats  # <--- این رو اضافه کن
)
async def route_message(message):
    chat_id = message["chat"]["id"]
    chat_type = message["chat"]["type"]  # private, group, supergroup
    text = message.get("text", "")
    user_id = message["from"]["id"]
    first_name = message["from"].get("first_name", "کاربر")
    username = message["from"].get("username", "")
    reply_to_message = message.get("reply_to_message")
    
    # ۱. لینک جوین گروه در پیوی
    if chat_type == "private":
        link_pattern = re.compile(r'(https?://splus\.ir/\S+|splus\.ir/\S+|@[\w_]+)', re.IGNORECASE)
        if link_pattern.search(text):
            link = text.strip()
            await send_message(chat_id, "⏳ در حال تلاش برای ورود به گروه...")
            res = await join_chat(link)
            
            if res and res.get("ok"):
                group_id = res["result"]["id"]
                group_name = res["result"].get("title", "گروه")
                count_res = await get_chat_member_count(group_id)
                member_count = count_res["result"] if count_res and count_res.get("ok") else 0
                
                if member_count < MIN_GROUP_MEMBERS:
                    await send_message(
                        chat_id, 
                        f"⚠️ گروه شما (<b>{group_name}</b>) فقط {member_count} عضو دارد.\n"
                        f"حداقل تعداد اعضا برای فعال‌سازی ربات {MIN_GROUP_MEMBERS} نفر است."
                    )
                else:
                    await send_message(
                        chat_id, 
                        f"✅ ربات با موفقیت وارد گروه <b>{group_name}</b> شد!\n\n"
                        f"🎯 مرحله بعد:\n"
                        f"۱. ربات را در گروه ادمین کنید.\n"
                        f"۲. در گروه دستور /install را بزنید."
                    )
                    await send_message(
                        group_id, 
                        f"👋 سلام به گروه <b>{group_name}</b>!\n"
                        f"من RafiBot هستم و اضافه شدم. لطفاً من را ادمین کنید و دستور /install را بزنید."
                    )
            else:
                await send_message(
                    chat_id, 
                    "❌ متأسفانه نتوانستم وارد گروه شوم. لطفاً بررسی کنید:\n"
                    "• لینک دعوت معتبر باشد\n"
                    "• ربات قبلاً عضو نشده باشد"
                )
            return

    # ۲. سیستم هوش مصنوعی خودکار (فرانس)
    is_reply_to_bot = reply_to_message and reply_to_message.get("from", {}).get("is_bot", False)
    starts_with_france = text.lower().startswith("فرانس") or text.lower().startswith("france")
    
    if not text.startswith("/") and (is_reply_to_bot or starts_with_france):
        if text.strip() in ["فرانس", "france"]:
            await send_message(chat_id, "🇫🇷 بله؟ سوالی داری؟")
            return
            
        clean_text = text.replace("فرانس", "", 1).replace("france", "", 1).strip()
        if not clean_text and is_reply_to_bot:
            clean_text = text
            
        if clean_text:
            await handle_direct_chat(chat_id, clean_text, user_id)
            return

    # ۳. دستورات سریع هوش مصنوعی
    if text.startswith("/ask"):
        await handle_ask(chat_id, text, user_id); return
    if text.startswith("/suggest"):
        await handle_suggest(chat_id, text, user_id); return
    if text == "/challenge":
        await handle_challenge(chat_id, user_id); return

    # ۴. دکمه‌های گروهی (ReplyKeyboardMarkup)
    if chat_type in ["group", "supergroup"]:
        if text == "🧠 سوال عمومی":
            await handle_trivia(chat_id); return
        elif text == "✂️ سنگ کاغذ قیچی":
            await handle_rps(chat_id); return
        elif text == "🎯 حدس عدد":
            await handle_guess(chat_id); return
        elif text == "🎯 انتخاب تصادفی":
            await handle_who(chat_id); return
        elif text == "🤔 حقیقت":
            await handle_truth(chat_id); return
        elif text == "🔥 جرئت":
            await handle_dare(chat_id); return
        elif text == "💰 موجودی":
            await handle_balance(chat_id, user_id, first_name); return
        elif text == "🎁 روزانه":
            await handle_daily(chat_id, user_id, first_name); return
        elif text == "💼 کار":
            await handle_work(chat_id, user_id, first_name); return
        elif text == "🪙 شیر یا خط":
            await send_message(chat_id, "❌ استفاده: /coinflip [شیر/خط] [مبلغ]"); return
        elif text == "🏪 فروشگاه":
            await handle_shop(chat_id); return
        elif text == "🔙 بازگشت":
            await send_message(chat_id, "🔙 به منوی اصلی برگشتید.", reply_markup=get_main_menu_keyboard())
            return

    # ۵. دکمه‌های منوی اصلی (همه چت‌ها)
    if text == "❓ راهنما" or text.startswith("/help"):
        await handle_help(chat_id, chat_type); return
    if text == "🏆 رتبه من" or text == "/profile":
        await handle_profile(chat_id, user_id, first_name); return
    if text == "🎮 بازی‌ها":
        await handle_games_menu(chat_id, chat_type); return
    if text == "😂 سرگرمی":
        await handle_fun_menu(chat_id, chat_type); return
    if text == "🛡 مدیریت":
        await handle_admin_panel(chat_id, user_id); return
    if text == "⚙️ تنظیمات":
        await handle_settings_menu(chat_id, chat_type); return
    if text == "💰 اقتصاد":
        await handle_economy_menu(chat_id, chat_type); return

    # ۶. دستورات ادمین گروه (با ریپلای)
    if text.startswith(("/warn", "/ban", "/mute", "/unmute", "/kick")):
        if await is_group_admin(chat_id, user_id):
            if text.startswith("/warn"): await handle_warn(chat_id, message)
            elif text.startswith("/ban"): await handle_ban(chat_id, message)
            elif text.startswith("/mute"): await handle_mute(chat_id, message, user_id)
            elif text.startswith("/unmute"): await handle_unmute(chat_id, message, user_id)
            elif text.startswith("/kick"): await handle_kick(chat_id, message, user_id)
        else:
            await send_message(chat_id, "⛔ این دستور فقط برای ادمین‌های گروه در دسترس است.")
        return

    # ۷. دستورات ادمین گروه (با تکست)
    if text.startswith(("/filter", "/setantilink", "/setwelcome", "/setrules")):
        if await is_group_admin(chat_id, user_id):
            if text.startswith("/filter"): await handle_filter(chat_id, text, user_id)
            elif text.startswith("/setantilink"): await handle_set_antilink(chat_id, text, user_id)
            elif text.startswith("/setwelcome"): await handle_set_welcome(chat_id, text, user_id)
            elif text.startswith("/setrules"): await handle_set_rules(chat_id, text, user_id)
        else:
            await send_message(chat_id, "⛔ این دستور فقط برای ادمین‌های گروه در دسترس است.")
        return

    # ۸. سایر دستورات ادمین
    if text == "/logs":
        if await is_group_admin(chat_id, user_id):
            await handle_logs(chat_id, user_id)
        else:
            await send_message(chat_id, "⛔ این دستور فقط برای ادمین‌های گروه در دسترس است.")
        return
        
    if text == "/endvote":
        if await is_group_admin(chat_id, user_id):
            await handle_end_vote(chat_id, user_id)
        else:
            await send_message(chat_id, "⛔ این دستور فقط برای ادمین‌های گروه در دسترس است.")
        return

    if text == "/install":
        if await is_group_admin(chat_id, user_id):
            await handle_install(chat_id, user_id)
        else:
            await send_message(chat_id, "⛔ فقط ادمین گروه می‌تواند ربات را نصب کند.")
        return

    # ۹. دستورات مالک ربات (سوپر ادمین)
    if text.startswith("/setpremium"):
        if is_super_admin(user_id, username):  # <-- username اضافه شد
            await handle_set_premium(chat_id, text, user_id)
        else:
            await send_message(chat_id, "⛔ این دستور فقط برای مالک ربات در دسترس است.")
        return

    # ۱۰. دستورات نیازمند ریپلای
    if text.startswith("/rob"):
        await handle_rob(chat_id, message, user_id, first_name); return
    if text.startswith("/give"):
        await handle_give(chat_id, message, text, user_id, first_name); return

    # ۱۱. دستورات عادی کاربران
    if text.startswith("/start"):
        await handle_start(chat_id, chat_type); return
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
        await handle_group_stats(chat_id, user_id); return
    if text == "/premium":
        await handle_premium_info(chat_id); return
        
    # ۱۲. دستورات اقتصاد
    if text == "/balance":
        await handle_balance(chat_id, user_id, first_name); return
    if text == "/daily":
        await handle_daily(chat_id, user_id, first_name); return
    if text.startswith("/coinflip"):
        await handle_coinflip(chat_id, text, user_id, first_name); return
    if text == "/work":
        await handle_work(chat_id, user_id, first_name); return
    if text == "/shop":
        await handle_shop(chat_id); return
    if text.startswith("/buy"):
        await handle_buy(chat_id, text, user_id, first_name); return
    if text.startswith("/setpremium"):
        if is_super_admin(user_id):
            await handle_set_premium(chat_id, text, user_id)
        else:
            await send_message(chat_id, "⛔ این دستور فقط برای مالک ربات در دسترس است.")
        return
        
    # --- دستور مشاهده آمار ربات ---
    if text == "/botstats":
        if is_super_admin(user_id, username):  # <-- username اضافه شد
            await handle_bot_stats(chat_id, user_id)
        else:
            await send_message(chat_id, "⛔ این دستور فقط برای مالک ربات در دسترس است.")
        return