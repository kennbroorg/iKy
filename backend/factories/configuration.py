# -*- encoding: utf-8 -*-


def get_config():
    class Config:
        CELERY_BROKER_URL = 'redis://localhost:6379/0'
        CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
        CELERY_ACCEPT_CONTENT = ['json', 'yaml']
        CELERY_TASK_SERIALIZER = 'json'
        CELERY_RESULT_SERIALIZER = 'json'
        CELERY_IMPORTS = ('modules.keybase.keybase_tasks',
                'modules.gitlab.gitlab_tasks',
                'modules.github.github_tasks',
                'modules.usersearch.usersearch_tasks')
    return Config

