#!/bin/bash
# 開發環境啟動腳本

echo "=== VideoQnA 開發環境啟動 ==="

echo "1. 啟動後端服務器 (Flask - Port 5000)..."
cd app/backend
python app.py &
BACKEND_PID=$!

echo "2. 等待後端啟動..."
sleep 3

echo "3. 啟動前端開發服務器 (Vite - Port 5173)..."
cd ../frontend
npm run dev &
FRONTEND_PID=$!

echo "=== 服務啟動完成 ==="
echo "前端: http://localhost:5173"
echo "後端: http://localhost:5000"
echo "按 Ctrl+C 停止所有服務"

# 等待中斷信號
trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait
