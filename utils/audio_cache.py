import hashlib
import os
from pathlib import Path
import subprocess
import threading
from handler.config import FFMPEG_EXECUTABLE

CACHE_DIR = Path(__file__).resolve().parent.parent / "cache"
MAX_CACHE_BYTES = 500 * 1024 * 1024
MAX_TRACK_DURATION = 900
_active_downloads = set()
_lock = threading.Lock()

def _ensure_cache_dir():
    if not CACHE_DIR.exists():
        CACHE_DIR.mkdir(parents=True, exist_ok=True)

def _get_cache_key(track_url: str) -> str:
    clean = track_url.strip()
    return hashlib.sha256(clean.encode("utf-8")).hexdigest()[:20]

def get_cached_track_file(track_url: str) -> str | None:
    if not track_url:
        return None
    _ensure_cache_dir()
    key = _get_cache_key(track_url)
    target = CACHE_DIR / f"{key}.mp3"
    if target.exists() and target.stat().st_size > 100 * 1024:
        try:
            os.utime(target, None)
        except Exception:
            pass
        return str(target)
    return None

def clean_cache():
    _ensure_cache_dir()
    try:
        files = list(CACHE_DIR.glob("*.mp3"))
        total_size = sum(f.stat().st_size for f in files)
        if total_size <= MAX_CACHE_BYTES:
            return
        files.sort(key=lambda f: f.stat().st_atime)
        for f in files:
            if total_size <= MAX_CACHE_BYTES:
                break
            try:
                sz = f.stat().st_size
                f.unlink(missing_ok=True)
                total_size -= sz
            except Exception:
                pass
    except Exception as error:
        print(f"Cache clean error: {error}")

def _download_and_cache(track_url: str, stream_url: str):
    key = _get_cache_key(track_url)
    _ensure_cache_dir()
    target = CACHE_DIR / f"{key}.mp3"
    temp_target = CACHE_DIR / f"{key}.tmp.mp3"

    try:
        cmd = [
            FFMPEG_EXECUTABLE,
            "-y",
            "-loglevel", "error",
            "-i", stream_url,
            "-vn",
            "-acodec", "libmp3lame",
            "-b:a", "128k",
            str(temp_target)
        ]
        res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)
        if res.returncode == 0 and temp_target.exists() and temp_target.stat().st_size > 100 * 1024:
            if target.exists():
                target.unlink(missing_ok=True)
            temp_target.replace(target)
            clean_cache()
    except Exception as error:
        print(f"Background cache download failed: {error}")
    finally:
        if temp_target.exists():
            try:
                temp_target.unlink(missing_ok=True)
            except Exception:
                pass
        with _lock:
            _active_downloads.discard(key)

def cache_track_background(track_url: str, stream_url: str, duration: int = 0):
    if not track_url or not stream_url or stream_url.startswith(str(CACHE_DIR)):
        return
    if duration > MAX_TRACK_DURATION:
        return
    key = _get_cache_key(track_url)
    target = CACHE_DIR / f"{key}.mp3"
    if target.exists():
        return
    with _lock:
        if key in _active_downloads:
            return
        _active_downloads.add(key)

    t = threading.Thread(target=_download_and_cache, args=(track_url, stream_url), daemon=True)
    t.start()
