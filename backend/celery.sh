#!/usr/bin/env bash
# celery worker -A celery_worker.celery -l info -c 5
celery worker -A celery_worker.celery --loglevel=DEBUG
