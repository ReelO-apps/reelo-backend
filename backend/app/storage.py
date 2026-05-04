"""
File storage helpers.

Files are written to  app/public/{audio,images,videos}/
and served by FastAPI's StaticFiles mount at /public/*.
"""
from __future__ import annotations

import os
import uuid
from pathlib import Path

# Resolve the public directory relative to this file so the module works
# regardless of the working directory.
_HERE = Path(__file__).parent
PUBLIC_DIR = _HERE / "public"

AUDIO_DIR = PUBLIC_DIR / "audio"
IMAGES_DIR = PUBLIC_DIR / "images"
VIDEOS_DIR = PUBLIC_DIR / "videos"


def ensure_dirs() -> None:
    """Create all public sub-directories if they don't already exist."""
    for d in (AUDIO_DIR, IMAGES_DIR, VIDEOS_DIR):
        d.mkdir(parents=True, exist_ok=True)


def _ext(filename: str) -> str:
    """Return the file extension (including the dot), lower-cased."""
    _, ext = os.path.splitext(filename)
    return ext.lower() if ext else ""


def save_audio(data: bytes, original_filename: str) -> str:
    """
    Persist *data* as an audio file and return the storage-relative path
    (e.g. ``audio/abc123.mp3``) that can be turned into a public URL.
    """
    ensure_dirs()
    name = f"{uuid.uuid4()}{_ext(original_filename)}"
    dest = AUDIO_DIR / name
    dest.write_bytes(data)
    return f"audio/{name}"


def save_image(data: bytes, original_filename: str) -> str:
    """Persist *data* as an image file and return the storage-relative path."""
    ensure_dirs()
    name = f"{uuid.uuid4()}{_ext(original_filename)}"
    dest = IMAGES_DIR / name
    dest.write_bytes(data)
    return f"images/{name}"


def save_video(data: bytes, original_filename: str) -> str:
    """Persist *data* as a video file and return the storage-relative path."""
    ensure_dirs()
    name = f"{uuid.uuid4()}{_ext(original_filename)}"
    dest = VIDEOS_DIR / name
    dest.write_bytes(data)
    return f"videos/{name}"


def public_url(base_url: str, relative_path: str) -> str:
    """
    Build a fully-qualified public URL from the server's *base_url* and a
    storage-relative path returned by one of the ``save_*`` helpers.

    Example::

        public_url("https://api.example.com", "audio/abc.mp3")
        # → "https://api.example.com/public/audio/abc.mp3"
    """
    return f"{base_url.rstrip('/')}/public/{relative_path}"


def write_dummy_mp4(relative_path: str) -> None:
    """
    Write a minimal valid-ish MP4 stub to *relative_path* (relative to
    PUBLIC_DIR).  Used by the fake job runner so the result URL resolves to
    an actual file.
    """
    ensure_dirs()
    dest = PUBLIC_DIR / relative_path
    dest.parent.mkdir(parents=True, exist_ok=True)
    # Smallest possible ftyp + mdat box — enough for a 200 response.
    stub = (
        b"\x00\x00\x00\x18ftypisom\x00\x00\x00\x00isom"
        b"\x00\x00\x00\x08mdat"
    )
    dest.write_bytes(stub)
