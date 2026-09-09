# handlers/base.py
from core.api_client import send_message
from services.economy_service import get_balance

# --- کیبوردها ---
def get_main_menu_keyboard():
    return {
        "keyboard": [
            [{"text": "🎮 بازی‌ها"}, {"text": "🏆 رتبه من"}],
            [{"text": "😂 فان"}, {"text": "🛡 مدیریت"}],
            [{"text": "⚙️ تنظیمات"}, {"text": "❓ راهنما"}]
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
            [{"text": "🎲 حدس عدد", "callback_data": "game_guess"}],
            [{"text": "✂️ سنگ کاغذ قیچی", "callback_data": "game_rps"}],
            [{"text": "🧠 سوال عمومی", "callback_data": "game_trivia"}],
            [{"text": "🔙 بازگشت به منوی اصلی", "callback_data": "main_menu"}]
        ]
    }

# --- هندلرهای پایه ---
async def handle_start(chat_id):
    text = (
        "🤖 <b>RafiBot</b>\n\n"
        "رفیق هوشمند گروه‌های شما!\n"
        "من مدیریت گروه، سرگرمی و سیستم امتیازدهی رو ترکیب می‌کنم.\n\n"
        "👇 از منوی پایین انتخاب کن یا روی دکمه‌های شیشه‌ای کلیک کن:"
    )
    await send_message(chat_id, text, reply_markup=get_main_menu_keyboard())
    await send_message(chat_id, "✨ برای ادامه روی دکمه زیر کلیک کن:", reply_markup=get_start_inline_keyboard())

async def handle_help(chat_id):
    text = (
        "📖 <b>راهنما</b>\n\n"
        "🛡 <b>مدیریت:</b>\n"
        "/warn [reply] - اخطار به کاربر\n"
        "/ban [reply] - بن کردن مجازی\n"
        "/filter [word] - اضافه کردن کلمه ممنوع\n\n"
        "🎮 <b>سرگرمی:</b> (به زودی)\n"
        "💰 <b>اقتصاد:</b>\n"
        "/balance - نمایش موجودی سکه‌ها\n"
        "/daily - دریافت پاداش روزانه\n"
        "/coinflip [شیر/خط] [مبلغ] - شرط‌بندی شیر یا خط\n\n"
    )
    await send_message(chat_id, text)

# --- هندلرهای دکمه‌های منو ---
async def handle_rank_menu(chat_id):
    await send_message(chat_id, "🏆 <b>سیستم XP و Level</b>\n\nاین بخش در مرحله دوم توسعه اضافه خواهد شد. به زودی با هر پیام امتیاز می‌گیرید!")

async def handle_games_menu(chat_id):
    text = "🎮 <b>منوی بازی‌ها</b>\n\nیک بازی را برای شروع انتخاب کن:"
    await send_message(chat_id, text, reply_markup=get_games_inline_keyboard())

async def handle_fun_menu(chat_id):
    text = (
        "😂 <b>بخش فان</b>\n\n"
        "دستورات قابل استفاده در گروه:\n\n"
        "🎲 <code>/who</code> - انتخاب یک نفر تصادفی\n"
        "📊 <code>/vote [موضوع]</code> - رأی‌گیری\n"
        "🤔 <code>/truth</code> - سوال حقیقت\n"
        "🔥 <code>/dare</code> - چالش (جرئت)"
        "💰 <b>اقتصاد:</b>\n"
        "/balance - نمایش موجودی سکه‌ها\n"
        "/daily - دریافت پاداش روزانه\n"
        "/coinflip [شیر/خط] [مبلغ] - شرط‌بندی شیر یا خط\n\n"
    )
    await send_message(chat_id, text)

async def handle_admin_menu(chat_id):
    text = (
        "🛡 <b>منوی مدیریت گروه</b>\n\n"
        "⚠️ این دستورات فقط برای ادمین‌های گروه فعال هستند.\n\n"
        "برای /warn و /ban روی پیام کاربر ریپلای کنید:\n\n"
        "<code>/warn</code> - دادن اخطار به کاربر\n"
        "<code>/ban</code> - بن کردن مجازی کاربر\n"
        "<code>/filter [word]</code> - مسدود کردن کلمه\n"
        "<code>/setantilink [on/off]</code> - روشن/خاموش کردن آنتی‌لینک\n\n"
        "💡 تنظیمات پیشرفته مدیریتی در نسخه Premium!"
    )
    await send_message(chat_id, text)

async def handle_settings_menu(chat_id):
    await send_message(chat_id, "⚙️ <b>تنظیمات</b>\n\nبزودی می‌توانید پیام خوش‌آمدگویی، قوانین و تنظیمات ضد اسپم گروه را از اینجا تغییر دهید.")

# handlers/base.py (این توابع را به انتهای فایل اضافه کنید)
from services.xp_service import get_user_stats, get_top_users

# در ابتدای فایل handlers/base.py این ایمپورت را اضافه کنید:
from services.economy_service import get_balance, get_achievements, add_achievement

async def handle_profile(chat_id, user_id, first_name):
    stats = await get_user_stats(user_id, chat_id)
    balance = await get_balance(user_id, chat_id)
    
    # اعطای دستاورد اولین پیام
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
        f"🎮 برای کسب امتیاز بیشتر، در بازی‌ها شرکت کنید!"
    )
    await send_message(chat_id, text)

async def handle_leaderboard(chat_id):
    top_users = await get_top_users(chat_id)
    if not top_users:
        await send_message(chat_id, "📊 هنوز کسی در این گروه امتیازی کسب نکرده است.")
        return
        
    text = "📊 <b>برترین اعضای گروه</b>\n\n"
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
    
    for i, user in enumerate(top_users):
        text += f"{medals[i]} کاربر {user['user_id']} - سطح {user['level']} ({user['xp']} XP)\n"
        
    await send_message(chat_id, text)