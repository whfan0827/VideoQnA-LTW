#!/usr/bin/env python3
"""
驗證 Azure OpenAI 環境變數設定腳本
確認所有必要的環境變數都已正確設定
"""
import os
import sys
from pathlib import Path

# Add backend path to Python path
backend_path = Path(__file__).parent / "app" / "backend"
sys.path.insert(0, str(backend_path))

from vi_search.utils.azure_utils import get_azd_env_values

def verify_azure_openai_config():
    """驗證 Azure OpenAI 設定"""
    print("🔍 驗證 Azure OpenAI 環境變數設定...")
    print("=" * 50)
    
    # 從環境變數讀取設定
    env_values = get_azd_env_values()
    
    required_keys = [
        'AZURE_OPENAI_SERVICE',
        'AZURE_OPENAI_API_KEY', 
        'AZURE_OPENAI_CHATGPT_DEPLOYMENT',
        'AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT'
    ]
    
    print("📋 必要環境變數檢查:")
    all_set = True
    
    for key in required_keys:
        value = env_values.get(key)
        if value:
            # 遮掩 API Key 顯示
            if 'API_KEY' in key:
                display_value = f"{value[:8]}***{value[-4:]}" if len(value) > 12 else "***"
            else:
                display_value = value
            print(f"  ✅ {key}: {display_value}")
        else:
            print(f"  ❌ {key}: 未設定")
            all_set = False
    
    print()
    if all_set:
        print("✅ 所有必要的 Azure OpenAI 環境變數都已正確設定！")
        print("\n📝 當前設定:")
        print(f"   服務名稱: {env_values['AZURE_OPENAI_SERVICE']}")
        print(f"   ChatGPT 部署: {env_values['AZURE_OPENAI_CHATGPT_DEPLOYMENT']}")
        print(f"   Embeddings 部署: {env_values['AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT']}")
        print(f"   服務端點: https://{env_values['AZURE_OPENAI_SERVICE']}.openai.azure.com/")
        return True
    else:
        print("❌ 部分環境變數未設定，請檢查 .env 檔案")
        return False

def verify_env_file():
    """驗證 .env 檔案存在並包含必要設定"""
    env_file = Path("app/backend/.env")
    
    if not env_file.exists():
        print("⚠️ .env 檔案不存在於 app/backend/.env")
        return False
    
    print(f"📁 找到 .env 檔案: {env_file.absolute()}")
    
    with open(env_file, 'r', encoding='utf-8') as f:
        content = f.read()
        
    required_vars = [
        'AZURE_OPENAI_SERVICE=',
        'AZURE_OPENAI_API_KEY=',
        'AZURE_OPENAI_CHATGPT_DEPLOYMENT=',
        'AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT='
    ]
    
    missing_vars = []
    for var in required_vars:
        if var not in content:
            missing_vars.append(var.rstrip('='))
    
    if missing_vars:
        print(f"⚠️ .env 檔案缺少以下變數: {', '.join(missing_vars)}")
        return False
    
    print("✅ .env 檔案包含所有必要變數")
    return True

if __name__ == "__main__":
    print("🚀 VideoQnA-LTW 環境變數驗證工具")
    print("=" * 50)
    
    # 驗證 .env 檔案
    env_file_ok = verify_env_file()
    print()
    
    # 驗證環境變數設定
    config_ok = verify_azure_openai_config()
    
    print("\n" + "=" * 50)
    if env_file_ok and config_ok:
        print("🎉 環境設定驗證通過！可以開始使用應用程式。")
        sys.exit(0)
    else:
        print("❌ 環境設定驗證失敗，請修正後再試。")
        sys.exit(1)