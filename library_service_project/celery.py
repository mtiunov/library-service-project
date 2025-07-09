import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "library_service_project_api.settings")

app = Celery("library_service_project_api")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()
