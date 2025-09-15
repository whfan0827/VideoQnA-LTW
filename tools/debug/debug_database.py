#!/usr/bin/env python3
"""
Debug database settings - Check why settings override index
"""
import sys
from pathlib import Path
import sqlite3

# Add backend to path
backend_path = Path(__file__).parent / "app" / "backend"
sys.path.insert(0, str(backend_path))

from database.init_db import get_connection
from services.settings_service import SettingsService

def debug_settings_override():
    """Debug settings override issue"""
    
    print("=== Checking library settings in database ===")
    
    # Query database directly
    try:
        with get_connection() as conn:
            cursor = conn.execute("""
                SELECT library_name, prompt_template, temperature, max_tokens, semantic_ranker 
                FROM library_settings 
                ORDER BY library_name
            """)
            rows = cursor.fetchall()
            
            print(f"Found {len(rows)} library settings in database:")
            for row in rows:
                print(f"  Library: {row['library_name']}")
                if row['prompt_template']:
                    print(f"    prompt_template: {row['prompt_template'][:100]}...")
                print(f"    temperature: {row['temperature']}")
                print(f"    max_tokens: {row['max_tokens']}")
                print(f"    semantic_ranker: {row['semantic_ranker']}")
                print()
                
    except Exception as e:
        print(f"Database query error: {e}")
    
    print("\n=== Testing SettingsService ===")
    
    settings_service = SettingsService()
    
    # Test possible library names
    test_libraries = [
        "machine-instruction-index",
        "vi-machine-instruction-index", 
        "vi-asiadigital-talkshow-index",
        "default"
    ]
    
    for lib_name in test_libraries:
        print(f"\nTesting library: '{lib_name}'")
        try:
            settings = settings_service.get_settings(lib_name)
            print(f"  Got settings: {settings}")
            
            # Check if contains index field
            if 'index' in settings:
                print(f"  ❌ PROBLEM FOUND! Settings contain index: {settings['index']}")
            else:
                print(f"  ✅ Settings don't contain index field")
                
        except Exception as e:
            print(f"  Error: {e}")

if __name__ == "__main__":
    debug_settings_override()