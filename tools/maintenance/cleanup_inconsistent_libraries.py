#!/usr/bin/env python3
"""
清理不一致的library設定
"""
import sys
from pathlib import Path

backend_path = Path(__file__).parent / "app" / "backend"
sys.path.insert(0, str(backend_path))

from database.init_db import get_connection

def cleanup_inconsistent_libraries():
    """清理database中不一致的library設定"""
    
    print("=== Library Settings Cleanup ===")
    
    # 查看所有設定
    with get_connection() as conn:
        cursor = conn.execute("SELECT library_name FROM library_settings")
        settings_libs = [row[0] for row in cursor.fetchall()]
    
    print(f"Found settings for these libraries: {settings_libs}")
    
    # 你可以選擇：
    print("\n1. Delete specific problematic libraries")
    print("2. Keep only specific libraries")  
    print("3. Show current settings and decide")
    
    choice = input("\nEnter choice (1/2/3): ").strip()
    
    if choice == "1":
        # 刪除特定的問題library
        problematic = [
            "test-lib",
            "vi-trumpnews-index"  # 如果你不需要這些
        ]
        
        for lib in problematic:
            if lib in settings_libs:
                print(f"Deleting settings for: {lib}")
                with get_connection() as conn:
                    conn.execute("DELETE FROM library_settings WHERE library_name = ?", (lib,))
                    conn.commit()
    
    elif choice == "2":
        # 只保留你需要的
        keep_only = [
            "vi-machine-instructions-index",  # 改成正確名稱
            "vi-asiadigital-talkshow-index"
        ]
        
        for lib in settings_libs:
            if lib not in keep_only:
                print(f"Deleting settings for: {lib}")
                with get_connection() as conn:
                    conn.execute("DELETE FROM library_settings WHERE library_name = ?", (lib,))
                    conn.commit()
    
    elif choice == "3":
        # 顯示詳細設定讓你決定
        with get_connection() as conn:
            cursor = conn.execute("""
                SELECT library_name, prompt_template, temperature, max_tokens 
                FROM library_settings 
                ORDER BY library_name
            """)
            
            for row in cursor.fetchall():
                print(f"\n--- {row[0]} ---")
                print(f"Temperature: {row[2]}")
                print(f"Max tokens: {row[3]}")
                print(f"Prompt preview: {row[1][:100]}...")
                
                delete = input(f"Delete this library settings? (y/N): ").strip().lower()
                if delete == 'y':
                    with get_connection() as conn2:
                        conn2.execute("DELETE FROM library_settings WHERE library_name = ?", (row[0],))
                        conn2.commit()
                    print(f"Deleted {row[0]}")
    
    print("\nCleanup completed!")

if __name__ == "__main__":
    cleanup_inconsistent_libraries()