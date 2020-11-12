<div align="center" style="margin-bottom: 10px;">
    <a href="https://twitter.com/intent/follow?screen_name=kennbroorg">
	<img alt="follow on Twitter" src="https://img.shields.io/twitter/follow/kennbroorg.svg?label=follow%20&style=for-the-badge&logo=twitter&labelColor=abcdef&color=1da1f2">
    </a>
</div>

<div align="center" style="margin-bottom: 10px;">
    <img alt="Redis" src="https://img.shields.io/badge/storage-redis-red.svg?style=for-the-badge">
    <img alt="Python" src="https://img.shields.io/badge/python-3.7-informational.svg?style=for-the-badge">
    <img alt="Celery" src="https://img.shields.io/badge/multiprocessing-celery-green.svg?style=for-the-badge">
    <img alt="Flask" src="https://img.shields.io/badge/interface-flask-yellowgreen.svg?style=for-the-badge">
    <img alt="Node" src="https://img.shields.io/badge/node-12.x-brightgreen.svg?style=for-the-badge">
    <img alt="Angular" src="https://img.shields.io/badge/web%20framwork-angular%207-red.svg?style=for-the-badge">
</div>

<!--
<div align="center" style="margin-bottom: 10px;">
    <img alt="Boostrap" src="https://img.shields.io/badge/toolkit-boostrap-blueviolet.svg?style=for-the-badge">
    <img alt="UI Kit" src="https://img.shields.io/badge/UI%20Kit-Nebular-9cf.svg?style=for-the-badge">
</div>
-->

<div align="center">
    <a href="https://gitlab.com/kennbroorg/iKy/blob/iKy/README.md">
	<img alt="README English" src="https://img.shields.io/badge/README-English-orange.svg?style=for-the-badge">
    </a>
</div>

---

<div align="center">
    <img alt="Logo" src="https://kennbroorg.gitlab.io/ikyweb/assets/img/Logo-Circular.png">
</div>

---

<div align="center">   

[Descripción](#description)&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;[Instalación](#installation)&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;[Website][website]&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;[Módulos](#modules)&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;[Issues][issues]&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;[Supporting](#sponsor)

</div>

---

<!--
Website References
-->
[website]:https://kennbroorg.gitlab.io/ikyweb/
[issues]:https://gitlab.com/kennbroorg/iKy/-/issues/new?issue%5Bassignee_id%5D=&issue%5Bmilestone_id%5D=
[readmees]: README.es.md
[readmeen]: README.md

<h1 align="center">iKy</h1>

<h1 id="description">Description</h1>
El proyecto iKy es una herramienta que colecta información a partir de una dirección de e-mail y muestra los resultados en una interface visual.

Visite el Gitlab Page del [Projecto](https://kennbroorg.gitlab.io/ikyweb/)

<div align="center">
    <a href="https://vimeo.com/434501702"><img src="https://kennbroorg.gitlab.io/ikyweb/assets/img/Giba.gif"></a>
</div>

[Video Demo](https://vimeo.com/434501702 "Video Demo - Click to Watch!")

<h1 id="modules">Módulos</h1>

<div align="center" style="margin-bottom: 10px;">
    <img alt="fullcontact" src="https://img.shields.io/badge/module-fullcontact-blue.svg?style=flat-square">
    <img alt="twitter" src="https://img.shields.io/badge/module-twitter-blue.svg?style=flat-square">
    <img alt="linkedin" src="https://img.shields.io/badge/module-linkedin-blue.svg?style=flat-square">
    <img alt="github" src="https://img.shields.io/badge/module-github-blue.svg?style=flat-square">
    <img alt="keybase" src="https://img.shields.io/badge/module-keybase-blue.svg?style=flat-square">
    <img alt="ghostproject" src="https://img.shields.io/badge/module-ghostproject-red.svg?style=flat-square">
    <img alt="haveibeenpwned" src="https://img.shields.io/badge/module-haveibeenpwned-blue.svg?style=flat-square">
    <img alt="emailrep.io" src="https://img.shields.io/badge/amodule-emailrep.io-blue.svg?style=flat-square">
    <img alt="socialscan" src="https://img.shields.io/badge/module-socialscan-blue.svg?style=flat-square">
    <img alt="instagram" src="https://img.shields.io/badge/module-instagram-blue.svg?style=flat-square">
    <img alt="tiktok" src="https://img.shields.io/badge/module-tiktok-blue.svg?style=flat-square">
    <img alt="sherlock" src="https://img.shields.io/badge/module-sherlock-blue.svg?style=flat-square">
    <img alt="skype" src="https://img.shields.io/badge/module-skype-blue.svg?style=flat-square">
    <img alt="tinder" src="https://img.shields.io/badge/module-tinder-blue.svg?style=flat-square">
    <img alt="venmo" src="https://img.shields.io/badge/module-venmo-blue.svg?style=flat-square">
    <img alt="darkpass" src="https://img.shields.io/badge/module-darkpass-blue.svg?style=flat-square">
    <img alt="tweetiment" src="https://img.shields.io/badge/module-tweetiment-blue.svg?style=flat-square">
    <img alt="peopledatalabs" src="https://img.shields.io/badge/module-peopledatalabs-blue.svg?style=flat-square">
    <img alt="reddit" src="https://img.shields.io/badge/module-reddit-blue.svg?style=flat-square">
    <img alt="leaklookup" src="https://img.shields.io/badge/module-leaklookup-blue.svg?style=flat-square">
</div>

<h1 id="installation">Instalación</h1>

<div align="left" style="margin-bottom: 10px;">
    <h2><img alt="important" height="30" src="https://kennbroorg.gitlab.io/ikyweb/assets/img/important.png"> Easy installation (Python only)</h2>
</div>

Se debe instalar Redis

```shell
wget http://download.redis.io/redis-stable.tar.gz
tar xvzf redis-stable.tar.gz
cd redis-stable
make
sudo make install
```

Vaya a nuestro [website][website]. Descargar el ZIP y descomprimirlo.
```
unzip iKy.zip
cd iKy-pack
pip install -r requirements.txt
cd backend
python app.py -e prod
```

Y finalmente, [browsearlo](#browse).

## Instalación completa (DEV)

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

#### Python y Celery

Se debe instalar las librerías en requirements.txt

```shell
python3 -m pip install -r requirements.txt
```

### Instalar Frontend

#### Node

Primero que nada, instalar [nodejs](https://nodejs.org/es/).

#### Dependencias

Dentro del directorio **frontend** instalar las dependencias

```shell
cd frontend
npm install
```

## Encender iKy Tool

### Encender el Backend

#### Redis

Y ejecutar el server en una terminal

```shell
redis-server
```

#### Python y Celery

Ejecutar celery en otra terminal, dentro del directorio **backend**

```shell
cd backend
./celery.sh
```

Otra vez, en otra terminal ejecutar app.py dentro del directorio **backend** 

```shell
python3 app.py
```

### Encender el Frontend

Finalmente, ejecutar dentro del directorio **frontend** el siguiente comando :

```shell
npm start
```

<!--
### Pantalla luego de encender iKy

<div align="center">
    <img src="frontend/src/assets/images/Screens1000.png">
</div>
-->

<h3 id="browser">Browse</h3>

Abrir el browser en esta [url](http://127.0.0.1:4200)

### Config API Keys

Una vez que la aplicación esté cargada en el browser, deberá ir a la opción Api Keys y llenar los valores de las APIs que se necesitan.

- Fullcontact : Generar las APIs desde [aquí](https://support.fullcontact.com/hc/en-us/articles/115003415888-Getting-Started-FullContact-v2-APIs)
- PeopleDataLabs : Generar las APIs desde [aquí](https://www.peopledatalabs.com/signup)
- Linkedin : Solo se debe cargar el usuario y contraseña de su cuenta 
- Instagram : Solo se debe cargar el usuario y contraseña de su cuenta 
- HaveIBeenPwned : Generar las APIs desde [aquí](https://haveibeenpwned.com/API/Key) (Paga)
- Emailrep.io : Generar las APIs desde [aqui](https://emailrep.io/key)
- Leaklookup : Generar las APIs desde [aqui](https://leak-lookup.com/api)
- Twitter: Generar las APIs desde [aqui](https://developer.twitter.com/en/docs/basics/authentication/guides/access-tokens.html)


# Wiki
- [iKy Wiki](https://gitlab.com/kennbroorg/iKy/-/wikis/home)
- [iKy Page](https://kennbroorg.gitlab.io/ikyweb/)
- Installation
  - [Easy Install](https://gitlab.com/kennbroorg/iKy/-/wikis/Installation/EasyInstall)
  - [Vagrant](https://gitlab.com/kennbroorg/iKy/-/wikis/Installation/Vagrant)
  - [Manual install (Compacted)](https://gitlab.com/kennbroorg/iKy/-/wikis/Installation/Manual-install-(Compacted))
  - [Manual install (Detailed)](https://gitlab.com/kennbroorg/iKy/-/wikis/Installation/Manual-install-(Detailed))
- Update
  - [Soft Update](https://gitlab.com/kennbroorg/iKy/-/wikis/Update/Soft)
- Wake Up 
  - [Turn on the project](https://gitlab.com/kennbroorg/iKy/-/wikis/Wakeup/WakeUp)
- APIs
  - [APIs through frontend](https://gitlab.com/kennbroorg/iKy/-/wikis/APIs/ApiKeys-through-the-browser)
  - [APIs through backend](https://gitlab.com/kennbroorg/iKy/-/wikis/APIs/APIs-through-the-backend)
- Backend
  - [Backend through URL](https://gitlab.com/kennbroorg/iKy/-/wikis/Backend/Backend-through-url)
- Videos
  - [Installation videos](https://gitlab.com/kennbroorg/iKy/-/wikis/Videos/Installations)
    - [Installation in Kali 2019](https://vimeo.com/350877994) 
    - [Installation in ubuntu 18.04](https://vimeo.com/347435255) 
    - [Installation in ubuntu 16.04](https://vimeo.com/332359273) 
  - [Demo videos](https://gitlab.com/kennbroorg/iKy/-/wikis/Videos/Demos)
    - [iKy eko15](https://vimeo.com/397862772)
    - [iKy version 2](https://vimeo.com/347085110)
    - [Testing iKy with Emiliano](https://vimeo.com/349011105)
    - [Testing iKy with Giba](https://vimeo.com/342843348)
    - [iKy version 1](https://vimeo.com/326114716)
    - [iKy version 0](https://vimeo.com/272495754)
- [Disclaimer](https://gitlab.com/kennbroorg/iKy/-/wikis/Disclaimer)

## Video Demo

<div align="center">
    <a href="https://vimeo.com/434501702"><img alt="Kali 2019" src="https://kennbroorg.gitlab.io/ikyweb/assets/img/iKy-01.png"></a>
    <p>Vimeo</p>
</div>

<h1 id="sponsor">Apoyar el proyecto</h1>
Ya sea que use este proyecto, haya aprendido algo de él o simplemente le guste, por favor considere apoyarlo comprándome un café, para que pueda dedicar más tiempo a proyectos de código abierto como este.

<div align="center" style="margin-top: 30px;">
<a href="https://www.buymeacoffee.com/kennbro" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 60px !important;width: 217px !important;" ></a>
</div>

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
