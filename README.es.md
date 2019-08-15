<div align="center">
    <a href="https://twitter.com/intent/follow?screen_name=kennbroorg">
	<img alt="follow on Twitter" src="https://img.shields.io/twitter/follow/kennbroorg.svg?label=follow%20%40kennbroorg&style=social">
    </a>
</div>

---

<div align="center">
    <img alt="Redis" src="https://img.shields.io/badge/storage-redis-red.svg">
    <img alt="Python" src="https://img.shields.io/badge/python-3.7-informational.svg">
    <img alt="Celery" src="https://img.shields.io/badge/multiprocessing-celery-green.svg">
    <img alt="Flask" src="https://img.shields.io/badge/interface-flask-yellowgreen.svg">
</div>
<div align="center">
    <img alt="Node" src="https://img.shields.io/badge/node-%3E%208.x-brightgreen.svg">
    <img alt="Angular" src="https://img.shields.io/badge/web%20framwork-angular%207-red.svg">
    <img alt="Boostrap" src="https://img.shields.io/badge/toolkit-boostrap-blueviolet.svg">
    <img alt="UI Kit" src="https://img.shields.io/badge/UI%20Kit-Nebular-9cf.svg">
</div>
<div align="center">
    <img alt="fullcontact" src="https://img.shields.io/badge/module-fullcontact-blue.svg">
    <img alt="twitter" src="https://img.shields.io/badge/module-twitter-blue.svg">
    <img alt="linkedin" src="https://img.shields.io/badge/module-linkedin-blue.svg">
    <img alt="github" src="https://img.shields.io/badge/module-github-blue.svg">
    <img alt="keybase" src="https://img.shields.io/badge/module-keybase-blue.svg">
    <img alt="ghostproject" src="https://img.shields.io/badge/module-ghostproject-red.svg">
    <img alt="emailrep.io" src="https://img.shields.io/badge/module-emailrep.io-blue.svg">
    <img alt="haveibeenpwned" src="https://img.shields.io/badge/module-haveibeenpwned-blue.svg">
</div>

---

<div align="center">
    <a href="https://gitlab.com/kennbroorg/iKy/blob/iKy/README.md">
	<img alt="README English" src="https://img.shields.io/badge/README-English-orange.svg">
    </a>
</div>

---

<div align="center" style="background: #111">
    <img alt="Logo" src="https://kennbroorg.gitlab.io/ikyweb/assets/img/Logo-Circular.png">
</div>

---

# iKy

## Descripción

El proyecto iKy es una herramienta que colecta información a partir de una dirección de e-mail y muestra los resultados en una interface visual.

Visite el Gitlab Page del [Projecto](https://kennbroorg.gitlab.io/ikyweb/)

[![Video Demo](https://kennbroorg.gitlab.io/ikyweb/assets/img/Giba.gif)](https://vimeo.com/347085110 "Video Demo - Click to Watch!") 

[Video Demo](https://vimeo.com/347085110 "Video Demo - Click to Watch!")

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

## Aviso Legal

Todo aquel que contribuya o haya contribuído con el proyecto, incluyendome, no somos responsables por el uso de la herramienta (Ni el uso legal ni el uso ilegal, ni el "otro" uso). 

Tenga en cuenta que este software fue inicialmente escrito para una broma, luego con fines educativos (para educarnos a nosotros mismos), y ahora el objetivo es colaborar con la comunidad haciendo software libre de calidad, y si bien la calidad no es excelente (a veces ni siquiera buena) nos esforzamos en perseguir la excelencia.

Considere que toda la informacion recolectada está libre y disponible por internet, la herramienta solo intenta descubrirla, recolectarla y mostrarla.
Muchas veces la herramienta ni siquiera puede lograr su objetivo de descubrimiento y recolección. Por favor, cargue las APIs necesarias antes de acordarse de mi madre.
Si aún con las APIs no muestra cosas "lindas" que usted espera ver, pruebe con otros e-mails antes de acordarse de mi madre.
Si aún probando con otros e-mails no ve las cosas "lindas" que usted espera ver, puede crear un issue, contactarnos por e-mail o por cualquiera de las RRSS, pero tenga en cuenta que mi madre no es ni la creadora ni contribuye con el proyecto.

No reembolsamos su dinero si no está satisfecho.

Espero que disfrute la utilizacion de la herramienta tanto como nosotros disfrutamos hacerla. El esfuerzo fue y es enorme (Tiempo, conocimiento, codificacion, pruebas, revisiones, etc) pero lo haríamos de nuevo.

No use la herramienta si no puede leer claramente las instrucciones y/o el presente Aviso Legal.

Por cierto, para quienes insistan en acordarse de mi madre, ella murió hace muchos años pero la amo como si estuviera aquí mismo.

[readmees]: README.es.md
[readmeen]: README.md

