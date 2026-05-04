"""
ReelO FastAPI backend.

Endpoints
---------
GET  /health
POST /api/uploads/audio
POST /api/uploads/images
POST /api/music-video/jobs
GET  /api/music-video/jobs/{job_id}
GET  /api/music-video/jobs/{job_id}/result
POST /api/stories/{story_id}/generate-film
GET  /public/*   (static files)
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import List

from fastapi import FastAPI, File, HTTPException, Request, UploadFile, status
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from . import storage
from .jobs import job_store, start_job
from .schemas import (
    CreateMusicVideoJobRequest,
    CreateMusicVideoJobResponse,
    GenerateFilmRequest,
    GenerateFilmResponse,
    HealthResponse,
    JobResultResponse,
    JobStatusResponse,
    UploadAudioResponse,
    UploadImagesResponse,
)

# ── App setup ─────────────────────────────────────────────────────────────────

_START_TIME = time.time()
_VERSION = "1.0.0"

app = FastAPI(
    title="ReelO Backend",
    version=_VERSION,
    description="Music-video and film generation API",
)

# Ensure public sub-directories exist before mounting static files.
storage.ensure_dirs()

_PUBLIC_DIR = Path(__file__).parent / "public"
app.mount("/public", StaticFiles(directory=str(_PUBLIC_DIR)), name="public")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _base_url(request: Request) -> str:
    """Return the scheme + host of the incoming request (no trailing slash)."""
    return str(request.base_url).rstrip("/")


# ── Health ────────────────────────────────────────────────────────────────────

@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        uptime=round(time.time() - _START_TIME, 3),
        version=_VERSION,
        timestamp=time.time(),
    )


# ── Audio upload ──────────────────────────────────────────────────────────────

@app.post(
    "/api/uploads/audio",
    response_model=UploadAudioResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload an audio file",
)
async def upload_audio(
    request: Request,
    file: UploadFile = File(..., description="Audio file (mp3, wav, aac, …)"),
) -> UploadAudioResponse:
    data = await file.read()
    relative = storage.save_audio(data, file.filename or "audio.bin")
    url = storage.public_url(_base_url(request), relative)
    return UploadAudioResponse(url=url)


# ── Image upload ──────────────────────────────────────────────────────────────

@app.post(
    "/api/uploads/images",
    response_model=UploadImagesResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload one or more image files",
)
async def upload_images(
    request: Request,
    files: List[UploadFile] = File(..., description="Image files (jpg, png, …)"),
) -> UploadImagesResponse:
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one image file is required.",
        )
    urls: List[str] = []
    for f in files:
        data = await f.read()
        relative = storage.save_image(data, f.filename or "image.bin")
        urls.append(storage.public_url(_base_url(request), relative))
    return UploadImagesResponse(urls=urls)


# ── Music-video jobs ──────────────────────────────────────────────────────────

@app.post(
    "/api/music-video/jobs",
    response_model=CreateMusicVideoJobResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a music-video generation job",
)
def create_music_video_job(
    request: Request,
    body: CreateMusicVideoJobRequest,
) -> CreateMusicVideoJobResponse:
    job = start_job(_base_url(request))
    return CreateMusicVideoJobResponse(job_id=job.job_id, status=job.status)


@app.get(
    "/api/music-video/jobs/{job_id}",
    response_model=JobStatusResponse,
    summary="Get the status of a music-video job",
)
def get_music_video_job(job_id: str) -> JobStatusResponse:
    job = job_store.get(job_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{job_id}' not found.",
        )
    return JobStatusResponse(
        job_id=job.job_id,
        status=job.status,
        progress=job.progress,
        video_url=job.video_url,
        error=job.error,
    )


@app.get(
    "/api/music-video/jobs/{job_id}/result",
    response_model=JobResultResponse,
    summary="Get the result of a completed music-video job",
)
def get_music_video_job_result(job_id: str) -> JobResultResponse:
    job = job_store.get(job_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{job_id}' not found.",
        )
    if job.status != "complete":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Job '{job_id}' is not complete yet (status: {job.status}).",
        )
    return JobResultResponse(job_id=job.job_id, video_url=job.video_url)  # type: ignore[arg-type]


# ── Film generation ───────────────────────────────────────────────────────────

@app.post(
    "/api/stories/{story_id}/generate-film",
    response_model=GenerateFilmResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a film from a story",
)
def generate_film(
    story_id: str,
    request: Request,
    body: GenerateFilmRequest,
) -> GenerateFilmResponse:
    job = start_job(_base_url(request))
    return GenerateFilmResponse(
        job_id=job.job_id,
        story_id=story_id,
        status=job.status,
    )


# ── Global exception handler ──────────────────────────────────────────────────

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected error occurred.", "error": str(exc)},
    )
