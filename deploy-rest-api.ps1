# 使用 REST API 直接部署 Container App
param(
    [string]$SubscriptionId = "***REMOVED_SUBSCRIPTION_ID***",
    [string]$ResourceGroupName = "***REMOVED_RESOURCE_GROUP***",
    [string]$ContainerAppName = "videoqna-ltw",
    [string]$AzureOpenAiApiKey,
    [string]$AzureSearchKey,
    [string]$AzureClientSecret
)

Write-Host "🚀 使用 REST API 部署 Container App" -ForegroundColor Green

# 獲取 Access Token
$context = Get-AzContext
if (-not $context) {
    Write-Host "請先登入 Azure: Connect-AzAccount" -ForegroundColor Red
    exit 1
}

$token = [Microsoft.Azure.Commands.Common.Authentication.AzureSession]::Instance.AuthenticationFactory.Authenticate($context.Account, $context.Environment, $context.Tenant.Id, $null, $null, $null, $null).AccessToken

$headers = @{
    "Authorization" = "Bearer $token"
    "Content-Type" = "application/json"
}

# Container App 配置 JSON
$containerAppConfig = @{
    location = "eastus"
    properties = @{
        managedEnvironmentId = "/subscriptions/$SubscriptionId/resourceGroups/$ResourceGroupName/providers/Microsoft.App/managedEnvironments/videoqna-env"
        configuration = @{
            secrets = @(
                @{ name = "azure-openai-api-key"; value = $AzureOpenAiApiKey }
                @{ name = "azure-search-key"; value = $AzureSearchKey }
                @{ name = "azure-client-secret"; value = $AzureClientSecret }
            )
            ingress = @{
                external = $true
                targetPort = 5000
                transport = "http"
                traffic = @(@{ weight = 100; latestRevision = $true })
            }
        }
        template = @{
            containers = @(@{
                image = "***REMOVED_ACR_URL***/videoqna-ltw:latest"
                name = "videoqna-app"
                resources = @{
                    cpu = 2.0
                    memory = "4.0Gi"
                }
                env = @(
                    @{ name = "FLASK_ENV"; value = "production" }
                    @{ name = "PYTHONPATH"; value = "/app" }
                    @{ name = "LANGUAGE_MODEL"; value = "openai" }
                    @{ name = "AZURE_OPENAI_API_KEY"; secretRef = "azure-openai-api-key" }
                    @{ name = "AZURE_SEARCH_KEY"; secretRef = "azure-search-key" }
                    @{ name = "AZURE_CLIENT_SECRET"; secretRef = "azure-client-secret" }
                )
            })
            scale = @{
                minReplicas = 1
                maxReplicas = 3
            }
        }
    }
} | ConvertTo-Json -Depth 10

# 調用 REST API
$uri = "https://management.azure.com/subscriptions/$SubscriptionId/resourceGroups/$ResourceGroupName/providers/Microsoft.App/containerApps/$ContainerAppName" + "?api-version=2022-10-01"

try {
    $response = Invoke-RestMethod -Uri $uri -Method PUT -Headers $headers -Body $containerAppConfig
    Write-Host "✅ Container App 部署成功！" -ForegroundColor Green
    Write-Host "URL: https://$($response.properties.configuration.ingress.fqdn)" -ForegroundColor Cyan
} catch {
    Write-Host "❌ 部署失敗: $($_.Exception.Message)" -ForegroundColor Red
}