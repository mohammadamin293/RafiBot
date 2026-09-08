# services/permission_service.py
"""
بررسی سطح دسترسی کاربران:
- Super Admin: مالک ربات (ADMIN_ID در .env) — دسترسی کامل به همه گروه‌ها، از جمله /setpremium
- Group Admin: ادمین/سازنده همون گروه تلگرام/سروش که دستور توش زده شده — دسترسی به دستورات مدیریتی گروه
"""
import logging
from config import ADMIN_ID
from core.api_client import get_chat_member

GROUP_ADMIN_STATUSES = {"administrator", "creator", "owner"}


def is_super_admin(user_id) -> bool:
    """آیا کاربر، مالک/ادمین اصلی ربات است؟"""
    return ADMIN_ID != 0 and int(user_id) == ADMIN_ID


async def is_group_admin(chat_id, user_id) -> bool:
    """
    آیا کاربر در همین گروه ادمین یا سازنده است؟
    مالک ربات (super admin) همیشه true برمی‌گردد.
    """
    if is_super_admin(user_id):
        return True

    result = await get_chat_member(chat_id, user_id)
    if not result or not result.get("ok"):
        # اگر نتونستیم وضعیت رو بگیریم، برای امنیت دسترسی رد می‌شود
        logging.error(f"getChatMember failed for chat={chat_id} user={user_id}: {result}")
        return False

    status = result.get("result", {}).get("status", "")
    return status in GROUP_ADMIN_STATUSES
