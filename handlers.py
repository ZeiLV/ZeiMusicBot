"""
ZeiMusicBot — Barcha handlerlar
"""
import time

from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, Message

import config
from utils.admin import is_admin
from utils.downloader import download_audio, download_video, make_track, search_yt
from utils.keyboards import loop_kb, player_kb, search_kb
from utils.logger import log
from utils.queue import Track, queue
from utils.streamer import streamer


# ═══════════════════════════════════════════════════════════
#  YORDAMCHI FUNKSIYALAR
# ═══════════════════════════════════════════════════════════

def dur(seconds: int) -> str:
    m, s = divmod(seconds, 60)
    h, m2 = divmod(m, 60)
    if h:
        return f"{h:02d}:{m2:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def now_playing_text(track: Track) -> str:
    emoji = "🎬" if track.is_video else "🎵"
    return (
        f"{emoji} **Ijro etilmoqda**\n\n"
        f"🎼 **{track.title}**\n"
        f"⏱ `{track.duration_str}`\n"
        f"👤 {track.requested_by_name}"
    )


def added_text(track: Track, pos: int) -> str:
    if pos == 1:
        return (
            f"▶️ **Ijro boshlanmoqda!**\n\n"
            f"🎼 **{track.title}**\n"
            f"⏱ `{track.duration_str}`"
        )
    return (
        f"✅ **Navbatga qo'shildi!**\n\n"
        f"🎼 **{track.title}**\n"
        f"⏱ `{track.duration_str}`\n"
        f"📋 Navbat: `#{pos}`"
    )


# ═══════════════════════════════════════════════════════════
#  /start va /help
# ═══════════════════════════════════════════════════════════

@Client.on_message(filters.command("start"))
async def cmd_start(client: Client, msg: Message):
    await msg.reply(
        f"🎵 **{config.BOT_NAME}**\n\n"
        "Guruhda Voice Chat yoqib, `/play` yozing!\n\n"
        "**Buyruqlar:**\n"
        "`/play` — Musiqa ijro\n"
        "`/vplay` — Video ijro\n"
        "`/queue` — Navbat\n"
        "`/help` — Yordam"
    )


@Client.on_message(filters.command("help"))
async def cmd_help(client: Client, msg: Message):
    await msg.reply(
        "📖 **Yordam**\n\n"
        "**🎵 Musiqa:**\n"
        "`/play [nom/url]` — Audio ijro\n"
        "`/vplay [nom/url]` — Video ijro\n"
        "`/pause` — To'xtatib turish\n"
        "`/resume` — Davom ettirish\n"
        "`/stop` — To'xtatish\n"
        "`/seek [soniya]` — Vaqtga o'tish\n"
        "`/replay` — Qayta boshlash\n"
        "`/loop` — Loop rejimi\n\n"
        "**📋 Navbat:**\n"
        "`/queue` — Navbatni ko'rish\n"
        "`/skip` — Keyingiga o'tish\n"
        "`/skipall` — Hammasini skip\n"
        "`/shuffle` — Aralashtirish\n"
        "`/remove [N]` — N-raqamni o'chirish\n"
        "`/clearqueue` — Navbatni tozalash\n\n"
        "**ℹ️ Boshqa:**\n"
        "`/ping` — Bot holati\n"
        "`/stats` — Statistika"
    )


# ═══════════════════════════════════════════════════════════
#  /ping va /stats
# ═══════════════════════════════════════════════════════════

_start_time = time.time()


@Client.on_message(filters.command("ping"))
async def cmd_ping(client: Client, msg: Message):
    s = time.time()
    m = await msg.reply("🏓 ...")
    ms = round((time.time() - s) * 1000, 1)
    up = int(time.time() - _start_time)
    d, r = divmod(up, 86400)
    h, r2 = divmod(r, 3600)
    mn, sc = divmod(r2, 60)
    uptime = f"{d}k {h}s {mn}d {sc}son" if d else f"{h}s {mn}d {sc}son"
    await m.edit(f"🏓 **Pong!**\n📡 `{ms}ms`\n⏱ `{uptime}`")


@Client.on_message(filters.command("stats"))
async def cmd_stats(client: Client, msg: Message):
    try:
        import psutil, os
        proc = psutil.Process(os.getpid())
        ram = proc.memory_info().rss / 1024 / 1024
        cpu = psutil.cpu_percent(0.1)
        await msg.reply(
            f"📊 **Bot Statistikasi**\n\n"
            f"💾 RAM: `{ram:.1f} MB`\n"
            f"🖥 CPU: `{cpu}%`"
        )
    except Exception:
        await msg.reply("📊 **Bot ishlayapti!**")


# ═══════════════════════════════════════════════════════════
#  /play
# ═══════════════════════════════════════════════════════════

@Client.on_message(filters.command(["play", "p"]) & filters.group)
async def cmd_play(client: Client, msg: Message):
    if not await is_admin(client, msg.chat.id, msg.from_user.id):
        return await msg.reply("❌ Faqat adminlar!")

    chat_id = msg.chat.id
    user = msg.from_user

    # Reply audio
    if msg.reply_to_message and (msg.reply_to_message.audio or msg.reply_to_message.voice):
        m = await msg.reply("⬇️ Yuklanmoqda...")
        r = msg.reply_to_message
        path = await client.download_media(r, file_name=f"downloads/tg_{msg.id}")
        media = r.audio or r.voice
        track = Track(
            title=getattr(media, "title", None) or getattr(media, "file_name", "Fayl") or "Fayl",
            url="telegram",
            duration=getattr(media, "duration", 0) or 0,
            file_path=path,
            requested_by=user.id,
            requested_by_name=user.first_name,
        )
        pos = queue.add(chat_id, track)
        if pos == 1:
            ok = await streamer.play(chat_id, track)
            if ok:
                await m.edit(now_playing_text(track), reply_markup=player_kb(chat_id))
            else:
                queue.clear(chat_id)
                await m.edit("❌ Voice Chat topilmadi! Avval VC yoqing.")
        else:
            await m.edit(added_text(track, pos), reply_markup=player_kb(chat_id))
        return

    if len(msg.command) < 2:
        return await msg.reply("❓ `/play [nom yoki url]`")

    query = " ".join(msg.command[1:])
    m = await msg.reply("🔍 Qidirilmoqda...")

    if not query.startswith("http"):
        results = await search_yt(query, 5)
        if not results:
            return await m.edit("❌ Topilmadi!")
        if len(results) == 1:
            query = results[0]["url"]
        else:
            return await m.edit(
                "🔍 **Natijalar:**\n\n" + "\n".join(
                    f"`{i}.` {r['title']} — `{dur(r['duration'])}`"
                    for i, r in enumerate(results, 1)
                ),
                reply_markup=search_kb(results, vplay=False),
            )

    await m.edit("⬇️ Yuklanmoqda...")
    path, info = await download_audio(query)
    if not path:
        return await m.edit("❌ Yuklab bo'lmadi!")

    track = make_track(info, path, user.id, user.first_name, is_video=False)
    pos = queue.add(chat_id, track)

    if pos == 1:
        ok = await streamer.play(chat_id, track)
        if ok:
            await m.edit(now_playing_text(track), reply_markup=player_kb(chat_id))
        else:
            queue.clear(chat_id)
            await m.edit("❌ Voice Chat topilmadi! Avval VC yoqing.")
    else:
        await m.edit(added_text(track, pos), reply_markup=player_kb(chat_id))


# ═══════════════════════════════════════════════════════════
#  /vplay
# ═══════════════════════════════════════════════════════════

@Client.on_message(filters.command(["vplay", "vp"]) & filters.group)
async def cmd_vplay(client: Client, msg: Message):
    if not await is_admin(client, msg.chat.id, msg.from_user.id):
        return await msg.reply("❌ Faqat adminlar!")

    chat_id = msg.chat.id
    user = msg.from_user

    if len(msg.command) < 2:
        return await msg.reply("❓ `/vplay [nom yoki url]`")

    query = " ".join(msg.command[1:])
    m = await msg.reply("🔍 Qidirilmoqda...")

    if not query.startswith("http"):
        results = await search_yt(query, 5)
        if not results:
            return await m.edit("❌ Topilmadi!")
        if len(results) == 1:
            query = results[0]["url"]
        else:
            return await m.edit(
                "🔍 **Natijalar:**\n\n" + "\n".join(
                    f"`{i}.` {r['title']} — `{dur(r['duration'])}`"
                    for i, r in enumerate(results, 1)
                ),
                reply_markup=search_kb(results, vplay=True),
            )

    await m.edit("⬇️ Video yuklanmoqda... _(bir necha daqiqa)_")
    path, info = await download_video(query)
    if not path:
        return await m.edit("❌ Video yuklab bo'lmadi!")

    track = make_track(info, path, user.id, user.first_name, is_video=True)
    pos = queue.add(chat_id, track)

    if pos == 1:
        ok = await streamer.play(chat_id, track)
        if ok:
            await m.edit("🎬 " + now_playing_text(track), reply_markup=player_kb(chat_id))
        else:
            queue.clear(chat_id)
            await m.edit("❌ Video Chat topilmadi!")
    else:
        await m.edit("🎬 " + added_text(track, pos), reply_markup=player_kb(chat_id))


# ═══════════════════════════════════════════════════════════
#  PLAYBACK CONTROLS
# ═══════════════════════════════════════════════════════════

@Client.on_message(filters.command("pause") & filters.group)
async def cmd_pause(client: Client, msg: Message):
    if not await is_admin(client, msg.chat.id, msg.from_user.id):
        return
    ok = await streamer.pause(msg.chat.id)
    cur = queue.current(msg.chat.id)
    if ok:
        await msg.reply(
            f"⏸ **To'xtatildi!**\n🎵 {cur.title if cur else ''}",
            reply_markup=player_kb(msg.chat.id, paused=True),
        )
    else:
        await msg.reply("❌ Hozir hech narsa ijro etilmayapti!")


@Client.on_message(filters.command("resume") & filters.group)
async def cmd_resume(client: Client, msg: Message):
    if not await is_admin(client, msg.chat.id, msg.from_user.id):
        return
    ok = await streamer.resume(msg.chat.id)
    cur = queue.current(msg.chat.id)
    if ok:
        await msg.reply(
            f"▶️ **Davom ettirildi!**\n🎵 {cur.title if cur else ''}",
            reply_markup=player_kb(msg.chat.id),
        )
    else:
        await msg.reply("❌ Xatolik!")


@Client.on_message(filters.command("stop") & filters.group)
async def cmd_stop(client: Client, msg: Message):
    if not await is_admin(client, msg.chat.id, msg.from_user.id):
        return
    await streamer.stop(msg.chat.id)
    await msg.reply("⏹ **To'xtatildi!**")


@Client.on_message(filters.command("seek") & filters.group)
async def cmd_seek(client: Client, msg: Message):
    if not await is_admin(client, msg.chat.id, msg.from_user.id):
        return
    if len(msg.command) < 2:
        return await msg.reply("❓ `/seek [soniya]`  Misol: `/seek 90`")
    try:
        sec = int(msg.command[1])
        assert sec >= 0
    except Exception:
        return await msg.reply("❌ To'g'ri soniya kiriting!")
    ok = await streamer.seek(msg.chat.id, sec)
    await msg.reply(f"⏩ `{dur(sec)}` ga o'tildi!" if ok else "❌ Xatolik!")


@Client.on_message(filters.command("replay") & filters.group)
async def cmd_replay(client: Client, msg: Message):
    if not await is_admin(client, msg.chat.id, msg.from_user.id):
        return
    cur = queue.current(msg.chat.id)
    if not cur:
        return await msg.reply("❌ Hech narsa ijro etilmayapti!")
    ok = await streamer.seek(msg.chat.id, 0)
    if ok:
        await msg.reply(f"🔄 Qayta boshlandi!\n🎵 {cur.title}")
    else:
        await streamer.play(msg.chat.id, cur)
        await msg.reply(f"🔄 Qayta boshlandi!\n🎵 {cur.title}")


@Client.on_message(filters.command("loop") & filters.group)
async def cmd_loop(client: Client, msg: Message):
    if not await is_admin(client, msg.chat.id, msg.from_user.id):
        return
    mode = queue.get_loop(msg.chat.id)
    await msg.reply(
        f"🔁 **Loop Rejimi**\nHozir: `{mode}`",
        reply_markup=loop_kb(msg.chat.id, mode),
    )


# ═══════════════════════════════════════════════════════════
#  NAVBAT BUYRUQLARI
# ═══════════════════════════════════════════════════════════

@Client.on_message(filters.command(["queue", "q"]) & filters.group)
async def cmd_queue(client: Client, msg: Message):
    tracks = queue.get_all(msg.chat.id)
    if not tracks:
        return await msg.reply("📋 **Navbat bo'sh!**\n`/play` bilan musiqa qo'shing.")

    lines = [f"📋 **Navbat** — {len(tracks)} ta\n"]
    for i, t in enumerate(tracks, 1):
        prefix = "▶️" if i == 1 else f"`{i}.`"
        lines.append(f"{prefix} {t.title} — `{t.duration_str}`")
    await msg.reply("\n".join(lines))


@Client.on_message(filters.command(["skip", "s"]) & filters.group)
async def cmd_skip(client: Client, msg: Message):
    if not await is_admin(client, msg.chat.id, msg.from_user.id):
        return
    cur = queue.current(msg.chat.id)
    if not cur:
        return await msg.reply("❌ Navbat bo'sh!")
    nxt = queue.skip(msg.chat.id)
    if nxt:
        ok = await streamer.play(msg.chat.id, nxt)
        if ok:
            await msg.reply(
                f"⏭ Skip!\n\n" + now_playing_text(nxt),
                reply_markup=player_kb(msg.chat.id),
            )
        else:
            await msg.reply("⏭ Skiplandi, lekin keyingi yuklanmadi!")
    else:
        await streamer.stop(msg.chat.id)
        await msg.reply("⏭ Skip! Navbat tugadi.")


@Client.on_message(filters.command(["skipall", "fs"]) & filters.group)
async def cmd_skipall(client: Client, msg: Message):
    if not await is_admin(client, msg.chat.id, msg.from_user.id):
        return
    n = queue.size(msg.chat.id)
    await streamer.stop(msg.chat.id)
    await msg.reply(f"⏭ {n} ta musiqa skiplandi!")


@Client.on_message(filters.command("shuffle") & filters.group)
async def cmd_shuffle(client: Client, msg: Message):
    if not await is_admin(client, msg.chat.id, msg.from_user.id):
        return
    ok = queue.shuffle(msg.chat.id)
    await msg.reply("🔀 Aralashtirildi!" if ok else "❌ Aralashtirish uchun kamida 3 ta musiqa kerak!")


@Client.on_message(filters.command("remove") & filters.group)
async def cmd_remove(client: Client, msg: Message):
    if not await is_admin(client, msg.chat.id, msg.from_user.id):
        return
    if len(msg.command) < 2:
        return await msg.reply("❓ `/remove [raqam]`  Misol: `/remove 3`")
    try:
        idx = int(msg.command[1])
    except ValueError:
        return await msg.reply("❌ Raqam kiriting!")
    if idx == 1:
        return await msg.reply("❌ Joriy musiqani o'chirish uchun `/skip` yozing!")
    removed = queue.remove(msg.chat.id, idx)
    if removed:
        await msg.reply(f"🗑 O'chirildi: **{removed.title}**")
    else:
        await msg.reply(f"❌ {idx}-raqam topilmadi! Navbatda {queue.size(msg.chat.id)} ta bor.")


@Client.on_message(filters.command(["clearqueue", "cq"]) & filters.group)
async def cmd_clearqueue(client: Client, msg: Message):
    if not await is_admin(client, msg.chat.id, msg.from_user.id):
        return
    n = queue.clear_except_current(msg.chat.id)
    cur = queue.current(msg.chat.id)
    if n > 0:
        await msg.reply(
            f"🗑 {n} ta musiqa o'chirildi!\n"
            f"▶️ Hozir: {cur.title if cur else '-'}"
        )
    else:
        await msg.reply("ℹ️ Navbat allaqachon bo'sh!")


# ═══════════════════════════════════════════════════════════
#  CALLBACK QUERYLAR (Tugmalar)
# ═══════════════════════════════════════════════════════════

@Client.on_callback_query(filters.regex(r"^pause:(-?\d+)$"))
async def cb_pause(client: Client, cb: CallbackQuery):
    chat_id = int(cb.matches[0].group(1))
    if not await is_admin(client, chat_id, cb.from_user.id):
        return await cb.answer("❌ Faqat adminlar!", show_alert=True)
    ok = await streamer.pause(chat_id)
    if ok:
        await cb.edit_message_reply_markup(player_kb(chat_id, paused=True))
        await cb.answer("⏸ To'xtatildi!")
    else:
        await cb.answer("❌ Xatolik!", show_alert=True)


@Client.on_callback_query(filters.regex(r"^resume:(-?\d+)$"))
async def cb_resume(client: Client, cb: CallbackQuery):
    chat_id = int(cb.matches[0].group(1))
    if not await is_admin(client, chat_id, cb.from_user.id):
        return await cb.answer("❌ Faqat adminlar!", show_alert=True)
    ok = await streamer.resume(chat_id)
    if ok:
        await cb.edit_message_reply_markup(player_kb(chat_id, paused=False))
        await cb.answer("▶️ Davom!")
    else:
        await cb.answer("❌ Xatolik!", show_alert=True)


@Client.on_callback_query(filters.regex(r"^skip:(-?\d+)$"))
async def cb_skip(client: Client, cb: CallbackQuery):
    chat_id = int(cb.matches[0].group(1))
    if not await is_admin(client, chat_id, cb.from_user.id):
        return await cb.answer("❌ Faqat adminlar!", show_alert=True)
    nxt = queue.skip(chat_id)
    if nxt:
        ok = await streamer.play(chat_id, nxt)
        if ok:
            await cb.message.edit(now_playing_text(nxt), reply_markup=player_kb(chat_id))
    else:
        await streamer.stop(chat_id)
        await cb.message.delete()
    await cb.answer("⏭ Skip!")


@Client.on_callback_query(filters.regex(r"^stop:(-?\d+)$"))
async def cb_stop(client: Client, cb: CallbackQuery):
    chat_id = int(cb.matches[0].group(1))
    if not await is_admin(client, chat_id, cb.from_user.id):
        return await cb.answer("❌ Faqat adminlar!", show_alert=True)
    await streamer.stop(chat_id)
    await cb.message.delete()
    await cb.answer("⏹ To'xtatildi!")


@Client.on_callback_query(filters.regex(r"^queue:(-?\d+)$"))
async def cb_queue(client: Client, cb: CallbackQuery):
    chat_id = int(cb.matches[0].group(1))
    tracks = queue.get_all(chat_id)
    if not tracks:
        return await cb.answer("📋 Navbat bo'sh!", show_alert=True)
    lines = [f"📋 **Navbat** — {len(tracks)} ta\n"]
    for i, t in enumerate(tracks, 1):
        prefix = "▶️" if i == 1 else f"`{i}.`"
        lines.append(f"{prefix} {t.title} — `{t.duration_str}`")
    await cb.answer()
    await cb.message.reply("\n".join(lines))


@Client.on_callback_query(filters.regex(r"^shuffle:(-?\d+)$"))
async def cb_shuffle(client: Client, cb: CallbackQuery):
    chat_id = int(cb.matches[0].group(1))
    if not await is_admin(client, chat_id, cb.from_user.id):
        return await cb.answer("❌ Faqat adminlar!", show_alert=True)
    ok = queue.shuffle(chat_id)
    await cb.answer("🔀 Aralashtirildi!" if ok else "❌ Musiqa kam!")


@Client.on_callback_query(filters.regex(r"^loop:(-?\d+)$"))
async def cb_loop(client: Client, cb: CallbackQuery):
    chat_id = int(cb.matches[0].group(1))
    if not await is_admin(client, chat_id, cb.from_user.id):
        return await cb.answer("❌ Faqat adminlar!", show_alert=True)
    mode = queue.get_loop(chat_id)
    await cb.message.reply(f"🔁 Loop: `{mode}`", reply_markup=loop_kb(chat_id, mode))
    await cb.answer()


@Client.on_callback_query(filters.regex(r"^lp:(-?\d+):(\w+)$"))
async def cb_set_loop(client: Client, cb: CallbackQuery):
    chat_id = int(cb.matches[0].group(1))
    mode = cb.matches[0].group(2)
    if not await is_admin(client, chat_id, cb.from_user.id):
        return await cb.answer("❌ Faqat adminlar!", show_alert=True)
    queue.set_loop(chat_id, mode)
    names = {"off": "O'chiq", "track": "Track", "queue": "Navbat"}
    await cb.edit_message_reply_markup(loop_kb(chat_id, mode))
    await cb.answer(f"🔁 Loop: {names.get(mode, mode)}")


@Client.on_callback_query(filters.regex(r"^sa:(.+)$"))
async def cb_select_audio(client: Client, cb: CallbackQuery):
    url = cb.matches[0].group(1)
    chat_id = cb.message.chat.id
    user = cb.from_user

    await cb.message.edit("⬇️ Yuklanmoqda...")
    path, info = await download_audio(url)
    if not path:
        return await cb.message.edit("❌ Yuklab bo'lmadi!")

    track = make_track(info, path, user.id, user.first_name)
    pos = queue.add(chat_id, track)

    if pos == 1:
        ok = await streamer.play(chat_id, track)
        if ok:
            await cb.message.edit(now_playing_text(track), reply_markup=player_kb(chat_id))
        else:
            queue.clear(chat_id)
            await cb.message.edit("❌ Voice Chat topilmadi!")
    else:
        await cb.message.edit(added_text(track, pos), reply_markup=player_kb(chat_id))
    await cb.answer()


@Client.on_callback_query(filters.regex(r"^sv:(.+)$"))
async def cb_select_video(client: Client, cb: CallbackQuery):
    url = cb.matches[0].group(1)
    chat_id = cb.message.chat.id
    user = cb.from_user

    await cb.message.edit("⬇️ Video yuklanmoqda...")
    path, info = await download_video(url)
    if not path:
        return await cb.message.edit("❌ Yuklab bo'lmadi!")

    track = make_track(info, path, user.id, user.first_name, is_video=True)
    pos = queue.add(chat_id, track)

    if pos == 1:
        ok = await streamer.play(chat_id, track)
        if ok:
            await cb.message.edit("🎬 " + now_playing_text(track), reply_markup=player_kb(chat_id))
        else:
            queue.clear(chat_id)
            await cb.message.edit("❌ Video Chat topilmadi!")
    else:
        await cb.message.edit("🎬 " + added_text(track, pos), reply_markup=player_kb(chat_id))
    await cb.answer()


@Client.on_callback_query(filters.regex(r"^close$"))
async def cb_close(client: Client, cb: CallbackQuery):
    await cb.message.delete()
    await cb.answer()


# ═══════════════════════════════════════════════════════════
#  HANDLERLARNI RO'YXATDAN O'TKAZISH
# ═══════════════════════════════════════════════════════════

def register_handlers(bot: Client, call):
    streamer.setup(call)
    log.info("Barcha handlerlar yuklandi!")
