# handlers/callbacks.py
import random
from core.api_client import answer_callback, edit_message_text
from services.xp_service import add_xp
from handlers.games import active_trivias, handle_trivia
from handlers.fun import process_vote

def get_back_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "🔙 بازگشت به منوی اصلی", "callback_data": "main_menu"}]
        ]
    }

def get_rps_keyboard():
    return {
        "inline_keyboard": [
            [
                {"text": "🪨 سنگ", "callback_data": "rps_rock"},
                {"text": "📄 کاغذ", "callback_data": "rps_paper"},
                {"text": "✂️ قیچی", "callback_data": "rps_scissors"}
            ]
        ]
    }

async def handle_callback_query(callback_query):
    data = callback_query.get("data")
    user_id = callback_query["from"]["id"]
    first_name = callback_query["from"].get("first_name", "کاربر")
    
    message = callback_query.get("message")
    if not message:
        message = callback_query.get("maybe_inaccessible_message")
        
    if not message: return

    chat_id = message.get("chat", {}).get("id")
    message_id = message.get("message_id")
    callback_id = callback_query.get("id")
    
    if not chat_id or not message_id: return
        
    await answer_callback(callback_id)

    # --- منوهای اصلی ---
    if data == "help_menu":
        text = "📖 <b>راهنمای کامل</b>\n\n/warn\n/ban\n/filter\n/profile\n/top\n/who\n/vote\n/trivia"
        await edit_message_text(chat_id, message_id, text, reply_markup=get_back_keyboard())
    elif data == "premium_menu":
        text = "💳 <b>Premium</b>\n\nبزودی..."
        await edit_message_text(chat_id, message_id, text, reply_markup=get_back_keyboard())
    elif data == "main_menu":
        text = "🤖 <b>RafiBot</b>\n\nیکی از گزینه‌ها را انتخاب کنید:"
        from handlers.base import get_start_inline_keyboard
        await edit_message_text(chat_id, message_id, text, reply_markup=get_start_inline_keyboard())
        
    # --- بازی‌ها ---
    elif data == "game_guess":
        await edit_message_text(chat_id, message_id, "🎲 <b>حدس عدد</b>\n\nبه زودی!")
    elif data == "game_rps":
        await edit_message_text(chat_id, message_id, "✂️ <b>سنگ، کاغذ، قیچی</b>\n\nانتخاب کن:", reply_markup=get_rps_keyboard())
    elif data == "game_trivia":
        await handle_trivia(chat_id)
        await edit_message_text(chat_id, message_id, "🧠 مسابقه عمومی شروع شد! به پیام بالایی نگاه کنید.")
        
    # --- لاجیک بازی سنگ کاغذ قیچی ---
    elif data.startswith("rps_"):
        user_choice = data.split("_")[1]
        bot_choice = random.choice(["rock", "paper", "scissors"])
        choices = {"rock": "🪨 سنگ", "paper": "📄 کاغذ", "scissors": "✂️ قیچی"}
        
        if user_choice == bot_choice:
            result_text = "🤝 <b>مساوی شدیم!</b>"
        elif (user_choice == "rock" and bot_choice == "scissors") or \
             (user_choice == "paper" and bot_choice == "rock") or \
             (user_choice == "scissors" and bot_choice == "paper"):
            result_text = "🎉 <b>شما برنده شدید! (+20 XP)</b>"
            await add_xp(user_id, chat_id, 20)
        else:
            result_text = "😢 <b>من برنده شدم!</b>"
            
        response = f"شما: {choices[user_choice]}\nمن: {choices[bot_choice]}\n\n{result_text}"
        await edit_message_text(chat_id, message_id, response, reply_markup=get_back_keyboard())

    # --- لاجیک رأی‌گیری (Vote) ---
    elif data in ["vote_yes", "vote_no"]:
        choice = "yes" if data == "vote_yes" else "no"
        result = await process_vote(chat_id, message_id, user_id, choice)
        
        if result == "voted":
            await answer_callback(callback_id, text="شما قبلاً رأی داده‌اید!", show_alert=True)
        elif result == "expired":
            await answer_callback(callback_id, text="زمان این رأی‌گیری به پایان رسیده است.", show_alert=True)
        else:
            await answer_callback(callback_id, text="رأی شما ثبت شد! ✅")

    # --- لاجیک مسابقه عمومی (Trivia) ---
    elif data.startswith("trivia_"):
        if message_id not in active_trivias:
            await answer_callback(callback_id, text="زمان این سوال به پایان رسیده است!", show_alert=True)
            return
            
        game = active_trivias[message_id]
        
        if user_id in game["answered_by"]:
            await answer_callback(callback_id, text="شما قبلاً جواب داده‌اید!", show_alert=True)
            return
            
        game["answered_by"].append(user_id)
        user_choice = int(data.split("_")[1])
        
        if user_choice == game["answer"]:
            del active_trivias[message_id]
            await add_xp(user_id, chat_id, 50)
            await answer_callback(callback_id, text="🎉 درست بود! ۵۰ امتیاز گرفتید!", show_alert=True)
            await edit_message_text(chat_id, message_id, f"🧠 <b>مسابقه عمومی</b>\n\n🏆 برنده: <b>{first_name}</b>!\n+50 XP به شما اضافه شد.")
        else:
            await answer_callback(callback_id, text="❌ جواب اشتباه بود!", show_alert=True)