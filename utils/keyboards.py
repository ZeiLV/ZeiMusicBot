from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def player_kb(chat_id: int, paused: bool = False) -> InlineKeyboardMarkup:
    pause_btn = (
        InlineKeyboardButton("▶️ Davom", callback_data=f"resume:{chat_id}")
        if paused else
        InlineKeyboardButton("⏸ Pauza", callback_data=f"pause:{chat_id}")
    )
    return InlineKeyboardMarkup([
        [
            pause_btn,
            InlineKeyboardButton("⏭ Skip", callback_data=f"skip:{chat_id}"),
            InlineKeyboardButton("⏹ Stop", callback_data=f"stop:{chat_id}"),
        ],
        [
            InlineKeyboardButton("📋 Navbat", callback_data=f"queue:{chat_id}"),
            InlineKeyboardButton("🔀 Aralashtir", callback_data=f"shuffle:{chat_id}"),
            InlineKeyboardButton("🔁 Loop", callback_data=f"loop:{chat_id}"),
        ],
        [
            InlineKeyboardButton("❌ Yopish", callback_data="close"),
        ],
    ])


def search_kb(results: list, vplay: bool = False) -> InlineKeyboardMarkup:
    cmd = "sv" if vplay else "sa"
    rows = []
    for i, r in enumerate(results[:5], 1):
        title = r["title"][:40] + "..." if len(r["title"]) > 40 else r["title"]
        rows.append([InlineKeyboardButton(
            f"{i}. {title}",
            callback_data=f"{cmd}:{r['url']}",
        )])
    rows.append([InlineKeyboardButton("❌ Bekor", callback_data="close")])
    return InlineKeyboardMarkup(rows)


def loop_kb(chat_id: int, mode: str) -> InlineKeyboardMarkup:
    def mark(m): return "✅ " if mode == m else ""
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(f"{mark('off')}❌ Off", callback_data=f"lp:{chat_id}:off"),
        InlineKeyboardButton(f"{mark('track')}🔂 Track", callback_data=f"lp:{chat_id}:track"),
        InlineKeyboardButton(f"{mark('queue')}🔁 Navbat", callback_data=f"lp:{chat_id}:queue"),
    ]])
