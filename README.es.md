# iKy

## PROYECTO
Visitar el Gitlab Page del [Proyecto](https://kennbroorg.gitlab.io/ikyweb/)

## INSTALAR BACKEND

### Redis
Se debe instalar Redis
```shell
wget http://download.redis.io/redis-stable.tar.gz
tar xvzf redis-stable.tar.gz
cd redis-stable
make
sudo make install
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
./celery.sh
```

Finalmente, otra vez, en otra terminal encender la app de backend desde el directorio **backend** 
```shell
python app.py
```

## INSTALAR FRONTEND

### Dependencias
Primero que nada, instalar [nodejs](https://nodejs.org/es/) 8.

Ejemplo en Ubuntu 16.04
```shell
sudo apt-get update
sudo apt-get install -y curl python-software-properties
sudo curl -sL https://deb.nodesource.com/setup_8.x | sudo -E bash -
sudo apt-get install -y nodejs
node -v
npm -v 
```

Y luego se debe instalar **bower**, **gulp** y las dependencias desde el directorio **frontend**
```shell
sudo npm install -g bower
sudo npm install -g gulp
cd frontend
npm install
```

Por último, para encender el frontend, se debe ejecutar 
```shell
gulp serve
```

# DISFRUTE
Abrir el navegador y [DISFRUTAR](http://127.0.0.1:3000)

## CONFIGURACION DE APIKEYS
Por ahora lo ideal es cargar las apiKeys de [fullcontact](https://support.fullcontact.com/hc/en-us/articles/115003415888-Getting-Started-FullContact-v2-APIs) y [twitter](https://developer.twitter.com/en/docs/basics/authentication/guides/access-tokens.html) a través del frontend desde la opción de **API Keys**. Es intuitivo.  

# Proximamente
Prometo meter todo junto en un script
