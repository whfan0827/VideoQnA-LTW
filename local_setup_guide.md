# VideoQnA-LTW Local Development Environment Setup Guide

## Prerequisites

1. **Python 3.10** - Required for backend
   ```powershell
   python --version  # Should show Python 3.10.x
   ```

2. **Node.js** (recommended 16+) - Required for frontend
   ```powershell
   node --version
   npm --version
   ```

3. **Azure Service Account** (if using actual Azure services)
   - Azure OpenAI Service
   - Azure AI Search Service
   - Azure Video Indexer Account

## Local Development Setup Steps

### Step 1: Install Python Dependencies

```powershell
cd c:\PS\VideoQnA-LTW\app\backend
pip install -r requirements.txt
```

### 步驟 2: 設置環境變數

創建本機開發用的環境變數文件：

```powershell
# 在 app\backend\ 目錄下創建 .env 文件
# 複製並修改現有的 .env 文件
```

### 步驟 3: 安裝前端依賴

```powershell
cd c:\PS\VideoQnA-LTW\app\frontend
npm install
```

### 步驟 4: 構建前端

```powershell
# 在 frontend 目錄下
npm run build
```

這會將前端文件構建到 `backend/static/` 目錄，讓 Flask 可以提供靜態文件服務。

### 步驟 5: 運行後端服務

```powershell
cd c:\PS\VideoQnA-LTW\app\backend

# 設置 Python 路徑
$env:PYTHONPATH += ";$(Get-Location)"

# 運行 Flask 應用
python app.py
```

### 步驟 6: 訪問應用

打開瀏覽器，訪問: `http://localhost:5000`

## 開發模式運行

如果你想要前端熱重載開發：

**終端 1 - 運行後端:**
```powershell
cd c:\PS\VideoQnA-LTW\app\backend
$env:PYTHONPATH += ";$(Get-Location)"
$env:FLASK_ENV = "development"
python app.py
```

**終端 2 - 運行前端開發服務器:**
```powershell
cd c:\PS\VideoQnA-LTW\app\frontend
npm run dev
```

前端開發服務器通常會運行在 `http://localhost:3000` 或類似端口。

## 環境變數配置

在 `app\backend\.env` 文件中設置：

```env
# 使用測試模式
LANGUAGE_MODEL=dummy
PROMPT_CONTENT_DB=chromadb
PROMPT_CONTENT_DB_NAME=vi-test-index

# 或者如果你有 Azure 服務
LANGUAGE_MODEL=openai
PROMPT_CONTENT_DB=azure_search
AZURE_OPENAI_API_KEY=your_api_key
AZURE_OPENAI_SERVICE=your_service_name
# ... 其他 Azure 配置
```

## 疑難排解

1. **Python 路徑問題**: 確保設置了 PYTHONPATH
2. **依賴問題**: 確保所有 pip 和 npm 依賴都已安裝
3. **Azure 服務問題**: 可以先使用 dummy 模式測試本機運行
