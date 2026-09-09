# handlers/base.py
from core.api_client import send_message, edit_message_text
from services.economy_service import get_balance, get_achievements, add_achievement
from services.xp_service import get_user_stats, get_top_users

# --- کیبوردهای بهبود یافته ---

def get_main_menu_keyboard():
    return {
        "keyboard": [
            [{"text": "🎮 بازی‌ها"}, {"text": "😂 سرگرمی"}],
            [{"text": "🏆 رتبه من"}, {"text": "💰 اقتصاد"}],
            [{"text": "🛡 مدیریت"}, {"text": "⚙️ تنظیمات"}],
            [{"text": "❓ راهنما"}]
        ],
        "resize_keyboard": True
    }

def get_start_inline_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "📖 راهنمای کامل", "callback_data": "help_menu"}],
            [{"text": "💳 خرید Premium", "callback_data": "premium_menu"}]
        ]
    }

def get_games_inline_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "🎯 حدس عدد", "callback_data": "game_guess"}],
            [{"text": "✂️ سنگ کاغذ قیچی", "callback_data": "game_rps"}],
            [{"text": "🧠 سوال عمومی", "callback_data": "game_trivia"}],
            [{"text": "🔙 بازگشت به منوی اصلی", "callback_data": "main_menu"}]
        ]
    }

def get_back_to_menu_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "🔙 بازگشت", "callback_data": "back_to_previous"}],
            [{"text": "🏠 منوی اصلی", "callback_data": "main_menu"}]
        ]
    }

def get_back_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "🔙 بازگشت به منوی اصلی", "callback_data": "main_menu"}]
        ]
    }

def get_help_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "🤖 هوش مصنوعی", "callback_data": "help_ai"}],
            [{"text": "💰 اقتصاد", "callback_data": "help_economy"}],
            [{"text": "🎮 بازی‌ها", "callback_data": "help_games"}],
            [{"text": "🛡 مدیریت", "callback_data": "help_moderation"}],
            [{"text": "👤 پروفایل", "callback_data": "help_profile"}],
            [{"text": "🏠 منوی اصلی", "callback_data": "main_menu"}]
        ]
    }

# --- هندلرهای پایه ---

async def handle_start(chat_id):
    text = (
        "🤖 <b>RafiBot</b>\n\n"
        "رفیق هوشمند گروه‌های شما!\n"
        "من مدیریت گروه، سرگرمی و سیستم امتیازدهی رو ترکیب می‌کنم.\n\n"
        "👇 از منوی پایین انتخاب کن یا روی دکمه‌های زیر کلیک کن:"
    )
    await send_message(chat_id, text, reply_markup=get_main_menu_keyboard())
    await send_message(
        chat_id, 
        "✨ برای ادامه روی دکمه زیر کلیک کن:",
        reply_markup=get_start_inline_keyboard()
    )

async def handle_help(chat_id):
    text = (
        "❓ <b>راهنمای رفی‌بات</b>\n\n"
        "برای مشاهده هر بخش، روی دکمه مربوطه کلیک کن:"
    )
    await send_message(chat_id, text, reply_markup=get_help_keyboard())

async def handle_profile(chat_id, user_id, first_name):
    stats = await get_user_stats(user_id, chat_id)
    balance = await get_balance(user_id, chat_id)
    
    await add_achievement(user_id, chat_id, "💬 اولین پیام")
    
    badges = await get_achievements(user_id, chat_id)
    badges_text = "\n".join([f"🏅 {b}" for b in badges]) if badges else "بدون مدال"
    
    text = (
        f"🏆 <b>پروفایل کاربری</b>\n\n"
        f"👤 نام: <b>{first_name}</b>\n"
        f"⭐ سطح: <b>{stats['level']}</b>\n"
        f"⚡ امتیاز (XP): <b>{stats['xp']}</b>\n"
        f"💰 سکه: <b>{balance}</b>\n\n"
        f"🎖 <b>دستاوردها:</b>\n{badges_text}\n\n"
        f"🎮 برای کسب امتیاز بیشتر، در بازی‌ها شرکت کن!"
    )
    await send_message(chat_id, text, reply_markup=get_back_to_menu_keyboard())

async def handle_leaderboard(chat_id):
    top_users = await get_top_users(chat_id)
    if not top_users:
        await send_message(
            chat_id, 
            "📊 هنوز کسی در این گروه امتیازی کسب نکرده است.\n"
            "اولین نفر باش! 🚀",
            reply_markup=get_back_to_menu_keyboard()
        )
        return
        
    text = "📊 <b>برترین اعضای گروه</b>\n\n"
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
    
    for i, user in enumerate(top_users):
        text += f"{medals[i]} کاربر {user['user_id']} - سطح {user['level']} ({user['xp']} XP)\n"
        
    await send_message(chat_id, text, reply_markup=get_back_to_menu_keyboard())

async def handle_games_menu(chat_id):
    text = "🎮 <b>منوی بازی‌ها</b>\n\nیک بازی را برای شروع انتخاب کن:"
    await send_message(chat_id, text, reply_markup=get_games_inline_keyboard())

async def handle_fun_menu(chat_id):
    text = (
        "😂 <b>بخش فان</b>\n\n"
        "دستورات قابل استفاده در گروه:\n\n"
        "🎯 <code>/who</code> - انتخاب یک نفر تصادفی\n"
        "📊 <code>/vote [موضوع]</code> - رأی‌گیری\n"
        "🤔 <code>/truth</code> - سوال حقیقت\n"
        "🔥 <code>/dare</code> - چالش (جرئت)"
    )
    await send_message(chat_id, text, reply_markup=get_back_to_menu_keyboard())

async def handle_settings_menu(chat_id):
    text = (
        "⚙️ <b>تنظیمات</b>\n\n"
        "به‌زودی می‌توانید پیام خوش‌آمدگویی، قوانین و تنظیمات ضد اسپم گروه را از اینجا تغییر دهید.\n\n"
        "💡 فعلاً از دستورات زیر استفاده کنید:\n"
        "<code>/setwelcome [متن]</code>\n"
        "<code>/setrules [متن]</code>\n"
        "<code>/setantilink [on/off]</code>"
    )
    await send_message(chat_id, text, reply_markup=get_back_to_menu_keyboard())