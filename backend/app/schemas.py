from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel


# ── Upload responses ──────────────────────────────────────────────────────────

class UploadAudioResponse(BaseModel):
    url: str


class UploadImagesResponse(BaseModel):
    urls: List[str]


# ── Music-video job ───────────────────────────────────────────────────────────

class CreateMusicVideoJobRequest(BaseModel):
    audio_url: str
    image_urls: List[str]
    title: Optional[str] = None


class CreateMusicVideoJobResponse(BaseModel):
    job_id: str
    status: str


class JobStatusResponse(BaseModel):
    job_id: str
    status: str          # queued | processing | complete | failed
    progress: float      # 0.0 – 1.0
    video_url: Optional[str] = None
    error: Optional[str] = None


class JobResultResponse(BaseModel):
    job_id: str
    video_url: str


# ── Film generation ───────────────────────────────────────────────────────────

class GenerateFilmRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None


class GenerateFilmResponse(BaseModel):
    job_id: str
    story_id: str
    status: str


# ── Health ────────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    uptime: float
    version: str
    timestamp: float
