#!/usr/bin/env python3
"""
檢查所有本地存儲中的machine instructions相關數據
"""
import sys
from pathlib import Path
import json

backend_path = Path(__file__).parent / "app" / "backend"
sys.path.insert(0, str(backend_path))

from database.init_db import get_connection

def check_all_storage():
    """檢查所有可能存儲machine instructions數據的地方"""
    
    print("=== Checking All Local Storage ===\n")
    
    # 1. SQLite 數據庫檢查
    print("1. SQLite Database Check:")
    try:
        with get_connection() as conn:
            # 檢查 library_settings 表
            cursor = conn.execute("SELECT library_name FROM library_settings WHERE library_name LIKE '%machine%'")
            machine_settings = cursor.fetchall()
            if machine_settings:
                print("   [X] Found machine-related library_settings:")
                for row in machine_settings:
                    print(f"      - {row[0]}")
            else:
                print("   [OK] No machine-related library_settings found")
            
            # 檢查其他可能的表
            tables = ['tasks', 'videos', 'ai_templates']
            for table in tables:
                try:
                    cursor = conn.execute(f"SELECT COUNT(*) FROM {table} WHERE library_name LIKE '%machine%' OR video_id LIKE '%machine%' OR name LIKE '%machine%'")
                    count = cursor.fetchone()[0]
                    if count > 0:
                        print(f"   [X] Found {count} machine-related records in {table}")
                        # 顯示具體記錄
                        cursor = conn.execute(f"SELECT * FROM {table} WHERE library_name LIKE '%machine%' OR video_id LIKE '%machine%' OR name LIKE '%machine%'")
                        records = cursor.fetchall()
                        for record in records[:3]:  # 只顯示前3個
                            print(f"      - {dict(record)}")
                    else:
                        print(f"   [OK] No machine-related records in {table}")
                except Exception as e:
                    print(f"   [WARNING] Could not check {table}: {e}")
                    
    except Exception as e:
        print(f"   [X] Database error: {e}")
    
    # 2. 檢查文件緩存
    print("\n2. File Cache Check:")
    cache_files = [
        backend_path / "data" / "file_hash_cache.json",
        backend_path / "data" / "app_data.db",
        backend_path / "data" / "ai_templates.db"
    ]
    
    for cache_file in cache_files:
        if cache_file.exists():
            print(f"   Checking {cache_file.name}:")
            if cache_file.suffix == '.json':
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    machine_entries = []
                    for key, value in data.items():
                        if 'machine' in key.lower() or (isinstance(value, dict) and any('machine' in str(v).lower() for v in value.values())):
                            machine_entries.append((key, value))
                    
                    if machine_entries:
                        print(f"      [X] Found {len(machine_entries)} machine-related entries:")
                        for key, value in machine_entries[:3]:
                            print(f"         - {key}: {str(value)[:100]}...")
                    else:
                        print(f"      [OK] No machine-related entries in {cache_file.name}")
                        
                except Exception as e:
                    print(f"      [WARNING] Could not read {cache_file.name}: {e}")
            else:
                print(f"      [OK] {cache_file.name} is not a JSON file")
        else:
            print(f"   [OK] {cache_file.name} does not exist")
    
    # 3. 檢查日誌文件
    print("\n3. Log Files Check:")
    log_dir = backend_path / "logs"
    if log_dir.exists():
        log_files = list(log_dir.glob("*.log"))
        for log_file in log_files[-2:]:  # 只檢查最近2個日誌文件
            print(f"   Checking {log_file.name}:")
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'machine' in content.lower():
                        lines = content.split('\n')
                        machine_lines = [line for line in lines if 'machine' in line.lower()]
                        print(f"      [X] Found {len(machine_lines)} machine-related log entries (recent 3):")
                        for line in machine_lines[-3:]:
                            print(f"         - {line.strip()}")
                    else:
                        print(f"      [OK] No machine-related entries in {log_file.name}")
            except Exception as e:
                print(f"      [WARNING] Could not read {log_file.name}: {e}")
    else:
        print("   [OK] No logs directory found")
    
    # 4. 建議清理操作
    print("\n4. Cleanup Recommendations:")
    print("   To clean up any remaining machine-related data:")
    print("   - Run: python cleanup_inconsistent_libraries.py")
    print("   - Clear browser localStorage (F12 -> Application -> Local Storage -> Clear)")
    print("   - Restart the backend server")

if __name__ == "__main__":
    check_all_storage()