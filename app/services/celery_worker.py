from celery import Celery
from celery.utils.log import get_task_logger
from app.core.config import settings

REDIS_HOST = settings.REDIS_HOST
REDIS_PORT = settings.REDIS_PORT
REDIS_BROKER_DB = settings.REDIS_BROKER_DB
redis_url = f"{REDIS_HOST}://{REDIS_HOST}:{REDIS_PORT}/{REDIS_BROKER_DB}"

c_worker = Celery(
    "c_worker",
    broker=redis_url,
    backend=redis_url
    )
c_log = get_task_logger(__name__)

c_worker.autodiscover_tasks([
    "app.services.conversation.tasks",
    "app.services.diarize.tasks",
    "app.services.summarize.tasks",
    "app.services.transcribe.tasks",
])
