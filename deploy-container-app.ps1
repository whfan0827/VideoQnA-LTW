# Azure Container App 部署腳本
# 使用 ARM Template 部署，不需要 containerapp 擴展

param(
    [Parameter(Mandatory=$true)]
    [string]$AzureOpenAiApiKey,
    
    [Parameter(Mandatory=$true)]
    [string]$AzureSearchKey,
    
    [Parameter(Mandatory=$true)]
    [string]$AzureClientSecret
)

Write-Host "🚀 開始部署 VideoQnA-LTW 到 Azure Container Apps" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green

# 設定變數
$resourceGroupName = "***REMOVED_RESOURCE_GROUP***"
$location = "eastus"
$containerAppName = "videoqna-ltw"
$environmentName = "videoqna-env"
$acrName = "***REMOVED_ACR_NAME***"
$subscriptionId = "***REMOVED_SUBSCRIPTION_ID***"

# Azure CLI 完整路徑
$azPath = "C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd"

# 將 Azure CLI 加入到 PATH 環境變數
$azCliPath = "C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin"
if ($env:PATH -notlike "*$azCliPath*") {
    Write-Host "🔧 將 Azure CLI 加入到 PATH 環境變數..." -ForegroundColor Yellow
    $env:PATH = "$azCliPath;$env:PATH"
    Write-Host "✅ Azure CLI 已加入到當前會話的 PATH" -ForegroundColor Green
}

try {
    # 修復 Azure CLI 連線問題
    Write-Host "🔧 設定 Azure CLI 連線參數..." -ForegroundColor Yellow
    & $azPath config set core.disable_connection_pooling=true 2>$null
    
    # 檢查登入狀態
    Write-Host "📋 檢查 Azure 登入狀態..." -ForegroundColor Yellow
    $account = & $azPath account show --query name --output tsv 2>$null
    if (-not $account) {
        Write-Host "⚠️ 未登入 Azure，開始登入..." -ForegroundColor Yellow
        & $azPath login
        & $azPath account set --subscription $subscriptionId
    } else {
        Write-Host "✅ 已登入 Azure: $account" -ForegroundColor Green
        & $azPath account set --subscription $subscriptionId
    }

    # 註冊必要的資源提供者
    Write-Host "🔧 檢查並註冊 Azure 資源提供者..." -ForegroundColor Yellow
    $providers = @(
        "Microsoft.ContainerRegistry",
        "Microsoft.App", 
        "Microsoft.OperationalInsights"
    )
    
    foreach ($provider in $providers) {
        try {
            $status = & $azPath provider show --namespace $provider --query "registrationState" --output tsv 2>$null
            if ([string]::IsNullOrEmpty($status) -or $status -ne "Registered") {
                Write-Host "📝 註冊資源提供者: $provider" -ForegroundColor Yellow
                & $azPath provider register --namespace $provider
                
                # 簡化等待邏輯，不阻塞部署流程
                Start-Sleep 3
                $newStatus = & $azPath provider show --namespace $provider --query "registrationState" --output tsv 2>$null
                if ($newStatus -eq "Registered") {
                    Write-Host "✅ $provider 註冊成功" -ForegroundColor Green
                } elseif ($newStatus -eq "Registering") {
                    Write-Host "⏳ $provider 註冊中，將在背景繼續..." -ForegroundColor Yellow
                } else {
                    Write-Host "⚠️ $provider 註冊狀態: $newStatus" -ForegroundColor Yellow
                }
            } else {
                Write-Host "✅ $provider 已註冊" -ForegroundColor Green
            }
        } catch {
            Write-Host "⚠️ 檢查 $provider 時發生錯誤，繼續執行..." -ForegroundColor Yellow
        }
    }

    # 檢查 Docker 映像是否存在
    Write-Host "📦 檢查 Docker 映像..." -ForegroundColor Yellow
    $imageExists = docker images "$acrName.azurecr.io/videoqna-ltw" --format "{{.Repository}}:{{.Tag}}"
    if (-not $imageExists) {
        Write-Host "🏗️ 建立 Docker 映像..." -ForegroundColor Yellow
        docker build -t "$acrName.azurecr.io/videoqna-ltw:latest" .
        if ($LASTEXITCODE -ne 0) {
            throw "Docker 建立失敗"
        }
    }

    # 確保 ACR 存在並推送映像
    Write-Host "🔐 登入 Container Registry..." -ForegroundColor Yellow
    
    # 先檢查 ACR 是否存在
    $acrExists = & $azPath acr show --name $acrName --resource-group $resourceGroupName 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "🏗️ 建立 Container Registry..." -ForegroundColor Yellow
        & $azPath acr create --resource-group $resourceGroupName --name $acrName --sku Basic
        if ($LASTEXITCODE -ne 0) {
            throw "建立 Container Registry 失敗"
        }
        Write-Host "✅ Container Registry 建立成功" -ForegroundColor Green
    }
    
    # 重試登入 ACR
    $loginRetries = 3
    $loginSuccess = $false
    for ($i = 1; $i -le $loginRetries; $i++) {
        Write-Host "🔐 嘗試登入 Container Registry (第 $i 次)..." -ForegroundColor Yellow
        & $azPath acr login --name $acrName
        if ($LASTEXITCODE -eq 0) {
            $loginSuccess = $true
            Write-Host "✅ Container Registry 登入成功" -ForegroundColor Green
            break
        } else {
            Write-Host "⚠️ 登入失敗，等待 5 秒後重試..." -ForegroundColor Yellow
            Start-Sleep 5
        }
    }
    
    if (-not $loginSuccess) {
        throw "Container Registry 登入失敗，已重試 $loginRetries 次"
    }

    Write-Host "📤 推送映像到 Registry..." -ForegroundColor Yellow
    docker push "$acrName.azurecr.io/videoqna-ltw:latest"
    if ($LASTEXITCODE -ne 0) {
        throw "映像推送失敗"
    }

    # 部署 ARM Template
    Write-Host "🚀 部署 Container App..." -ForegroundColor Yellow
    $deploymentName = "containerapp-deployment-$(Get-Date -Format 'yyyyMMddHHmmss')"
    
    # 建立參數檔案以處理 securestring
    $parametersJson = @{
        containerAppName = @{ value = $containerAppName }
        environmentName = @{ value = $environmentName }
        location = @{ value = $location }
        containerImage = @{ value = "$acrName.azurecr.io/videoqna-ltw:latest" }
        azureOpenAiApiKey = @{ value = $AzureOpenAiApiKey }
        azureSearchKey = @{ value = $AzureSearchKey }
        azureClientSecret = @{ value = $AzureClientSecret }
    } | ConvertTo-Json -Depth 3
    
    $parametersFile = "deployment-parameters-temp.json"
    $parametersJson | Out-File -FilePath $parametersFile -Encoding UTF8
    
    # 重試部署邏輯
    $deployRetries = 3
    $deploySuccess = $false
    
    for ($i = 1; $i -le $deployRetries; $i++) {
        try {
            Write-Host "🚀 嘗試部署 (第 $i 次)..." -ForegroundColor Yellow
            & $azPath deployment group create `
                --resource-group $resourceGroupName `
                --template-file "container-app-template.json" `
                --name "$deploymentName-attempt$i" `
                --parameters "@$parametersFile" `
                --no-wait
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✅ 部署指令成功送出，檢查狀態..." -ForegroundColor Green
                
                # 等待並檢查部署狀態
                $timeout = 300 # 5 分鐘超時
                $elapsed = 0
                
                do {
                    Start-Sleep 30
                    $elapsed += 30
                    Write-Host "⏳ 檢查部署狀態... ($elapsed 秒)" -ForegroundColor Yellow
                    
                    $deployStatus = & $azPath deployment group show `
                        --resource-group $resourceGroupName `
                        --name "$deploymentName-attempt$i" `
                        --query "properties.provisioningState" `
                        --output tsv 2>$null
                    
                    if ($deployStatus -eq "Succeeded") {
                        $deploySuccess = $true
                        Write-Host "✅ 部署成功完成！" -ForegroundColor Green
                        break
                    } elseif ($deployStatus -eq "Failed") {
                        Write-Host "❌ 部署失敗" -ForegroundColor Red
                        break
                    } else {
                        Write-Host "⏳ 部署進行中... 狀態: $deployStatus" -ForegroundColor Yellow
                    }
                } while ($elapsed -lt $timeout)
                
                if ($deploySuccess) {
                    break
                }
            }
        } catch {
            Write-Host "⚠️ 部署嘗試 $i 失敗: $($_.Exception.Message)" -ForegroundColor Yellow
        }
        
        if ($i -lt $deployRetries) {
            Write-Host "⏳ 等待 30 秒後重試..." -ForegroundColor Yellow
            Start-Sleep 30
        }
    }
    
    # 清理臨時參數檔案
    if (Test-Path $parametersFile) {
        Remove-Item $parametersFile -Force
    }
    
    if (-not $deploySuccess) {
        throw "ARM Template 部署失敗，已重試 $deployRetries 次"
    }

    # 取得應用程式 URL
    Write-Host "📋 取得應用程式資訊..." -ForegroundColor Yellow
    $fqdn = & $azPath deployment group show --resource-group $resourceGroupName --name "$deploymentName-attempt$i" --query "properties.outputs.containerAppFQDN.value" --output tsv 2>$null
    
    if ($fqdn) {
        Write-Host "🌐 應用程式 URL: https://$fqdn" -ForegroundColor Cyan
    }
    Write-Host "📊 管理入口: https://portal.azure.com/#@/resource/subscriptions/$subscriptionId/resourceGroups/$resourceGroupName/providers/Microsoft.App/containerApps/$containerAppName/overview" -ForegroundColor Cyan

} catch {
    Write-Host "❌ 部署失敗: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host "🎉 部署完成！" -ForegroundColor Green