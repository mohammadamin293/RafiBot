# handlers/economy.py
import random
from core.api_client import send_message
from services.economy_service import get_balance, add_coins, claim_daily

async def handle_balance(chat_id, user_id, first_name):
    balance = await get_balance(user_id, chat_id)
    text = (
        f"💰 <b>موجودی شما</b>\n\n"
        f"👤 نام: <b>{first_name}</b>\n"
        f"💵 سکه: <b>{balance}</b>\n\n"
        f"برای دریافت سکه رایگان، دستور /daily را بزنید!"
    )
    await send_message(chat_id, text)

async def handle_daily(chat_id, user_id, first_name):
    success, data = await claim_daily(user_id, chat_id)
    if success:
        text = f"🎁 <b>پاداش روزانه!</b>\n\n{first_name} عزیز، شما <b>{data} سکه</b> دریافت کردید! 💵"
    else:
        # محاسبه زمان باقی‌مانده (تبدیل ثانیه به ساعت و دقیقه)
        hours = data // 3600
        minutes = (data % 3600) // 60
        text = f"⏳ <b>شما امروز پاداش خود را گرفته‌اید!</b>\n\nزمان باقی‌مانده برای پاداش بعدی: <b>{hours} ساعت و {minutes} دقیقه</b>"
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