#!/bin/bash

# Config:
env_path=/home/vagrant/workspace/SCG/envs/chat_dn
host=172.16.7.61
port=5001

# Run BE in the background
cd "$PWD"
cd ../backend
echo $PWD

echo "Build frontend source"
chmod +x deploy/start_build_frontend.sh
sh deploy/start_build_frontend.sh

# Activate env
echo "Activate env: $env_path"
source $host/bin/activate

# Install env
echo "Install env: $env_path"
pip install -r requirements.txt

# Install $port
echo "Kill port: $port"
sudo fuser -k $port/tcp

# Start web app
echo "Start web app: http://$host:$port"
nohup uvicorn main:app --host $host --port $port &
echo "Go to <http://$host:$port>"
