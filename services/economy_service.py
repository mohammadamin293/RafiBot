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
import random

# آیتم‌های فروشگاه
SHOP_ITEMS = {
    "vip_badge": {"name": "🏆 بج وی‌آی‌پی", "price": 5000},
    "custom_name": {"name": "🎨 اسم رنگی", "price": 2000},
    "rob_shield": {"name": "🛡 سپر دزدی (۲۴ ساعت)", "price": 1500}
}

async def do_work(user_id, chat_id):
    """کار کردن برای کسب سکه (هر ۱ ساعت یک‌بار)"""
    now = int(time.time())
    row = await execute_query("SELECT last_work FROM user_stats WHERE user_id=? AND chat_id=?", (user_id, chat_id), fetch=True)
    
    if row and row[0]["last_work"]:
        if now - row[0]["last_work"] < 3600: # 1 ساعت
            remaining = 3600 - (now - row[0]["last_work"])
            return False, remaining
            
    reward = random.randint(50, 200)
    await add_coins(user_id, chat_id, reward)
    await execute_query("UPDATE user_stats SET last_work=? WHERE user_id=? AND chat_id=?", (now, user_id, chat_id))
    return True, reward

async def do_rob(user_id, chat_id, target_id):
    """دزدی از کاربر دیگر (هر ۶ ساعت یک‌بار)"""
    now = int(time.time())
    row = await execute_query("SELECT last_rob FROM user_stats WHERE user_id=? AND chat_id=?", (user_id, chat_id), fetch=True)
    
    if row and row[0]["last_rob"]:
        if now - row[0]["last_rob"] < 21600: # 6 ساعت
            remaining = 21600 - (now - row[0]["last_rob"])
            return "cooldown", remaining
            
    target_balance = await get_balance(target_id, chat_id)
    if target_balance < 100:
        return "poor_target", 0
        
    # ۵۰ درصد شانس موفقیت
    if random.random() < 0.5:
        stolen = random.randint(50, min(200, target_balance))
        await add_coins(user_id, chat_id, stolen)
        await add_coins(target_id, chat_id, -stolen)
        await execute_query("UPDATE user_stats SET last_rob=? WHERE user_id=? AND chat_id=?", (now, user_id, chat_id))
        return "success", stolen
    else:
        # جریمه شکست
        fine = 50
        await add_coins(user_id, chat_id, -fine)
        await execute_query("UPDATE user_stats SET last_rob=? WHERE user_id=? AND chat_id=?", (now, user_id, chat_id))
        return "failed", fine

async def transfer_coins(user_id, chat_id, target_id, amount):
    """انتقال سکه به کاربر دیگر"""
    balance = await get_balance(user_id, chat_id)
    if balance < amount:
        return False
    await add_coins(user_id, chat_id, -amount)
    await add_coins(target_id, chat_id, amount)
    return True

async def buy_item(user_id, chat_id, item_id):
    """خرید آیتم از فروشگاه"""
    if item_id not in SHOP_ITEMS:
        return False, "آیتم وجود ندارد."
        
    price = SHOP_ITEMS[item_id]["price"]
    balance = await get_balance(user_id, chat_id)
    if balance < price:
        return False, "سکه کافی ندارید."
        
    await add_coins(user_id, chat_id, -price)
    await execute_query("INSERT OR IGNORE INTO user_inventory (user_id, chat_id, item) VALUES (?, ?, ?)", (user_id, chat_id, item_id))
    return True, SHOP_ITEMS[item_id]["name"]