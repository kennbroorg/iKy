# iKy

## INSTALL

### Redis
Se debe instalar Redis
```shell
wget http://download.redis.io/redis-stable.tar.gz
tar xvzf redis-stable.tar.gz
cd redis-stable
make
```

Y encender el server
```shell
redis-server
```

### Celery
Se debe instalar Celery
```shell
pip install celery[redis]
```



