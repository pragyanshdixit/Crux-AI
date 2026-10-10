"""Crux AI Audio Preprocessing & Storage Management Module.
Handles session-isolated audio downloads, yt-dlp challenge solving,
lightweight audio streaming, and automatic disk space reclamation.
"""

import os
import shutil
import uuid
import yt_dlp
from pydub import AudioSegment

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


class AudioChunksList(list):
    """Subclass of list holding audio chunk paths with cleanup capability.
    Operates identically to a standard list for complete backwards compatibility.
    """
    def __init__(self, chunks: list[str], temp_files: list[str] = None, session_dir: str = None):
        super().__init__(chunks)
        self.temp_files = temp_files or []
        self.session_dir = session_dir

    def cleanup(self):
        """Remove all intermediate and chunk audio files created during processing."""
        cleanup_files(self.temp_files)
        cleanup_files(list(self))
        if self.session_dir and os.path.exists(self.session_dir):
            cleanup_session_dir(self.session_dir)


def cleanup_files(file_paths: list[str]):
    """Safely remove a list of audio or chunk files."""
    for p in file_paths:
        try:
            if p and os.path.isfile(p):
                os.remove(p)
        except Exception as e:
            print(f"Warning: Could not remove file {p}: {e}")


def cleanup_session_dir(directory: str):
    """Safely remove a temporary session directory and all its contents."""
    try:
        if directory and os.path.isdir(directory):
            shutil.rmtree(directory, ignore_errors=True)
    except Exception as e:
        print(f"Warning: Could not remove directory {directory}: {e}")


def purge_all_downloads(target_dir: str = DOWNLOAD_DIR):
    """Purge all generated audio files (.wav, .webm, .m4a, .mp3) from the downloads directory.
    Safe for production maintenance or cleanup routines.
    """
    if not os.path.exists(target_dir):
        return
    for item in os.listdir(target_dir):
        item_path = os.path.join(target_dir, item)
        try:
            if os.path.isfile(item_path) and item_path.lower().endswith(('.wav', '.webm', '.m4a', '.mp3', '.ogg')):
                os.remove(item_path)
            elif os.path.isdir(item_path) and item.startswith("session_"):
                shutil.rmtree(item_path, ignore_errors=True)
        except Exception as e:
            print(f"Warning: Could not purge {item_path}: {e}")


import re
from urllib.parse import urlparse, parse_qs

def _sanitize_youtube_url(url: str) -> str:
    """Clean and normalize YouTube URL to avoid query parameter issues."""
    url = url.strip()
    # Handle youtu.be shortlinks
    if "youtu.be/" in url:
        match = re.search(r"youtu\.be/([a-zA-Z0-9_-]{11})", url)
        if match:
            return f"https://www.youtube.com/watch?v={match.group(1)}"
    # Handle youtube.com/shorts/
    if "youtube.com/shorts/" in url:
        match = re.search(r"youtube\.com/shorts/([a-zA-Z0-9_-]{11})", url)
        if match:
            return f"https://www.youtube.com/watch?v={match.group(1)}"
    # Handle standard watch URLs with tracking params
    if "youtube.com/watch" in url:
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        if "v" in params:
            return f"https://www.youtube.com/watch?v={params['v'][0]}"
    return url


def download_youtube_audio(url: str, output_dir: str = DOWNLOAD_DIR) -> str:
    os.makedirs(output_dir, exist_ok=True)
    clean_url = _sanitize_youtube_url(url)
    output_template = os.path.join(
        output_dir,
        "%(id)s.%(ext)s"
    )

    # Detect installed JS runtime (e.g. Node.js) to solve YouTube JS challenges
    js_runtimes = {}
    if shutil.which("node"):
        js_runtimes["node"] = {}
    elif shutil.which("deno"):
        js_runtimes["deno"] = {}

    ydl_opts = {
        "format": "ba[ext=m4a]/ba[ext=mp3]/bestaudio/best",
        "outtmpl": output_template,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "96",
            }
        ],
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "js_runtimes": js_runtimes,
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "ios", "mweb", "web"],
                "player_skip": ["webpage", "configs"]
            }
        },
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        }
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(clean_url, download=True)
        filename = ydl.prepare_filename(info)
        # FFmpeg changes the extension to .mp3
        filename = os.path.splitext(filename)[0] + ".mp3"

    return filename


def convert_to_wav(input_file: str, output_dir: str = None) -> str:
    """Convert an audio file to WAV format using pydub if needed."""
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        base_name = os.path.splitext(os.path.basename(input_file))[0]
        output_path = os.path.join(output_dir, f"{base_name}_converted.wav")
    else:
        output_path = os.path.splitext(input_file)[0] + "_converted.wav"

    audio = AudioSegment.from_file(input_file)
    audio = audio.set_channels(1).set_frame_rate(16000)
    audio.export(output_path, format="wav")
    return output_path


def chunk_audio(audio_path: str, chunk_minutes: int = 15, output_dir: str = None) -> list:
    """Split audio into large chunks (default 15 minutes) only when exceeding Groq's 25MB limit."""
    audio = AudioSegment.from_file(audio_path)
    chunk_ms = chunk_minutes * 60 * 1000
    chunks = []
    
    base_dir = output_dir or os.path.dirname(audio_path) or "."
    base_name = os.path.splitext(os.path.basename(audio_path))[0]
    ext = os.path.splitext(audio_path)[1].lstrip(".") or "mp3"

    for i, start in enumerate(range(0, len(audio), chunk_ms)):
        chunk = audio[start:start+chunk_ms]
        chunk_path = os.path.join(base_dir, f"{base_name}_part_{i}.{ext}")
        chunk.export(chunk_path, format=ext)
        chunks.append(chunk_path)
    return chunks


def process_input(source: str, session_id: str = None) -> AudioChunksList:
    """Process the input source (YouTube URL or local audio file).
    Optimized for maximum speed: avoids redundant conversions and uses direct single-file
    processing whenever audio is within Groq's 25MB payload threshold.
    """
    clean_source = source.strip().strip("'\"")
    
    session_dir = None
    target_dir = DOWNLOAD_DIR
    if session_id:
        session_dir = os.path.join(DOWNLOAD_DIR, f"session_{session_id}")
        target_dir = session_dir
        os.makedirs(target_dir, exist_ok=True)

    temp_files = []

    if clean_source.startswith("http://") or clean_source.startswith("https://"):
        print(f"[Crux AI] Fetching audio from YouTube: {clean_source}")
        audio_file = download_youtube_audio(clean_source, output_dir=target_dir)
        temp_files.append(audio_file)
    elif os.path.isfile(clean_source):
        print(f"[Crux AI] Using local audio file: {clean_source}")
        audio_file = clean_source
    else:
        raise ValueError(
            f"Invalid input: '{source}'. Please enter a valid YouTube URL (e.g., https://youtu.be/...) "
            f"or an existing local audio file path."
        )

    # Check file size (Groq limit is 25MB)
    MAX_PAYLOAD = 24 * 1024 * 1024  # 24 MB safety margin
    file_size = os.path.getsize(audio_file)

    if file_size <= MAX_PAYLOAD:
        # Ultra-fast path: No chunking needed! Entire audio is processed in one direct pass
        print(f"[Crux AI] Audio size is {round(file_size / (1024 * 1024), 2)}MB (<= 24MB). Processing in 1 fast pass.")
        chunks = [audio_file]
    else:
        # Fallback for very long recordings: split into 15-minute segments
        print(f"[Crux AI] Audio file exceeds 24MB ({round(file_size / (1024 * 1024), 2)}MB). Splitting into 15-min parts...")
        chunks = chunk_audio(audio_file, chunk_minutes=15, output_dir=target_dir)
        temp_files.extend(chunks)
        print(f"[Crux AI] Created {len(chunks)} audio segments.")

    return AudioChunksList(chunks, temp_files=temp_files, session_dir=session_dir)

