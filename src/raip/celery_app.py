from celery import Celery
from celery.schedules import crontab

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
        "raip.tasks.canary",
    ],
)
celery_app.conf.update(
    task_track_started=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
)


def _canary_schedule() -> crontab:
    """Parse RAIP_CANARY_CRON ('m h dom mon dow'); default hourly on the minute."""
    fields = (settings.raip_canary_cron or "0 * * * *").split()
    if len(fields) == 5:
        m, h, dom, mon, dow = fields
        return crontab(
            minute=m, hour=h, day_of_month=dom, month_of_year=mon, day_of_week=dow
        )
    return crontab(minute=0)


# The governance canary runs only when the gaas profile is enabled; harmless otherwise (it just
# probes the target model and publishes to the bus).
if settings.raip_gaas_enabled:
    celery_app.conf.beat_schedule = {
        "gov-canary": {"task": "raip.gov_canary", "schedule": _canary_schedule()},
    }
