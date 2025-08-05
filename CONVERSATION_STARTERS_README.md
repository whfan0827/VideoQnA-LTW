# Conversation Starters 功能使用說明

## 功能概述
這個功能允許在 Developer Settings 頁面中編輯聊天頁面顯示的範例問題（Conversation Starters）。

## 功能特色
- 在 Developer Settings 頁面中提供三個輸入欄位
- 支援本地存儲（localStorage）
- 即時更新前端顯示
- 可重設為預設值
- 支援空值過濾

## 使用方法

### 1. 編輯 Conversation Starters
1. 進入應用程式的 Developer Settings 頁面
2. 找到 "Conversation Starters" 區塊
3. 在三個文字輸入欄位中輸入您想要的問題：
   - Starter 1: 第一個範例問題
   - Starter 2: 第二個範例問題
   - Starter 3: 第三個範例問題
4. 點擊 "Save Conversation Starters" 按鈕保存

### 2. 重設為預設值
- 點擊 "Reset to Defaults" 按鈕
- 確認重設操作
- 系統會恢復為預設的三個範例問題

### 3. 查看變更
- 保存後，前端聊天頁面的範例問題會立即更新
- 無需重新整理頁面

## 技術實現

### 資料存儲
- 使用瀏覽器的 localStorage 存儲自定義設定
- 資料格式：JSON 陣列，包含 text 和 value 屬性
- 儲存鍵名：`conversation_starters`

### 資料結構
```json
[
  {
    "text": "範例問題文字",
    "value": "範例問題值"
  }
]
```

### 元件通訊
- 使用自定義事件 `conversation_starters_updated` 進行元件間通訊
- DeveloperSettingsPanel 發送事件
- ExampleList 監聽事件並更新顯示

## 預設值
系統預設的三個範例問題：
1. "What insights are included with Azure AI Video Indexer?"
2. "What is OCR?"
3. "What is the distance to Mars?"

## 錯誤處理
- 如果 localStorage 資料損壞，系統會自動使用預設值
- 空白的輸入欄位會被自動過濾
- 提供使用者友善的錯誤訊息

## 測試工具
專案根目錄中的 `test_conversation_starters.html` 檔案提供了測試工具：
- 查看目前存儲的 conversation starters
- 設定測試資料
- 清除存儲的資料
- 觸發更新事件

## 檔案異動
### 修改的檔案
1. `app/frontend/src/components/DeveloperSettingsPanel/DeveloperSettingsPanel.tsx`
   - 新增 Conversation Starters 設定區塊
   - 新增相關狀態管理和處理函數
   - 移除 emoji 符號

2. `app/frontend/src/components/Example/ExampleList.tsx`
   - 新增動態載入功能
   - 支援 localStorage 讀取
   - 監聽自定義事件進行更新

### 新增的檔案
1. `test_conversation_starters.html` - 測試工具

## 未來擴展
- 支援更多數量的範例問題
- 新增匯出/匯入功能
- 支援 Azure Blob Storage 存儲
- 新增範例問題的分類管理
