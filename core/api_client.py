# core/api_client.py
import httpx
import logging
from config import API_BASE_URL

logging.basicConfig(level=logging.INFO)

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
            error_msg = data.get("description", "Unknown error")
            logging.error(f"API Error {method}: {error_msg}")
            return {"ok": False, "description": error_msg}
        return data
    except httpx.TimeoutException:
        logging.error(f"Request timeout {method}")
        return {"ok": False, "description": "⏳ زمان پاسخگویی سرور به پایان رسید"}
    except Exception as e:
        logging.error(f"Request failed {method}: {e}")
        return {"ok": False, "description": "❌ اتصال به سرور برقرار نشد"}

async def send_message(chat_id, text, reply_markup=None, parse_mode="HTML", reply_to_message_id=None):
    payload = {
        "chat_id": chat_id, 
        "text": text, 
        "parse_mode": parse_mode
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    if reply_to_message_id:
        payload["reply_to_message_id"] = reply_to_message_id
    return await api_call("sendMessage", payload)

async def delete_message(chat_id, message_id):
    return await api_call("deleteMessage", {"chat_id": chat_id, "message_id": message_id})

async def answer_callback(callback_query_id, text=None, show_alert=False, cache_time=None):
    payload = {"callback_query_id": callback_query_id}
    if text is not None:
        payload["text"] = text
    if show_alert:
        payload["show_alert"] = show_alert
    if cache_time is not None:
        payload["cache_time"] = cache_time
    return await api_call("answerCallbackQuery", payload)

async def send_typing_action(chat_id):
    return await api_call("sendChatAction", {"chat_id": chat_id, "action": "typing"})

async def edit_message_text(chat_id, message_id, text, reply_markup=None, parse_mode="HTML"):
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
    return await api_call("getChatMember", {"chat_id": chat_id, "user_id": user_id})

async def join_chat(chat_id_or_link):
    return await api_call("joinChat", {"chat_id": chat_id_or_link})

async def get_chat_member_count(chat_id):
    return await api_call("getChatMemberCount", {"chat_id": chat_id})

async def kick_chat_member(chat_id, user_id):
    return await api_call("kickChatMember", {"chat_id": chat_id, "user_id": user_id})