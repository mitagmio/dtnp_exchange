#!/bin/bash

# install Docker, docker-compose
echo "# install Docker, docker-compose"
apt-get remove docker docker-engine docker.io containerd runc
apt-get update -y
apt-get install ca-certificates curl gnupg lsb-release -y
mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
apt-get update -y
apt-get install docker-ce docker-ce-cli containerd.io docker-compose-plugin -y
echo   "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
apt-get update -y
apt-get install docker-ce docker-ce-cli containerd.io docker-compose-plugin -y
docker --version
curl -L "https://github.com/docker/compose/releases/download/v2.6.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/bin/docker-compose
chmod +x /usr/bin/docker-compose
docker-compose --version

# Install Python
echo "# Install Python"
apt update -y && apt upgrade -y
apt install software-properties-common -y
add-apt-repository ppa:deadsnakes/ppa
apt update -y
apt remove python3.8 python3.8-dev python3.8-venv python3.8-distutils python3.8-lib2to3 python3.8-gdbm python3.8-tk python-is-python3  python3-pip -y
sudo apt --fix-missing purge $(dpkg -l | grep 'python3' | awk '{print $2}')
rm /usr/bin/pip*
rm /usr/bin/python*
apt install python3.10 python3.10-dev python3.10-venv python3.10-distutils python3.10-lib2to3 python3.10-gdbm python3.10-tk -y
update-alternatives --install /usr/bin/python python /usr/bin/python3.10 1
update-alternatives --install /usr/bin/python3 python3 /usr/bin/python 10
curl -sS https://bootstrap.pypa.io/get-pip.py | python
cp /usr/local/bin/*pip* /usr/bin/
python -m pip install --upgrade pip
python --version
python3 --version
pip --version
pip3 --version

# Init venv
python3 -m venv dtb_venv
source dtb_venv/bin/activate
python3 -m pip install --upgrade pip

# Install requirements
pip install -r requirements.txt

#env
cp .env_example .env
cp .env_db_example .env_db
cp .env_web_example .env_web
cp .env_letsencrypt_example .env_letsencrypt