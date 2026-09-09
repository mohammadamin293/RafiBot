# handlers/ai.py
import time
from core.api_client import send_message, send_typing_action
from services.ai_service import ask_ai
from config import AI_RATE_LIMIT, MAX_AI_PROMPT_LENGTH

# محدودیت نرخ درخواست
_ai_requests = {}  # {user_id: [timestamp1, timestamp2, ...]}

async def check_rate_limit(user_id):
    """بررسی محدودیت نرخ درخواست برای کاربر"""
    now = time.time()
    if user_id not in _ai_requests:
        _ai_requests[user_id] = []
    
    # پاک کردن درخواست‌های قدیمی (بیش از ۱ دقیقه)
    _ai_requests[user_id] = [t for t in _ai_requests[user_id] if now - t < 60]
    
    if len(_ai_requests[user_id]) >= AI_RATE_LIMIT:
        return False
    
    _ai_requests[user_id].append(now)
    return True

async def handle_ask(chat_id, text, user_id):
    if not await check_rate_limit(user_id):
        await send_message(
            chat_id, 
            "⏳ کمی صبر کن و دوباره امتحان کن.\n"
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
            f"⚠️ سوال شما خیلی طولانی است.\n"
            f"حداکثر {MAX_AI_PROMPT_LENGTH} کاراکتر مجاز است."
        )
        return
    
    await send_typing_action(chat_id)
    answer = await ask_ai(question)
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
            f"⚠️ موضوع شما خیلی طولانی است.\n"
            f"حداکثر {MAX_AI_PROMPT_LENGTH} کاراکتر مجاز است."
        )
        return
    
    await send_typing_action(chat_id)
    prompt = f"۳ تا ایده خفن و جذاب برای این موضوع به فارسی بده. فقط اسم‌ها رو با ایموجی لیست کن: {topic}"
    answer = await ask_ai(prompt)
    await send_message(chat_id, f"💡 <b>پیشنهادهای فرانس:</b>\n\n{answer}")

async def handle_challenge(chat_id, user_id):
    if not await check_rate_limit(user_id):
        await send_message(
            chat_id, 
            f"⏳ کمی صبر کن و دوباره امتحان کن.\n"
            f"حداکثر {AI_RATE_LIMIT} درخواست در دقیقه می‌توانی بفرستی."
        )
        return
    
    await send_typing_action(chat_id)
    prompt = (
        "یک چالش فان و گروهی برای نوجوانان در یک پیام‌رسان بساز. "
        "چالش باید کوتاه و قابل انجام باشد. فقط خود چالش را بنویس."
    )
    answer = await ask_ai(prompt)
    await send_message(chat_id, f"🔥 <b>چالش فرانس:</b>\n\n{answer}")

async def handle_direct_chat(chat_id, text, user_id):
    if not await check_rate_limit(user_id):
        await send_message(
            chat_id, 
            f"⏳ کمی صبر کن و دوباره امتحان کن.\n"
            f"حداکثر {AI_RATE_LIMIT} درخواست در دقیقه می‌توانی بفرستی."
        )
        return
        
    if len(text) > MAX_AI_PROMPT_LENGTH:
        await send_message(
            chat_id,
            f"⚠️ پیام شما خیلی طولانی است.\n"
            f"حداکثر {MAX_AI_PROMPT_LENGTH} کاراکتر مجاز است."
        )
        return
        
    await send_typing_action(chat_id)
    answer = await ask_ai(text)
    await send_message(chat_id, f"🇫🇷 <b>فرانس:</b>\n\n{answer}")