from celery import Celery
from flask import Flask


def create_celery(application: Flask | tuple) -> Celery:
    """Configure a Celery instance from a Flask application.

    *application* may be a plain ``Flask`` instance **or** the
    ``(Flask, SocketIO)`` tuple returned by ``create_application()``.
    """
    # Unpack tuple returned by the updated create_application()
    if isinstance(application, tuple):
        application = application[0]

    cfg = application.config
    celery = Celery(
        application.import_name, broker=cfg["CELERY_BROKER_URL"]
    )
    celery.conf.update(
        result_backend=cfg["CELERY_RESULT_BACKEND"],
        accept_content=cfg["CELERY_ACCEPT_CONTENT"],
        task_serializer=cfg["CELERY_TASK_SERIALIZER"],
        result_serializer=cfg["CELERY_RESULT_SERIALIZER"],
        imports=cfg["CELERY_IMPORTS"],
    )
    TaskBase = celery.Task

    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with application.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask
    return celery
