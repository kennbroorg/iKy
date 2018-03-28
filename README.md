# iKy

## INSTALL BACKEND

### Redis
You must install Redis
```shell
wget http://download.redis.io/redis-stable.tar.gz
tar xvzf redis-stable.tar.gz
cd redis-stable
make
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
First of all, install **[nodejs]**(https://nodejs.org/en/)

And then you must install **gulp** and the dependencies from the directory **frontend**
```shell
cd frontend
sudo npm install -g bower
sudo npm install --save gulp-install
sudo npm install
```

Finally, to run frontend server, execute:
```shell
gulp serve
```

## CONFIG APIKEYS
This is not strictly necessary because the app works with modules that do not require apikeys.
But if you have them you can load them from the **API Keys** option in the frontend.

# ENJOY
For now it works on Chrome (And Chromium). Open the browser and [ENJOY](http://127.0.0.1:3000)

# Coming soon
I promise to put everything together in a script.
