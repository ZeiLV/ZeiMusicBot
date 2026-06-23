import asyncio
import hashlib
import os
from typing import Optional, Tuple

import yt_dlp

import config
from utils.logger import log
from utils.queue import Track


def _audio_opts(out_path: str) -> dict:
    return {
        "format": "bestaudio/best",
        "outtmpl": out_path,
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": str(config.AUDIO_QUALITY),
        }],
    }


def _video_opts(out_path: str) -> dict:
    return {
        "format": f"bestvideo[height<={config.VIDEO_QUALITY}]+bestaudio/best",
        "outtmpl": out_path,
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "merge_output_format": "mp4",
    }


def _info_opts() -> dict:
    return {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "noplaylist": True,
    }


async def search_yt(query: str, n: int = 5) -> list:
    loop = asyncio.get_event_loop()

    def _do():
        opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": True,
            "default_search": f"ytsearch{n}",
        }
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(query, download=False)
            results = []
            for e in (info.get("entries") or []):
                results.append({
                    "title": e.get("title", "Noma'lum"),
                    "url": f"https://youtube.com/watch?v={e.get('id','')}",
                    "duration": e.get("duration", 0),
                    "thumbnail": e.get("thumbnail", ""),
                })
            return results

    try:
        return await loop.run_in_executor(None, _do)
    except Exception as e:
        log.error(f"Qidiruv xatosi: {e}")
        return []


async def download_audio(url_or_query: str) -> Tuple[Optional[str], Optional[dict]]:
    if not url_or_query.startswith("http"):
        results = await search_yt(url_or_query, 1)
        if not results:
            return None, None
        url_or_query = results[0]["url"]

    uid = hashlib.md5(url_or_query.encode()).hexdigest()[:10]
    out = os.path.join(config.DOWNLOAD_DIR, f"{uid}.%(ext)s")
    loop = asyncio.get_event_loop()

    def _do():
        with yt_dlp.YoutubeDL(_audio_opts(out)) as ydl:
            return ydl.extract_info(url_or_query, download=True)

    try:
        log.info(f"Audio yuklanmoqda: {url_or_query}")
        info = await loop.run_in_executor(None, _do)

        for ext in ["mp3", "m4a", "webm", "ogg"]:
            path = os.path.join(config.DOWNLOAD_DIR, f"{uid}.{ext}")
            if os.path.exists(path):
                return path, info

        return None, info
    except Exception as e:
        log.error(f"Audio yuklash xatosi: {e}")
        return None, None


async def download_video(url_or_query: str) -> Tuple[Optional[str], Optional[dict]]:
    if not url_or_query.startswith("http"):
        results = await search_yt(url_or_query, 1)
        if not results:
            return None, None
        url_or_query = results[0]["url"]

    uid = hashlib.md5(url_or_query.encode()).hexdigest()[:10]
    out = os.path.join(config.DOWNLOAD_DIR, f"v{uid}.%(ext)s")
    loop = asyncio.get_event_loop()

    def _do():
        with yt_dlp.YoutubeDL(_video_opts(out)) as ydl:
            return ydl.extract_info(url_or_query, download=True)

    try:
        log.info(f"Video yuklanmoqda: {url_or_query}")
        info = await loop.run_in_executor(None, _do)

        for ext in ["mp4", "mkv", "webm"]:
            path = os.path.join(config.DOWNLOAD_DIR, f"v{uid}.{ext}")
            if os.path.exists(path):
                return path, info

        return None, info
    except Exception as e:
        log.error(f"Video yuklash xatosi: {e}")
        return None, None


def make_track(info: dict, file_path: str, user_id: int,
               user_name: str, is_video: bool = False) -> Track:
    return Track(
        title=info.get("title", "Noma'lum"),
        url=info.get("webpage_url", ""),
        duration=int(info.get("duration", 0)),
        file_path=file_path,
        requested_by=user_id,
        requested_by_name=user_name,
        is_video=is_video,
        thumbnail=info.get("thumbnail", ""),
    )
