# iKy

## INSTALL BACKEND

### Redis
You must install Redis
```shell
wget http://download.redis.io/redis-stable.tar.gz
tar xvzf redis-stable.tar.gz
cd redis-stable
make
```

And turn on the server in a terminal
```shell
redis-server
```

### Python stuff and Celery
You must install the requirements
```shell
pip install -r requirements.txt
```

And turn on Celery in another terminal, within the directory **backend**
```shell
celery worker -A celery_config -l info -c 5
```

### Test run
Use the python terminal (or ipython) and from the directory **backend**, running the following

```python
from modules.github.github_tasks import t_github
from modules.gitlab.gitlab_tasks import t_gitlab
from modules.keybase.keybase_tasks import t_keybase
from modules.username.username_tasks import t_username

# Without Celery, the processes run in sequence
t_github('kennbro')
t_gitlab('kennbro')
t_keybase('kennbro') # there is no user
t_username('kennbro')

# With Celery, the processes are all executed together
t_github.delay('kennbro')
t_gitlab.delay('kennbro')
t_keybase.delay('kennbro') # there is no user
t_username.delay('kennbro')
```

## INSTALL FRONTEND

### Dependencies
First of all, install **[nodejs]**(https://nodejs.org/en/)

And then you must install **gulp** and the dependencies from the directory **frontend**
```shell
cd frontend
npm install --save gulp-install
npm install
```

Finally, to run frontend server, execute:
```shell
gulp serve
```

# ENJOY
For now it works on Chrome (And Chromium). Open the browser and [ENJOY](http://127.0.0.1:3000)

# Coming soon
I promise to put everything together in a script.
