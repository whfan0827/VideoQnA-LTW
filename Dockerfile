# 使用 Python 3.10 官方映像
FROM python:3.10-slim

# 設置工作目錄
WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安裝 Node.js (用於構建前端)
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs

# 複製前端代碼並構建
COPY app/frontend/package*.json ./frontend/
WORKDIR /app/frontend
RUN npm install

COPY app/frontend/ ./
RUN npm run build

# 回到工作目錄並設置後端
WORKDIR /app
COPY app/backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 複製後端代碼
COPY app/backend/ ./

# 前端建置已直接輸出到 ../backend/static，無需額外複製

# 創建應用內的 data 目錄
RUN mkdir -p /app/data

# 設置環境變數
ENV PYTHONPATH=/app
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV DATA_DIR=/app/data

# 暴露端口
EXPOSE 5000

# 啟動應用
CMD ["python", "app.py"]
