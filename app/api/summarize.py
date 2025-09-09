import jsonpickle
import librosa
import io
from fastapi import APIRouter, status, HTTPException, UploadFile, File
from typing import Dict, Any
from app.services.cache import REDIS_CACHE, S3_CACHE
from app.services.celery_worker import c_worker
from app.services.summarize.utils import DocumentGenerator
from celery import chord, signature
from celery.result import AsyncResult

router = APIRouter()
DOC_GEN = DocumentGenerator()


@router.post("/query", status_code=status.HTTP_200_OK, summary="Upload audio for summarization")
async def query(file: UploadFile = File(...)) -> Dict[str, str]:
    """
    Accepts an audio file and submits it for summarization.
    """
    audio_bytes = await file.read()

    try:
        _, _ = librosa.load(io.BytesIO(audio_bytes))
    except Exception:
        return {"status": "Invalid audio file"}

    bytes_key = S3_CACHE.save(audio_bytes)

    task = chord(
        [
            signature(
                "app.services.transcribe.tasks.transcribe",
                kwargs={"bytes_key": bytes_key}
            ),
            signature(
                "app.services.diarize.tasks.diarize",
                kwargs={"bytes_key": bytes_key}
            )
        ],
        signature("app.services.conversation.tasks.create_conversation") |
        signature("app.services.summarize.tasks.summarize_text")
    ).delay()

    return {"id": task.id, "status": task.state}

@router.get("/task_result")
def task_result(task_id: str) -> Dict[str, Any]:
    """
    Returns the status and result of a Celery task.
    """
    task = AsyncResult(task_id, app=c_worker)
    state = task.state
    result = task.result

    if state == "SUCCESS":
        key = task.get()
        result = REDIS_CACHE.load(key)
        result = jsonpickle.encode(result)
    elif state == "FAILURE":
        result = str(result)

    return {"status": state, "result": result}


@router.get("/export_pdf")
def export_pdf(task_id: str) -> Dict[str, Any]:
    """
    Generates a PDF 
    """
    task = AsyncResult(task_id, app=c_worker)
    if task.state != "SUCCESS":
        raise HTTPException(
            status_code=400,
            detail=f"Task state is still {task.state} or doesn't exist."
        )

    key = task.get()
    result = REDIS_CACHE.load(key)
    pdf_bytes = DOC_GEN.generate_pdf(result)
    key = S3_CACHE.save(pdf_bytes)
    url = S3_CACHE.get_presigned_url(key, expires_in=3600) 

    return {"status": task.state, "url": url}