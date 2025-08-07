import sqlite3
import os

DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'library.db')

def check_database_structure():
    """Check the current database structure"""
    if not os.path.exists(DATABASE_PATH):
        print(f"Database not found at: {DATABASE_PATH}")
        return
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print("Database Tables:")
        print("-" * 30)
        for table in tables:
            table_name = table[0]
            print(f"Table: {table_name}")
            
            # Get table structure
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            print("  Columns:")
            for col in columns:
                print(f"    {col[1]} ({col[2]})")
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"  Row count: {count}")
            
            # Show some sample data
            if count > 0:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
                rows = cursor.fetchall()
                print("  Sample data:")
                for i, row in enumerate(rows, 1):
                    print(f"    Row {i}: {row}")
            
            print()
        
    except Exception as e:
        print(f"Error checking database: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_database_structure()
