## To deploy Azure

### I. Monitoring Azure portal: 
1. Login Azure portal `https://portal.azure.com/`
2. Go to Container Apps 
3. Go to `CONTAINERAPP_NAME=ai-assistant-v0-test` for example.
4. Activity log -> check deployment logs
5. Application Url (Allow microphone)

### II. Deploy Azure servers:
- V0 - Test/Production => Local (priority)/Internet Search
- V1 - Test/Production => NO-Local/Internet Search
- V2 - Test/Production => Local Search (only)
- Manual deploy pipeline

*NOTE*:
- DO NOT re-deploy `V0/V1/V2-Production`, without getting PM/TL/Customer's approval.
- DO NOT re-deploy `V0/V1/V2-Test`, without informing for BE/FE/...

### 1. Deploy V0 - Test/Production => Local (priority)/Internet Search
#### 1.1 Deploy V0 - Test:
- Config below paras at `deploy/start_Azure_v0_test.sh` if needed:
```
    CONTAINERAPP_ENV_NAME=ai-assistant-env-v0-test
    CONTAINERAPP_IMAGE=ai-assistant-v0-test:1.0
    CONTAINERAPP_NAME=ai-assistant-v0-test
```
- Run script:
```
    chmod +x deploy/start_Azure_v0_test.sh
    source deploy/start_Azure_v0_test.sh
```
- Go to  URL at `Access your app at <https://...>`  (Allow microphone)
#### 1.2 Deploy V0 - Production:
- Config below paras at `deploy/start_Azure_v0_pro.sh` if needed:
```
    CONTAINERAPP_ENV_NAME=ai-assistant-env-v0-pro
    CONTAINERAPP_IMAGE=ai-assistant-v0-pro:1.0
    CONTAINERAPP_NAME=ai-assistant-v0-pro
```
- Run script:
```
    chmod +x deploy/start_Azure_v0_pro.sh
    source deploy/start_Azure_v0_pro.sh
```
- Go to  URL at `Access your app at <https://...>`  (Allow microphone)

### 2. Deploy V1 - Test/Production => NO-Local/Internet Search
- Config : `./backend/app/conf/searcher.yaml`: `search_with_emotion` as `True`
#### 2.1 Deploy V1 - Test:
- Config below paras at `deploy/start_Azure_v1_test.sh` if needed:
```
    CONTAINERAPP_ENV_NAME=ai-assistant-env-v1-test
    CONTAINERAPP_IMAGE=ai-assistant-v1-test:1.0
    CONTAINERAPP_NAME=ai-assistant-v1-test    
```
- Run script:
```
    chmod +x deploy/start_Azure_v1_test.sh
    source deploy/start_Azure_v1_test.sh
```
- Go to  URL at `Access your app at <https://...>`  (Allow microphone)

#### 2.2 Deploy V1 - Production:
- Config below paras at `deploy/start_Azure_v1_pro.sh` if needed:
```
    CONTAINERAPP_ENV_NAME=ai-assistant-env-v1-pro
    CONTAINERAPP_IMAGE=ai-assistant-v1-pro:1.0
    CONTAINERAPP_NAME=ai-assistant-v1-pro
```
- Run script:
```
    chmod +x deploy/start_Azure_v1_pro.sh
    source deploy/start_Azure_v1_pro.sh
```
- Go to  URL at `Access your app at <https://...>`  (Allow microphone)

### 3. Deploy V2 - Test/Production => Local Search (only)
#### 3.1 Deploy V2 - Test:
- Config below paras at `deploy/start_Azure_v2_test.sh` if needed:
```
    CONTAINERAPP_ENV_NAME=ai-assistant-env-v2-test
    CONTAINERAPP_IMAGE=ai-assistant-v2-test:1.0
    CONTAINERAPP_NAME=ai-assistant-v2-test    
```
- Run script:
```
    chmod +x deploy/start_Azure_v2_test.sh
    source deploy/start_Azure_v2_test.sh
```
- Go to  URL at `Access your app at <https://...>`  (Allow microphone)

#### 3.2 Deploy V2 - Production:
- Config below paras at `deploy/start_Azure_v2_pro.sh` if needed:
```
    CONTAINERAPP_ENV_NAME=ai-assistant-env-v2-pro
    CONTAINERAPP_IMAGE=ai-assistant-v2-pro:1.0
    CONTAINERAPP_NAME=ai-assistant-v2-pro
```
- Run script:
```
    chmod +x deploy/start_Azure_v2_pro.sh
    source deploy/start_Azure_v2_pro.sh
```
- Go to  URL at `Access your app at <https://...>`  (Allow microphone)


### 5. To manual deploy Azure - Pro
- Config below paras:
```
    TENANT_ID=53c1716f-3e67-4e52-b573-775b069e29f4
    RESOURCE_GROUP_NAME=ai_training_testbed
    LOCATION=southeastasia
    REGISTRY_NAME=acrdn001
    SKU=Standard
    CONTAINERAPP_ENV_NAME=ai-assistant-env    
    CONTAINERAPP_IMAGE=ai-assistant:1.0  
    CONTAINERAPP_NAME=ai-assistant       
    TARGET_PORT=3000                     
```
- Run manually:
```
    cd ai-danang/
    #Azure login
    az login --tenant ${TENANT_ID}
    #Delete containerapp
    az containerapp delete --name ${CONTAINERAPP_NAME} --resource-group $RESOURCE_GROUP_NAME -y

    #Create registry
    az acr create --name ${REGISTRY_NAME} --sku ${SKU} --resource-group ${RESOURCE_GROUP_NAME}
    #Create containerapp env
    az containerapp env create --name ${CONTAINERAPP_ENV_NAME} --location ${LOCATION} -g ${RESOURCE_GROUP_NAME}
    #Build containerapp image
    az acr build --image ${CONTAINERAPP_IMAGE} --registry ${REGISTRY_NAME} ./
    #Create containerapp
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
```