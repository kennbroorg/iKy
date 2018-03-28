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
./celery.sh
```

Finalmente, otra vez, en otra terminal encender la app de backend desde el directorio **backend** 
```shell
python app.py
```

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

# DISFRUTE
Por ahora solo funciona en Chrome (y Chromium). Abrir el navegador y [DISFRUTAR](http://127.0.0.1:3000)

## CONFIGURACION DE APIKEYS
Esto no es estrictamente necesario porque la aplicación trabaja con módulos que no requieren apikeys.
Pero si las tiene puede cargarlas desde la opción de **API Keys** en el frontend.  

# Proximamente
Prometo meter todo junto en un script
