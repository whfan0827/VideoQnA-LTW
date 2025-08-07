#!/usr/bin/env python3
"""
Simple script to check the contents of the settings database
"""
import sqlite3
import os

def check_database():
    db_path = "settings.db"
    
    print(f"Checking database: {os.path.abspath(db_path)}")
    print(f"Database exists: {os.path.exists(db_path)}")
    
    if not os.path.exists(db_path):
        print("Database file not found!")
        return
    
    try:
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row  # Enable dict-like access
            cursor = conn.cursor()
            
            # Check if table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            print(f"\nTables in database: {[table[0] for table in tables]}")
            
            # Check library_settings table
            cursor.execute("SELECT * FROM library_settings;")
            rows = cursor.fetchall()
            
            print(f"\nNumber of library settings records: {len(rows)}")
            
            if rows:
                print("\nStored library settings:")
                print("-" * 80)
                for row in rows:
                    print(f"ID: {row['id']}")
                    print(f"Library: {row['library_name']}")
                    print(f"Temperature: {row['temperature']}")
                    print(f"Max Tokens: {row['max_tokens']}")
                    print(f"Semantic Ranker: {row['semantic_ranker']}")
                    print(f"Created: {row['created_at']}")
                    print(f"Updated: {row['updated_at']}")
                    print(f"Prompt Template: {row['prompt_template'][:100]}..." if row['prompt_template'] else "None")
                    print("-" * 80)
            else:
                print("No library settings found in database")
                
            # Check AI templates table
            try:
                cursor.execute("SELECT * FROM ai_templates;")
                template_rows = cursor.fetchall()
                
                print(f"\nNumber of AI template records: {len(template_rows)}")
                
                if template_rows:
                    print("\nStored AI templates:")
                    print("-" * 80)
                    for row in template_rows:
                        print(f"ID: {row['id']}")
                        print(f"Template Name: {row['template_name']}")
                        print(f"Display Name: {row['display_name']}")
                        print(f"Category: {row['category']}")
                        print(f"Temperature: {row['temperature']}")
                        print(f"Max Tokens: {row['max_tokens']}")
                        print(f"System Default: {row['is_system_default']}")
                        print(f"Created By: {row['created_by']}")
                        print(f"Prompt Template: {row['prompt_template'][:100]}..." if row['prompt_template'] else "None")
                        print("-" * 80)
                else:
                    print("No AI templates found in database")
            except Exception as e:
                print(f"AI templates table not found: {e}")
                
    except Exception as e:
        print(f"Error checking database: {e}")

if __name__ == "__main__":
    check_database()
