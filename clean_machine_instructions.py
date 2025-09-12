#!/usr/bin/env python3
"""
清理所有machine instructions殘留數據
"""
import sys
import json
from pathlib import Path

backend_path = Path(__file__).parent / "app" / "backend"
sys.path.insert(0, str(backend_path))

from database.init_db import get_connection

def clean_all_machine_data():
    """清理所有machine instructions相關數據"""
    
    print("=== Cleaning All Machine Instructions Data ===\n")
    
    # 1. 清理SQLite數據庫
    print("1. Cleaning SQLite Database:")
    try:
        with get_connection() as conn:
            # 清理 library_settings
            cursor = conn.execute("DELETE FROM library_settings WHERE library_name LIKE '%machine%'")
            deleted_settings = cursor.rowcount
            conn.commit()
            print(f"   [OK] Deleted {deleted_settings} machine-related library_settings")
            
    except Exception as e:
        print(f"   [X] Database error: {e}")
    
    # 2. 清理文件緩存
    print("\n2. Cleaning File Cache:")
    
    # 清理 file_hash_cache.json
    cache_file = backend_path / "data" / "file_hash_cache.json"
    if cache_file.exists():
        try:
            # 讀取現有緩存
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # 找出machine相關條目
            machine_keys = []
            for key, value in cache_data.items():
                if isinstance(value, dict) and 'library_name' in value:
                    if 'machine' in value['library_name'].lower():
                        machine_keys.append(key)
            
            # 刪除machine相關條目
            for key in machine_keys:
                del cache_data[key]
            
            # 寫回清理後的數據
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
            
            print(f"   [OK] Cleaned {len(machine_keys)} machine entries from file_hash_cache.json")
            
        except Exception as e:
            print(f"   [X] Could not clean file_hash_cache.json: {e}")
    else:
        print("   [OK] file_hash_cache.json does not exist")
    
    # 3. 提醒清理瀏覽器localStorage
    print("\n3. Browser localStorage Cleanup:")
    print("   Please manually clear browser localStorage:")
    print("   - Open DevTools (F12)")
    print("   - Go to Application -> Local Storage")
    print("   - Delete keys containing 'machine' or 'target_library'")
    print("   - Or clear all localStorage: localStorage.clear()")
    
    # 4. 檢查清理結果
    print("\n4. Verification:")
    print("   After cleanup, please:")
    print("   - Restart your backend server")
    print("   - Refresh your browser")
    print("   - Check that machine instructions no longer appears in dropdown")
    
    print("\n[SUCCESS] Machine instructions data cleanup completed!")

if __name__ == "__main__":
    clean_all_machine_data()