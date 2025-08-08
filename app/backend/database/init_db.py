"""
Legacy database initialization module
This module is kept for backwards compatibility.
New code should use database_manager.py
"""

import sqlite3
import os
from pathlib import Path
from .database_manager import db_manager

def get_db_path():
    """Get the path to the SQLite database file"""
    return db_manager.config.SETTINGS_DB

def init_database():
    """Initialize the SQLite database with schema"""
    db_manager._ensure_databases_exist()
    print(f"Database initialized at: {get_db_path()}")

def get_connection():
    """Get a database connection"""
    conn = sqlite3.connect(db_manager.config.SETTINGS_DB)
    conn.row_factory = sqlite3.Row  # Enable dict-like access to rows
    return conn

if __name__ == "__main__":
    init_database()
