import asyncio
import time
import discord
from .track import Track
from .config import FFMPEG_OPTIONS, FFMPEG_EXECUTABLE
from .queue_manager import QueueManager, RepeatMode
from utils.utils import updateWorkingStreamLink

class MusicHandler:
    def __init__(self, bot):
        self.__queue_manager = QueueManager()
        self.__is_playing: bool = False
        self.__stop_flag: bool = False
        self.__skip_flag: bool = False
        self.__back_flag: bool = False
        self.__seeking: bool = False
        self.__volume: float = 1.0
        self.__bot = bot
        self.__idle_task: asyncio.Task | None = None
        self.__start_time: float = 0.0
        self.__paused_duration: float = 0.0
        self.__pause_start: float = 0.0

    def get_current_track(self) -> Track | None:
        return self.__queue_manager.get_current_track_for_embed()

    def get_queue(self) -> list:
        return self.__queue_manager.queue

    def get_history(self) -> list:
        return self.__queue_manager.history

    def add_track(self, track: Track) -> None:
        self.__cancel_idle_timer()
        self.__queue_manager.add_track(track)

    def add_tracks(self, tracks: list[Track]) -> None:
        self.__cancel_idle_timer()
        self.__queue_manager.add_tracks(tracks)

    def shuffle(self) -> bool:
        return self.__queue_manager.shuffle()

    def clear_queue(self) -> int:
        return self.__queue_manager.clear_queue()

    def remove_track(self, index: int) -> Track | None:
        return self.__queue_manager.remove_track(index)

    def toggle_repeat_mode(self, target_mode: RepeatMode) -> RepeatMode:
        current = self.__queue_manager.repeat_mode
        if current == target_mode:
            self.__queue_manager.repeat_mode = RepeatMode.NONE
        else:
            self.__queue_manager.repeat_mode = target_mode
        return self.__queue_manager.repeat_mode

    def cycle_repeat_mode(self) -> RepeatMode:
        current = self.__queue_manager.repeat_mode
        if current == RepeatMode.NONE:
            self.__queue_manager.repeat_mode = RepeatMode.ONE
        elif current == RepeatMode.ONE:
            self.__queue_manager.repeat_mode = RepeatMode.ALL
        else:
            self.__queue_manager.repeat_mode = RepeatMode.NONE
        return self.__queue_manager.repeat_mode

    @property
    def queue_empty(self) -> bool:
        return self.__queue_manager.queue_empty

    @property
    def history_empty(self) -> bool:
        return self.__queue_manager.history_empty

    @property
    def is_playing(self) -> bool:
        return self.__is_playing

    @property
    def back_flag(self) -> bool:
        return self.__back_flag

    @back_flag.setter
    def back_flag(self, flag: bool):
        self.__back_flag = flag

    @property
    def skip_flag(self) -> bool:
        return self.__skip_flag

    @skip_flag.setter
    def skip_flag(self, flag: bool):
        self.__skip_flag = flag

    @property
    def stop_flag(self) -> bool:
        return self.__stop_flag

    @stop_flag.setter
    def stop_flag(self, flag: bool):
        self.__stop_flag = flag

    def set_stop_flag(self, flag: bool) -> None:
        self.__stop_flag = flag

    def get_volume(self) -> int:
        return round(self.__volume * 100)

    def set_volume(self, percentage: int, voice: discord.VoiceClient | None = None) -> int:
        clamped = max(1, min(100, percentage))
        self.__volume = clamped / 100.0
        if voice and voice.source and isinstance(voice.source, discord.PCMVolumeTransformer):
            voice.source.volume = self.__volume
        return clamped

    def get_playback_position(self) -> int:
        if not self.__is_playing or self.__start_time == 0.0:
            return 0
        now = time.time()
        elapsed = now - self.__start_time - self.__paused_duration
        if self.__pause_start > 0.0:
            elapsed -= (now - self.__pause_start)
        return max(0, int(elapsed))

    def pause(self, voice: discord.VoiceClient) -> bool:
        if voice and voice.is_playing():
            voice.pause()
            self.__pause_start = time.time()
            return True
        return False

    def resume(self, voice: discord.VoiceClient) -> bool:
        if voice and voice.is_paused():
            voice.resume()
            if self.__pause_start > 0.0:
                self.__paused_duration += time.time() - self.__pause_start
                self.__pause_start = 0.0
            return True
        return False

    def clear(self) -> None:
        self.__cancel_idle_timer()
        self.__stop_flag = True
        self.__is_playing = False
        self.__queue_manager.clear_current()
        self.__start_time = 0.0
        self.__paused_duration = 0.0
        self.__pause_start = 0.0

    def __cancel_idle_timer(self):
        if self.__idle_task and not self.__idle_task.done():
            self.__idle_task.cancel()
            self.__idle_task = None

    def __start_idle_timer(self, voice: discord.VoiceProtocol):
        self.__cancel_idle_timer()
        self.__idle_task = asyncio.create_task(self.__idle_disconnect(voice))

    async def __idle_disconnect(self, voice: discord.VoiceProtocol):
        try:
            await asyncio.sleep(180)
            if not self.__is_playing and self.__queue_manager.queue_empty:
                if hasattr(voice, "is_connected") and voice.is_connected():
                    await voice.disconnect()
                self.clear()
        except asyncio.CancelledError:
            pass

    async def seek(self, seconds: int, voice: discord.VoiceProtocol) -> bool:
        current_track = self.__queue_manager.get_current_track_for_embed()
        if not current_track or current_track.empty:
            return False

        if hasattr(voice, "is_playing") and voice.is_playing():
            self.__seeking = True
            voice.stop()
            await asyncio.sleep(0.15)
            self.__seeking = False

        self.__is_playing = True

        custom_before_options = f"-ss {seconds} {FFMPEG_OPTIONS.get('before_options', '')}"
        try:
            raw_source = discord.FFmpegPCMAudio(
                current_track.stream_url,
                executable=FFMPEG_EXECUTABLE,
                before_options=custom_before_options,
                options=FFMPEG_OPTIONS.get("options", "-vn")
            )
            source = discord.PCMVolumeTransformer(raw_source, volume=self.__volume)
            self.__start_time = time.time() - seconds
            self.__paused_duration = 0.0
            self.__pause_start = 0.0

            def _after_seek(err):
                if self.__seeking:
                    return
                if err:
                    print(f"Seek playback error: {err}")
                asyncio.run_coroutine_threadsafe(
                    self.player(voice),
                    self.__bot.loop
                )

            voice.play(source, after=_after_seek)
            return True
        except Exception as error:
            print(f"Error during seek: {error}")
            self.__is_playing = False
            return False

    async def seek_relative(self, offset: int, voice: discord.VoiceProtocol) -> tuple[bool, int]:
        current_pos = self.get_playback_position()
        target_pos = max(0, current_pos + offset)
        current_track = self.__queue_manager.get_current_track_for_embed()
        if current_track and current_track.duration > 0:
            target_pos = min(target_pos, current_track.duration - 1)
        ok = await self.seek(target_pos, voice)
        return ok, target_pos

    async def player(self, voice: discord.VoiceProtocol):
        if not voice or not getattr(voice, "is_connected", lambda: True)():
            self.__is_playing = False
            return

        self.__is_playing = True

        if self.__stop_flag:
            self.__stop_flag = False
            self.__is_playing = False
            self.__queue_manager.clear_current()
            self.__start_idle_timer(voice)
            return

        if self.__skip_flag:
            self.__skip_flag = False
            track = self.__queue_manager.next_track(force_skip=True)
        elif self.__back_flag:
            self.__back_flag = False
            track = self.__queue_manager.back_track()
        else:
            track = self.__queue_manager.next_track()

        if not track or track.empty:
            self.__is_playing = False
            self.__start_idle_timer(voice)
            return

        self.__cancel_idle_timer()

        try:
            self.__queue_manager.current_track = await updateWorkingStreamLink(track)
            current = self.__queue_manager.current_track
            if not current.stream_url:
                raise ValueError(f"No stream URL found for {current.title}")
            await self.__play(track=current, voice=voice)
        except Exception as error:
            print(f"Error updating track: {error}")
            self.__is_playing = False
            self.__start_idle_timer(voice)

    async def __play(self, track: Track, voice: discord.VoiceProtocol):
        try:
            if hasattr(voice, "is_playing") and voice.is_playing():
                voice.stop()
            if hasattr(voice, "_connection") and getattr(voice._connection, "dave_protocol_version", 0) > 0:
                for _ in range(40):
                    if getattr(voice._connection, "can_encrypt", False):
                        break
                    await asyncio.sleep(0.05)
            raw_source = discord.FFmpegPCMAudio(
                track.stream_url,
                executable=FFMPEG_EXECUTABLE,
                **FFMPEG_OPTIONS
            )
            source = discord.PCMVolumeTransformer(raw_source, volume=self.__volume)
            self.__start_time = time.time()
            self.__paused_duration = 0.0
            self.__pause_start = 0.0

            def _after_play(err):
                if self.__seeking:
                    return
                if err:
                    print(f"Audio playback error: {err}")
                asyncio.run_coroutine_threadsafe(
                    self.player(voice),
                    self.__bot.loop
                )

            voice.play(source, after=_after_play)
        except Exception as error:
            print(f"Error during audio playback: {error}")
            self.__is_playing = False
            self.__start_idle_timer(voice)
