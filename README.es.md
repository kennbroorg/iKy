# iKy

## INSTALAR BACKEND

### Redis
Se debe instalar Redis
```shell
wget http://download.redis.io/redis-stable.tar.gz
tar xvzf redis-stable.tar.gz
cd redis-stable
make
```

Y encender el server en una terminal aparte
```shell
redis-server
```

### Librerias de python y Celery
Se debe instalar las librerias de requirements.txt
```shell
pip install -r requirements.txt
```

Y encender Celery en otra terminal aparte y parado en el directorio **backend**
```shell
celery worker -A celery_config -l info -c 5
```

### Corrida de prueba
Utilizar, por ahora, la terminal de python (o ipython) y desde el directorio **backend**, ejecutando lo siguiente

```python
from modules.github.github_tasks import t_github
from modules.gitlab.gitlab_tasks import t_gitlab
from modules.keybase.keybase_tasks import t_keybase
from modules.username.username_tasks import t_username

# Sin celery, uno atras del otro
t_github('kennbro')
t_gitlab('kennbro')
t_keybase('kennbro') # No devuelve nada por que no hay usuario
t_username('kennbro')

# Con celery
t_github.delay('kennbro')
t_gitlab.delay('kennbro')
t_keybase.delay('kennbro') # No devuelve nada por que no hay usuario
t_username.delay('kennbro')
```

El primer conjunto sin celery, cada uno espera al otro para ir ejecutandose y la salida se muestra por consola
El segundo grupo se arroja a celery, todos juntos y éste en conjunto con redis manejan la salida, por lo que la misma se mostrará en la consola que corre celery


## INSTALAR FRONTEND

### Dependencias
Primero que nada, instalar **[nodejs]**(https://nodejs.org/es/)

Y luego se debe instalar **gulp** y las dependencias desde el directorio **frontend**
```shell
cd frontend
npm install --save gulp-install
npm install
```

Por último, para encender el frontend, se debe ejecutar 
```shell
gulp serve
```

# DISFRUTA
Por ahora solo funciona en Chrome (y Chromium). Abrir el navegador y [DISFRUTAR](http://127.0.0.1:3000)

# Proximamente
Prometo meter todo junto en un script
