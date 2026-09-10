# handlers/economy.py
import random
from core.api_client import send_message
from services.economy_service import get_balance, add_coins, claim_daily
# متن تبلیغاتی شما (هر چند وقت یه بار میتونی این متن رو عوض کنی)
AD_TEXT = "\n\n📢 <i>جهت رزرو تبلیغات در این ربات پیام دهید: @Iambrrr</i>"

async def handle_balance(chat_id, user_id, first_name):
    balance = await get_balance(user_id, chat_id)
    text = (
        f"💰 <b>موجودی شما</b>\n\n"
        f"👤 نام: <b>{first_name}</b>\n"
        f"💵 سکه: <b>{balance}</b>\n\n"
        f"برای دریافت سکه رایگان، دستور /daily را بزنید!"
    )
    text += AD_TEXT
    await send_message(chat_id, text)

async def handle_daily(chat_id, user_id, first_name):
    success, data, streak = await claim_daily(user_id, chat_id)
    if success:
        reward = data
        text = (
            f"🎁 <b>پاداش روزانه!</b>\n\n"
            f"🎉 {first_name} عزیز، شما <b>{reward} سکه</b> دریافت کردید! 💵\n"
            f"🔥 استریک شما: <b>{streak} روز</b>\n\n"
            f"💡 هر روز برگردید تا استریک‌تان بیشتر شود و سکه‌های بیشتری بگیرید!"
        )
    else:
        remaining_seconds = data
        hours = remaining_seconds // 3600
        minutes = (remaining_seconds % 3600) // 60
        text = f"⏳ <b>شما امروز پاداش خود را گرفته‌اید!</b>\n\nزمان باقیمانده برای پاداش بعدی: <b>{hours} ساعت و {minutes} دقیقه</b>"
    
    text += AD_TEXT
    await send_message(chat_id, text)

async def handle_coinflip(chat_id, text, user_id, first_name):
    """بازی شیر یا خط برای شرط‌بندی سکه"""
    parts = text.split()
    if len(parts) < 3 or parts[1].lower() not in ["شیر", "خط"]:
        await send_message(chat_id, "❌ استفاده درست: /coinflip [شیر/خط] [مبلغ]\nمثال: /coinflip شیر 50")
        return
        
    try:
        bet = int(parts[2])
    except ValueError:
        await send_message(chat_id, "❌ مبلغ باید یک عدد صحیح باشد.")
        return
        
    if bet <= 0:
        await send_message(chat_id, "❌ مبلغ شرط باید بزرگتر از صفر باشد.")
        return
        
    balance = await get_balance(user_id, chat_id)
    if balance < bet:
        await send_message(chat_id, f"❌ موجودی شما کافی نیست.\nموجودی فعلی: {balance} سکه")
        return
        
    user_choice = parts[1].lower()
    # 0 = شیر (Heads), 1 = خط (Tails)
    result_num = random.randint(0, 1)
    result_text = "شیر" if result_num == 0 else "خط"
    
    if user_choice == result_text:
        await add_coins(user_id, chat_id, bet)
        text = f"🪙 <b>شیر یا خط!</b>\n\n انتخاب شما: {user_choice}\n نتیجه: {result_text}\n\n🎉 آفرین! شما <b>{bet} سکه</b> بردید!"
    else:
        await add_coins(user_id, chat_id, -bet)
        text = f"🪙 <b>شیر یا خط!</b>\n\n انتخاب شما: {user_choice}\n نتیجه: {result_text}\n\n😢 متأسفم! شما <b>{bet} سکه</b> باختید."
        
    await send_message(chat_id, text)

from services.economy_service import do_work, do_rob, transfer_coins, buy_item, SHOP_ITEMS

async def handle_work(chat_id, user_id, first_name):
    success, data = await do_work(user_id, chat_id)
    if success:
        await send_message(chat_id, f"💼 <b>{first_name}</b> کار کردی و <b>{data} سکه</b> گرفتی! 💵")
    else:
        mins = data // 60
        await send_message(chat_id, f"⏳ شما خسته هستید! {mins} دقیقه دیگه می‌تونی دوباره کار کنی.")

async def handle_rob(chat_id, message, user_id, first_name):
    if not message.get("reply_to_message"):
        await send_message(chat_id, "❌ برای دزدی باید روی پیام یک نفر ریپلای کنی: /rob")
        return
        
    target = message["reply_to_message"]["from"]
    if target["id"] == user_id:
        await send_message(chat_id, "❌ نمی‌تونی از خودت بدزدی!")
        return
        
    status, data = await do_rob(user_id, chat_id, target["id"])
    if status == "cooldown":
        hours = data // 3600
        mins = (data % 3600) // 60
        await send_message(chat_id, f"⏳ پلیس‌ها هنوز تو رو می‌گردن! {hours} ساعت و {mins} دقیقه دیگه امتحان کن.")
    elif status == "poor_target":
        await send_message(chat_id, "🤷 این کاربر انقدر فقیره که ارزش دزدی نداره!")
    elif status == "success":
        await send_message(chat_id, f"🦹 <b>{first_name}</b> از {target.get('first_name', 'کاربر')} <b>{data} سکه</b> دزدید! 🤑")
    elif status == "failed":
        await send_message(chat_id, f"🚨 <b>{first_name}</b> تو دزدی شکست خوردی و <b>{data} سکه</b> جریمه شدی! 👮")

async def handle_give(chat_id, message, text, user_id, first_name):
    parts = text.split()
    if len(parts) < 2 or not message.get("reply_to_message"):
        await send_message(chat_id, "❌ استفاده: روی پیام کاربر ریپلای کن و بنویس /give [مبلغ]")
        return
        
    try:
        amount = int(parts[1])
    except ValueError:
        await send_message(chat_id, "❌ مبلغ باید عدد باشد.")
        return
        
    if amount <= 0:
        await send_message(chat_id, "❌ مبلغ باید بزرگتر از صفر باشد.")
        return
        
    target = message["reply_to_message"]["from"]
    success = await transfer_coins(user_id, chat_id, target["id"], amount)
    if success:
        await send_message(chat_id, f"💸 <b>{first_name}</b> به {target.get('first_name', 'کاربر')} <b>{amount} سکه</b> هدیه داد! ❤️")
    else:
        await send_message(chat_id, "❌ موجودی شما کافی نیست.")

async def handle_shop(chat_id):
    text = "🛒 <b>فروشگاه رفیبات</b>\n\nبرای خرید، دستور /buy [آیدی آیتم] را بزنید:\n\n"
    for item_id, info in SHOP_ITEMS.items():
        text += f"🆔 <code>{item_id}</code>\n📦 {info['name']}\n💰 قیمت: {info['price']} سکه\n➖➖➖➖➖➖\n"
    await send_message(chat_id, text)

async def handle_buy(chat_id, text, user_id, first_name):
    parts = text.split()
    if len(parts) < 2:
        await send_message(chat_id, "❌ استفاده: /buy [آیدی آیتم]\nمثال: /buy vip_badge")
        return
    item_id = parts[1]
    success, msg = await buy_item(user_id, chat_id, item_id)
    if success:
        await send_message(chat_id, f"🎉 <b>{first_name}</b>، شما با موفقیت <b>{msg}</b> را خریدید! به اینونتوری شما اضافه شد.")
    else:
        await send_message(chat_id, f"❌ خطا در خرید: {msg}")