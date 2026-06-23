from pyrogram import Client
from pyrogram.enums import ChatMemberStatus

import config

# Cache: {chat_id: [user_id, ...]}
_admin_cache: dict = {}


async def is_admin(client: Client, chat_id: int, user_id: int) -> bool:
    if user_id == config.OWNER_ID:
        return True

    if chat_id in _admin_cache:
        return user_id in _admin_cache[chat_id]

    try:
        admins = []
        async for m in client.get_chat_members(chat_id, filter=ChatMemberStatus.ADMINISTRATOR):
            admins.append(m.user.id)
        _admin_cache[chat_id] = admins
        return user_id in admins
    except Exception:
        return False


def clear_admin_cache(chat_id: int):
    _admin_cache.pop(chat_id, None)
