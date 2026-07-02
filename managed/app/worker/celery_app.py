"""Celery application: broker on Redis, daily retention enforcement via beat.

The same container image runs this as ``celery -A app.worker.celery_app
worker`` and ``... beat`` (Compose services; Deployment/CronJob later on
Kubernetes).
"""

from celery import Celery

from app.config import get_settings


def build_celery() -> Celery:
    settings = get_settings()
    celery = Celery("clairvoyance-managed", broker=settings.redis_url)
    celery.conf.beat_schedule = {
        "enforce-retention-daily": {
            "task": "app.worker.tasks.enforce_retention",
            "schedule": 60 * 60 * 24,
        },
    }
    celery.conf.timezone = "UTC"
    celery.autodiscover_tasks(["app.worker"])
    return celery


celery_app = build_celery()
