from celery import Celery

from raip.config import get_settings

settings = get_settings()

celery_app = Celery(
    "raip",
    broker=settings.celery_broker,
    backend=settings.celery_backend,
    include=[
        "raip.tasks.eval",
        "raip.tasks.dataset_scan",
        "raip.tasks.lab_train",
        "raip.tasks.checkpoint_eval_task",
    ],
)
celery_app.conf.update(
    task_track_started=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
)
