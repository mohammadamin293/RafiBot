# handlers/ai.py
from core.api_client import send_message
from services.ai_service import ask_ai

async def handle_ask(chat_id, text):
    """پاسخ به سوالات عمومی کاربران"""
    parts = text.split(" ", 1)
    if len(parts) < 2:
        await send_message(chat_id, "❌ استفاده: /ask [سوال شما]\nمثال: /ask پایتخت ژاپن کجاست؟")
        return
        
    question = parts[1]
    # ارسال فوری پیام "در حال فکر کردن"
    await send_message(chat_id, "🤖 هوش مصنوعی در حال فکر کردن است...")
    
    answer = await ask_ai(question)
    await send_message(chat_id, f"🤖 <b>جواب AI:</b>\n\n{answer}")

async def handle_suggest(chat_id, text):
    """پیشنهاد اسم گروه، تیم یا ایده"""
    parts = text.split(" ", 1)
    if len(parts) < 2:
        await send_message(chat_id, "❌ استفاده: /suggest [موضوع]\nمثال: /suggest اسم تیم گیمینگ")
        return
        
    topic = parts[1]
    await send_message(chat_id, "💡 در حال تولید ایده‌های خفن...")
    
    prompt = f"۳ تا ایده خفن و جذاب برای این موضوع به فارسی بده. فقط اسم‌ها رو با ایموجی لیست کن: {topic}"
    answer = await ask_ai(prompt)
    
    await send_message(chat_id, f"💡 <b>پیشنهادهای AI:</b>\n\n{answer}")

async def handle_challenge(chat_id):
    """ساخت یک چالش تصادفی گروهی"""
    await send_message(chat_id, "🔥 در حال ساخت یک چالش جدید...")
    
    prompt = "یک چالش فان و گروهی برای نوجوانان در یک پیام‌رسان بساز. چالش باید کوتاه و قابل انجام باشد. فقط خود چالش را بنویس."
    answer = await ask_ai(prompt)
    
    await send_message(chat_id, f"🔥 <b>چالش روز:</b>\n\n{answer}")