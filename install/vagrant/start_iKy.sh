#!/bin/bash

echo "Executing START after RELOAD..."
cd $HOME
echo "Starting Redis..."
touch $HOME/log/redis.log
redis-server > $HOME/log/redis.log 2>&1 &
sleep 1
tail -n 50 $HOME/log/redis.log
echo " "
echo "Starting Celery..."
cd $HOME/iKy/backend
touch $HOME/log/celery.log
./celery.sh >$HOME/log/celery.log 2>&1 &
sleep 3
tail -n 50 $HOME/log/celery.log
echo " "
echo "Starting App..."
cd $HOME/iKy/backend
touch $HOME/log/app.log
python3.7 app.py -i 0.0.0.0 >$HOME/log/app.log 2>&1 &
sleep 3
tail -n 50 $HOME/log/app.log
echo " "
echo "Starting Frontend..."
cd $HOME/iKy/frontend
touch $HOME/log/npm.log
npm start >$HOME/log/npm.log 2>&1 &
sleep 180
tail -n 50 $HOME/log/npm.log
