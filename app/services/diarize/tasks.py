from typing import Any
import io
import torch
from pyannote.audio import Pipeline
from app.core.config import settings
from app.services.celery_worker import c_worker
from app.services.cache import CACHE

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

pipeline = Pipeline.from_pretrained(
    settings.DIARIZATION_MODEL,
    use_auth_token=settings.HF_TOKEN
)
pipeline.to(torch.device(DEVICE))


@c_worker.task
def diarize(bytes_key: str) -> str:
    """
    Diarize audio stored in cache and return a cache key for the result.

    Args:
        bytes_key (str): Cache key pointing to audio bytes.

    Returns:
        key (str): Cache key of the diarization result.
    """
    audio_bytes: bytes = CACHE.load(bytes_key)
    buffer: io.BytesIO = io.BytesIO(audio_bytes)
    diarization_result: Any = pipeline(buffer)
    key: str = CACHE.save(diarization_result)
    return key
