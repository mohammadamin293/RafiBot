# main.py
import asyncio
import logging
from core.api_client import api_call, delete_message
from core.database import init_db
from services.group_service import is_user_banned, increment_message_count
from services.xp_service import add_xp
from handlers.fun import track_user
from handlers.admin import handle_new_member, handle_left_member
from handlers.callbacks import handle_callback_query
from core.router import route_message
from handlers.moderation import check_message_violations

logging.basicConfig(level=logging.INFO)

MENU_BUTTON_TEXTS = ["🎮 بازی‌ها", "🏆 رتبه من", "😂 فان", "🛡 مدیریت", "⚙️ تنظیمات", "❓ راهنما"]

async def process_message(message):
    chat_id = message["chat"]["id"]
    text = message.get("text", "")
    user_id = message["from"]["id"]
    first_name = message["from"].get("first_name", "کاربر")

    # ۱. بررسی ورود و خروج اعضا
    if "new_chat_members" in message:
        for new_member in message["new_chat_members"]:
            if not new_member.get("is_bot"):
                await handle_new_member(chat_id, new_member.get("first_name", "کاربر"))
        return
    if "left_chat_member" in message:
        left_member = message["left_chat_member"]
        if not left_member.get("is_bot"):
            await handle_left_member(chat_id, left_member.get("first_name", "کاربر"))
        return

    # ۲. بررسی Ban مجازی
    if await is_user_banned(user_id, chat_id):
        await delete_message(chat_id, message["message_id"])
        return

    # ۳. بررسی تخلفات (لینک، فیلتر، اسپم)
    if await check_message_violations(chat_id, message):
        return

    # ۴. سیستم XP و شمارش پیام
    if not text.startswith("/") and text not in MENU_BUTTON_TEXTS:
        await add_xp(user_id, chat_id, 5)
        await increment_message_count(chat_id)
        await track_user(chat_id, user_id, first_name)

    # ۵. مسیریابی به هندلر مربوطه
    await route_message(message)

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