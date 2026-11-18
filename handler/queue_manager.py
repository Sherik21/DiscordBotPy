from collections import deque
from enum import Enum, auto
import random
from handler.track import Track

class RepeatMode(Enum):
    NONE = auto()
    ONE = auto()
    ALL = auto()

    @property
    def status_message(self) -> str:
        messages = {
            RepeatMode.NONE: "repeat.repeat_disabled",
            RepeatMode.ONE: "repeat.one_enabled",
            RepeatMode.ALL: "repeat.all_enabled"
        }
        return messages[self]

class QueueManager:
    def __init__(self):
        self.__current_track = Track()
        self.__queue = deque()
        self.__history = deque()
        self.__repeat_mode = RepeatMode.NONE

    def add_track(self, track: Track) -> None:
        self.__queue.append(track)

    def add_tracks(self, tracks: list[Track]) -> None:
        self.__queue.extend(tracks)

    def shuffle(self) -> bool:
        if len(self.__queue) < 2:
            return False
        items = list(self.__queue)
        random.shuffle(items)
        self.__queue = deque(items)
        return True

    def clear_queue(self) -> int:
        count = len(self.__queue)
        self.__queue.clear()
        return count

    def remove_track(self, index: int) -> Track | None:
        if 0 <= index < len(self.__queue):
            item = self.__queue[index]
            del self.__queue[index]
            return item
        return None

    @property
    def repeat_mode(self) -> RepeatMode:
        return self.__repeat_mode

    @repeat_mode.setter
    def repeat_mode(self, mode: RepeatMode):
        self.__repeat_mode = mode

    @property
    def queue_empty(self) -> bool:
        return len(self.__queue) == 0

    @property
    def history_empty(self) -> bool:
        return len(self.__history) == 0

    @property
    def queue_size(self) -> int:
        return len(self.__queue)

    @property
    def history_size(self) -> int:
        return len(self.__history)

    @property
    def current_track(self) -> Track:
        if self.__current_track.empty:
            self.__current_track = self.next_track()
        return self.__current_track

    def get_current_track_for_embed(self) -> Track | None:
        return self.__current_track

    @current_track.setter
    def current_track(self, track: Track):
        self.__current_track = track

    @property
    def queue(self) -> list:
        return list(self.__queue)

    @property
    def history(self) -> list:
        return list(self.__history)

    def clear_current(self):
        if not self.__current_track.empty:
            self.__history.append(self.__current_track)
        self.__current_track = Track()

    def next_track(self, force_skip: bool = False) -> Track | None:
        if self.__repeat_mode == RepeatMode.ONE and not self.__current_track.empty and not force_skip:
            return self.__current_track

        if not self.__current_track.empty:
            if self.__repeat_mode == RepeatMode.ALL:
                self.__queue.append(self.__current_track)
            else:
                self.__history.append(self.__current_track)

        if not self.__queue:
            self.__current_track = Track()
            return None

        self.__current_track = self.__queue.popleft()
        return self.__current_track

    def back_track(self) -> Track | None:
        if not self.__history:
            self.__current_track = Track()
            return None

        if not self.__current_track.empty:
            self.__queue.append(self.__current_track)

        self.__current_track = self.__history.pop()
        return self.__current_track
