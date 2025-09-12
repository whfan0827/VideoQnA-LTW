#!/usr/bin/env python3
"""
調試搜索問題 - 查看vi-asiadigital-talkshow-index中到底有什麼內容
"""
import os
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "app" / "backend"
sys.path.insert(0, str(backend_path))

from dotenv import load_dotenv
load_dotenv(backend_path / ".env")

def debug_search_issue():
    """調試搜索問題的主函數"""
    
    # 初始化組件
    print("=== 初始化組件 ===")
    
    search_db = os.environ.get("PROMPT_CONTENT_DB", "azure_search")
    print(f"使用數據庫: {search_db}")
    
    if search_db == "azure_search":
        from vi_search.prompt_content_db.azure_search import AzureVectorSearch
        prompt_content_db = AzureVectorSearch()
    else:
        print(f"不支持的數據庫類型: {search_db}")
        return
    
    # 初始化語言模型
    lang_model = os.environ.get("LANGUAGE_MODEL", "openai")
    print(f"使用語言模型: {lang_model}")
    
    if lang_model == "openai":
        from vi_search.language_models.azure_openai import OpenAI
        language_models = OpenAI()
    else:
        print(f"不支持的語言模型: {lang_model}")
        return
    
    # 檢查數據庫
    print("\n=== 檢查數據庫 ===")
    available_dbs = prompt_content_db.get_available_dbs()
    print(f"可用數據庫: {available_dbs}")
    
    target_db = "vi-asiadigital-talkshow-index"
    if target_db not in available_dbs:
        print(f"❌ 目標數據庫 '{target_db}' 不存在!")
        return
    
    print(f"✅ 目標數據庫 '{target_db}' 存在")
    
    # 切換到目標數據庫
    prompt_content_db.set_db(target_db)
    print(f"已切換到數據庫: {prompt_content_db.db_name}")
    
    # 測試搜索
    print("\n=== 測試搜索 ===")
    test_queries = [
        "machine instruction index",
        "機器指令索引", 
        "hello",
        "什麼是",
        "how to"
    ]
    
    for query in test_queries:
        print(f"\n查詢: '{query}'")
        try:
            # 生成embeddings
            embeddings_vector = language_models.get_text_embeddings(query)
            print(f"  Embeddings向量維度: {len(embeddings_vector)}")
            
            # 執行搜索
            docs_by_id, results_content = prompt_content_db.vector_search(embeddings_vector, n_results=5)
            print(f"  搜索結果數量: {len(results_content)}")
            
            # 顯示結果內容
            for i, result in enumerate(results_content[:3]):  # 只顯示前3個
                print(f"  結果 {i+1}: {result[:200]}{'...' if len(result) > 200 else ''}")
            
            if not results_content:
                print("  ❌ 沒有搜索結果!")
            
        except Exception as e:
            print(f"  ❌ 搜索出錯: {e}")
    
    # 檢查數據庫統計信息
    print("\n=== 數據庫統計 ===")
    try:
        # 嘗試獲取數據庫的一些統計信息
        search_client = prompt_content_db.db_handle
        if search_client:
            # 執行一個空搜索來獲取總數
            empty_results = list(search_client.search(search_text="*", top=1))
            print(f"數據庫中大約有文檔: {len(empty_results)} (這只是一個粗略估計)")
            
            if empty_results:
                doc = empty_results[0]
                print(f"樣本文檔字段: {list(doc.keys())}")
                print(f"樣本內容預覽: {str(doc.get('content', 'N/A'))[:200]}...")
        
    except Exception as e:
        print(f"無法獲取數據庫統計: {e}")

if __name__ == "__main__":
    debug_search_issue()