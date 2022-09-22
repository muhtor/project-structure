import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')
app.config_from_object('django.conf:settings')

app.autodiscover_tasks()

app.conf.beat_schedule = {
    'currency-rate-update': {
        'task': 'apps.billing.tasks.currency_rate_update',
        'schedule': crontab(minute=59,hour=23),  # change to crontab(minute=0, hour=0) if you want it to run daily at midnight
    },
}