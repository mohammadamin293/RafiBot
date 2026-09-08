# services/group_service.py
from core.database import execute_query

async def is_user_banned(user_id, chat_id):
    result = await execute_query("SELECT is_banned FROM users WHERE user_id=? AND chat_id=?", (user_id, chat_id), fetch=True)
    return bool(result and result[0]["is_banned"])

async def ban_user(user_id, chat_id):
    await execute_query("INSERT OR REPLACE INTO users (user_id, chat_id, is_banned) VALUES (?, ?, 1)", (user_id, chat_id))

async def add_warning(user_id, chat_id, reason):
    await execute_query("INSERT INTO warnings (chat_id, user_id, reason) VALUES (?, ?, ?)", (chat_id, user_id, reason))

async def get_warnings_count(user_id, chat_id):
    result = await execute_query("SELECT COUNT(*) as count FROM warnings WHERE user_id=? AND chat_id=?", (user_id, chat_id), fetch=True)
    return result[0]["count"] if result else 0

async def add_filter(chat_id, word):
    await execute_query("INSERT OR IGNORE INTO filters (chat_id, word) VALUES (?, ?)", (chat_id, word.lower()))

async def get_filters(chat_id):
    result = await execute_query("SELECT word FROM filters WHERE chat_id=?", (chat_id,), fetch=True)
    return [row["word"] for row in result] if result else []

# --- توابع مرحله ۴ ---

async def ensure_group_exists(chat_id):
    """اطمینان از اینکه گروه در دیتابیس ثبت شده است"""
    await execute_query("INSERT OR IGNORE INTO groups (chat_id) VALUES (?)", (chat_id,))

async def set_welcome(chat_id, text):
    await ensure_group_exists(chat_id)
    await execute_query("UPDATE groups SET welcome=? WHERE chat_id=?", (text, chat_id))

async def get_welcome(chat_id):
    await ensure_group_exists(chat_id)
    row = await execute_query("SELECT welcome FROM groups WHERE chat_id=?", (chat_id,), fetch=True)
    if row and row[0]["welcome"]:
        return row[0]["welcome"]
    return None

async def set_rules(chat_id, text):
    await ensure_group_exists(chat_id)
    await execute_query("UPDATE groups SET rules=? WHERE chat_id=?", (text, chat_id))

async def get_rules(chat_id):
    await ensure_group_exists(chat_id)
    row = await execute_query("SELECT rules FROM groups WHERE chat_id=?", (chat_id,), fetch=True)
    if row and row[0]["rules"]:
        return row[0]["rules"]
    return None
# services/group_service.py (اضافه شود به انتهای فایل)

async def is_group_premium(chat_id):
    await ensure_group_exists(chat_id)
    row = await execute_query("SELECT is_premium FROM groups WHERE chat_id=?", (chat_id,), fetch=True)
    return bool(row and row[0]["is_premium"])

async def set_group_premium(chat_id, status):
    await ensure_group_exists(chat_id)
    await execute_query("UPDATE groups SET is_premium=? WHERE chat_id=?", (1 if status else 0, chat_id))

async def get_filter_count(chat_id):
    row = await execute_query("SELECT COUNT(*) as count FROM filters WHERE chat_id=?", (chat_id,), fetch=True)
    return row[0]["count"] if row else 0

# --- آنتی‌لینک قابل تنظیم (قبلاً ستون antilink توی دیتابیس بود ولی جایی خونده نمی‌شد) ---

async def is_antilink_enabled(chat_id):
    await ensure_group_exists(chat_id)
    row = await execute_query("SELECT antilink FROM groups WHERE chat_id=?", (chat_id,), fetch=True)
    if row and row[0]["antilink"] is not None:
        return bool(row[0]["antilink"])
    return True  # پیش‌فرض: فعال

async def set_antilink(chat_id, enabled):
    await ensure_group_exists(chat_id)
    await execute_query("UPDATE groups SET antilink=? WHERE chat_id=?", (1 if enabled else 0, chat_id))

# --- شمارش واقعی پیام‌ها برای آمار گروه ---

async def increment_message_count(chat_id):
    await ensure_group_exists(chat_id)
    await execute_query("UPDATE groups SET total_messages = COALESCE(total_messages, 0) + 1 WHERE chat_id=?", (chat_id,))

async def get_message_count(chat_id):
    row = await execute_query("SELECT total_messages FROM groups WHERE chat_id=?", (chat_id,), fetch=True)
    return row[0]["total_messages"] if row and row[0]["total_messages"] is not None else 0
# services/group_service.py (اضافه شود به انتهای فایل)

async def get_group_settings(chat_id):
    """گرفتن تمام تنظیمات یک گروه"""
    await ensure_group_exists(chat_id)
    row = await execute_query("SELECT antilink, antispam, filter_enabled, welcome_enabled FROM groups WHERE chat_id=?", (chat_id,), fetch=True)
    return dict(row[0]) if row else {}

async def toggle_setting(chat_id, setting_name):
    """روشن یا خاموش کردن یک تنظیم خاص"""
    await ensure_group_exists(chat_id)
    # خواندن وضعیت فعلی
    row = await execute_query(f"SELECT {setting_name} FROM groups WHERE chat_id=?", (chat_id,), fetch=True)
    current = bool(row[0][setting_name]) if row else False
    new_val = 0 if current else 1
    # آپدیت در دیتابیس
    await execute_query(f"UPDATE groups SET {setting_name}=? WHERE chat_id=?", (new_val, chat_id))
    return new_val