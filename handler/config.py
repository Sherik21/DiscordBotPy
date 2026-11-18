import os
from pathlib import Path
import shutil
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

class NoWarningLogger:
    def debug(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        print(msg)

def get_ffmpeg_executable() -> str:
    path = shutil.which("ffmpeg")
    if path:
        return path
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"

def get_js_runtime() -> dict | None:
    deno_standard = r"C:\Users\Sherik\AppData\Local\Microsoft\WinGet\Packages\DenoLand.Deno_Microsoft.Winget.Source_8wekyb3d8bbwe\deno.exe"
    if os.path.exists(deno_standard):
        return {"deno": {"path": deno_standard}}
    deno_path = shutil.which("deno")
    if deno_path:
        return {"deno": {"path": deno_path}}
    node_path = shutil.which("node") or r"C:\Program Files\nodejs\node.exe"
    if os.path.exists(node_path):
        return {"node": {"path": node_path}}
    return None

FFMPEG_EXECUTABLE = get_ffmpeg_executable()
JS_RUNTIME = get_js_runtime()
PROXY = os.getenv("PROXY", "").strip() or None
COOKIES_PATH = Path(__file__).resolve().parent.parent / "cookies.txt"

YDL_OPTIONS = {
    "logger": NoWarningLogger(),
    "format": "bestaudio/best",
    "noplaylist": True,
    "quiet": True,
    "nocheckcertificate": True,
    "ignoreerrors": False,
    "cachedir": False,
    "default_search": "ytsearch",
    "socket_timeout": 10,
    "retries": 1,
    "extractor_retries": 1,
    "remote_components": ["ejs:github"]
}

if COOKIES_PATH.exists():
    YDL_OPTIONS["cookiefile"] = str(COOKIES_PATH)

if JS_RUNTIME:
    YDL_OPTIONS["js_runtimes"] = JS_RUNTIME

if PROXY:
    YDL_OPTIONS["proxy"] = PROXY

YDL_OPTIONS_FROM_TITLE = dict(YDL_OPTIONS)

before_opts = "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
if PROXY:
    before_opts += f" -http_proxy {PROXY}"

FFMPEG_OPTIONS = {
    "before_options": before_opts,
    "options": "-vn"
}
