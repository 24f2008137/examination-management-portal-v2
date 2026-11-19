"""Celery 
Scheduled jobs (times are in CELERY_TIMEZONE, default Asia/Kolkata):
    * daily exam reminder   - every day at REMINDER_HOUR:REMINDER_MINUTE (08:00)
    * monthly admin report  - 1st of every month at 07:00
"""
import os
import sys


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from celery import Celery, Task
from celery.schedules import crontab

REDIS_BASE = os.environ.get('REDIS_BASE_URL', 'redis://localhost:6379')


class FlaskContextTask(Task):
    """Run every task inside a Flask application context so the tasks can use
    SQLAlchemy models exactly like the route handlers do."""

    def __call__(self, *args, **kwargs):
        from app import app         
        with app.app_context():
            return self.run(*args, **kwargs)


celery = Celery(
    'emp',
    broker=os.environ.get('CELERY_BROKER_URL', f'{REDIS_BASE}/1'),
    backend=os.environ.get('CELERY_RESULT_BACKEND', f'{REDIS_BASE}/2'),
    include=['tasks'],
    task_cls=FlaskContextTask,
)

celery.conf.update(
    timezone=os.environ.get('CELERY_TIMEZONE', 'Asia/Kolkata'),
    enable_utc=False,
    task_track_started=True,
    result_expires=3600,
    broker_connection_timeout=2,
    broker_transport_options={'socket_connect_timeout': 2, 'socket_timeout': 2},
    result_backend_transport_options={'retry_policy': {'timeout': 2.0}},
    task_publish_retry_policy={'max_retries': 1, 'interval_start': 0,
                               'interval_step': 0.2, 'interval_max': 0.5},
    beat_schedule={
        'daily-exam-reminders': {
            'task': 'emp.send_daily_exam_reminders',
            'schedule': crontab(
                hour=int(os.environ.get('REMINDER_HOUR', 8)),
                minute=int(os.environ.get('REMINDER_MINUTE', 0)),
            ),
        },
        'monthly-admin-report': {
            'task': 'emp.send_monthly_report',
            'schedule': crontab(day_of_month=1, hour=7, minute=0),
        },
    },
)
