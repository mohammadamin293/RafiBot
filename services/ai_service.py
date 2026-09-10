# services/ai_service.py
import httpx
import logging
import asyncio
import json
from config import AVALAI_API_KEY

AVALAI_BASE_URL = "https://api.avalai.ir/v1"
_ai_client = httpx.AsyncClient(timeout=30.0)

# ایجاد یک Semaphore برای محدود کردن درخواست‌های همزمان (فقط ۲ درخواست همزمان)
_ai_semaphore = asyncio.Semaphore(2)

async def ask_ai(prompt):
    """ارسال درخواست به AvalAI با سیستم محدودیت همزمانی (صف)"""
    async with _ai_semaphore:
        headers = {
            "Authorization": f"Bearer {AVALAI_API_KEY}",
            "Content-Type": "application/json"
        }
        
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
            
            if resp.status_code == 429:
                logging.error("AvalAI Rate Limit Hit (429)")
                return "🇫🇷 فرانس الان مغزش خیلی درگیره! چند ثانیه دیگه دوباره سوالو بپرس."
            
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"]
            else:
                logging.error(f"AvalAI Error: {resp.status_code} - {resp.text}")
                return f"🇫🇷 فرانس الان جواب نمیده (کد خطا: {resp.status_code})."
                
        except httpx.TimeoutException:
            logging.error("AvalAI Timeout")
            return "⏳ پاسخ هوش مصنوعی طولانی شد، دوباره امتحان کن."
            
        except Exception as e:
            logging.error(f"AvalAI Error: {type(e).__name__} - {e}")
            return "🇫🇷 فرانس الان به اینترنت وصل نمیشه."


async def generate_trivia_question():
    """تولید سوال مسابقه توسط هوش مصنوعی"""
    # استفاده از صف برای جلوگیری از هنگی
    async with _ai_semaphore:
        prompt = (
            "یک سوال دانش عمومی جذاب و متنوع به زبان فارسی طراحی کن. سوال باید ۴ گزینه داشته باشد. "
            "لطفاً دقیقاً و فقط در فرمت JSON زیر پاسخ بده و هیچ متن یا توضیح اضافه‌ای ننویس:\n"
            '{"question": "متن سوال", "options": ["گزینه ۱", "گزینه ۲", "گزینه ۳", "گزینه ۴"], "answer": 0}\n'
            "مقدار answer باید عدد ایندکس گزینه درست باشد (از 0 تا 3)."
        )
        
        try:
            response = await ask_ai(prompt)
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            response = response.strip()
            
            data = json.loads(response)
            
            if "question" in data and "options" in data and "answer" in data:
                if len(data["options"]) == 4 and int(data["answer"]) in [0, 1, 2, 3]:
                    data["answer"] = int(data["answer"])
                    return data
        except Exception as e:
            logging.error(f"Trivia AI Error: {e}")
            
    return None