# This file is intentionally left empty to mark this directory as a Python package.

# Import the Celery app
from .celery import app as celery_app

__all__ = ('celery_app',) 