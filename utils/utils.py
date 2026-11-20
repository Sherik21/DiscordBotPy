import asyncio
import json
import re
import urllib.request
import discord
import yt_dlp
from handler.track import Track
from handler.config import YDL_OPTIONS, YDL_OPTIONS_FROM_TITLE

def createEmbed(track: Track) -> discord.Embed:
    duration_str = formatDuration(track.duration)
    embed = discord.Embed(
        title=track.title,
        url=track.url,
        color=0x5865F2
    )
    embed.add_field(name="Author", value=track.author or "Unknown", inline=True)
    embed.add_field(name="Duration", value=duration_str or "-", inline=True)
    if track.thumbnail:
        embed.set_thumbnail(url=track.thumbnail)
    return embed

def createProgressBar(current: int, total: int, length: int = 14) -> str:
    if total <= 0:
        return "🔘" + "─" * (length - 1)
    progress_ratio = min(1.0, max(0.0, current / total))
    marker_pos = int(progress_ratio * (length - 1))
    return "".join("🔘" if i == marker_pos else "─" for i in range(length))

def formatDuration(duration: int) -> str:
    if duration:
        m, s = divmod(duration, 60)
        h, m = divmod(m, 60)
        if h:
            return f"{h}:{m:02d}:{s:02d}"
        return f"{m}:{s:02d}"
    return "-"

def parseTimeString(time_input: str) -> int:
    clean = time_input.strip()
    if clean.isdigit():
        return int(clean)
    parts = clean.split(":")
    if len(parts) == 2 and all(p.isdigit() for p in parts):
        return int(parts[0]) * 60 + int(parts[1])
    if len(parts) == 3 and all(p.isdigit() for p in parts):
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    return -1

async def isValidUrl(url: str) -> bool:
    return bool(re.compile(r"^https?://[^\s]+$").match(url.strip()))

def cleanTrackUrl(url: str) -> str:
    clean = url.strip()
    if "watch?v=" in clean and "&list=" in clean:
        return clean.split("&list=")[0]
    return clean

def isPlaylistUrl(url: str) -> bool:
    clean = url.strip()
    if "list=RD" in clean or "list=UL" in clean or "list=LL" in clean:
        return False
    if "watch?v=" in clean and "list=" in clean:
        return False
    return "list=" in clean or "/playlist" in clean or "/sets/" in clean or "/album/" in clean

def _fetch_youtube_oembed_metadata(url: str) -> tuple[str, str]:
    clean_url = cleanTrackUrl(url)
    oembed_url = f"https://www.youtube.com/oembed?url={clean_url}&format=json"
    proxy_url = YDL_OPTIONS.get("proxy")
    try:
        if proxy_url:
            handler = urllib.request.ProxyHandler({"http": proxy_url, "https": proxy_url})
            opener = urllib.request.build_opener(handler)
        else:
            opener = urllib.request.build_opener()
        req = urllib.request.Request(oembed_url, headers={"User-Agent": "Mozilla/5.0"})
        with opener.open(req, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))
            return data.get("title", ""), data.get("author_name", "")
    except Exception:
        return "", ""

def _search_soundcloud_sync(query: str) -> Track | None:
    opts = dict(YDL_OPTIONS)
    opts.pop("cookiefile", None)
    opts["noplaylist"] = True
    opts["format"] = "bestaudio/best"
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            res = ydl.extract_info(f"scsearch1:{query}", download=False)
            if not res or "entries" not in res or not res["entries"]:
                return None
            entry = res["entries"][0]
            if not entry:
                return None
            track = Track()
            track.title = entry.get("title", "Unknown track")
            track.author = entry.get("uploader", "Unknown author")
            track.duration = int(entry.get("duration", 0) or 0)
            track.stream_url = entry.get("url", "")
            track.thumbnail = entry.get("thumbnail")
            track.url = entry.get("webpage_url") or entry.get("url", "")
            return track
    except Exception as error:
        print(f"SoundCloud fallback error: {error}")
        return None

async def updateWorkingStreamLink(track: Track) -> Track:
    if track.stream_url and track.stream_url.startswith("http"):
        return track
    new_stream_url = await _fetch_stream_url(track.url)
    if new_stream_url:
        track.stream_url = new_stream_url
    return track

def _extract_stream_url_sync(url: str) -> str:
    clean_url = cleanTrackUrl(url)
    try:
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(clean_url, download=False)
            if info:
                if "entries" in info and info["entries"]:
                    first_entry = info["entries"][0]
                    if first_entry and first_entry.get("url"):
                        return first_entry.get("url")
                if info.get("url"):
                    return info.get("url")
    except Exception as error:
        print(f"Primary stream URL extraction error: {error}")

    title, author = _fetch_youtube_oembed_metadata(clean_url)
    search_query = f"{title} {author}".strip()
    if search_query:
        sc_track = _search_soundcloud_sync(search_query)
        if sc_track and sc_track.stream_url:
            return sc_track.stream_url
    return ""

async def _fetch_stream_url(url: str) -> str:
    return await asyncio.to_thread(_extract_stream_url_sync, url)

def _extract_info_by_url_sync(url: str) -> Track:
    clean_url = cleanTrackUrl(url)
    try:
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(clean_url, download=False)
            if info:
                if "entries" in info and info["entries"]:
                    info = info["entries"][0]
                if info and info.get("url"):
                    track = Track()
                    track.title = info.get("title", "Unknown track")
                    track.author = info.get("uploader", "Unknown author")
                    track.duration = int(info.get("duration", 0) or 0)
                    track.stream_url = info.get("url", "")
                    track.thumbnail = info.get("thumbnail")
                    track_id = info.get("id", "")
                    track.url = f"{track.begin_url}{track_id}" if track_id else clean_url
                    return track
    except Exception as error:
        print(f"Primary URL extraction failed, attempting fallback: {error}")

    title, author = _fetch_youtube_oembed_metadata(clean_url)
    search_query = f"{title} {author}".strip() or clean_url
    sc_track = _search_soundcloud_sync(search_query)
    if sc_track:
        if title:
            sc_track.title = title
        if author:
            sc_track.author = author
        sc_track.url = clean_url
        return sc_track

    raise ValueError("No video or audio information found")

async def extractInfoByUrl(url: str) -> Track:
    return await asyncio.to_thread(_extract_info_by_url_sync, url)

def _extract_playlist_sync(url: str) -> list[Track]:
    playlist_opts = dict(YDL_OPTIONS)
    playlist_opts["noplaylist"] = False
    playlist_opts["extract_flat"] = "in_playlist"
    playlist_opts["playlistend"] = 50

    with yt_dlp.YoutubeDL(playlist_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        if not info or "entries" not in info:
            raise ValueError("No playlist entries found")

        tracks = []
        for entry in info["entries"]:
            if not entry:
                continue
            entry_id = entry.get("id", "")
            track = Track()
            track.title = entry.get("title", "Unknown track")
            track.author = entry.get("uploader", entry.get("channel", "Unknown author"))
            track.duration = int(entry.get("duration", 0) or 0)
            track.url = f"{track.begin_url}{entry_id}" if entry_id else entry.get("url", url)
            track.stream_url = ""
            tracks.append(track)
        return tracks

async def extractPlaylist(url: str) -> list[Track]:
    return await asyncio.to_thread(_extract_playlist_sync, url)

def _extract_info_by_title_sync(title: str) -> Track:
    try:
        with yt_dlp.YoutubeDL(YDL_OPTIONS_FROM_TITLE) as ydl:
            search_query = f"ytsearch1:{title}"
            info = ydl.extract_info(search_query, download=False)
            if info and "entries" in info and info["entries"]:
                entry = info["entries"][0]
                if entry and entry.get("url"):
                    track = Track()
                    track.title = entry.get("title", "Unknown track")
                    track.author = entry.get("uploader", "Unknown author")
                    track.duration = int(entry.get("duration", 0) or 0)
                    track.stream_url = entry.get("url", "")
                    track.thumbnail = entry.get("thumbnail")
                    track_id = entry.get("id", "")
                    track.url = f"{track.begin_url}{track_id}" if track_id else ""
                    return track
    except Exception as error:
        print(f"YouTube search error, attempting SoundCloud: {error}")

    sc_track = _search_soundcloud_sync(title)
    if sc_track:
        return sc_track

    raise ValueError("No tracks found for this title")

async def extractInfoByTitle(title: str) -> Track:
    return await asyncio.to_thread(_extract_info_by_title_sync, title)
