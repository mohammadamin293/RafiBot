# services/group_service.py
import time
from core.database import execute_query, _db_conn

_settings_cache = {}
_filters_cache = {}

async def ensure_group_exists(chat_id):
    await execute_query("INSERT OR IGNORE INTO groups (chat_id) VALUES (?)", (chat_id,))

async def get_group_settings(chat_id):
    """گرفتن تنظیمات با کش ۵ دقیقه‌ای"""
    current_time = time.time()
    if chat_id in _settings_cache and current_time - _settings_cache[chat_id]["time"] < 300:
        return _settings_cache[chat_id]["data"]
        
    await ensure_group_exists(chat_id)
    row = await execute_query("SELECT antilink, antispam, filter_enabled, welcome_enabled, lock_links, lock_photos, lock_videos, lock_stickers, lock_forward FROM groups WHERE chat_id=?", (chat_id,), fetch=True)
    data = dict(row[0]) if row else {}
    _settings_cache[chat_id] = {"time": current_time, "data": data}
    return data

async def toggle_setting(chat_id, setting_name):
    """روشن یا خاموش کردن تنظیمات و ذخیره فوری"""
    await ensure_group_exists(chat_id)
    row = await execute_query(f"SELECT {setting_name} FROM groups WHERE chat_id=?", (chat_id,), fetch=True)
    current = bool(row[0][setting_name]) if row else False
    new_val = 0 if current else 1
    await execute_query(f"UPDATE groups SET {setting_name}=? WHERE chat_id=?", (new_val, chat_id))
    
    # ذخیره فوری در دیتابیس (Commit)
    if _db_conn:
        await _db_conn.commit()
    
    # آپدیت کش
    if chat_id in _settings_cache:
        _settings_cache[chat_id]["data"][setting_name] = new_val
    else:
        _settings_cache[chat_id] = {"time": time.time(), "data": {setting_name: new_val}}
        
    return new_val

async def get_filters(chat_id):
    current_time = time.time()
    if chat_id in _filters_cache and current_time - _filters_cache[chat_id]["time"] < 300:
        return _filters_cache[chat_id]["data"]
        
    result = await execute_query("SELECT word FROM filters WHERE chat_id=?", (chat_id,), fetch=True)
    data = [row["word"] for row in result] if result else []
    _filters_cache[chat_id] = {"time": current_time, "data": data}
    return data

async def add_filter(chat_id, word):
    await execute_query("INSERT OR IGNORE INTO filters (chat_id, word) VALUES (?, ?)", (chat_id, word.lower()))
    if _db_conn:
        await _db_conn.commit()
    if chat_id in _filters_cache: 
        del _filters_cache[chat_id]

async def is_user_banned(user_id, chat_id):
    result = await execute_query("SELECT is_banned FROM users WHERE user_id=? AND chat_id=?", (user_id, chat_id), fetch=True)
    return bool(result and result[0]["is_banned"])

async def ban_user(user_id, chat_id):
    await execute_query("INSERT OR REPLACE INTO users (user_id, chat_id, is_banned) VALUES (?, ?, 1)", (user_id, chat_id))
    if _db_conn:
        await _db_conn.commit()

async def add_warning(user_id, chat_id, reason):
    await execute_query("INSERT INTO warnings (chat_id, user_id, reason) VALUES (?, ?, ?)", (chat_id, user_id, reason))
    if _db_conn:
        await _db_conn.commit()

async def get_warnings_count(user_id, chat_id):
    result = await execute_query("SELECT COUNT(*) as count FROM warnings WHERE user_id=? AND chat_id=?", (user_id, chat_id), fetch=True)
    return result[0]["count"] if result else 0

async def set_welcome(chat_id, text):
    await ensure_group_exists(chat_id)
    await execute_query("UPDATE groups SET welcome=? WHERE chat_id=?", (text, chat_id))
    if _db_conn:
        await _db_conn.commit()

async def get_welcome(chat_id):
    await ensure_group_exists(chat_id)
    row = await execute_query("SELECT welcome FROM groups WHERE chat_id=?", (chat_id,), fetch=True)
    if row and row[0]["welcome"]:
        return row[0]["welcome"]
    return None

async def set_rules(chat_id, text):
    await ensure_group_exists(chat_id)
    await execute_query("UPDATE groups SET rules=? WHERE chat_id=?", (text, chat_id))
    if _db_conn:
        await _db_conn.commit()

async def get_rules(chat_id):
    await ensure_group_exists(chat_id)
    row = await execute_query("SELECT rules FROM groups WHERE chat_id=?", (chat_id,), fetch=True)
    if row and row[0]["rules"]:
        return row[0]["rules"]
    return None

async def is_group_premium(chat_id):
    await ensure_group_exists(chat_id)
    row = await execute_query("SELECT is_premium FROM groups WHERE chat_id=?", (chat_id,), fetch=True)
    return bool(row and row[0]["is_premium"])

async def set_group_premium(chat_id, status):
    await ensure_group_exists(chat_id)
    await execute_query("UPDATE groups SET is_premium=? WHERE chat_id=?", (1 if status else 0, chat_id))
    if _db_conn:
        await _db_conn.commit()

async def get_filter_count(chat_id):
    row = await execute_query("SELECT COUNT(*) as count FROM filters WHERE chat_id=?", (chat_id,), fetch=True)
    return row[0]["count"] if row else 0

async def is_antilink_enabled(chat_id):
    await ensure_group_exists(chat_id)
    row = await execute_query("SELECT antilink FROM groups WHERE chat_id=?", (chat_id,), fetch=True)
    if row and row[0]["antilink"] is not None:
        return bool(row[0]["antilink"])
    return True

async def set_antilink(chat_id, enabled):
    await ensure_group_exists(chat_id)
    await execute_query("UPDATE groups SET antilink=? WHERE chat_id=?", (1 if enabled else 0, chat_id))
    if _db_conn:
        await _db_conn.commit()

async def increment_message_count(chat_id):
    await ensure_group_exists(chat_id)
    await execute_query("UPDATE groups SET total_messages = COALESCE(total_messages, 0) + 1 WHERE chat_id=?", (chat_id,))

async def get_message_count(chat_id):
    row = await execute_query("SELECT total_messages FROM groups WHERE chat_id=?", (chat_id,), fetch=True)
    return row[0]["total_messages"] if row and row[0]["total_messages"] is not None else 0

async def mute_user(user_id, chat_id, duration_seconds):
    muted_until = int(time.time()) + duration_seconds
    await execute_query("INSERT OR REPLACE INTO users (user_id, chat_id, is_banned, muted_until) VALUES (?, ?, 0, ?)", (user_id, chat_id, muted_until))
    if _db_conn:
        await _db_conn.commit()

async def unmute_user(user_id, chat_id):
    await execute_query("UPDATE users SET muted_until=0 WHERE user_id=? AND chat_id=?", (user_id, chat_id))
    if _db_conn:
        await _db_conn.commit()

async def is_user_muted(user_id, chat_id):
    row = await execute_query("SELECT muted_until FROM users WHERE user_id=? AND chat_id=?", (user_id, chat_id), fetch=True)
    if row and row[0]["muted_until"] and int(row[0]["muted_until"]) > int(time.time()):
        return True
    return False

async def add_mod_log(chat_id, admin_id, action, target_id, reason):
    await execute_query(
        "INSERT INTO moderation_logs (chat_id, admin_id, action, target_id, reason) VALUES (?, ?, ?, ?, ?)",
        (chat_id, admin_id, action, target_id, reason)
    )
    if _db_conn:
        await _db_conn.commit()

async def get_mod_logs(chat_id, limit=5):
    rows = await execute_query("SELECT * FROM moderation_logs WHERE chat_id=? ORDER BY date DESC LIMIT ?", (chat_id, limit), fetch=True)
    return rows


async def get_bot_global_stats():
    """گرفتن لیست گروه‌ها و کاربران برای مالک ربات"""
    groups = await execute_query("SELECT chat_id FROM groups", fetch=True)
    users = await execute_query("SELECT user_id, username FROM user_stats", fetch=True)
    
    return groups, users