import httpx
import logging
from config import AVALAI_API_KEY

AVALAI_BASE_URL = "https://api.avalai.ir/v1"
# کلاینت دائمی برای reuse کردن کانکشن‌ها
_ai_client = httpx.AsyncClient(timeout=30.0)

async def ask_ai(prompt):
    """ارسال درخواست به AvalAI با شخصیت فرانس"""
    headers = {
        "Authorization": f"Bearer {AVALAI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # معرفی شخصیت فرانس به هوش مصنوعی
    system_prompt = "Your name is France (فرانس). You are a fun, smart, and friendly AI assistant inside a Telegram/Soroush group bot. Answer in Persian concisely and casually."
    
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 800
    }
    
    try:
        resp = await _ai_client.post(f"{AVALAI_BASE_URL}/chat/completions", headers=headers, json=payload)
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"]
        else:
            logging.error(f"AvalAI Error: {resp.status_code} - {resp.text}")
            return f"🇫🇷 فرانس الان جواب نمیده (کد خطا: {resp.status_code})."
    except Exception as e:
        logging.error(f"AvalAI Error: {type(e).__name__} - {e}")
        return "🇫🇷 فرانس الان به اینترنت وصل نمیشه."