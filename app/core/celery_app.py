from celery import Celery
from app.core.config import settings
from celery.schedules import crontab

celery_app=Celery(
    "clinexa",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.email_tasks",
              "app.tasks.reminder_tasks"],
)

celery_app.conf.timezone="Asia/Kolkata"

celery_app.conf.beat_schedule={
    "check-upcoming-appointments-every-minutes":{
        "task":"app.tasks.reminder_tasks.check_upcoming_appointments",
        "schedule":60.0,
    },
}

