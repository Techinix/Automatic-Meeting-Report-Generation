import whisper
import librosa
from app.core.config import settings
from app.services.celery_worker import c_worker
from app.services.cache import REDIS_CACHE, S3_CACHE
import io

model = whisper.load_model(settings.WHISPER_SIZE)

@c_worker.task
def transcribe(bytes_key: str, use_word_timestamps: bool=True) -> str:
    """Transcribe audio and returns text segments"""
    
    bytes = S3_CACHE.load(bytes_key)
    buffer = io.BytesIO(bytes)

    waveform, _ = librosa.load(buffer, mono=True, sr=int(settings.SAMPLE_RATE), dtype="float32")
    asr_result = model.transcribe(waveform, word_timestamps=use_word_timestamps)
    key = REDIS_CACHE.save(asr_result["segments"])
    return key