# 使用 Azure Container Instances 部署
param(
    [string]$ResourceGroupName = "***REMOVED_RESOURCE_GROUP***",
    [string]$ContainerName = "videoqna-ltw-aci",
    [string]$Location = "eastus",
    [string]$AzureOpenAiApiKey,
    [string]$AzureSearchKey,
    [string]$AzureClientSecret
)

Write-Host "🚀 部署到 Azure Container Instances" -ForegroundColor Green

# 設定環境變數
$envVars = @(
    @{name="FLASK_ENV"; value="production"}
    @{name="PYTHONPATH"; value="/app"}
    @{name="LANGUAGE_MODEL"; value="openai"}
    @{name="PROMPT_CONTENT_DB"; value="azure_search"}
    @{name="AZURE_OPENAI_SERVICE"; value="***REMOVED_RESOURCE_NAME***"}
    @{name="AZURE_OPENAI_API_KEY"; secureValue=$AzureOpenAiApiKey}
    @{name="AZURE_SEARCH_KEY"; secureValue=$AzureSearchKey}
    @{name="AZURE_CLIENT_SECRET"; secureValue=$AzureClientSecret}
    # 更多環境變數...
)

# 部署 Container Instance
az container create `
    --resource-group $ResourceGroupName `
    --name $ContainerName `
    --image "***REMOVED_ACR_URL***/videoqna-ltw:latest" `
    --cpu 2 `
    --memory 4 `
    --ports 5000 `
    --ip-address public `
    --location $Location `
    --environment-variables ($envVars | ConvertTo-Json -Depth 3)

Write-Host "✅ 部署完成！" -ForegroundColor Green