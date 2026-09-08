# handlers/admin.py
from core.api_client import send_message
from core.database import execute_query
from services.group_service import set_welcome, get_welcome, set_rules, get_rules, is_group_premium, set_group_premium
from services.permission_service import is_group_admin, is_super_admin

NO_PERMISSION_TEXT = "⛔ این دستور فقط برای ادمین‌های گروه در دسترس است."
NO_SUPER_PERMISSION_TEXT = "⛔ این دستور فقط برای مالک ربات در دسترس است."


async def handle_set_welcome(chat_id, text, user_id):
    if not await is_group_admin(chat_id, user_id):
        await send_message(chat_id, NO_PERMISSION_TEXT)
        return

    parts = text.split(" ", 1)
    if len(parts) < 2:
        await send_message(chat_id, "❌ استفاده: /setwelcome [متن خوش‌آمدگویی]")
        return
    welcome_text = parts[1]
    await set_welcome(chat_id, welcome_text)
    await send_message(chat_id, "✅ پیام خوش‌آمدگویی با موفقیت ذخیره شد.")


async def handle_set_rules(chat_id, text, user_id):
    if not await is_group_admin(chat_id, user_id):
        await send_message(chat_id, NO_PERMISSION_TEXT)
        return

    parts = text.split(" ", 1)
    if len(parts) < 2:
        await send_message(chat_id, "❌ استفاده: /setrules [متن قوانین]")
        return
    rules_text = parts[1]
    await set_rules(chat_id, rules_text)
    await send_message(chat_id, "✅ قوانین گروه با موفقیت ذخیره شد.")


async def handle_rules(chat_id):
    rules = await get_rules(chat_id)
    if rules:
        text = f"📜 <b>قوانین گروه</b>\n\n{rules}"
    else:
        text = "⚠️ هنوز قوانینی برای این گروه تنظیم نشده است."
    await send_message(chat_id, text)


async def handle_new_member(chat_id, new_member_name):
    welcome = await get_welcome(chat_id)
    if welcome:
        # جایگزینی اسم کاربر در متن (اگر از {name} استفاده کرده باشند)
        final_text = welcome.replace("{name}", new_member_name)
        text = f"👋 {final_text}"
        await send_message(chat_id, text)


async def handle_left_member(chat_id, left_member_name):
    text = f"👋 خداحافظ <b>{left_member_name}</b>! امیدواریم دوباره برگردی."
    await send_message(chat_id, text)


async def handle_set_premium(chat_id, text, user_id):
    """دستور: /setpremium on یا /setpremium off — فقط مالک ربات (ADMIN_ID) می‌تواند این کار را انجام دهد."""
    if not is_super_admin(user_id):
        await send_message(chat_id, NO_SUPER_PERMISSION_TEXT)
        return

    parts = text.split(" ", 1)
    if len(parts) < 2 or parts[1].strip().lower() not in ["on", "off"]:
        await send_message(chat_id, "❌ استفاده: /setpremium [on/off]")
        return

    status = parts[1].strip().lower() == "on"
    await set_group_premium(chat_id, status)
    if status:
        await send_message(chat_id, "💎 این گروه الان Premium شد! تمام محدودیت‌ها برداشته شد.")
    else:
        await send_message(chat_id, "⬇️ این گروه به نسخه رایگان برگشت.")


async def handle_group_stats(chat_id):
    is_premium = await is_group_premium(chat_id)
    if not is_premium:
        text = (
            "📊 <b>آمار گروه</b>\n\n"
            "🔒 این قابلیت فقط برای گروه‌های <b>Premium</b> در دسترس است.\n\n"
            "برای ارتقا گروه، با پشتیبانی در ارتباط باشید: @SupportID"
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
        "برای خرید با پشتیبانی در ارتباط باشید: @SupportID"
    )
    await send_message(chat_id, text)
