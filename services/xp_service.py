# services/xp_service.py
import time
from core.database import execute_query

async def add_xp(user_id, chat_id, amount=5):
    """افزودن XP با محدودیت زمانی (ضد اسپم)"""
    current_time = int(time.time())
    
    # بررسی آخرین زمان دریافت امتیاز
    row = await execute_query("SELECT last_xp_time, xp, level FROM user_stats WHERE user_id=? AND chat_id=?", (user_id, chat_id), fetch=True)
    
    if row:
        last_time = row[0]["last_xp_time"]
        xp = row[0]["xp"]
        level = row[0]["level"]
        
        # اگر کاربر در 30 ثانیه گذشته امتیاز گرفته، امتیاز ندهد (ضد اسپم)
        if current_time - last_time < 30:
            return
            
        new_xp = xp + amount
        new_level = (new_xp // 100) + 1 # هر 100 امتیاز = 1 سطح
        
        await execute_query(
            "UPDATE user_stats SET xp=?, level=?, last_xp_time=? WHERE user_id=? AND chat_id=?", 
            (new_xp, new_level, current_time, user_id, chat_id)
        )
    else:
        await execute_query(
            "INSERT INTO user_stats (user_id, chat_id, xp, level, last_xp_time) VALUES (?, ?, ?, ?, ?)",
            (user_id, chat_id, amount, 1, current_time)
        )

async def get_user_stats(user_id, chat_id):
    row = await execute_query("SELECT xp, level FROM user_stats WHERE user_id=? AND chat_id=?", (user_id, chat_id), fetch=True)
    if row:
        return {"xp": row[0]["xp"], "level": row[0]["level"]}
    return {"xp": 0, "level": 1}

async def get_top_users(chat_id, limit=5):
    rows = await execute_query("SELECT user_id, xp, level FROM user_stats WHERE chat_id=? ORDER BY xp DESC LIMIT ?", (chat_id, limit), fetch=True)
    return rows