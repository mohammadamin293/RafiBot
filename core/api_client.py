# core/api_client.py
import httpx
import logging
from config import API_BASE_URL

logging.basicConfig(level=logging.INFO)

# کلاینت httpx را برای استفاده مجدد نگه می‌داریم (تایم‌اوت 60 ثانیه برای جلوگیری از خطای Long Polling)
_client = None

async def get_client():
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(timeout=60.0)
    return _client

async def api_call(method, payload=None):
    client = await get_client()
    url = f"{API_BASE_URL}{method}"
    try:
        response = await client.post(url, json=payload or {})
        data = response.json()
        if not data.get("ok"):
            logging.error(f"API Error {method}: {data}")
        return data
    except Exception as e:
        # فقط خطاهای واقعی را لاگ می‌گیریم
        logging.error(f"Request failed {method}: {e}")
        return None

async def send_message(chat_id, text, reply_markup=None, parse_mode="HTML"):
    payload = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    return await api_call("sendMessage", payload)

async def delete_message(chat_id, message_id):
    return await api_call("deleteMessage", {"chat_id": chat_id, "message_id": message_id})

async def answer_callback(callback_query_id, text=None, show_alert=False):
    """پاسخ به callback query. show_alert=True یعنی به صورت پاپ‌آپ به کاربر نشان داده شود."""
    payload = {"callback_query_id": callback_query_id}
    if text is not None:
        payload["text"] = text
    if show_alert:
        payload["show_alert"] = show_alert
    return await api_call("answerCallbackQuery", payload)

async def send_typing_action(chat_id):
    """نمایش حالت در حال تایپ کردن برای حرفه‌ای‌تر شدن UX"""
    return await api_call("sendChatAction", {"chat_id": chat_id, "action": "typing"})

async def edit_message_text(chat_id, message_id, text, reply_markup=None, parse_mode="HTML"):
    """ویرایش متن یک پیام قبلی برای UX بهتر"""
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
        "parse_mode": parse_mode
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    return await api_call("editMessageText", payload)

async def get_chat_member(chat_id, user_id):
    """گرفتن وضعیت عضویت یک کاربر در گروه (برای چک کردن ادمین بودن)"""
    return await api_call("getChatMember", {"chat_id": chat_id, "user_id": user_id})
