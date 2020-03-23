#!/usr/bin/env bash
#set -x
RED='\033[0;31m'
GREEN='\033[1;32m'
NC='\033[0m' # No Color

echo -e "${NC}Checking APP...${NC}"
pid=(`pgrep -f app.py`)
[[ -z $pid ]] && echo -e "${RED}ERROR: ${NC}Failed to get the PID. The process is not running" && exit 1
echo -e "${GREEN}INFO: ${NC} The process is runinng PID $pid"
echo $(ps -ef | grep -i app.py | grep -v grep | grep -v status)

echo ""
echo -e "${GREEN}Last 50 output lines${NC}"
tail -n 50 $HOME/log/app.log
