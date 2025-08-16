參考以下連結
https://github.com/Azure/azure-sdk-for-python/blob/main/sdk/storage/azure-storage-blob/README.md

我想要前端可以上傳大於30GB的檔案，以下可行嗎?: 

第一種情境:
前端（React）請求後端 API 要上傳權限。
後端（Flask）用 Python Azure Storage SDK 產生短時效 SAS URL。
前端用這個 URL 直接 PUT 檔案到 Blob Storage。
上傳完成後，前端把 Blob URL 回報給後端，後端存進資料庫並進行後續影片處理（Video Indexer、ChromaDB 索引）。
第二種情境: 直接貼SAS URL ，檔案會給azure video indexer 處理