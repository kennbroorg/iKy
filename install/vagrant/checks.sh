#!/usr/bin/env bash
#set -x
RED='\033[0;31m'
GREEN='\033[1;32m'
NC='\033[0m' # No Color

CHECK=$(curl --head --silent -S localhost:4200 2>&1)
STATUS=$?
MSG=$(echo "${GULP_CHECK}" | head -n 1)

if [ $STATUS -eq 0 ]; then
    echo -e "${GREEN}INFO:${NC} $MSG"
else
    echo -e "${RED}ERROR:${NC} $MSG"
fi

exit $STATUS
