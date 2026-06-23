import asyncio
import os
import sys

from pyrogram import Client, idle
from pytgcalls import PyTgCalls

import config
from handlers import register_handlers
from utils.logger import log

# Bot client
bot = Client(
    name="ZeiMusicBot",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN,
)

# Userbot client (Voice Chat uchun)
userbot = Client(
    name="ZeiUserBot",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    session_string=config.SESSION_STRING,
)

# PyTgCalls (streaming)
call = PyTgCalls(userbot)


async def main():
    os.makedirs(config.DOWNLOAD_DIR, exist_ok=True)

    log.info("Bot ishga tushmoqda...")

    await userbot.start()
    log.info("Userbot ulandi!")

    await call.start()
    log.info("PyTgCalls ulandi!")

    await bot.start()
    me = await bot.get_me()
    log.info(f"Bot ulandi: @{me.username}")

    # Handlerlarni ro'yxatdan o'tkazish
    register_handlers(bot, call)

    log.info("=" * 40)
    log.info(f"  {config.BOT_NAME} ishga tushdi!")
    log.info("=" * 40)

    await idle()

    await bot.stop()
    await call.stop()
    await userbot.stop()


if __name__ == "__main__":
    if not config.API_ID or not config.API_HASH or not config.BOT_TOKEN or not config.SESSION_STRING:
        print("❌ config.py ni to'ldiring!")
        sys.exit(1)
    asyncio.run(main())
