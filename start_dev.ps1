# Windows PowerShell 開發環境啟動腳本

Write-Host "=== VideoQnA 開發環境啟動 ===" -ForegroundColor Green

Write-Host "1. 啟動後端服務器 (Flask - Port 5000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd 'app\backend'; python app.py"

Write-Host "2. 等待後端啟動..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

Write-Host "3. 啟動前端開發服務器 (Vite - Port 5173)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd 'app\frontend'; npm run dev"

Write-Host "=== 服務啟動完成 ===" -ForegroundColor Green
Write-Host "前端: http://localhost:5173" -ForegroundColor Cyan
Write-Host "後端: http://localhost:5000" -ForegroundColor Cyan
Write-Host "請在瀏覽器中開啟前端網址 (5173) 進行開發" -ForegroundColor Yellow
