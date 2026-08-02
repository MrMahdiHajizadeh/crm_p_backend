"""
Test settings for Django CRM backend.

Uses SQLite in-memory database instead of PostgreSQL for fast, isolated tests.
RLS (Row-Level Security) is PostgreSQL-only and is skipped on SQLite.
"""

from crm.settings import *  # noqa: F401, F403

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Disable Celery broker/result backend in tests (no Redis needed)
CELERY_BROKER_URL = "memory://"
CELERY_RESULT_BACKEND = "cache+memory://"

# Run Celery tasks synchronously in tests to avoid needing a running worker + Redis
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
