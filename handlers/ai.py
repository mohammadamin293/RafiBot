# handlers/ai.py
import time
import asyncio
from core.api_client import send_message, send_typing_action, edit_message_text
from services.ai_service import ask_ai
from config import AI_RATE_LIMIT, MAX_AI_PROMPT_LENGTH

# دیتابیس موقت برای محدودیت نرخ درخواست هر کاربر
_ai_requests = {}

async def check_rate_limit(user_id):
    """بررسی محدودیت نرخ درخواست برای کاربر"""
    now = time.time()
    if user_id not in _ai_requests:
        _ai_requests[user_id] = []
    
    _ai_requests[user_id] = [t for t in _ai_requests[user_id] if now - t < 60]
    
    if len(_ai_requests[user_id]) >= AI_RATE_LIMIT:
        return False
    
    _ai_requests[user_id].append(now)
    return True

async def handle_ask(chat_id, text, user_id):
    if not await check_rate_limit(user_id):
        await send_message(
            chat_id, 
            f"⏳ کمی صبر کن و دوباره امتحان کن.\n"
            f"حداکثر {AI_RATE_LIMIT} سوال در دقیقه می‌توانی بپرسی."
        )
        return
        
    parts = text.split(" ", 1)
    if len(parts) < 2:
        await send_message(
            chat_id, 
            "❌ استفاده: /ask [سوال شما]\n"
            "مثال: /ask پایتخت ژاپن کجاست؟"
        )
        return
        
    question = parts[1].strip()
    if len(question) > MAX_AI_PROMPT_LENGTH:
        await send_message(
            chat_id,
            f"⚠️ سوال شما خیلی طولانی است.\nحداکثر {MAX_AI_PROMPT_LENGTH} کاراکتر مجاز است."
        )
        return
    
    await send_typing_action(chat_id)
    
    # ارسال پیام "در صف هستید"
    wait_msg = await send_message(chat_id, "⏳ درخواست شما در صف پردازش هوش مصنوعی قرار گرفت...")
    wait_msg_id = wait_msg.get("result", {}).get("message_id") if wait_msg and wait_msg.get("ok") else None
    
    answer = await ask_ai(question)
    
    # ویرایش پیام "در صف" و قرار دادن جواب نهایی
    if wait_msg_id:
        await edit_message_text(chat_id, wait_msg_id, f"🇫🇷 <b>فرانس:</b>\n\n{answer}")
    else:
        await send_message(chat_id, f"🇫🇷 <b>فرانس:</b>\n\n{answer}")

async def handle_suggest(chat_id, text, user_id):
    if not await check_rate_limit(user_id):
        await send_message(
            chat_id, 
            f"⏳ کمی صبر کن و دوباره امتحان کن.\n"
            f"حداکثر {AI_RATE_LIMIT} درخواست در دقیقه می‌توانی بفرستی."
        )
        return
        
    parts = text.split(" ", 1)
    if len(parts) < 2:
        await send_message(
            chat_id, 
            "❌ استفاده: /suggest [موضوع]\n"
            "مثال: /suggest اسم تیم گیمینگ"
        )
        return
        
    topic = parts[1].strip()
    if len(topic) > MAX_AI_PROMPT_LENGTH:
        await send_message(
            chat_id,
            f"⚠️ موضوع شما خیلی طولانی است.\nحداکثر {MAX_AI_PROMPT_LENGTH} کاراکتر مجاز است."
        )
        return
    
    await send_typing_action(chat_id)
    wait_msg = await send_message(chat_id, "⏳ در حال تولید ایده‌ها توسط فرانس...")
    wait_msg_id = wait_msg.get("result", {}).get("message_id") if wait_msg and wait_msg.get("ok") else None
    
    prompt = f"۳ تا ایده خفن و جذاب برای این موضوع به فارسی بده. فقط اسم‌ها رو با ایموجی لیست کن: {topic}"
    answer = await ask_ai(prompt)
    
    if wait_msg_id:
        await edit_message_text(chat_id, wait_msg_id, f"💡 <b>پیشنهادهای فرانس:</b>\n\n{answer}")
    else:
        await send_message(chat_id, f"💡 <b>پیشنهادهای فرانس:</b>\n\n{answer}")

async def handle_challenge(chat_id, user_id):
    if not await check_rate_limit(user_id):
        await send_message(
            chat_id, 
            f"⏳ کمی صبر کن و دوباره امتحان کن.\n"
            f"حداکثر {AI_RATE_LIMIT} درخواست در دقیقه."
        )
        return
    
    await send_typing_action(chat_id)
    wait_msg = await send_message(chat_id, "⏳ در حال ساخت چالش...")
    wait_msg_id = wait_msg.get("result", {}).get("message_id") if wait_msg and wait_msg.get("ok") else None
    
    prompt = "یک چالش فان و گروهی برای نوجوانان در یک پیام‌رسان بساز. چالش باید کوتاه و قابل انجام باشد. فقط خود چالش را بنویس."
    answer = await ask_ai(prompt)
    
    if wait_msg_id:
        await edit_message_text(chat_id, wait_msg_id, f"🔥 <b>چالش فرانس:</b>\n\n{answer}")
    else:
        await send_message(chat_id, f"🔥 <b>چالش فرانس:</b>\n\n{answer}")

async def handle_direct_chat(chat_id, text, user_id):
    if not await check_rate_limit(user_id):
        await send_message(
            chat_id, 
            f"⏳ کمی صبر کن و دوباره امتحان کن.\n"
            f"حداکثر {AI_RATE_LIMIT} درخواست در دقیقه."
        )
        return
        
    if len(text) > MAX_AI_PROMPT_LENGTH:
        await send_message(
            chat_id,
            f"⚠️ پیام شما خیلی طولانی است.\nحداکثر {MAX_AI_PROMPT_LENGTH} کاراکتر مجاز است."
        )
        return
        
    await send_typing_action(chat_id)
    answer = await ask_ai(text)
    await send_message(chat_id, f"🇫🇷 <b>فرانس:</b>\n\n{answer}")