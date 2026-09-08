# services/ai_service.py
import httpx
import logging
from urllib.parse import quote
from config import MAJID_API_TOKEN

async def ask_ai(prompt):
    """ارسال درخواست به Majid API Copilot"""
    
    encoded_prompt = quote(prompt)
    # اضافه کردن توکن در صورت وجود (برای اطمینان از عدم محدودیت)
    if MAJID_API_TOKEN:
        url = f"https://api.majidapi.ir/ai/copilot?token={MAJID_API_TOKEN}&q={encoded_prompt}"
    else:
        url = f"https://api.majidapi.ir/ai/copilot?q={encoded_prompt}"
    
    try:
        # تایم‌اوت 30 ثانیه
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(url)
            
            if resp.status_code == 200:
                # تلاش برای پارس کردن به صورت JSON، اگر نشد متن خام را برمی‌گردانیم
                try:
                    data = resp.json()
                    if isinstance(data, dict) and "result" in data:
                        return data["result"]
                    elif isinstance(data, dict) and "response" in data:
                        return data["response"]
                    else:
                        return str(data)
                except Exception:
                    return resp.text
            else:
                # برگرداندن متن خطای دقیق سرور
                logging.error(f"Majid Copilot Error: {resp.status_code} - {resp.text}")
                return f"🤖 خطای سرور (کد {resp.status_code}): {resp.text}"
            
    except Exception as e:
        logging.error(f"Majid Copilot Error: {type(e).__name__} - {e}")
        return f"🤖 خطای شبکه: {type(e).__name__} - {e}"