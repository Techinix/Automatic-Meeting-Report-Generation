import jsonpickle
import librosa
import io
import uuid

from fastapi import APIRouter, status, HTTPException, UploadFile
from typing import Dict, Any
from app.services.cache import REDIS_CACHE, S3_CACHE
from app.services.celery_worker import c_worker
from app.services.summarize.utils import DocumentGenerator
from app.api.deps import AuthUserDep, DBSessionDep
from app.models.job import Job
from sqlalchemy.future import select
from celery import chord, signature
from celery.result import AsyncResult

from app.utils.logging import setup_logging
import structlog

setup_logging()
logger = structlog.get_logger("fastapi-app")

router = APIRouter()
DOC_GEN = DocumentGenerator()


@router.post("/query", status_code=status.HTTP_200_OK, summary="Upload audio for summarization")
async def query(file: UploadFile , user: AuthUserDep, db: DBSessionDep
) -> Dict[str, str]:
    """
    Accepts an audio file and submits it for summarization.
    """
    audio_bytes = await file.read()

    try:
        _, _ = librosa.load(io.BytesIO(audio_bytes))
    except Exception:
        return {"status": "Invalid audio file"}
    
    size_mb = len(audio_bytes) / (1024 * 1024)
    logger.info(
        "job_request",
        user_id=user.id,
        audio_size=f"{size_mb:.2f} MB",
    )
    job_id = str(uuid.uuid4())
    audio_key = f"user_{user.id}/{job_id}/audio.wav"
    report_key = f"user_{user.id}/{job_id}/report.pdf"

    job = Job(
        id=job_id,
        user_id=user.id,
        audio_key=audio_key,
        report_key=report_key
    )
    bytes_key = S3_CACHE.save(audio_bytes, job.audio_key)
    
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

    logger.info(
        "job_submit",
        user_id=user.id,
        job_id=job.id,
        audio_size=f"{size_mb:.2f} MB",
        task_id=task.id,
        input_key=audio_key,
        output_key=report_key,
    )

    job.task_id = task.id
    db.add(job)
    await db.commit()
    await db.refresh(job)
    
    
    return {"id": job_id, "status": task.state}

@router.get("/export_pdf")
async def export_pdf(job_id: str, user: AuthUserDep, db: DBSessionDep) -> Dict[str, Any]:
    """
    Generates a PDF 
    """
    logger.info(
        "export_request",
        user_id=user.id,
        job_id=job_id,
    )
    result = await db.execute(select(Job).filter(Job.id == job_id, Job.user_id == user.id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(404, "Job not found")

    task = AsyncResult(job.task_id, app=c_worker)
    if task.state != "SUCCESS":
        raise HTTPException(
            status_code=400,
            detail=f"Task state is still {task.state} or doesn't exist."
        )

    key = task.get()
    result = REDIS_CACHE.load(key)
    pdf_bytes = DOC_GEN.generate_pdf(result)
    
    key = S3_CACHE.save(pdf_bytes, job.report_key)
    url = S3_CACHE.get_presigned_url(key, expires_in=3600) 
    logger.info(
        "export_success",
        user_id=user.id,
        job_id=job.id,
        task_id=task.id,
        input_key=job.audio_key,
        output_key=job.report_key,
    )
    return {"status": task.state, "url": url}