<div align="center">
    <a href="https://twitter.com/intent/follow?screen_name=kennbroorg">
	<img alt="follow on Twitter" src="https://img.shields.io/twitter/follow/kennbroorg.svg?label=follow%20%40kennbroorg&style=social">
    </a>
</div>

---

<div align="center">
    <img alt="Redis" src="https://img.shields.io/badge/storage-redis-red.svg">
    <img alt="Python" src="https://img.shields.io/badge/python-2%20or%203%20(compatible)-informational.svg">
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
    <img alt="haveibeenpwned" src="https://img.shields.io/badge/module-haveibeenpwned-blue.svg">
</div>

---

<div align="center">
    <a href="https://gitlab.com/kennbroorg/iKy/blob/iKy/README.es.md">
	<img alt="README Espanol" src="https://img.shields.io/badge/README-Espa%C3%B1ol-orange.svg">
    </a>
</div>

---

<div align="center">
    <img alt="Logo" src="https://kennbroorg.gitlab.io/ikyweb/assets/img/Logo-Circular.png">
</div>

---

# iKy

## Description
Project iKy is a tool that collects information from an email and shows results in a nice visual interface.

Visit the Gitlab Page of the [Project](https://kennbroorg.gitlab.io/ikyweb/)

[![Video Demo](https://kennbroorg.gitlab.io/ikyweb/assets/img/iKy-01.png)](https://vimeo.com/326114716 "Video Demo - Click to Watch!") 

[Video Demo](https://vimeo.com/326114716 "Video Demo - Click to Watch!")

## Project - Previous version
We want to warn you that we have changed the Frontend from AngularJS to Angular 7. For this reason we left the project with AngularJS as Frontend in the iKy-v1 branch.

The reason of changing the Frontend was to update the technology and get an easier way of installation.

## Installation
### Clone repository
```shell
git clone https://gitlab.com/kennbroorg/iKy.git
```

### Install Backend
#### Redis
You must install Redis
```shell
wget http://download.redis.io/redis-stable.tar.gz
tar xvzf redis-stable.tar.gz
cd redis-stable
make
sudo make install
```
And turn on the server in a terminal
```shell
redis-server
```

#### Python stuff and Celery
You must install the libraries inside requirements.txt
```shell
pip install -r requirements.txt
```
And turn on Celery in another terminal, within the directory **backend**
```shell
./celery.sh
```
Finally, again, in another terminal turn on backend app from directory **backend** 
```shell
python app.py
```

### Install Frontend
#### Node
First of all, install [nodejs](https://nodejs.org/en/).

#### Dependencias
Inside the directory **frontend** install the dependencies
```shell
npm install
```

#### Turn on Frontend Server
Finally, to run frontend server, execute:
```shell
npm start
```

### Browser
Open the browser in this [url](http://127.0.0.1:4200) 

### Config API Keys
Once the application is loaded in the browser, you should go to the Api Keys option and load the values of the APIs that are needed.

- Fullcontact: Generate the APIs from [here](https://support.fullcontact.com/hc/en-us/articles/115003415888-Getting-Started-FullContact-v2-APIs)
- Twitter: Generate the APIs from [here](https://developer.twitter.com/en/docs/basics/authentication/guides/access-tokens.html)
- Linkedin: Only the user and password of your account must be loaded

[readmees]: README.es.md
[readmeen]: README.md
