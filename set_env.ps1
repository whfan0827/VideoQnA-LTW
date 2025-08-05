# set_env.ps1 - 設定 Azure Developer CLI 所需環境變數

# Azure 基本配置
azd env set AZURE_LOCATION 'eastus'  # 主要资源在 East US
azd env set AZURE_SUBSCRIPTION_ID '***REMOVED_SUBSCRIPTION_ID***'
azd env set AZURE_TENANT_ID '***REMOVED_TENANT_ID***'
azd env set resourceGroupName '***REMOVED_RESOURCE_GROUP***'

# Azure OpenAI 配置 (East US)
azd env set AZURE_OPENAI_API_KEY '***REMOVED_OPENAI_KEY***'
azd env set AZURE_OPENAI_SERVICE '***REMOVED_RESOURCE_NAME***'
azd env set AZURE_OPENAI_RESOURCE_GROUP '***REMOVED_RESOURCE_GROUP***'
azd env set AZURE_OPENAI_CHATGPT_DEPLOYMENT 'gpt-4o'
azd env set AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT 'text-embedding-ada-002'
azd env set openAiServiceName '***REMOVED_RESOURCE_NAME***'
azd env set openAiResourceGroupName '***REMOVED_RESOURCE_GROUP***'

# Azure AI Search 配置 (East US 2)
azd env set AZURE_SEARCH_SERVICE '***REMOVED_RESOURCE_NAME***'
azd env set AZURE_SEARCH_KEY '***REMOVED_SEARCH_KEY***'
azd env set AZURE_SEARCH_LOCATION 'eastus2'
azd env set AZURE_SEARCH_SERVICE_RESOURCE_GROUP '***REMOVED_RESOURCE_GROUP***'
azd env set searchServiceName '***REMOVED_RESOURCE_NAME***'
azd env set searchServiceResourceGroupName '***REMOVED_RESOURCE_GROUP***'
azd env set searchServiceResourceGroupLocation 'eastus2'
azd env set useExistingSearch 'true'

# Video Indexer 配置
azd env set VIDEO_INDEXER_ACCOUNT_NAME 'vincentvideoindexerai'
azd env set VIDEO_INDEXER_RESOURCE_GROUP '***REMOVED_RESOURCE_GROUP***'

# Storage Account 配置
azd env set STORAGE_ACCOUNT_NAME 'vincentvi'

# 应用配置
azd env set LANGUAGE_MODEL 'openai'
azd env set PROMPT_CONTENT_DB 'azure_search'
azd env set PROMPT_CONTENT_DB_NAME 'vi-db-name-index'
