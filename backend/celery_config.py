from celery import Celery

app = Celery('celery_config', broker='redis://localhost:6379/0',
        include=['modules.github.github_tasks.t_github',
            ])
