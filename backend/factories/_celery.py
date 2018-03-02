# -*- encoding: utf-8 -*-
from celery import Celery


def create_celery(application):
    """
    Configures celery instance from application, using it's config
    :param application: Flask application instance
    :return: Celery instance
    """
    celery = Celery(application.import_name,
                    broker=application.config['CELERY_BROKER_URL'])
    celery.conf.update(application.config)
    TaskBase = celery.Task

    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with application.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask
    return celery
