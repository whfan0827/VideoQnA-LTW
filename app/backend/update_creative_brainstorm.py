#!/usr/bin/env python3
"""
Script to update the creative-brainstorm template temperature in the existing database
"""
import sqlite3
import os

def update_creative_brainstorm_temperature():
    """Update the creative-brainstorm template temperature from 1.2 to 0.9"""
    db_path = os.path.join(os.path.dirname(__file__), 'ai_templates.db')
    
    if not os.path.exists(db_path):
        print(f"Database not found at: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check current temperature value
        cursor.execute("SELECT temperature FROM ai_templates WHERE template_name = ?", ('creative-brainstorm',))
        result = cursor.fetchone()
        
        if result:
            current_temp = result[0]
            print(f"Current temperature for creative-brainstorm: {current_temp}")
            
            if current_temp != 0.9:
                # Update the temperature to 0.9
                cursor.execute(
                    "UPDATE ai_templates SET temperature = ? WHERE template_name = ?", 
                    (0.9, 'creative-brainstorm')
                )
                conn.commit()
                print("Updated creative-brainstorm temperature to 0.9")
            else:
                print("Temperature is already 0.9 - no update needed")
        else:
            print("creative-brainstorm template not found in database")
            
        # Verify the update
        cursor.execute("SELECT template_name, temperature, max_tokens FROM ai_templates WHERE template_name = ?", ('creative-brainstorm',))
        result = cursor.fetchone()
        if result:
            print(f"Verification - {result[0]}: temperature={result[1]}, max_tokens={result[2]}")
            
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error updating database: {e}")
        return False

if __name__ == "__main__":
    success = update_creative_brainstorm_temperature()
    if success:
        print("Database update completed successfully!")
    else:
        print("Database update failed!")
