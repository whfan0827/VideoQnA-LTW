# 🚀 VideoQnA-LTW 部署選項

你可以選擇以下任一方式運行這個應用：

## 🖥️ **方式一：直接本機運行（推薦開發）**

**優點：**
- 啟動速度快
- 直接除錯
- 熱重載友善
- 資源消耗少

**運行步驟：**
```powershell
.\check_environment.ps1  # 檢查環境
.\start_local.ps1        # 啟動應用
```

## 🐳 **方式二：Docker 容器化運行**

**優點：**
- 環境一致性
- 隔離性好
- 部署簡單
- 生產環境友善

**運行步驟：**
```powershell
.\start_docker.ps1       # Docker 版本啟動
```

---

## 🔧 **本機運行 vs Docker 對比**

| 特性 | 本機運行 | Docker |
|------|----------|--------|
| 啟動速度 | ⚡ 快 | 🐌 較慢（首次構建） |
| 環境隔離 | ❌ 無 | ✅ 完全隔離 |
| 熱重載 | ✅ 原生支援 | ⚡ 需要配置 |
| 除錯體驗 | ✅ 直接 | 🔧 需要配置 |
| 部署一致性 | ❌ 依賴本機環境 | ✅ 完全一致 |
| 資源消耗 | ✅ 低 | ⚖️ 中等 |

---

## 🎯 **建議使用場景**

### 📝 **開發階段** - 使用本機運行
```powershell
.\start_local.ps1
```
- 快速迭代
- 即時除錯
- 前端熱重載

### 🧪 **測試階段** - 使用 Docker
```powershell
.\start_docker.ps1
# 選擇 1: 測試模式
```
- 環境一致性測試
- 容器化驗證

### 🚀 **部署階段** - 使用 Docker
```powershell
docker compose up -d --build
```
- 生產環境部署
- 服務編排

---

## ⚡ **快速決策指南**

**如果你是：**
- **第一次使用** → 選擇本機運行（`.\start_local.ps1`）
- **前端開發者** → 選擇本機運行（支援熱重載）
- **後端開發者** → 任一方式都可以
- **部署運維** → 選擇 Docker（`.\start_docker.ps1`）
- **團隊協作** → 選擇 Docker（環境一致）

---

## 🔄 **切換方式**

你隨時可以在兩種方式間切換：

**從本機切換到 Docker：**
```powershell
# 停止本機服務（Ctrl+C）
.\start_docker.ps1
```

**從 Docker 切換到本機：**
```powershell
.\start_docker.ps1  # 選擇 4: 停止容器
.\start_local.ps1   # 啟動本機版本
```

---

## 🆘 **遇到問題？**

1. **本機運行問題** → 檢查 `LOCAL_DEVELOPMENT.md`
2. **Docker 問題** → 確保 Docker Desktop 已啟動
3. **環境問題** → 運行 `.\check_environment.ps1`

選擇最適合你當前需求的方式開始吧！🎉
