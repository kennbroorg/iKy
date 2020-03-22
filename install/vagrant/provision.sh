#!/bin/bash

cd ~
mkdir log
mkdir .config
echo
echo "Updating..."
sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get install -y build-essential
echo "========================================================================"
echo 

## echo "Installing pyenv and python3.7..."
## sudo apt-get install -y libffi-dev build-essential libbz2-dev libssl-dev libreadline-dev libsqlite3-dev tk-dev libxml2-dev libxslt1-dev git
## curl -L https://raw.githubusercontent.com/pyenv/pyenv-installer/master/bin/pyenv-installer | bash
## export PATH="~/.pyenv/bin:$PATH" >> ~/.bashrc
## echo export PATH="~/.pyenv/bin:$PATH" >> ~/.bashrc
## echo eval "$(pyenv init -)" >> ~/.bashrc
## echo eval "$(pyenv virtualenv-init -)" >> ~/.bashrc
## source ~/.bashrc
## pyenv install 3.7.4
## pyenv global 3.7.4
## # Falta setear el environment
## echo "========================================================================"
## echo 

echo "Installing python3.7..."
sudo apt-get install -y libffi-dev build-essential libbz2-dev libssl-dev libreadline-dev libsqlite3-dev tk-dev libxml2-dev libxslt1-dev git
sudo apt-get install -y software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt-get update
sudo apt-get install -y python3.7 python3.7-dev
echo "========================================================================"
echo 
 
echo "Installing redis..."
wget -q http://download.redis.io/redis-stable.tar.gz -O redis-stable.tar.gz
tar xvfz redis-stable.tar.gz
cd redis-stable
make
sudo make install
echo 
echo "Execute redis-server..."
redis-server > $HOME/log/redis.log 2>&1 &
cd /home/vagrant
pwd
echo "========================================================================"
echo 

# sudo apt-get install -y curl python-software-properties  # 16.04
sudo apt-get install -y curl software-properties-common  # 18.04
curl -sL https://deb.nodesource.com/setup_12.x | sudo -E bash -
echo
echo "Installing nodejs..."
sudo apt-get install -y nodejs
node -v
npm -v 
echo "========================================================================"
echo

echo "Cloning Repo"
# su vagrant -c 'git clone https://gitlab.com/kennbroorg/iKy.git'
git clone https://gitlab.com/kennbroorg/iKy.git
cd iKy/
pwd
## echo "Setting pyenv..."
## export PATH="~/.pyenv/bin:$PATH"
## pyenv virtualenv 3.7.4 iKy374
## echo iKy374 > .python-version
## echo "Installing celery and package from pip..."
sudo apt-get install -y python3-pip
## sudo apt-get install -y python3-celery
echo "Installing pip and requirements..."
python3.7 -m pip install --upgrade pip
python3.7 -m pip install --user -r requirements.txt
export PATH="/home/vagrant/.local/bin:$PATH"
echo export PATH="/home/vagrant/.local/bin:$PATH" >> ~/.bashrc
echo "========================================================================"
echo 

echo "Execute celery..."
cd backend 
pwd
./celery.sh >$HOME/log/celery.log 2>&1 &
echo "Execute app..."
python3.7 app.py -i 0.0.0.0 >$HOME/log/app.log 2>&1 &
# su vagrant -c 'python app.py &'
echo "========================================================================"
echo

echo "Installing package from frontend..."
cd ..
cd frontend
pwd
sed -i -e 's/ng serve/ng serve --host 0.0.0.0/g' package.json
npm install >$HOME/log/npm_install.log 2>&1
npm start >$HOME/log/npm.log 2>&1 &
sleep 180
tail -n 50 $HOME/log/npm.log

# Make some checks
/vagrant/checks.sh
