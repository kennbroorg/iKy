#!/usr/bin/env bash
#set -x
RED='\033[0;31m'
GREEN='\033[1;32m'
NC='\033[0m' # No Color

echo ""
echo "${NC}Running checks..."
echo "Checking NODE..."

CHECK_NPM=$(curl --head --silent -S localhost:4200 2>&1)
STATUS=$?
MSG=$(echo "${CHECK_NPM}" | head -n 1)

if [ $STATUS -eq 0 ]; then
    echo -e "${GREEN}INFO NPM:${NC} $MSG"
else
    echo -e "${RED}ERROR NPM:${NC} $MSG"
fi

echo ""
echo "Checking CELERY..."
CHECK_CELERY=$(curl --silent -S --header "Content-Type: application/json" --request POST --data '{"username": "x", "from": ""}' http://127.0.0.1:5000/github 2>&1)
STATUS=$?
MSG=$(echo "${CHECK_CELERY}" | head -n 1)

if [ $STATUS -eq 0 ]; then
    echo -e "${GREEN}INFO CELERY:${NC} $MSG"
else
    echo -e "${RED}ERROR CELERY:${NC} $MSG"
fi

echo ""
echo "Checking APP..."
CHECK_APP=$(curl --head --silent -S localhost:5000/tasklist 2>&1)
STATUS=$?
MSG=$(echo "${CHECK_APP}" | head -n 1)

if [ $STATUS -eq 0 ]; then
    echo -e "${GREEN}INFO APP:${NC} $MSG"
else
    echo -e "${RED}ERROR APP:${NC} $MSG"
fi

exit $STATUS
