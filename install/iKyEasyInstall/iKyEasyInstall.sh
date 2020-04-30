#!/usr/bin/env bash

# Thanks to The RetroPie Project

__version="0.0.1"

banner_message()
{
  echo "+------------------------------------------+"
  printf "|`tput bold` %-40s `tput sgr0`|\n" "$@"
  echo "+------------------------------------------+"
}

function compareVersions() {
    dpkg --compare-versions "$1" "$2" "$3" >/dev/null
    return $?
}

[[ "$__debug" -eq 1 ]] && set -x

echo " "
echo "Version : $__version"
echo " _ _  __       _____                  ___           _        _ _ "
echo "(_) |/ /   _  | ____|__ _ ___ _   _  |_ _|_ __  ___| |_ __ _| | |"
echo "| | ' / | | | |  _| / _\` / __| | | |  | || '_ \/ __| __/ _\` | | |"
echo "| | . \ |_| | | |__| (_| \__ \ |_| |  | || | | \__ \ || (_| | | |"
echo "|_|_|\_\__, | |_____\__,_|___/\__, | |___|_| |_|___/\__\__,_|_|_|"
echo "       |___/                  |___/                              "
printf "   Or not"
echo " "
echo " "

banner_message "Starting the Installation"

__ERRMSGS=()
__INFMSGS=()

__memory_phys=$(free -m | awk '/^Mem:/{print $2}')
__memory_total=$(free -m -t | awk '/^Total:/{print $2}')

# get os distributor id, description, release number and codename
mapfile -t os < <(lsb_release -sidrc)
__os_id="${os[0]}"
__os_desc="${os[1]}"
__os_release="${os[2]}"
__os_codename="${os[3]}"

printf "\t SO  : `tput bold` %-40s `tput sgr0`\n" "$__os_desc"
printf "\t Mem : `tput bold` %-40s `tput sgr0`\n" "$__memory_total Mb"
echo " "

error=""
case "$__os_id" in
    Ubuntu)
        if compareVersions "$__os_release" lt 18.04; then
            error="You need Ubuntu 18.04 or newer"
        else
            # if no apt-get we need to fail
            [[ -z "$(which apt-get)" ]] && fatalError "Unsupported OS - No apt-get command found"
            echo " "
            echo "Launch Provisioning..."
            echo " "
            bash scripts/ubuntu1804.sh
        fi
        ;;
    Kali)
        if compareVersions "$__os_release" lt 2020; then
            error="You need Kali 2020 or newer"
        else
            # if no apt-get we need to fail
            [[ -z "$(which apt-get)" ]] && echo "Unsupported OS - No apt-get command found"
            echo " "
            echo "Launch Provisioning..."
            echo " "
            bash scripts/ubuntu1804.sh
        fi
        ;;
    *)
        error="Unsupported OS"
        ;;
esac

[[ -n "$error" ]] && echo "$error\n\n$(lsb_release -idrc)"

