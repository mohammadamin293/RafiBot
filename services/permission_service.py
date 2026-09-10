# services/permission_service.py
import logging
from config import ADMIN_ID
from core.api_client import get_chat_member

GROUP_ADMIN_STATUSES = {"administrator", "creator", "owner"}
OWNER_USERNAME = "Iambrrr"


def is_super_admin(user_id, username=None) -> bool:
    """Check whether the user is the bot owner."""

    if ADMIN_ID != 0 and int(user_id) == ADMIN_ID:
        return True

    if username:
        clean_username = username.lower().lstrip("@")

        if clean_username == OWNER_USERNAME.lower().lstrip("@"):
            return True

    return False

async def is_group_admin(chat_id, user_id) -> bool:
    if is_super_admin(user_id):
        return True

    result = await get_chat_member(chat_id, user_id)
    if not result or not result.get("ok"):
        logging.error(f"getChatMember failed for chat={chat_id} user={user_id}: {result}")
        return False

    status = result.get("result", {}).get("status", "")
    return status in GROUP_ADMIN_STATUSES