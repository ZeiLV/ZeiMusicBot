from typing import Optional

from pytgcalls import PyTgCalls
from pytgcalls.types import AudioQuality, VideoQuality
from pytgcalls.types.input_stream import AudioPiped, AudioVideoPiped

from utils.logger import log
from utils.queue import Track, queue


class StreamManager:
    def __init__(self):
        self._call: Optional[PyTgCalls] = None

    def setup(self, call: PyTgCalls):
        self._call = call
        self._register()

    def _register(self):
        @self._call.on_stream_end()
        async def on_end(_, update):
            chat_id = update.chat_id
            loop_mode = queue.get_loop(chat_id)

            if loop_mode == "track":
                cur = queue.current(chat_id)
                if cur:
                    await self.play(chat_id, cur)
            elif loop_mode == "queue":
                cur = queue.current(chat_id)
                nxt = queue.skip(chat_id)
                if cur:
                    queue.add(chat_id, cur)
                if nxt:
                    await self.play(chat_id, nxt)
            else:
                nxt = queue.skip(chat_id)
                if nxt:
                    await self.play(chat_id, nxt)
                    log.info(f"[{chat_id}] Keyingi: {nxt.title}")
                else:
                    log.info(f"[{chat_id}] Navbat tugadi")

        @self._call.on_closed_voice_chat()
        async def on_close(_, update):
            queue.clear(update.chat_id)

    async def play(self, chat_id: int, track: Track) -> bool:
        if not self._call:
            return False
        try:
            if track.is_video:
                stream = AudioVideoPiped(
                    track.file_path,
                    audio_parameters=AudioQuality.HIGH,
                    video_parameters=VideoQuality.HD_720p,
                )
            else:
                stream = AudioPiped(
                    track.file_path,
                    audio_parameters=AudioQuality.HIGH,
                )

            try:
                await self._call.change_stream(chat_id, stream)
            except Exception:
                await self._call.join_group_call(chat_id, stream)

            return True
        except Exception as e:
            log.error(f"[{chat_id}] Play xatosi: {e}")
            return False

    async def pause(self, chat_id: int) -> bool:
        try:
            await self._call.pause_stream(chat_id)
            return True
        except Exception as e:
            log.error(f"Pause xatosi: {e}")
            return False

    async def resume(self, chat_id: int) -> bool:
        try:
            await self._call.resume_stream(chat_id)
            return True
        except Exception as e:
            log.error(f"Resume xatosi: {e}")
            return False

    async def stop(self, chat_id: int) -> bool:
        try:
            await self._call.leave_group_call(chat_id)
            queue.clear(chat_id)
            return True
        except Exception as e:
            log.error(f"Stop xatosi: {e}")
            queue.clear(chat_id)
            return False

    async def seek(self, chat_id: int, seconds: int) -> bool:
        try:
            cur = queue.current(chat_id)
            if not cur:
                return False
            stream = AudioPiped(
                cur.file_path,
                audio_parameters=AudioQuality.HIGH,
                additional_ffmpeg_parameters=f"-ss {seconds}",
            )
            await self._call.change_stream(chat_id, stream)
            return True
        except Exception as e:
            log.error(f"Seek xatosi: {e}")
            return False


streamer = StreamManager()
