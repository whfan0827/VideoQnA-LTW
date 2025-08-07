#!/usr/bin/env python3
"""
Script to update the creative-brainstorm template temperature in the library.db file
"""
import sqlite3
import os

def update_creative_brainstorm_in_library_db():
    """Update the creative-brainstorm template temperature from 1.0 to 0.9 in library.db"""
    db_path = os.path.join(os.path.dirname(__file__), 'library.db')
    
    if not os.path.exists(db_path):
        print(f"Database not found at: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check current temperature value
        cursor.execute("SELECT template_name, temperature, max_tokens FROM ai_templates WHERE template_name = ?", ('creative-brainstorm',))
        result = cursor.fetchone()
        
        if result:
            current_temp = result[1]
            print(f"Current values in library.db - creative-brainstorm: temperature={current_temp}, max_tokens={result[2]}")
            
            if current_temp != 0.9:
                # Update the temperature to 0.9
                cursor.execute(
                    "UPDATE ai_templates SET temperature = ? WHERE template_name = ?", 
                    (0.9, 'creative-brainstorm')
                )
                conn.commit()
                print("Updated creative-brainstorm temperature to 0.9 in library.db")
            else:
                print("Temperature is already 0.9 in library.db - no update needed")
        else:
            print("creative-brainstorm template not found in library.db")
            
        # Verify the update
        cursor.execute("SELECT template_name, temperature, max_tokens FROM ai_templates WHERE template_name = ?", ('creative-brainstorm',))
        result = cursor.fetchone()
        if result:
            print(f"Verification - {result[0]}: temperature={result[1]}, max_tokens={result[2]}")
            
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error updating library.db: {e}")
        return False

if __name__ == "__main__":
    success = update_creative_brainstorm_in_library_db()
    if success:
        print("library.db update completed successfully!")
    else:
        print("library.db update failed!")
