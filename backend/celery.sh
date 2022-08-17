#!/usr/bin/env bash
# celery worker -A celery_worker.celery --loglevel=DEBUG
celery -A celery_worker.celery worker --loglevel=INFO
