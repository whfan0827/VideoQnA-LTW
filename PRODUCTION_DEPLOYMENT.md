# Production Deployment Guide

本文檔說明如何將 VideoQnA-LTW 部署到生產環境。

## 🚀 快速部署

### 方法 1: Docker Compose (推薦)

```bash
# 1. 複製環境變數範本
cp .env.production.template .env.production

# 2. 編輯環境變數
nano .env.production  # 填入你的 Azure 服務配置

# 3. 建構並啟動服務
docker-compose -f docker-compose.prod.yml --env-file .env.production up -d

# 4. (可選) 啟動 Nginx 反向代理
docker-compose -f docker-compose.prod.yml --profile with-nginx --env-file .env.production up -d
```

### 方法 2: Azure Container Apps

```bash
# 使用 Azure Developer CLI
azd up
```

## 📋 環境準備

### 必要條件

1. **Azure 服務**:
   - Azure OpenAI Service
   - Azure AI Search
   - Azure Video Indexer
   - Azure App Registration (Service Principal)

2. **系統需求**:
   - Docker & Docker Compose
   - 至少 2GB RAM
   - 10GB 可用磁碟空間

### 環境變數配置

複製 `.env.production.template` 為 `.env.production` 並填入以下資訊:

```bash
# 必填項目
AZURE_OPENAI_SERVICE=your_service_name
AZURE_OPENAI_API_KEY=your_api_key
AZURE_SEARCH_SERVICE=your_search_service
AZURE_SEARCH_KEY=your_search_key
AZURE_CLIENT_ID=your_client_id
AZURE_CLIENT_SECRET=your_client_secret

# 其他重要設定
FLASK_ENV=production
LOG_LEVEL=info
```

## 🔧 部署選項

### 選項 1: 基本部署

最小化部署，只包含主應用:

```bash
docker-compose -f docker-compose.prod.yml up -d videoqna-app redis
```

### 選項 2: 完整部署

包含 Nginx 反向代理和 SSL:

```bash
docker-compose -f docker-compose.prod.yml --profile with-nginx up -d
```

### 選項 3: Azure 雲端部署

```bash
# 首次部署
azd init
azd up

# 更新部署
azd deploy
```

## 🔒 安全性配置

### SSL/TLS 設定

1. **購買 SSL 憑證** 或使用 Let's Encrypt
2. **放置憑證檔案** 到 `./ssl/` 目錄
3. **配置 Nginx** (詳見 nginx.conf 範例)

### 防火牆設定

開放必要端口:
- `80` (HTTP)
- `443` (HTTPS)
- `5000` (應用程式，僅內部存取)

### 安全標頭

生產環境自動啟用:
- HTTPS 強制跳轉
- Content Security Policy
- X-Frame-Options
- X-Content-Type-Options

## 📊 監控與日誌

### 健康檢查

```bash
# 檢查應用程式狀態
curl http://localhost:5000/indexes

# 檢查 Docker 容器狀態
docker-compose -f docker-compose.prod.yml ps
```

### 日誌查看

```bash
# 應用程式日誌
docker-compose -f docker-compose.prod.yml logs -f videoqna-app

# 系統日誌 (在容器內)
docker exec -it videoqna-app tail -f logs/app_$(date +%Y%m%d).log
```

### 效能監控

可選的監控服務整合:
- Sentry (錯誤追蹤)
- New Relic (效能監控)
- Azure Application Insights

## 🔄 維護與更新

### 更新應用程式

```bash
# 停止服務
docker-compose -f docker-compose.prod.yml down

# 重新建構映像
docker-compose -f docker-compose.prod.yml build --no-cache

# 啟動服務
docker-compose -f docker-compose.prod.yml up -d
```

### 資料備份

```bash
# 備份資料庫
docker run --rm -v videoqna-ltw_app_data:/data -v $(pwd):/backup alpine tar czf /backup/app_data_$(date +%Y%m%d).tar.gz -C /data .

# 備份 Redis
docker exec videoqna-ltw_redis_1 redis-cli BGSAVE
```

### 日誌輪替

建議設定 logrotate:

```bash
# /etc/logrotate.d/videoqna
/var/lib/docker/volumes/videoqna-ltw_app_logs/_data/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 root root
}
```

## 🚨 故障排除

### 常見問題

1. **應用程式無法啟動**
   ```bash
   # 檢查環境變數
   docker-compose -f docker-compose.prod.yml config
   
   # 檢查日誌
   docker-compose -f docker-compose.prod.yml logs videoqna-app
   ```

2. **Azure 服務連接失敗**
   - 確認 API keys 正確
   - 檢查網路連接
   - 驗證 Service Principal 權限

3. **效能問題**
   - 調整 Gunicorn worker 數量
   - 增加記憶體限制
   - 檢查資料庫索引

### 緊急復原

```bash
# 快速回滾到上一版本
docker-compose -f docker-compose.prod.yml down
docker image ls | grep videoqna  # 找到上一版本
docker tag previous_image_id videoqna-app:latest
docker-compose -f docker-compose.prod.yml up -d
```

## 📈 效能優化

### 建議配置

- **CPU**: 2+ cores
- **RAM**: 4GB+
- **Storage**: SSD preferred
- **Network**: 100Mbps+

### Gunicorn 調優

在 `.env.production` 中設定:

```bash
GUNICORN_WORKERS=4  # 2 * CPU cores
GUNICORN_TIMEOUT=60  # 根據處理時間調整
```

### Redis 優化

```bash
# 在 docker-compose.prod.yml 中調整
command: redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru
```

## 📞 支援

如有問題，請檢查:
1. 應用程式日誌
2. Docker 容器狀態
3. Azure 服務狀態
4. 網路連接

更多技術支援請參考項目文檔或提交 Issue。