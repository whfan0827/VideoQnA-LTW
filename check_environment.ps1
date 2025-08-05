# 環境檢查腳本
# 運行: .\check_environment.ps1

Write-Host "=== VideoQnA-LTW 環境檢查 ===" -ForegroundColor Green

# 檢查 Python
Write-Host "`n檢查 Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    if ($pythonVersion -like "*Python 3.10*") {
        Write-Host "✓ Python: $pythonVersion" -ForegroundColor Green
    } else {
        Write-Host "⚠ Python 版本: $pythonVersion (建議使用 Python 3.10)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "✗ Python 未安裝或不在 PATH 中" -ForegroundColor Red
}

# 檢查 Node.js
Write-Host "`n檢查 Node.js..." -ForegroundColor Yellow
try {
    $nodeVersion = node --version 2>&1
    Write-Host "✓ Node.js: $nodeVersion" -ForegroundColor Green
    
    $npmVersion = npm --version 2>&1
    Write-Host "✓ npm: $npmVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Node.js 或 npm 未安裝" -ForegroundColor Red
}

# 檢查項目文件
Write-Host "`n檢查項目文件..." -ForegroundColor Yellow
$backendPath = Join-Path $PSScriptRoot "app" "backend"
$frontendPath = Join-Path $PSScriptRoot "app" "frontend"

if (Test-Path $backendPath) {
    Write-Host "✓ 後端目錄存在" -ForegroundColor Green
    
    $requirementsPath = Join-Path $backendPath "requirements.txt"
    if (Test-Path $requirementsPath) {
        Write-Host "✓ requirements.txt 存在" -ForegroundColor Green
    } else {
        Write-Host "✗ requirements.txt 不存在" -ForegroundColor Red
    }
    
    $envPath = Join-Path $backendPath ".env"
    if (Test-Path $envPath) {
        Write-Host "✓ .env 文件存在" -ForegroundColor Green
    } else {
        Write-Host "⚠ .env 文件不存在（可使用 .env.example 作為模板）" -ForegroundColor Yellow
    }
} else {
    Write-Host "✗ 後端目錄不存在" -ForegroundColor Red
}

if (Test-Path $frontendPath) {
    Write-Host "✓ 前端目錄存在" -ForegroundColor Green
    
    $packageJsonPath = Join-Path $frontendPath "package.json"
    if (Test-Path $packageJsonPath) {
        Write-Host "✓ package.json 存在" -ForegroundColor Green
    } else {
        Write-Host "✗ package.json 不存在" -ForegroundColor Red
    }
} else {
    Write-Host "✗ 前端目錄不存在" -ForegroundColor Red
}

# 檢查虛擬環境
Write-Host "`n檢查 Python 虛擬環境..." -ForegroundColor Yellow
$venvPath = Join-Path $backendPath "venv"
if (Test-Path $venvPath) {
    Write-Host "✓ Python 虛擬環境已創建" -ForegroundColor Green
} else {
    Write-Host "⚠ Python 虛擬環境未創建（將在首次運行時創建）" -ForegroundColor Yellow
}

# 檢查node_modules
Write-Host "`n檢查前端依賴..." -ForegroundColor Yellow
$nodeModulesPath = Join-Path $frontendPath "node_modules"
if (Test-Path $nodeModulesPath) {
    Write-Host "✓ 前端依賴已安裝" -ForegroundColor Green
} else {
    Write-Host "⚠ 前端依賴未安裝（需要運行 npm install）" -ForegroundColor Yellow
}

Write-Host "`n=== 檢查完成 ===" -ForegroundColor Green
Write-Host "`n準備開始？運行以下命令：" -ForegroundColor Cyan
Write-Host ".\start_local.ps1" -ForegroundColor White
