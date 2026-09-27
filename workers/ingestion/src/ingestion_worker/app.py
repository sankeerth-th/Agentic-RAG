from app.core.config import Settings
from celery import Celery


def create_worker(settings: Settings | None = None) -> Celery:
    settings = settings or Settings()
    worker = Celery("rag_ingestion", broker=settings.redis_url.get_secret_value())
    worker.conf.update(
        task_default_queue="ingestion",
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        task_ignore_result=True,
        worker_prefetch_multiplier=1,
        broker_connection_retry_on_startup=True,
        broker_connection_max_retries=3,
        timezone="UTC",
        enable_utc=True,
    )
    return worker


app = create_worker()
