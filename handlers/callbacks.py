# handlers/callbacks.py
import random
from core.api_client import answer_callback, edit_message_text, delete_message, send_message
from services.xp_service import add_xp
from handlers.games import active_trivias, handle_trivia
from handlers.fun import process_vote
from services.group_service import toggle_setting, get_group_settings
from services.permission_service import is_group_admin
from handlers.admin import get_admin_panel_keyboard
from handlers.base import (
    get_back_keyboard, 
    get_help_keyboard,
    get_games_inline_keyboard,
    get_main_menu_keyboard
)

def get_rps_keyboard():
    return {
        "inline_keyboard": [
            [
                {"text": "🪨 سنگ", "callback_data": "rps_rock"},
                {"text": "📄 کاغذ", "callback_data": "rps_paper"},
                {"text": "✂️ قیچی", "callback_data": "rps_scissors"}
            ],
            [{"text": "🔙 بازگشت به بازی‌ها", "callback_data": "games_menu"}]
        ]
    }

async def handle_callback_query(callback_query):
    data = callback_query.get("data")
    user_id = callback_query["from"]["id"]
    first_name = callback_query["from"].get("first_name", "کاربر")
    callback_id = callback_query.get("id")
    
    message = callback_query.get("message") or callback_query.get("maybe_inaccessible_message")
    if not message:
        await answer_callback(callback_id, "❌ پیام یافت نشد", show_alert=True)
        return

    chat_id = message.get("chat", {}).get("id")
    message_id = message.get("message_id")
    
    if not chat_id or not message_id:
        await answer_callback(callback_id, "❌ خطا در دریافت اطلاعات", show_alert=True)
        return

    # ---------------- منوهای اصلی ----------------
    if data == "main_menu":
        await delete_message(chat_id, message_id)
        await send_message(
            chat_id, 
            "🤖 <b>RafiBot</b>\n\nیکی از گزینه‌ها را انتخاب کنید:",
            reply_markup=get_main_menu_keyboard()
        )
        await answer_callback(callback_id) # پایان لودینگ

    elif data == "help_menu":
        text = "❓ <b>راهنمای رفی‌بات</b>\n\nبرای مشاهده هر بخش، روی دکمه مربوطه کلیک کن:"
        await edit_message_text(chat_id, message_id, text, reply_markup=get_help_keyboard())
        await answer_callback(callback_id)
    
    elif data == "help_ai":
        text = (
            "🤖 <b>هوش مصنوعی (فرانس)</b>\n\n"
            "دستورات:\n"
            "<code>/ask [سوال]</code> - پرسیدن سوال از فرانس\n"
            "<code>/suggest [موضوع]</code> - گرفتن ایده از فرانس\n"
            "<code>/challenge</code> - ساخت چالش تصادفی\n\n"
            "💡 می‌توانی کلمه «فرانس» را اول پیام بیاوری یا روی پیام بات ریپلای کنی!"
        )
        await edit_message_text(chat_id, message_id, text, reply_markup=get_back_keyboard("help_menu"))
        await answer_callback(callback_id)
    
    elif data == "help_economy":
        text = (
            "💰 <b>اقتصاد و سکه</b>\n\n"
            "<code>/balance</code> - نمایش موجودی شما\n"
            "<code>/daily</code> - دریافت پاداش روزانه (با سیستم استریک)\n"
            "<code>/work</code> - کار کردن و کسب سکه\n"
            "<code>/coinflip [شیر/خط] [مبلغ]</code> - شرط‌بندی شیر یا خط\n"
            "<code>/rob</code> - (ریپلای روی کاربر) دزدی از سکه دیگران\n"
            "<code>/give [مبلغ]</code> - (ریپلای روی کاربر) هدیه دادن سکه\n"
            "<code>/shop</code> - نمایش فروشگاه\n"
            "<code>/buy [آیدی آیتم]</code> - خرید از فروشگاه"
        )
        await edit_message_text(chat_id, message_id, text, reply_markup=get_back_keyboard("help_menu"))
        await answer_callback(callback_id)
    
    elif data == "help_games":
        text = (
            "🎮 <b>بازی‌ها و فان</b>\n\n"
            "<code>/trivia</code> - مسابقه عمومی ۴ گزینه‌ای\n"
            "<code>/who</code> - انتخاب یک نفر تصادفی از افراد فعال\n"
            "<code>/vote [موضوع]</code> - رأی‌گیری گروهی\n"
            "<code>/truth</code> - سوال حقیقت\n"
            "<code>/dare</code> - چالش جرئت"
        )
        await edit_message_text(chat_id, message_id, text, reply_markup=get_back_keyboard("help_menu"))
        await answer_callback(callback_id)
    
    elif data == "help_moderation":
        text = (
            "🛡 <b>مدیریت گروه (فقط ادمین‌ها)</b>\n\n"
            "<code>/warn</code> - (ریپلای) دادن اخطار به کاربر\n"
            "<code>/mute</code> - (ریپلای) میوت کردن کاربر\n"
            "<code>/unmute</code> - (ریپلای) آزاد کردن کاربر\n"
            "<code>/ban</code> - (ریپلای) بن مجازی کاربر\n"
            "<code>/kick</code> - (ریپلای) اخراج کاربر از گروه\n"
            "<code>/filter [کلمه]</code> - مسدود کردن کلمه ممنوعه\n"
            "<code>/setwelcome [متن]</code> - تنظیم پیام خوش‌آمدگویی\n"
            "<code>/setrules [متن]</code> - تنظیم قوانین گروه\n"
            "<code>/rules</code> - مشاهده قوانین گروه\n"
            "<code>/setantilink [on/off]</code> - خاموش/روشن کردن حذف لینک‌ها\n"
            "<code>/logs</code> - مشاهده آخرین اقدامات ادمین‌ها\n"
            "<code>/endvote</code> - پایان دادن به نظرسنجی فعال"
        )
        await edit_message_text(chat_id, message_id, text, reply_markup=get_back_keyboard("help_menu"))
        await answer_callback(callback_id)
    
    elif data == "help_profile":
        text = (
            "👤 <b>پروفایل و لول</b>\n\n"
            "<code>/profile</code> - نمایش پروفایل شما (سطح، سکه، مدال‌ها)\n"
            "<code>/top</code> - لیست برترین اعضای گروه\n\n"
            "💡 با ارسال پیام در گروه، امتیاز (XP) کسب می‌کنی!\n"
            "هر ۱۰۰ امتیاز = ۱ سطح"
        )
        await edit_message_text(chat_id, message_id, text, reply_markup=get_back_keyboard("help_menu"))
        await answer_callback(callback_id)
    
    elif data == "premium_menu":
        text = (
            "💳 <b>نسخه Premium</b>\n\n"
            "ویژگی‌های نسخه Premium:\n"
            "🔹 فیلتر کلمات نامحدود (رایگان فقط ۳ کلمه)\n"
            "🔹 دسترسی به آمار دقیق گروه\n"
            "🔹 بازی‌های اختصاصی بیشتر\n"
            "🔹 هوش مصنوعی پیشرفته\n\n"
            "برای خرید با پشتیبانی در ارتباط باشید: @Iambrrr" # <--- اینجا تغییر کرد
        )
        await edit_message_text(chat_id, message_id, text, reply_markup=get_back_keyboard("help_menu"))
        await answer_callback(callback_id)
        
    # ---------------- بخش بازی‌ها ----------------
    elif data == "games_menu":
        text = "🎮 <b>منوی بازی‌ها</b>\n\nیک بازی را برای شروع انتخاب کن:"
        await edit_message_text(chat_id, message_id, text, reply_markup=get_games_inline_keyboard())
        await answer_callback(callback_id)

    elif data == "game_guess":
        await edit_message_text(
            chat_id, message_id, 
            "🎯 <b>حدس عدد</b>\n\nاین بخش به‌زودی اضافه خواهد شد!",
            reply_markup=get_back_keyboard("games_menu")
        )
        await answer_callback(callback_id)
        
    elif data == "game_rps":
        await edit_message_text(
            chat_id, message_id, 
            "✂️ <b>سنگ، کاغذ، قیچی</b>\n\nانتخاب کن:",
            reply_markup=get_rps_keyboard()
        )
        await answer_callback(callback_id)
        
    elif data == "game_trivia":
        await handle_trivia(chat_id)
        await edit_message_text(
            chat_id, message_id, 
            "🧠 مسابقه شروع شد! به پیام بالایی نگاه کنید.\n\nبرای بازگشت به منو روی دکمه زیر کلیک کنید.",
            reply_markup=get_back_keyboard("games_menu")
        )
        await answer_callback(callback_id)
        
    # ---------------- پنل مدیریت ----------------
    elif data == "admin_panel":
        settings = await get_group_settings(chat_id)
        text = "🛡 <b>پنل مدیریت گروه</b>\n\nبا کلیک روی هر دکمه، آن قابلیت را روشن یا خاموش کن:"
        await edit_message_text(chat_id, message_id, text, reply_markup=get_admin_panel_keyboard(settings))
        await answer_callback(callback_id)

    elif data.startswith("toggle_"):
        setting_key = data.split("_")[1]
        
        if not await is_group_admin(chat_id, user_id):
            await answer_callback(callback_id, text="⛔ شما ادمین گروه نیستید!", show_alert=True)
            return
            
        await toggle_setting(chat_id, setting_key)
        settings = await get_group_settings(chat_id)
        
        text = "🛡 <b>پنل مدیریت گروه</b>\n\nبا کلیک روی هر دکمه، آن قابلیت را روشن یا خاموش کنید:"
        await edit_message_text(chat_id, message_id, text, reply_markup=get_admin_panel_keyboard(settings))
        await answer_callback(callback_id, text="✅ تنظیمات با موفقیت ذخیره شد!")
        
    # ---------------- بازی سنگ کاغذ قیچی ----------------
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
            
        response = (
            f"شما: {choices[user_choice]}\n"
            f"من: {choices[bot_choice]}\n\n"
            f"{result_text}"
        )
        await edit_message_text(chat_id, message_id, response, reply_markup=get_rps_keyboard())
        await answer_callback(callback_id, text="✅ انتخاب شما ثبت شد!")

    # ---------------- رأی‌گیری (Vote) ----------------
    elif data in ["vote_yes", "vote_no"]:
        choice = "yes" if data == "vote_yes" else "no"
        result = await process_vote(chat_id, message_id, user_id, choice)
        
        if result == "voted":
            await answer_callback(callback_id, text="⛔ شما قبلاً رأی داده‌اید!", show_alert=True)
        elif result == "expired":
            await answer_callback(callback_id, text="⏳ زمان این رأی‌گیری به پایان رسیده است.", show_alert=True)
        else:
            await answer_callback(callback_id, text="✅ رأی شما ثبت شد!")

    # ---------------- مسابقه عمومی (Trivia) ----------------
    elif data.startswith("trivia_"):
        if data == "trivia_end":
            if message_id in active_trivias:
                del active_trivias[message_id]
                await edit_message_text(
                    chat_id, message_id,
                    "🧠 <b>مسابقه پایان یافت</b>\n\nمسابقه بدون برنده لغو شد."
                )
            await answer_callback(callback_id)
            return
            
        if message_id not in active_trivias:
            await answer_callback(callback_id, text="⏳ زمان این سوال به پایان رسیده است!", show_alert=True)
            return
            
        game = active_trivias[message_id]
        
        if user_id in game["answered_by"]:
            await answer_callback(callback_id, text="⛔ شما قبلاً جواب داده‌اید!", show_alert=True)
            return
            
        game["answered_by"].append(user_id)
        user_choice = int(data.split("_")[1])
        
        if user_choice == game["answer"]:
            del active_trivias[message_id]
            await add_xp(user_id, chat_id, 50)
            await edit_message_text(
                chat_id, message_id,
                f"🧠 <b>مسابقه عمومی</b>\n\n🏆 برنده: <b>{first_name}</b>!\n+50 XP به شما اضافه شد.\n\n✅ مسابقه توسط برنده بسته شد."
            )
            await answer_callback(callback_id, text="🎉 درست بود! ۵۰ امتیاز گرفتی!", show_alert=True)
        else:
            await answer_callback(callback_id, text="❌ جواب اشتباه بود!", show_alert=True)