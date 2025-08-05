# 本機開發快速開始

## 🚀 快速啟動

1. **檢查環境**
   ```powershell
   .\check_environment.ps1
   ```

2. **啟動應用**
   ```powershell
   .\start_local.ps1
   ```

3. **訪問應用**
   - 打開瀏覽器訪問: http://localhost:5000

## 📋 前置需求

- Python 3.10
- Node.js 16+
- PowerShell 7+

## 🔧 手動設置

如果自動腳本有問題，可以手動執行：

### 後端設置
```powershell
cd app\backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
# 編輯 .env 文件設定
$env:PYTHONPATH = "$(Get-Location)"
python app.py
```

### 前端設置
```powershell
cd app\frontend
npm install
npm run build  # 生產模式
# 或
npm run dev    # 開發模式
```

## 🧪 測試模式

預設使用測試模式，不需要真實的 Azure 服務：
- `LANGUAGE_MODEL=dummy` - 使用模擬的語言模型
- `PROMPT_CONTENT_DB=chromadb` - 使用本機向量資料庫

## 🔑 使用真實 Azure 服務

如果你有 Azure 服務帳號，編輯 `.env` 文件：
```env
LANGUAGE_MODEL=openai
PROMPT_CONTENT_DB=azure_search
AZURE_OPENAI_API_KEY=your_key
AZURE_OPENAI_SERVICE=your_service
# ... 其他設定
```

## 🐛 常見問題

1. **Python 版本錯誤**: 確保使用 Python 3.10
2. **模組找不到**: 確保設置了 `PYTHONPATH`
3. **連接埠被佔用**: 修改 `app.py` 中的 port 設定
4. **前端構建失敗**: 確保 Node.js 版本正確並重新安裝依賴

## 📁 項目結構

```
VideoQnA-LTW/
├── app/
│   ├── backend/          # Flask 後端
│   │   ├── app.py       # 主要應用文件
│   │   ├── .env         # 環境設定
│   │   └── vi_search/   # 核心邏輯
│   └── frontend/        # React 前端
├── start_local.ps1      # 啟動腳本
└── check_environment.ps1 # 環境檢查
```
