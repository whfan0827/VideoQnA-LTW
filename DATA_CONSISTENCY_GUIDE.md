# 數據一致性管理指南

## 🚨 問題背景

之前系統存在**數據散布**問題，當你刪除一個library時，數據可能殘留在5個不同的地方：
- Azure Search Index (向量數據)
- SQLite Database (設定、記錄)
- File Hash Cache (緩存文件)
- Browser LocalStorage (用戶選擇)
- Frontend React State (UI狀態)

這導致**系統不穩定** - 明明刪除了，卻還顯示存在！

## ✅ 新的解決方案

我們實施了**統一數據管理系統**，包含：

### 1. **統一Library管理服務** (`LibraryManager`)
- 級聯刪除：一次操作清理所有相關數據
- 錯誤恢復：部分失敗時提供詳細報告
- 數據驗證：檢查所有組件的一致性

### 2. **自動監控系統** (`DataConsistencyMonitor`)
- 定期檢查數據一致性
- 自動發現不一致問題
- 支援自動修復功能

### 3. **前端同步機制** (`useLibrarySync`)
- 實時檢測數據狀態
- 自動清理無效選擇
- 跨標籤頁同步

## 🛠️ 使用方法

### **立即解決現有問題**

1. **檢查當前狀態**：
   ```bash
   GET /libraries/status
   ```

2. **自動清理不一致數據**：
   ```bash
   POST /libraries/cleanup-inconsistent
   ```

3. **或使用Python腳本**：
   ```bash
   python clean_machine_instructions.py
   ```

### **防止未來問題**

#### **1. 啟用自動監控**
```bash
POST /system/data-consistency/monitor
Content-Type: application/json

{
  "interval_minutes": 60
}
```

#### **2. 使用新的刪除API**
前端刪除library時，系統會自動：
- 刪除Azure Search Index
- 清理SQLite設定和記錄
- 清理文件緩存
- 提供詳細的清理報告

#### **3. 前端自動同步**
在React組件中使用：
```typescript
import { useLibrarySync } from '../hooks/useLibrarySync';

function MyComponent() {
  const { 
    syncStatus, 
    hasInconsistencies, 
    autoFixInconsistencies,
    isCurrentLibraryValid
  } = useLibrarySync();
  
  // 自動檢測並修復不一致
  if (hasInconsistencies) {
    autoFixInconsistencies();
  }
}
```

## 🔍 手動檢查和修復

### **檢查數據一致性**
```bash
# 查看所有library狀態
GET /libraries/status

# 強制執行一致性檢查  
POST /system/data-consistency/check
```

### **手動清理特定問題**
```bash
# 清理所有不一致的libraries
POST /libraries/cleanup-inconsistent

# 自動修復並重新檢查
POST /system/data-consistency/auto-fix
```

### **監控系統狀態**
```bash
# 查看監控狀態
GET /system/data-consistency/status

# 停止監控
DELETE /system/data-consistency/monitor
```

## 🚨 緊急處理步驟

如果系統出現數據不一致：

### **步驟1：立即診斷**
```bash
python check_local_storage.py
```

### **步驟2：自動清理**
```bash
python clean_machine_instructions.py
```

### **步驟3：重啟系統**
```bash
# 重啟後端
cd app\backend && python app.py

# 清理瀏覽器localStorage
# F12 -> Application -> Local Storage -> Clear All
```

### **步驟4：驗證修復**
- 檢查library列表是否正確
- 測試查詢功能
- 確認不再有殘留數據

## 📊 監控和維護

### **定期檢查項目**
- [ ] 每週檢查 `/libraries/status`
- [ ] 監控 `/system/data-consistency/status`  
- [ ] 查看後端日誌中的一致性警告
- [ ] 驗證前端library選擇功能

### **預防措施**
1. **始終使用新的刪除API** - 避免直接操作資料庫
2. **啟用自動監控** - 提早發現問題
3. **定期清理** - 每月執行一次 cleanup-inconsistent
4. **備份重要設定** - 防止意外刪除

## 🎯 最佳實踐

### **開發者**
- 修改library操作時，使用 `LibraryManager`
- 添加新存儲位置時，更新一致性檢查
- 測試時驗證所有組件的清理

### **用戶**
- 使用系統內建的刪除功能
- 定期檢查數據一致性狀態
- 發現問題立即使用自動修復

### **管理員**
- 啟用自動監控系統
- 定期查看系統健康報告  
- 設定告警通知機制

## 🔧 故障排除

### **常見問題**

**Q: 刪除library後仍然顯示？**
A: 執行 `POST /libraries/cleanup-inconsistent`

**Q: 前端選擇無法同步？**
A: 清空browser localStorage並重新整理

**Q: 監控系統無法啟動？**
A: 檢查後端日誌，確保沒有權限問題

**Q: 自動修復失敗？**
A: 查看 `cleanup_result.errors` 欄位的詳細錯誤信息

## 📞 支援

如果遇到問題：
1. 查看後端日誌 (`logs/app_YYYYMMDD.log`)
2. 執行診斷腳本 (`python check_local_storage.py`)
3. 使用自動修復功能
4. 重啟系統並清理緩存

**現在你的系統應該不會再出現數據殘留問題了！** 🎉