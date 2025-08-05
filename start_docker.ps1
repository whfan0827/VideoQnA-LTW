# Docker 版本啟動腳本
# 運行: .\start_docker.ps1

Write-Host "=== VideoQnA-LTW Docker 部署 ===" -ForegroundColor Green

# 檢查 Docker 是否安裝
Write-Host "`n檢查 Docker..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version 2>&1
    Write-Host "✓ Docker: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker 未安裝或不在 PATH 中" -ForegroundColor Red
    Write-Host "請先安裝 Docker Desktop: https://www.docker.com/products/docker-desktop" -ForegroundColor Cyan
    exit 1
}

# 檢查 Docker Compose
try {
    $composeVersion = docker compose version 2>&1
    Write-Host "✓ Docker Compose: $composeVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker Compose 未安裝" -ForegroundColor Red
    exit 1
}

# 檢查 Docker 是否運行
Write-Host "`n檢查 Docker 服務..." -ForegroundColor Yellow
try {
    docker info > $null 2>&1
    Write-Host "✓ Docker 服務正在運行" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker 服務未運行，請啟動 Docker Desktop" -ForegroundColor Red
    exit 1
}

Write-Host "`n選擇運行模式：" -ForegroundColor Yellow
Write-Host "1. 測試模式（使用模擬服務，無需 Azure 配置）"
Write-Host "2. Azure 模式（需要配置 Azure 服務）"
Write-Host "3. 開發模式（代碼熱重載）"
Write-Host "4. 停止並清理容器"
Write-Host "5. 查看日誌"
Write-Host "6. 退出"

$choice = Read-Host "請輸入選擇 (1-6)"

switch ($choice) {
    "1" {
        Write-Host "`n啟動測試模式..." -ForegroundColor Green
        Write-Host "使用模擬的語言模型和本機向量資料庫" -ForegroundColor Cyan
        
        # 使用預設的 docker-compose.yml（已設定為測試模式）
        docker compose up --build -d
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "`n✓ 服務啟動成功！" -ForegroundColor Green
            Write-Host "應用網址: http://localhost:5000" -ForegroundColor Cyan
            Write-Host "`n查看日誌: docker compose logs -f" -ForegroundColor Gray
        } else {
            Write-Host "✗ 啟動失敗，請檢查錯誤訊息" -ForegroundColor Red
        }
    }
    
    "2" {
        Write-Host "`n啟動 Azure 模式..." -ForegroundColor Green
        Write-Host "⚠ 需要先配置 Azure 服務資訊" -ForegroundColor Yellow
        
        # 檢查是否有 .env 文件
        if (-not (Test-Path ".env")) {
            Write-Host "創建 .env 文件..." -ForegroundColor Cyan
            @"
# Azure 服務配置
LANGUAGE_MODEL=openai
PROMPT_CONTENT_DB=azure_search

# Azure OpenAI
AZURE_OPENAI_API_KEY=your_api_key_here
AZURE_OPENAI_SERVICE=your_service_name
AZURE_OPENAI_CHATGPT_DEPLOYMENT=gpt-4o
AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT=text-embedding-ada-002

# Azure Search
AZURE_SEARCH_SERVICE=your_search_service
AZURE_SEARCH_KEY=your_search_key

# Video Indexer
AccountName=your_vi_account
ResourceGroup=your_resource_group
SubscriptionId=your_subscription_id
"@ | Out-File -FilePath ".env" -Encoding UTF8
            
            Write-Host "✓ 已創建 .env 文件" -ForegroundColor Green
            Write-Host "請編輯 .env 文件並填入你的 Azure 服務資訊，然後重新運行此腳本" -ForegroundColor Yellow
            exit 0
        }
        
        docker compose --env-file .env up --build -d
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "`n✓ 服務啟動成功！" -ForegroundColor Green
            Write-Host "應用網址: http://localhost:5000" -ForegroundColor Cyan
        } else {
            Write-Host "✗ 啟動失敗，請檢查 Azure 服務配置" -ForegroundColor Red
        }
    }
    
    "3" {
        Write-Host "`n啟動開發模式..." -ForegroundColor Green
        Write-Host "代碼變更將自動重載" -ForegroundColor Cyan
        
        # 開發模式，掛載源碼目錄
        docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
    }
    
    "4" {
        Write-Host "`n停止並清理容器..." -ForegroundColor Yellow
        docker compose down -v
        docker system prune -f
        Write-Host "✓ 清理完成" -ForegroundColor Green
    }
    
    "5" {
        Write-Host "`n查看服務日誌..." -ForegroundColor Yellow
        docker compose logs -f
    }
    
    "6" {
        Write-Host "退出" -ForegroundColor Gray
        exit 0
    }
    
    default {
        Write-Host "無效選擇" -ForegroundColor Red
        exit 1
    }
}
