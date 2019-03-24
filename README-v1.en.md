# iKy

## PROJECT
Visit the Gitlab Page of the [Project](https://kennbroorg.gitlab.io/ikyweb/)

```shell
git clone https://gitlab.com/kennbroorg/iKy.git
```

[![Video Demo](https://kennbroorg.gitlab.io/ikyweb/assets/img/i-1.png)](https://vimeo.com/272495754 "Video Demo - Click to Watch!")

[Video Demo](https://vimeo.com/272495754 "Video Demo - Click to Watch!")

We also have a vagrant machine to simplify installation

```shell
git clone https://gitlab.com/kennbroorg/iKy-vagrant.git
```

## INSTALL BACKEND

### Redis
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

### Python stuff and Celery
You must install the requirements
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

## INSTALL FRONTEND

### Dependencies
First of all, install [nodejs](https://nodejs.org/en/) 8.
**Be sure to install version 8 LTS. The 10 LTS version was recently launched and we must adapt the project**

Ubuntu 16.04 example
```shell
sudo apt-get update
sudo apt-get install -y curl python-software-properties
sudo curl -sL https://deb.nodesource.com/setup_8.x | sudo -E bash -
sudo apt-get install -y nodejs
node -v
npm -v 
```

And then you must install **bower**, **gulp** and the dependencies from the directory **frontend**
```shell
sudo npm install -g bower
sudo npm install -g gulp
cd frontend
npm install
```

Finally, to run frontend server, execute:
```shell
gulp serve
```

# ENJOY
Open the browser and [ENJOY](http://127.0.0.1:3000)

## CONFIG APIKEYS
For now please load the apiKeys of [fullcontact](https://support.fullcontact.com/hc/en-us/articles/115003415888-Getting-Started-FullContact-v2-APIs) and [twitter](https://developer.twitter.com/en/docs/basics/authentication/guides/access-tokens.html) through the **API Keys** option in the frontend.
Recently we have merged the linkedin branch. You must put the user and password of linkedin to obtain data from the module.
