#!/usr/bin/env bash
#set -x
RED='\033[0;31m'
GREEN='\033[1;32m'
NC='\033[0m' # No Color

echo -e "{GREEN}****************************************************"
echo -e "****************************************************{NC}"
echo "Executing STOP after RELOAD..."

echo "Stopping redis..."
ps -ef | grep redis-server | grep -v grep | awk '{print $2}' | xargs kill
echo "Stopping app..."
ps -ef | grep "python app.py" | grep -v grep | awk '{print $2}' | xargs kill
echo "Stopping celery..."
ps -ef | grep "./celery.sh" | grep -v grep | awk '{print $2}' | xargs kill
echo "Stopping npm..."
ps -ef | grep "ng serve" | grep -v grep | awk '{print $2}' | xargs kill

touch $HOME/log/redis.log
touch $HOME/log/app.log
touch $HOME/log/celery.log
touch $HOME/log/npm.log

sleep 5

echo ""
echo "${NC}Checking redis..."
pid=(`pgrep -f redis-server`)
if [ -z $pid ]
then
    echo -e "${GREEN}INFO: ${NC}redis stopped"
else
    echo -e "${RED}INFO: ${NC}redis not stopped" && exit 4
fi

echo "${NC}Checking app..."
pid=(`pgrep -f "python app.py"`)
if [ -z $pid ]
then
    echo -e "${GREEN}INFO: ${NC}app stopped"
else
    echo -e "${RED}INFO: ${NC}app not stopped" && exit 4
fi

echo "${NC}Checking celery..."
pid=(`pgrep -f "./celery.sh"`)
if [ -z $pid ]
then
    echo -e "${GREEN}INFO: ${NC}celery stopped"
else
    echo -e "${RED}INFO: ${NC}celery not stopped" && exit 4
fi

echo "${NC}Checking npm..."
pid=(`pgrep -f "ng serve"`)
if [ -z $pid ]
then
    echo -e "${GREEN}INFO: ${NC}npm stopped"
else
    echo -e "${RED}INFO: ${NC}npm not stopped" && exit 4
fi
