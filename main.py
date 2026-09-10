# main.py
import asyncio
import logging
from core.api_client import api_call, delete_message, send_message
from core.database import init_db, db_commit_task
from services.group_service import is_user_banned, is_user_muted, increment_message_count
from services.xp_service import add_xp, get_user_stats
from handlers.fun import track_user
from handlers.admin import handle_new_member, handle_left_member
from handlers.callbacks import handle_callback_query
from core.router import route_message
from handlers.moderation import check_message_violations
from core.api_client import api_call

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# متن دکمه‌های منو
MENU_BUTTON_TEXTS = ["🎮 بازی‌ها", "🏆 رتبه من", "😂 سرگرمی", "🛡 مدیریت", "⚙️ تنظیمات", "❓ راهنما", "💰 اقتصاد"]

# صف پردازش پیام‌ها و دکمه‌ها
message_queue = asyncio.Queue()

async def process_message(message):
    chat_id = message["chat"]["id"]
    text = message.get("text", "")
    user_id = message["from"]["id"]
    first_name = message["from"].get("first_name", "کاربر")

    # عضو جدید
    if "new_chat_members" in message:
        for new_member in message["new_chat_members"]:
            if not new_member.get("is_bot"):
                await handle_new_member(chat_id, new_member)
        return
        
    # خروج عضو
    if "left_chat_member" in message:
        left_member = message["left_chat_member"]
        if not left_member.get("is_bot"):
            await handle_left_member(chat_id, left_member)
        return

    # بررسی بن و میوت
    if await is_user_banned(user_id, chat_id):
        await delete_message(chat_id, message["message_id"])
        return
        
    if await is_user_muted(user_id, chat_id):
        await delete_message(chat_id, message["message_id"])
        return

    # بررسی تخلفات
    if await check_message_violations(chat_id, message):
        return

    # افزودن XP برای پیام‌های عادی
    if not text.startswith("/") and text not in MENU_BUTTON_TEXTS:
        leveled_up = await add_xp(user_id, chat_id, 5)
        await increment_message_count(chat_id)
        await track_user(chat_id, user_id, first_name)
        await track_user(chat_id, user_id, first_name, username)
        
        # پیام سطح‌آپ
        if leveled_up:
            stats = await get_user_stats(user_id, chat_id)
            await send_message(
                chat_id, 
                f"🎉 تبریک <b>{first_name}</b>!\n"
                f"شما به <b>Level {stats['level']}</b> رسیدید! 🚀"
            )

    # هدایت به مسیریاب
    await route_message(message)

async def worker():
    """کارگر برای پردازش آیتم‌های داخل صف"""
    while True:
        item_type, item_data = await message_queue.get()
        try:
            if item_type == "message":
                await process_message(item_data)
            elif item_type == "callback":
                await handle_callback_query(item_data)
        except Exception as e:
            logging.error(f"Error processing {item_type}: {e}")
        finally:
            message_queue.task_done()

async def main():
    logging.info("Initializing Database...")
    await init_db()
    
    # ---- تنظیم منوی کشویی کامندها (دکمه پایین چت) ----
    commands = [
        {"command": "start", "description": "شروع کار با بات"},
        {"command": "help", "description": "دریافت راهنمای کامل"},
        {"command": "profile", "description": "مشاهده پروفایل و امتیاز"},
        {"command": "top", "description": "لیست برترین اعضا"},
        {"command": "balance", "description": "مشاهده موجودی سکه"},
        {"command": "daily", "description": "دریافت پاداش روزانه"},
        {"command": "work", "description": "کار کردن برای کسب سکه"},
        {"command": "coinflip", "description": "شرط‌بندی شیر یا خط"},
        {"command": "rob", "description": "دزدی سکه (ریپلای روی کاربر)"},
        {"command": "give", "description": "هدیه دادن سکه (ریپلای روی کاربر)"},
        {"command": "shop", "description": "مشاهده فروشگاه"},
        {"command": "buy", "description": "خرید آیتم از فروشگاه"},
        {"command": "trivia", "description": "شروع مسابقه عمومی"},
        {"command": "who", "description": "انتخاب یک نفر تصادفی"},
        {"command": "vote", "description": "ایجاد نظرسنجی"},
        {"command": "endvote", "description": "پایان نظرسنجی فعال"},
        {"command": "truth", "description": "سوال حقیقت"},
        {"command": "dare", "description": "چالش جرئت"},
        {"command": "rules", "description": "مشاهده قوانین گروه"},
        {"command": "warn", "description": "اخطار به کاربر (ریپلای)"},
        {"command": "mute", "description": "میوت کردن (ریپلای)"},
        {"command": "unmute", "description": "آزاد کردن (ریپلای)"},
        {"command": "ban", "description": "بن مجازی (ریپلای)"},
        {"command": "kick", "description": "اخراج از گروه (ریپلای)"},
        {"command": "filter", "description": "مسدود کردن کلمه"},
        {"command": "setwelcome", "description": "تنظیم خوش‌آمدگویی"},
        {"command": "setrules", "description": "تنظیم قوانین گروه"},
        {"command": "setantilink", "description": "روشن/خاموش آنتی‌لینک"},
        {"command": "logs", "description": "اقدامات ادمین‌ها"},
        {"command": "install", "description": "نصب ربات در گروه"},
        {"command": "premium", "description": "وضعیت پریمیوم گروه"},
        {"command": "botstats", "description": "آمار کلی ربات (فقط مالک)"}
    ]
    await api_call("setMyCommands", {"commands": commands})
    logging.info("Bot commands menu updated!")
    # ------------------------------------------------
    
    # شروع تایمر ذخیره دیتابیس
    asyncio.create_task(db_commit_task())
    
    # شروع ۳ کارگر برای پردازش موازی
    for _ in range(3):
        asyncio.create_task(worker())
    
    logging.info("RafiBot Async is starting...")
    offset = 0
    
    while True:
        try:
            payload = {
                "offset": offset, 
                "timeout": 30, 
                "allowed_updates": ["message", "callback_query"]
            }
            updates = await api_call("getUpdates", payload)
            
            # بررسی اینکه updates معتبر است و result دارد
            if updates and isinstance(updates, dict) and updates.get("ok") and updates.get("result"):
                for update in updates["result"]:
                    offset = update["update_id"] + 1
                    if "message" in update:
                        await message_queue.put(("message", update["message"]))
                    elif "edited_message" in update:
                        await message_queue.put(("message", update["edited_message"]))
                    elif "callback_query" in update:
                        await message_queue.put(("callback", update["callback_query"]))
            else:
                # اگر خطایی از API برگشت یا result خالی بود
                error_msg = updates.get("description", "Unknown error") if updates else "No response"
                logging.warning(f"No updates or API error: {error_msg}")
                await asyncio.sleep(1)
                
        except Exception as e:
            logging.error(f"Error in main loop: {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())