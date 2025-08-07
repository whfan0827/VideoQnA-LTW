import sqlite3
import os
from pathlib import Path

def get_db_path():
    """Get the path to the SQLite database file"""
    backend_dir = Path(__file__).parent.parent
    return backend_dir / "settings.db"

def init_database():
    """Initialize the SQLite database with schema"""
    db_path = get_db_path()
    
    # Read schema from file
    schema_path = Path(__file__).parent / "schema.sql"
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema = f.read()
    
    # Create database and execute schema
    with sqlite3.connect(db_path) as conn:
        conn.executescript(schema)
        conn.commit()
        print(f"Database initialized at: {db_path}")

def get_connection():
    """Get a database connection"""
    db_path = get_db_path()
    
    # Initialize database if it doesn't exist
    if not db_path.exists():
        init_database()
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Enable dict-like access to rows
    return conn

if __name__ == "__main__":
    init_database()
