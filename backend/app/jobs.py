"""
In-memory, thread-safe job store and fake video-generation worker.
"""
from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, Optional

from . import storage


# ── Data model ────────────────────────────────────────────────────────────────

@dataclass
class Job:
    job_id: str
    status: str = "queued"      # queued | processing | complete | failed
    progress: float = 0.0       # 0.0 – 1.0
    video_url: Optional[str] = None
    error: Optional[str] = None
    created_at: float = field(default_factory=time.time)


# ── Thread-safe store ─────────────────────────────────────────────────────────

class JobStore:
    """A simple dict-backed store protected by a re-entrant lock."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._jobs: Dict[str, Job] = {}

    def create(self) -> Job:
        job = Job(job_id=str(uuid.uuid4()))
        with self._lock:
            self._jobs[job.job_id] = job
        return job

    def get(self, job_id: str) -> Optional[Job]:
        with self._lock:
            return self._jobs.get(job_id)

    def update(self, job_id: str, **kwargs) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return
            for key, value in kwargs.items():
                setattr(job, key, value)


# ── Singleton store used by the whole application ─────────────────────────────

job_store = JobStore()


# ── Fake worker ───────────────────────────────────────────────────────────────

_STEPS = 5          # number of progress increments
_STEP_DELAY = 1.0   # seconds between increments


def run_fake_video_job(job_id: str, base_url: str) -> None:
    """
    Simulate a video-generation pipeline.

    Runs in a background thread; updates the job's *status* and *progress*
    fields as it goes, then writes a stub MP4 and marks the job complete.
    """
    try:
        job_store.update(job_id, status="processing", progress=0.0)

        for step in range(1, _STEPS + 1):
            time.sleep(_STEP_DELAY)
            job_store.update(job_id, progress=round(step / _STEPS, 2))

        # Write a stub MP4 so the URL resolves to a real file.
        relative = f"videos/{job_id}.mp4"
        storage.write_dummy_mp4(relative)
        url = storage.public_url(base_url, relative)

        job_store.update(job_id, status="complete", progress=1.0, video_url=url)

    except Exception as exc:  # noqa: BLE001
        job_store.update(job_id, status="failed", error=str(exc))


def start_job(base_url: str) -> Job:
    """
    Create a new job, spin up a background thread to process it, and return
    the job immediately so the caller can respond with the job_id.
    """
    job = job_store.create()
    t = threading.Thread(
        target=run_fake_video_job,
        args=(job.job_id, base_url),
        daemon=True,
    )
    t.start()
    return job
