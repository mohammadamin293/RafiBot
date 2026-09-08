# services/economy_service.py
import time
from core.database import execute_query

async def get_balance(user_id, chat_id):
    row = await execute_query("SELECT coins FROM user_stats WHERE user_id=? AND chat_id=?", (user_id, chat_id), fetch=True)
    return row[0]["coins"] if row and row[0]["coins"] is not None else 0

async def add_coins(user_id, chat_id, amount):
    # اطمینان از وجود کاربر در دیتابیس
    await execute_query("INSERT OR IGNORE INTO user_stats (user_id, chat_id) VALUES (?, ?)", (user_id, chat_id))
    # آپدیت سکه‌ها (اگه منفی شد جلوگیری می‌کنیم)
    if amount < 0:
        await execute_query("UPDATE user_stats SET coins = MAX(0, COALESCE(coins, 0) + ?) WHERE user_id=? AND chat_id=?", (amount, user_id, chat_id))
    else:
        await execute_query("UPDATE user_stats SET coins = COALESCE(coins, 0) + ? WHERE user_id=? AND chat_id=?", (amount, user_id, chat_id))

async def claim_daily(user_id, chat_id):
    row = await execute_query("SELECT last_daily FROM user_stats WHERE user_id=? AND chat_id=?", (user_id, chat_id), fetch=True)
    now = int(time.time())
    
    if row and row[0]["last_daily"]:
        last_claim = row[0]["last_daily"]
        # 24 ساعت بر حسب ثانیه = 86400
        if now - last_claim < 86400:
            remaining_seconds = 86400 - (now - last_claim)
            return False, remaining_seconds
            
    # اعطای پاداش روزانه (مثلا 100 سکه)
    reward = 100
    await add_coins(user_id, chat_id, reward)
    await execute_query("UPDATE user_stats SET last_daily=? WHERE user_id=? AND chat_id=?", (now, user_id, chat_id))
    return True, reward