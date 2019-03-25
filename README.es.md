# iKy

## Descripción

El proyecto iKy es una herramienta que colecta información a partir de una dirección de e-mail y muestra los resultados en una interface visual.

Visite el Gitlab Page del [Projecto](https://kennbroorg.gitlab.io/ikyweb/)

[![Video Demo](https://kennbroorg.gitlab.io/ikyweb/assets/img/iKy-01.png)](https://vimeo.com/326114716 "Video Demo - Click to Watch!") 

[Video Demo](https://vimeo.com/326114716 "Video Demo - Click to Watch!")

## Proyecto

Primero que nada queremos aclarar que hemos cambiado el Frontend de AngularJS a Angular 7. Por esta razón hemos dejado al proyecto con AngularJS como Frontend en la rama iKy-v1 y la documentación para su instalación [aquí][readmev1es].

El motivo del cambio de Frontend fue actualizar la tecnología y obtener una forma más fácil de instalación.

## Instalación

### Clonar el repositorio

```shell
git clone https://gitlab.com/kennbroorg/iKy.git
```

### Instalar Backend

#### Redis
Se debe instalar Redis
```shell
wget http://download.redis.io/redis-stable.tar.gz
tar xvzf redis-stable.tar.gz
cd redis-stable
make
sudo make install
```

Y ejecutar el server en una terminal
```shell
redis-server
```

#### Python y Celery
Se debe instalar las librerías en requirements.txt

```shell
pip install -r requirements.txt
```

Y ejecutar celery en otra terminal, dentro del directorio **backend**

```shell
./celery.sh
```

Por último, otra vez, en otra terminal ejecutar app.py dentro del directorio **backend** 

```shell
python app.py
```

### Instalar Frontend

#### Node
Primero que nada, instalar [nodejs](https://nodejs.org/es/).

#### Dependencias

Dentro del directorio **frontend** instalar las dependencias

```shell
npm install
```
#### Encender servidor

Finalmente, ejecutar dentro del directorio **frontend** el siguiente comando :

```shell
npm start
```

### Browser
Abrir el browser en esta [url](http://127.0.0.1:4200)

### Config API Keys
Una vez que la aplicación esté cargada en el browser, deberá ir a la opción Api Keys y llenar los valores de las APIs que se necesitan.

- Fullcontact : Generar las APIs desde [aquí](https://support.fullcontact.com/hc/en-us/articles/115003415888-Getting-Started-FullContact-v2-APIs)
- Twitter : Generar las APIs desde [aquí](https://developer.twitter.com/en/docs/basics/authentication/guides/access-tokens.html)
- Linkedin : Solo se debe cargar el usuario y contraseña de su cuenta 

[readmev1en]: README-v1.en.md
[readmev1es]: README-v1.es.md
[readmees]: README.es.md
[readmeen]: README.md

