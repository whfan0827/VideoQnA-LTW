# 簡化版 Azure Container App 部署腳本
# 使用 Azure CLI containerapp 指令直接部署
# 從環境變數或參數讀取設定值

param(
    [Parameter(Mandatory=$true)]
    [string]$AzureOpenAiApiKey,
    
    [Parameter(Mandatory=$true)]
    [string]$AzureSearchKey,
    
    [Parameter(Mandatory=$true)]
    [string]$AzureClientSecret,
    
    [Parameter(Mandatory=$false)]
    [string]$AzureOpenAiService = $env:AZURE_OPENAI_SERVICE,
    
    [Parameter(Mandatory=$false)]
    [string]$AzureOpenAiChatGptDeployment = $env:AZURE_OPENAI_CHATGPT_DEPLOYMENT,
    
    [Parameter(Mandatory=$false)]
    [string]$AzureOpenAiEmbeddingsDeployment = $env:AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT
)

Write-Host "🚀 開始部署 VideoQnA-LTW 到 Azure Container Apps (簡化版)" -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Green

# 從 .env 檔案讀取預設值（如果參數未提供）
if (-not $AzureOpenAiService) { $AzureOpenAiService = "***REMOVED_RESOURCE_NAME***" }
if (-not $AzureOpenAiChatGptDeployment) { $AzureOpenAiChatGptDeployment = "gpt-4.1-mini" }
if (-not $AzureOpenAiEmbeddingsDeployment) { $AzureOpenAiEmbeddingsDeployment = "text-embedding-ada-002" }

Write-Host "📋 使用設定:" -ForegroundColor Yellow
Write-Host "   Azure OpenAI Service: $AzureOpenAiService" -ForegroundColor Cyan
Write-Host "   ChatGPT Deployment: $AzureOpenAiChatGptDeployment" -ForegroundColor Cyan
Write-Host "   Embeddings Deployment: $AzureOpenAiEmbeddingsDeployment" -ForegroundColor Cyan

# 設定變數
$resourceGroupName = "***REMOVED_RESOURCE_GROUP***"
$containerAppName = "videoqna-ltw"
$environmentName = "videoqna-env"
$acrName = "***REMOVED_ACR_NAME***"

try {
    # 設定 Azure CLI 連線參數
    Write-Host "🔧 設定 Azure CLI 連線參數..." -ForegroundColor Yellow
    az config set core.disable_connection_pooling=true

    # 檢查登入狀態
    Write-Host "📋 檢查 Azure 登入狀態..." -ForegroundColor Yellow
    $account = az account show --query name --output tsv 2>$null
    if (-not $account) {
        Write-Host "⚠️ 請先執行 az login 登入 Azure" -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ 已登入 Azure: $account" -ForegroundColor Green

    # 檢查 Container App Environment 是否存在
    Write-Host "🏗️ 檢查 Container App Environment..." -ForegroundColor Yellow
    $envExists = az containerapp env show --name $environmentName --resource-group $resourceGroupName 2>$null
    if (-not $envExists) {
        Write-Host "🏗️ 建立 Container App Environment..." -ForegroundColor Yellow
        az containerapp env create `
            --name $environmentName `
            --resource-group $resourceGroupName `
            --location eastus
        
        if ($LASTEXITCODE -ne 0) {
            throw "Container App Environment 建立失敗"
        }
        Write-Host "✅ Container App Environment 建立成功" -ForegroundColor Green
    } else {
        Write-Host "✅ Container App Environment 已存在" -ForegroundColor Green
    }

    # 取得 ACR 密碼
    Write-Host "🔐 取得 Container Registry 認證..." -ForegroundColor Yellow
    $acrPassword = az acr credential show --name $acrName --query "passwords[0].value" --output tsv
    if (-not $acrPassword) {
        throw "無法取得 ACR 認證，請確認 ACR 管理員使用者已啟用"
    }

    # 部署 Container App
    Write-Host "🚀 部署 Container App..." -ForegroundColor Yellow
    az containerapp create `
        --name $containerAppName `
        --resource-group $resourceGroupName `
        --environment $environmentName `
        --image "$acrName.azurecr.io/videoqna-ltw:latest" `
        --target-port 5000 `
        --ingress external `
        --registry-server "$acrName.azurecr.io" `
        --registry-username $acrName `
        --registry-password $acrPassword `
        --cpu 2.0 `
        --memory 4.0Gi `
        --min-replicas 1 `
        --max-replicas 3 `
        --env-vars `
            "FLASK_ENV=production" `
            "PYTHONPATH=/app" `
            "LANGUAGE_MODEL=openai" `
            "PROMPT_CONTENT_DB=azure_search" `
            "PROMPT_CONTENT_DB_NAME=local_vi_azure_search_db" `
            "AZURE_OPENAI_SERVICE=$AzureOpenAiService" `
            "AZURE_OPENAI_CHATGPT_DEPLOYMENT=$AzureOpenAiChatGptDeployment" `
            "AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT=$AzureOpenAiEmbeddingsDeployment" `
            "AZURE_SEARCH_SERVICE=***REMOVED_RESOURCE_NAME***" `
            "AZURE_SEARCH_INDEX=vi-db-name-index" `
            "AccountName=vincentvideoindexerai01" `
            "ResourceGroup=***REMOVED_RESOURCE_GROUP***" `
            "SubscriptionId=***REMOVED_SUBSCRIPTION_ID***" `
            "AZURE_TENANT_ID=***REMOVED_TENANT_ID***" `
            "AZURE_SUBSCRIPTION_ID=***REMOVED_SUBSCRIPTION_ID***" `
            "AZURE_CLIENT_ID=***REMOVED_CLIENT_ID***" `
        --secrets `
            "azure-openai-api-key=$AzureOpenAiApiKey" `
            "azure-search-key=$AzureSearchKey" `
            "azure-client-secret=$AzureClientSecret" `
        --env-vars `
            "AZURE_OPENAI_API_KEY=secretref:azure-openai-api-key" `
            "AZURE_SEARCH_KEY=secretref:azure-search-key" `
            "AZURE_CLIENT_SECRET=secretref:azure-client-secret"

    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ 部署成功完成！" -ForegroundColor Green
        
        # 取得應用程式 URL
        Write-Host "📋 取得應用程式資訊..." -ForegroundColor Yellow
        $fqdn = az containerapp show --name $containerAppName --resource-group $resourceGroupName --query "properties.configuration.ingress.fqdn" --output tsv
        
        Write-Host "🌐 應用程式 URL: https://$fqdn" -ForegroundColor Cyan
        Write-Host "📊 管理入口: https://portal.azure.com/#@/resource/subscriptions/***REMOVED_SUBSCRIPTION_ID***/resourceGroups/$resourceGroupName/providers/Microsoft.App/containerApps/$containerAppName/overview" -ForegroundColor Cyan
        
    } else {
        throw "Container App 部署失敗"
    }

} catch {
    Write-Host "❌ 部署失敗: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host "🎉 部署完成！" -ForegroundColor Green