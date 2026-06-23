import logging
import os

os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/bot.log", encoding="utf-8"),
    ],
)

log = logging.getLogger("ZeiBot")

# Keraksiz loglarni o'chirish
for name in ["pyrogram", "pytgcalls"]:
    logging.getLogger(name).setLevel(logging.WARNING)
