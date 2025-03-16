import os
from celery import Celery
from celery.schedules import crontab, timedelta

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Create the Celery app
app = Celery('leaderboard')

# Load configuration from Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()

# Define the scheduled tasks
app.conf.beat_schedule = {
    'update-winners-every-5-minutes': {
        'task': 'api.tasks.update_winners_task',
        'schedule': timedelta(minutes=5),  # Run every 5 minutes
    },
} 