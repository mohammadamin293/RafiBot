# handlers/base.py
from core.api_client import send_message, edit_message_text
from services.economy_service import get_balance, get_achievements, add_achievement
from services.xp_service import get_user_stats, get_top_users

# --- کیبوردهای Reply (برای گروه‌ها) ---

def get_main_menu_keyboard():
    """منوی اصلی با ReplyKeyboardMarkup - برای همه چت‌ها"""
    return {
        "keyboard": [
            [{"text": "🎮 بازی‌ها"}, {"text": "😂 سرگرمی"}],
            [{"text": "🏆 رتبه من"}, {"text": "💰 اقتصاد"}],
            [{"text": "🛡 مدیریت"}, {"text": "⚙️ تنظیمات"}],
            [{"text": "❓ راهنما"}]
        ],
        "resize_keyboard": True
    }

def get_games_reply_keyboard():
    """کیبورد بازی‌ها برای گروه (ReplyKeyboardMarkup)"""
    return {
        "keyboard": [
            [{"text": "🧠 سوال عمومی"}, {"text": "✂️ سنگ کاغذ قیچی"}],
            [{"text": "🎯 حدس عدد"}, {"text": "🔙 بازگشت"}]
        ],
        "resize_keyboard": True
    }

def get_fun_reply_keyboard():
    """کیبورد سرگرمی برای گروه (ReplyKeyboardMarkup)"""
    return {
        "keyboard": [
            [{"text": "🎯 انتخاب تصادفی"}, {"text": "📊 رأی‌گیری"}],
            [{"text": "🤔 حقیقت"}, {"text": "🔥 جرئت"}],
            [{"text": "🔙 بازگشت"}]
        ],
        "resize_keyboard": True
    }

def get_economy_reply_keyboard():
    """کیبورد اقتصاد برای گروه (ReplyKeyboardMarkup)"""
    return {
        "keyboard": [
            [{"text": "💰 موجودی"}, {"text": "🎁 روزانه"}],
            [{"text": "💼 کار"}, {"text": "🪙 شیر یا خط"}],
            [{"text": "🏪 فروشگاه"}, {"text": "🔙 بازگشت"}]
        ],
        "resize_keyboard": True
    }

# --- کیبوردهای Inline (برای پیوی) ---

def get_games_inline_keyboard():
    """منوی بازی‌ها"""
    return {
        "inline_keyboard": [
            [{"text": "🧠 سوال عمومی", "callback_data": "game_trivia"}],
            [{"text": "✂️ سنگ کاغذ قیچی", "callback_data": "game_rps"}],
            [{"text": "🎯 حدس عدد", "callback_data": "game_guess"}],
            [{"text": "🏠 منوی اصلی", "callback_data": "main_menu"}]
        ]
    }

def get_start_inline_keyboard():
    """کیبورد شروع برای پیوی"""
    return {
        "inline_keyboard": [
            [{"text": "📖 راهنمای کامل", "callback_data": "help_menu"}],
            [{"text": "💳 خرید Premium", "callback_data": "premium_menu"}]
        ]
    }

def get_back_keyboard(callback_data="main_menu"):
    """ساخت دکمه بازگشت با قابلیت تعیین مقصد"""
    return {
        "inline_keyboard": [
            [{"text": "🔙 بازگشت", "callback_data": callback_data}]
        ]
    }

def get_back_inline_keyboard():
    """دکمه بازگشت به منوی اصلی (همان get_back_keyboard)"""
    return get_back_keyboard()

def get_help_keyboard():
    """منوی راهنما"""
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

def get_back_to_menu_keyboard():
    """دکمه بازگشت به منوی اصلی"""
    return get_back_keyboard()

# --- هندلرهای اصلی ---

async def handle_start(chat_id, chat_type="private"):
    text = (
        "🤖 <b>RafiBot</b>\n\n"
        "رفیق هوشمند گروه‌های شما!\n"
        "من مدیریت گروه، سرگرمی و سیستم امتیازدهی رو ترکیب می‌کنم.\n\n"
        "👇 از منوی پایین انتخاب کن:"
    )
    await send_message(chat_id, text, reply_markup=get_main_menu_keyboard())
    await send_message(
        chat_id, 
        "✨ برای ادامه روی دکمه زیر کلیک کن:",
        reply_markup=get_start_inline_keyboard()
    )

async def handle_help(chat_id, chat_type="private"):
    if chat_type == "private":
        text = "❓ <b>راهنمای رفی‌بات</b>\n\nبرای مشاهده هر بخش، روی دکمه مربوطه کلیک کن:"
        await send_message(chat_id, text, reply_markup=get_help_keyboard())
    else:
        text = (
            "❓ <b>راهنمای رفی‌بات</b>\n\n"
            "📖 برای مشاهده راهنما، به پیوی بات برو:\n"
            "@rafibot\n\n"
            "دستورات اصلی:\n"
            "/help - نمایش این پیام\n"
            "/profile - پروفایل شما\n"
            "/top - برترین‌ها\n"
            "/rules - قوانین گروه"
        )
        await send_message(chat_id, text)

async def handle_games_menu(chat_id, chat_type="private"):
    if chat_type == "private":
        text = "🎮 <b>منوی بازی‌ها</b>\n\nیک بازی را برای شروع انتخاب کن:"
        await send_message(chat_id, text, reply_markup=get_games_inline_keyboard())
    else:
        text = "🎮 <b>منوی بازی‌ها</b>\n\nاز دکمه‌های زیر انتخاب کن:"
        await send_message(chat_id, text, reply_markup=get_games_reply_keyboard())

async def handle_fun_menu(chat_id, chat_type="private"):
    if chat_type == "private":
        text = (
            "😂 <b>بخش فان</b>\n\n"
            "دستورات:\n"
            "<code>/who</code> - انتخاب تصادفی\n"
            "<code>/vote [موضوع]</code> - رأی‌گیری\n"
            "<code>/truth</code> - حقیقت\n"
            "<code>/dare</code> - جرئت"
        )
        await send_message(chat_id, text, reply_markup=get_back_keyboard())
    else:
        text = "😂 <b>بخش فان</b>\n\nاز دکمه‌های زیر انتخاب کن:"
        await send_message(chat_id, text, reply_markup=get_fun_reply_keyboard())

async def handle_economy_menu(chat_id, chat_type="private"):
    if chat_type == "private":
        text = (
            "💰 <b>اقتصاد</b>\n\n"
            "دستورات:\n"
            "/balance - موجودی\n"
            "/daily - پاداش روزانه\n"
            "/work - کار کردن\n"
            "/coinflip - شیر یا خط"
        )
        await send_message(chat_id, text, reply_markup=get_back_keyboard())
    else:
        text = "💰 <b>اقتصاد</b>\n\nاز دکمه‌های زیر انتخاب کن:"
        await send_message(chat_id, text, reply_markup=get_economy_reply_keyboard())

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
    await send_message(chat_id, text, reply_markup=get_back_keyboard())

async def handle_leaderboard(chat_id):
    top_users = await get_top_users(chat_id)
    if not top_users:
        await send_message(
            chat_id, 
            "📊 هنوز کسی در این گروه امتیازی کسب نکرده است.\n"
            "اولین نفر باش! 🚀",
            reply_markup=get_back_keyboard()
        )
        return
        
    text = "📊 <b>برترین اعضای گروه</b>\n\n"
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
    
    for i, user in enumerate(top_users):
        # ساخت لینک قابل کلیک برای آیدی کاربر
        # وقتی روش کلیک کنی، مستقیم پروفایلش باز میشه
        user_link = f"<a href=\"tg://user?id={user['user_id']}\">کاربر {user['user_id']}</a>"
        text += f"{medals[i]} {user_link} - سطح {user['level']} ({user['xp']} XP)\n"
        
    await send_message(chat_id, text, reply_markup=get_back_keyboard())

async def handle_settings_menu(chat_id, chat_type="private"):
    text = (
        "⚙️ <b>تنظیمات</b>\n\n"
        "💡 از دستورات زیر استفاده کنید:\n"
        "<code>/setwelcome [متن]</code>\n"
        "<code>/setrules [متن]</code>\n"
        "<code>/setantilink [on/off]</code>"
    )
    await send_message(chat_id, text, reply_markup=get_back_keyboard())

def get_main_inline_keyboard():
    """کيبرد شیشه‌ای منوی اصلی (برای استفاده داخل منوهای شیشه‌ای)"""
    return {
        "inline_keyboard": [
            [{"text": "🎮 بازی‌ها", "callback_data": "games_menu"}],
            [{"text": "💰 اقتصاد", "callback_data": "economy_menu"}],
            [{"text": "📖 راهنما", "callback_data": "help_menu"}],
            [{"text": "💳 خرید Premium", "callback_data": "premium_menu"}]
        ]
    }