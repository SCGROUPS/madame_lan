#!/bin/bash
red=`tput setaf 1`
green=`tput setaf 2`
reset=`tput sgr0`
 
TARGET_CONFIGS='
TENANT_ID
RESOURCE_GROUP_NAME
LOCATION
REGISTRY_NAME
SKU
CONTAINERAPP_ENV_NAME
CONTAINERAPP_IMAGE
CONTAINERAPP_NAME
TARGET_PORT'
 
# Azure configuration parameters
echo "${green}Azure configuration parameters:${reset}"
for config in $TARGET_CONFIGS; do
    unset -v $config
done
 
TENANT_ID=53c1716f-3e67-4e52-b573-775b069e29f4
RESOURCE_GROUP_NAME=ai_training_testbed
LOCATION=southeastasia
REGISTRY_NAME=scgchatbot
SKU=Standard
CONTAINERAPP_ENV_NAME=scg-backup-env
CONTAINERAPP_IMAGE=madame-lan-backup
CONTAINERAPP_NAME=madame-lan-backup
TARGET_PORT=3000
 
for config in $TARGET_CONFIGS; do
    echo "${green} -${config}=${!config}${reset}"
done
 
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ROOT_DIR=$(cd "${SCRIPT_DIR}/.." && pwd)
 
increment_tag() {
    local latest_tag=$1
    IFS='.' read -r -a version_parts <<< "$latest_tag"
    version_parts[2]=$((version_parts[2] + 1))
    echo "${version_parts[0]}.${version_parts[1]}.${version_parts[2]}"
}
is_valid_tag() {
    local tag=$1
    if [[ $tag =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        return 0
    else
        return 1
    fi
}
deploy(){
    echo "${green}Azure login...${reset}"
    az login --tenant ${TENANT_ID}
 
    echo "${green}Check if registry exists...${reset}"
    if ! az acr show --name ${REGISTRY_NAME} --resource-group ${RESOURCE_GROUP_NAME} &> /dev/null; then
        echo "${green}Create registry...${reset}"
        az acr create --name ${REGISTRY_NAME} --sku ${SKU} --resource-group ${RESOURCE_GROUP_NAME} --location ${LOCATION}
    fi
    echo "${green}Enable admin user for ACR...${reset}"
    az acr update -n ${REGISTRY_NAME} --admin-enabled true
    echo "${green}Check if containerapp env exists...${reset}"
    if ! az containerapp env show --name ${CONTAINERAPP_ENV_NAME} --resource-group ${RESOURCE_GROUP_NAME} &> /dev/null; then
        echo "${green}Create containerapp env...${reset}"
        az containerapp env create --name ${CONTAINERAPP_ENV_NAME} --location ${LOCATION} --resource-group ${RESOURCE_GROUP_NAME}
    fi
 
    echo "${green}Fetching latest containerapp image tag...${reset}"
    latest_tag=$(az acr repository show-tags --name ${REGISTRY_NAME} --repository ${CONTAINERAPP_IMAGE} --orderby time_desc --top 1 --output tsv)
    echo "${green}Latest containerapp image tag: ${latest_tag}${reset}"
    if [ -z "$latest_tag" ] || ! is_valid_tag "$latest_tag"; then
        echo "${red}No valid existing tags found. Using default tag 1.0.0${reset}"
        new_tag="1.0.0"
    else
        new_tag=$(increment_tag $latest_tag)
    fi
    CONTAINERAPP_IMAGE=${CONTAINERAPP_IMAGE}:${new_tag}
    echo "${green}New containerapp image with tag: ${CONTAINERAPP_IMAGE}${reset}"
    echo "${green}Build containerapp image...${reset}"
    az acr build --image ${CONTAINERAPP_IMAGE} --registry ${REGISTRY_NAME} --file ${ROOT_DIR}/Dockerfile ${ROOT_DIR}
    echo "${green}Check if containerapp exists...${reset}"
    if az containerapp show --name ${CONTAINERAPP_NAME} --resource-group ${RESOURCE_GROUP_NAME} &> /dev/null; then
        echo "${green}Update existing containerapp...${reset}"
        az containerapp update --name ${CONTAINERAPP_NAME} \
                               --image ${REGISTRY_NAME}.azurecr.io/${CONTAINERAPP_IMAGE} \
                               --resource-group ${RESOURCE_GROUP_NAME} \
                               --query properties.configuration.ingress
    else
        echo "${green}Create containerapp...${reset}"
        az containerapp create --name ${CONTAINERAPP_NAME} \
                               --image ${REGISTRY_NAME}.azurecr.io/${CONTAINERAPP_IMAGE} \
                               --resource-group ${RESOURCE_GROUP_NAME} \
                               --environment ${CONTAINERAPP_ENV_NAME} \
                               --registry-server ${REGISTRY_NAME}.azurecr.io \
                               --target-port ${TARGET_PORT} \
                               --min-replicas 1 \
                               --max-replicas 1 \
                               --ingress external \
                               --query properties.configuration.ingress
    fi
}
 
cd "$PWD"
# Deploy Azure
echo "${green}Deploy Azure:${reset}"
deploy
 