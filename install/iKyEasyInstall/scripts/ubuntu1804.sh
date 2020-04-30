#!/usr/bin/bash
echo "========================================================================"
echo " PROVISIONING"
echo "========================================================================"

while [ `echo $PWD | grep install` ]
    do
       cd ..
    done
WD=$PWD
echo "Working directory $WD"

if [ ! -d "$WD/log" ]; then
    mkdir log
fi
echo
echo "Updating..."
sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get install -y build-essential
echo "========================================================================"
echo 

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
redis-server > $WD/log/redis.log 2>&1 &
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

# echo "Cloning Repo"
# git clone https://gitlab.com/kennbroorg/iKy.git
# cd iKy/
# pwd
# sudo apt-get install -y python3-pip
sudo apt install -y python3-testresources
curl -O https://bootstrap.pypa.io/get-pip.py
sudo python3.7 get-pip.py
## sudo apt-get install -y python3-celery
echo "Installing pip and requirements..."
python3.7 -m pip install --upgrade pip
python3.7 -m pip install --user -r $WD/requirements.txt
# export PATH="/home/vagrant/.local/bin:$PATH"
# echo export PATH="/home/vagrant/.local/bin:$PATH" >> ~/.bashrc
echo "========================================================================"
echo 

echo "Execute celery..."
cd $WD/backend 
pwd
./celery.sh >$WD/log/celery.log 2>&1 &
echo "Execute app..."
python3.7 app.py -i 127.0.0.1 >$WD/log/app.log 2>&1 &
# python3.7 app.py -i 0.0.0.0 >$WD/log/app.log 2>&1 &
echo "========================================================================"
echo

echo "Installing package from frontend..."
cd ..
cd $WD/frontend
pwd
# sed -i -e 's/ng serve/ng serve --host 0.0.0.0/g' package.json
npm install 
npm audit fix 
npm start >$WD/log/npm.log 2>&1 &
sleep 180
tail -n 50 $WD/log/npm.log

