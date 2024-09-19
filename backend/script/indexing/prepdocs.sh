echo "Setting environment variables..."
export searchkey="zPnpMRtjC2fPGkLq2BdHobp73pxz8pgcRkjTADNqAcAzSeCZbzKc"
export openaikey="79705c47f01c47abbdb45b131340385a"
export formrecognizerkey="96943c14adca4514a52e4ff2f904f683"
export storagekey="f0pz9vxyP/giZOMmOyF1R+sXH8ElOQTJOdGlKxJ+FxueeinVL24p2H285jrsbslavSSr6Swy9rU/+AStbgJRfQ=="
export AZURE_STORAGE_ACCOUNT="stmipb2mp7a2q7u"
export AZURE_STORAGE_CONTAINER="madamelantest"
export AZURE_SEARCH_SERVICE="gptkb-mipb2mp7a2q7u"
export AZURE_OPENAI_SERVICE="eastusaoai001"
export AZURE_OPENAI_EMB_DEPLOYMENT="text-embedding-3-small"
export AZURE_OPENAI_CHAT_DEPLOYMENT="gpt-4o-mini"
export AZURE_FORMRECOGNIZER_RESOURCE_GROUP="ai_training_testbed"
export AZURE_FORMRECOGNIZER_SERVICE="cog-di-mipb2mp7a2q7u"
export AZURE_TENANT_ID="53c1716f-3e67-4e52-b573-775b069e29f4"
export AZURE_SEARCH_ADMIN_KEY="zPnpMRtjC2fPGkLq2BdHobp73pxz8pgcRkjTADNqAcAzSeCZbzKc"
export AZURE_SEARCH_INDEX_NAME="madame_lan_test"

echo "Environment variables set:"
echo "AZURE_STORAGE_ACCOUNT: $AZURE_STORAGE_ACCOUNT"
echo "AZURE_STORAGE_CONTAINER: $AZURE_STORAGE_CONTAINER"
echo "AZURE_SEARCH_SERVICE: $AZURE_SEARCH_SERVICE"
echo "AZURE_OPENAI_SERVICE: $AZURE_OPENAI_SERVICE"
echo "AZURE_OPENAI_EMB_DEPLOYMENT: $AZURE_OPENAI_EMB_DEPLOYMENT"
echo "AZURE_OPENAI_CHAT_DEPLOYMENT: $AZURE_OPENAI_CHAT_DEPLOYMENT"
echo "AZURE_FORMRECOGNIZER_SERVICE: $AZURE_FORMRECOGNIZER_SERVICE"
echo "AZURE_TENANT_ID: $AZURE_TENANT_ID"
echo "AZURE_SEARCH_INDEX_NAME: $AZURE_SEARCH_INDEX_NAME"

# Run the script
echo "Running prepdocs.py..."
python prepdocs.py "./data/madamelan" \
  --storageaccount "$AZURE_STORAGE_ACCOUNT" \
  --container "$AZURE_STORAGE_CONTAINER" \
  --searchservice "$AZURE_SEARCH_SERVICE" \
  --openaiservice "$AZURE_OPENAI_SERVICE" \
  --openaiembdeployment "$AZURE_OPENAI_EMB_DEPLOYMENT" \
  --openaideployment "$AZURE_OPENAI_CHAT_DEPLOYMENT" \
  --searchkey "$AZURE_SEARCH_ADMIN_KEY" \
  --index "$AZURE_SEARCH_INDEX_NAME" \
  --formrecognizerservice "$AZURE_FORMRECOGNIZER_SERVICE" \
  --tenantid "$AZURE_TENANT_ID" \
  --openaikey "$openaikey" \
  --formrecognizerkey "$formrecognizerkey" \
  --storagekey "$storagekey" \
  -v