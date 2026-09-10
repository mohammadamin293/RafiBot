# handlers/admin.py
from core.api_client import send_message, edit_message_text
from core.database import execute_query
from services.group_service import (
    set_welcome, get_welcome, set_rules, get_rules, 
    is_group_premium, set_group_premium, get_group_settings
)
from services.permission_service import is_group_admin, is_super_admin

NO_PERMISSION_TEXT = "⛔ این دستور فقط برای ادمین‌های گروه در دسترس است."
NO_SUPER_PERMISSION_TEXT = "⛔ این دستور فقط برای مالک ربات در دسترس است."

# در handlers/admin.py تابع get_admin_panel_keyboard را اصلاح کنید:

def get_admin_panel_keyboard(settings):
    def status_btn(key, label):
        val = settings.get(key, 0)
        status = "🟢" if val else "🔴"
        return {"text": f"{label} {status}", "callback_data": f"toggle_{key}"}

    return {
        "inline_keyboard": [
            [status_btn("antilink", "آنتی‌لینک"), status_btn("antispam", "ضد اسپم")],
            [status_btn("filter_enabled", "فیلتر کلمات"), status_btn("welcome_enabled", "خوش‌آمدگویی")],
            [status_btn("lock_links", "🔗 قفل لینک"), status_btn("lock_photos", "🖼 قفل عکس")],
            [status_btn("lock_videos", "🎬 قفل ویدیو"), status_btn("lock_stickers", "🏷 قفل استیکر")],
            [status_btn("lock_forward", "📤 قفل فوروارد")],
            [{"text": "🔙 بازگشت به منوی اصلی", "callback_data": "main_menu"}]
        ]
    }

async def handle_admin_panel(chat_id, user_id):
    """نمایش پنل مدیریت - فقط برای ادمین‌ها"""
    if not await is_group_admin(chat_id, user_id):
        await send_message(chat_id, NO_PERMISSION_TEXT)
        return
        
    settings = await get_group_settings(chat_id)
    text = (
        "🛡 <b>پنل مدیریت گروه</b>\n\n"
        "با کلیک روی هر دکمه، آن قابلیت را روشن یا خاموش کن:\n\n"
        "🟢 = فعال | 🔴 = غیرفعال"
    )
    await send_message(chat_id, text, reply_markup=get_admin_panel_keyboard(settings))

async def handle_set_welcome(chat_id, text, user_id):
    if not await is_group_admin(chat_id, user_id):
        await send_message(chat_id, NO_PERMISSION_TEXT)
        return

    parts = text.split(" ", 1)
    if len(parts) < 2:
        await send_message(chat_id, "❌ استفاده: /setwelcome [متن خوش‌آمدگویی]")
        return
        
    welcome_text = parts[1].strip()
    if len(welcome_text) > 500:
        await send_message(chat_id, "⚠️ متن خوش‌آمدگویی نباید بیشتر از ۵۰۰ کاراکتر باشد.")
        return
        
    await set_welcome(chat_id, welcome_text)
    await send_message(chat_id, "✅ پیام خوش‌آمدگویی با موفقیت ذخیره شد.\n\n💡 برای شخصی‌سازی می‌توانی از متغیرهای زیر استفاده کنی:\n{name} - نام کاربر\n{username} - نام کاربری\n{member_count} - تعداد اعضا")

async def handle_set_rules(chat_id, text, user_id):
    if not await is_group_admin(chat_id, user_id):
        await send_message(chat_id, NO_PERMISSION_TEXT)
        return

    parts = text.split(" ", 1)
    if len(parts) < 2:
        await send_message(chat_id, "❌ استفاده: /setrules [متن قوانین]")
        return
        
    rules_text = parts[1].strip()
    if len(rules_text) > 2000:
        await send_message(chat_id, "⚠️ متن قوانین نباید بیشتر از ۲۰۰۰ کاراکتر باشد.")
        return
        
    await set_rules(chat_id, rules_text)
    await send_message(chat_id, "✅ قوانین گروه با موفقیت ذخیره شد.")

async def handle_rules(chat_id):
    rules = await get_rules(chat_id)
    if rules:
        text = f"📜 <b>قوانین گروه</b>\n\n{rules}"
    else:
        text = "⚠️ هنوز قوانینی برای این گروه تنظیم نشده است.\n\n💡 ادمین‌ها می‌توانند با دستور /setrules قوانین را تنظیم کنند."
    await send_message(chat_id, text)

async def handle_new_member(chat_id, new_member):
    welcome = await get_welcome(chat_id)
    if welcome:
        member_name = new_member.get("first_name", "کاربر")
        username = f"@{new_member.get('username')}" if new_member.get('username') else "ندارد"
        user_id = new_member.get("id", "")
        
        from core.api_client import get_chat_member_count
        count_res = await get_chat_member_count(chat_id)
        member_count = count_res["result"] if count_res and count_res.get("ok") else "نامشخص"
        
        final_text = welcome.replace("{name}", member_name).replace("{username}", username).replace("{user_id}", str(user_id)).replace("{member_count}", str(member_count))
        text = f"👋 {final_text}"
        await send_message(chat_id, text)

async def handle_left_member(chat_id, left_member):
    left_name = left_member.get("first_name", "کاربر")
    text = f"👋 خداحافظ <b>{left_name}</b>! امیدواریم دوباره برگردی."
    await send_message(chat_id, text)

async def handle_set_premium(chat_id, text, user_id, username=None):
    if not is_super_admin(user_id, username):
        await send_message(chat_id, NO_SUPER_PERMISSION_TEXT)
        return

    parts = text.split(" ", 1)

    if len(parts) < 2 or parts[1].strip().lower() not in ["on", "off"]:
        await send_message(chat_id, "❌ استفاده: /setpremium [on/off]")
        return

    status = parts[1].strip().lower() == "on"

    await set_group_premium(chat_id, status)

    if status:
        await send_message(
            chat_id,
            "💎 این گروه الآن Premium شد! تمام محدودیت‌ها برداشته شد."
        )
    else:
        await send_message(
            chat_id,
            "⬇️ این گروه به نسخه رایگان برگشت."
        )

async def handle_group_stats(chat_id, user_id):
    if not await is_group_admin(chat_id, user_id):
        await send_message(chat_id, NO_PERMISSION_TEXT)
        return
        
    is_premium = await is_group_premium(chat_id)
    if not is_premium:
        text = (
            "📊 <b>آمار گروه</b>\n\n"
            "🔒 این قابلیت فقط برای گروه‌های <b>Premium</b> در دسترس است.\n\n"
            "برای ارتقا گروه، با پشتیبانی در ارتباط باشید: @Iambrrr"
        )
        await send_message(chat_id, text)
        return

    from services.group_service import get_message_count

    total_users = len(await execute_query("SELECT user_id FROM user_stats WHERE chat_id=?", (chat_id,), fetch=True))
    total_messages = await get_message_count(chat_id)

    text = (
        "📊 <b>آمار دقیق گروه (Premium)</b>\n\n"
        f"👥 تعداد کاربران فعال: <b>{total_users}</b>\n"
        f"💬 مجموع پیام‌های ثبت شده: <b>{total_messages}</b>\n"
        "✅ وضعیت: گروه Premium"
    )
    await send_message(chat_id, text)

async def handle_premium_info(chat_id):
    is_premium = await is_group_premium(chat_id)
    status = "💎 Premium" if is_premium else "🆓 رایگان (Free)"
    text = (
        f"💳 <b>وضعیت اشتراک گروه</b>\n\n"
        f"وضعیت فعلی: <b>{status}</b>\n\n"
        "<b>تفاوت‌های نسخه Premium:</b>\n"
        "🔹 فیلتر کلمات نامحدود (رایگان فقط ۳ کلمه)\n"
        "🔹 دسترسی به آمار دقیق گروه\n"
        "🔹 بازی‌های اختصاصی بیشتر\n"
        "🔹 هوش مصنوعی پیشرفته\n\n"
        "برای خرید با پشتیبانی در ارتباط باشید: @Iambrrr"
    )
    await send_message(chat_id, text)

async def handle_install(chat_id, user_id):
    if not await is_group_admin(chat_id, user_id):
        await send_message(chat_id, "⛔ فقط ادمین گروه می‌تواند ربات را نصب کند.")
        return
        
    text = (
        "✅ <b>ربات با موفقیت نصب شد!</b>\n\n"
        "🎉 RafiBot آماده کار است.\n\n"
        "💡 برای تنظیمات، روی دکمه 🛡 مدیریت در منوی پایین کلیک کنید.\n"
        "برای دیدن دستورات، /help را بزنید."
    )
    await send_message(chat_id, text)

async def handle_bot_stats(chat_id, user_id):
    # چون این دستور قبلاً در router.py چک شده که شما اونر هستید، اینجا دیگه چک نمیکنیم
    
    from services.group_service import get_bot_global_stats
    groups, users = await get_bot_global_stats()
    
    text = (
        "📊 <b>آمار کلی ربات شما</b>\n\n"
        f"👥 تعداد کل گروه‌های متصل: <b>{len(groups)}</b>\n"
        f"👤 تعداد کل کاربران ثبت شده: <b>{len(users)}</b>\n\n"
    )
    
    # نمایش لیست گروه‌ها (فقط ۵۰ گروه اول)
    text += "<b>📋 لیست گروه‌ها (آیدی‌ها):</b>\n"
    for g in groups[:50]:
        text += f"• <code>{g['chat_id']}</code>\n"
        
    # نمایش لیست کاربران (لینک‌دار بر اساس یوزرنیم یا آیدی، فقط ۱۰۰ کاربر اول)
    text += "\n<b>👤 لیست کاربران:</b>\n"
    for u in users[:100]:
        user_id = u["user_id"]
        username = u["username"] if u["username"] else None
        
        # اگه کاربر یوزرنیم داشت، یوزرنیم رو نشون میده، اگه نداشت آیدی عددی رو نشون میده
        display_name = f"@{username}" if username else f"{user_id}"
        
        # ساخت لینک قابل کلیک (با کلیک روی اسم میره تو پروفایل)
        user_link = f"<a href=\"tg://user?id={user_id}\">{display_name}</a>"
        text += f"• {user_link}\n"
        
    if len(users) > 100:
        text += "\n<i>(برای جلوگیری از طولانی شدن پیام، فقط ۱۰۰ کاربر اول نمایش داده شدند)</i>"
        
    await send_message(chat_id, text)