import random
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class Track:
    title: str
    url: str
    duration: int       # soniya
    file_path: str
    requested_by: int
    requested_by_name: str
    is_video: bool = False
    thumbnail: str = ""

    @property
    def duration_str(self) -> str:
        m, s = divmod(self.duration, 60)
        h, m2 = divmod(m, 60)
        if h:
            return f"{h:02d}:{m2:02d}:{s:02d}"
        return f"{m:02d}:{s:02d}"


class Queue:
    def __init__(self):
        self._data: Dict[int, List[Track]] = {}
        self._loop: Dict[int, str] = {}   # off | track | queue

    def add(self, chat_id: int, track: Track) -> int:
        if chat_id not in self._data:
            self._data[chat_id] = []
        self._data[chat_id].append(track)
        return len(self._data[chat_id])

    def get_all(self, chat_id: int) -> List[Track]:
        return self._data.get(chat_id, [])

    def current(self, chat_id: int) -> Optional[Track]:
        q = self.get_all(chat_id)
        return q[0] if q else None

    def skip(self, chat_id: int) -> Optional[Track]:
        q = self._data.get(chat_id, [])
        if q:
            q.pop(0)
        return q[0] if q else None

    def remove(self, chat_id: int, index: int) -> Optional[Track]:
        # index 1 dan boshlanadi, 1-raqam joriy track
        q = self._data.get(chat_id, [])
        if index < 2 or index > len(q):
            return None
        return q.pop(index - 1)

    def clear(self, chat_id: int):
        self._data[chat_id] = []

    def clear_except_current(self, chat_id: int) -> int:
        q = self._data.get(chat_id, [])
        if len(q) <= 1:
            return 0
        count = len(q) - 1
        self._data[chat_id] = [q[0]]
        return count

    def shuffle(self, chat_id: int) -> bool:
        q = self._data.get(chat_id, [])
        if len(q) < 3:
            return False
        current = q[0]
        rest = q[1:]
        random.shuffle(rest)
        self._data[chat_id] = [current] + rest
        return True

    def size(self, chat_id: int) -> int:
        return len(self.get_all(chat_id))

    def is_empty(self, chat_id: int) -> bool:
        return self.size(chat_id) == 0

    def set_loop(self, chat_id: int, mode: str):
        self._loop[chat_id] = mode

    def get_loop(self, chat_id: int) -> str:
        return self._loop.get(chat_id, "off")


# Global queue
queue = Queue()
