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
    row = await execute_query("SELECT last_daily, daily_streak FROM user_stats WHERE user_id=? AND chat_id=?", (user_id, chat_id), fetch=True)
    now = int(time.time())
    
    if row and row[0]["last_daily"]:
        last_claim = row[0]["last_daily"]
        current_streak = row[0]["daily_streak"]
        
        # ۲۴ ساعت بر حسب ثانیه
        if now - last_claim < 86400:
            remaining_seconds = 86400 - (now - last_claim)
            return False, remaining_seconds, current_streak
            
        # اگر بین ۲۴ تا ۴۸ ساعت گذشته باشه، استریک حفظ میشه
        if now - last_claim < 172800:
            new_streak = current_streak + 1
        else:
            new_streak = 1 # اگر بیشتر از ۴۸ ساعت گذشت، استریک ریست میشه
    else:
        new_streak = 1 # اولین بار
        
    # محاسبه جایزه: ۱۰۰ سکه پایه + ۲۰ سکه برای هر روز استریک
    reward = 100 + (new_streak - 1) * 20
    await add_coins(user_id, chat_id, reward)
    await execute_query("UPDATE user_stats SET last_daily=?, daily_streak=? WHERE user_id=? AND chat_id=?", (now, new_streak, user_id, chat_id))
    
    # چک کردن دستاورد استریک ۷ روزه
    if new_streak == 7:
        await add_achievement(user_id, chat_id, "🔥 استریک ۷ روزه")
        
    return True, reward, new_streak

async def add_achievement(user_id, chat_id, badge):
    """اعطای یک دستاورد به کاربر"""
    await execute_query("INSERT OR IGNORE INTO user_achievements (user_id, chat_id, badge) VALUES (?, ?, ?)", (user_id, chat_id, badge))

async def get_achievements(user_id, chat_id):
    """گرفتن لیست دستاوردهای کاربر"""
    rows = await execute_query("SELECT badge FROM user_achievements WHERE user_id=? AND chat_id=?", (user_id, chat_id), fetch=True)
    return [row["badge"] for row in rows] if rows else []