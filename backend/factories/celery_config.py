from celery import Celery

app = Celery('celery_config', broker='redis://localhost:6379/0',
             backend='redis://localhost:6379/0',
             include=['modules.github.github_tasks',
                      'modules.gitlab.gitlab_tasks',
                      'modules.leaks.leaks_tasks',
                      'modules.keybase.keybase_tasks',
                      'modules.twitter.twitter_tasks',
                      'modules.linkedin.linkedin_tasks',
                      'modules.username.username_tasks',
                      'modules.fullcontact.fullcontact_tasks',
                      ])
