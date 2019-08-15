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
    <img alt="haveibeenpwned" src="https://img.shields.io/badge/module-haveibeenpwned-blue.svg">
    <img alt="emailrep.io" src="https://img.shields.io/badge/module-emailrep.io-blue.svg">
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

[![Video Demo](https://kennbroorg.gitlab.io/ikyweb/assets/img/Giba.gif)](https://vimeo.com/347085110 "Video Demo - Click to Watch!") 

[Video Demo](https://vimeo.com/347085110 "Video Demo - Click to Watch!")

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

## Disclaimer

Anyone who contributes or contributed to the project, including me, is not responsible for the use of the tool (Neither the legal use nor the illegal use, nor the "other" use).

Keep in mind that this software was initially written for a joke, then for educational purposes (to educate ourselves), and now the goal is to collaborate with the community making quality free software, and while the quality is not excellent (sometimes not even good) we strive to pursue excellence.

Consider that all the information collected is free and available online, the tool only tries to discover, collect and display it.
Many times the tool cannot even achieve its goal of discovery and collection. Please load the necessary APIs before remembering my mother.
If even with the APIs it doesn't show "nice" things that you expect to see, try other e-mails before you remember my mother.
If you still do not see the "nice" things you expect to see, you can create an issue, contact us by e-mail or by any of the RRSS, but keep in mind that my mother is neither the creator nor Contribute to the project.

We do not refund your money if you are not satisfied.
I hope you enjoy using the tool as much as we enjoy doing it. The effort was and is enormous (Time, knowledge, coding, tests, reviews, etc.) but we would do it again.
Do not use the tool if you cannot read the instructions and / or this disclaimer clearly.

By the way, for those who insist on remembering my mother, she died many years ago but I love her as if she were right here.

[readmees]: README.es.md
[readmeen]: README.md
