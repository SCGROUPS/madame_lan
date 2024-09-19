#!/bin/bash
red=`tput setaf 1`
green=`tput setaf 2`
reset=`tput sgr0`

echo "------------------ STARTING Build Frontend ------------------"

cd "$PWD"
# remove dist folder
cd ../frontend/
rm -rf ./dist/

# Update ./frontend/.env file
FE_env=.env
BE_URL=""
echo "${green}Update ${FE_env} file, replace VITE_API_URL=${BE_URL}!${reset}"
sed -i "/^VITE_API_URL/c VITE_API_URL=${BE_URL}" ${FE_env}

echo "${green}Remove folder /frontend/dist success!${reset}"

# Install global packages if needed
echo "${green}Run npm/yarn install if needed!${reset}"
sudo apt-get -y install npm
curl -s https://deb.nodesource.com/setup_20.x | sudo bash
sudo apt-get -y install nodejs
sudo apt-get -y install vite
sudo apt-get -y autoremove
sudo npm install yarn

# Build source react
echo "${green}Run yarn install install!${reset}"
yarn install

echo "${green}Start build ReactJS ${reset}"
yarn build
echo "${green}Build ReactJS success!${reset}"


# Check if the directory exists
if [ ! -d "../backend/app/static/reactjs/" ]; then
  # If the directory does not exist, create it
  mkdir -p ../backend/app/static/reactjs/
  echo "Directory ../backend/app/static/reactjs/ created."
else
  echo "Directory ../backend/app/static/reactjs/ already exists."
  # Remove old files backend
  rm -rf ../backend/app/static/reactjs/*
fi

# Move files static from frontend to backend
cp -rp ./dist/* ../backend/app/static/reactjs/

echo "${green}Move source to /backend/app/static/reactjs success!${reset}"

cd ../backend/
echo "${green}Remove source build frontend/dist ${reset}"
echo "${green}Process success!${reset}"

echo "------------------ Finish Build Frontend ------------------"