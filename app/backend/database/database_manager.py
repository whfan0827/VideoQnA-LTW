"""
Unified Database Management System for VideoQnA Application

This module provides centralized database connections and management
for all database operations in the application.
"""

import sqlite3
import logging
from pathlib import Path
from typing import Any, Dict, Optional, ContextManager
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class DatabaseConfig:
    """Database configuration constants"""
    
    # Database paths
    BACKEND_DIR = Path(__file__).parent.parent
    SETTINGS_DB = BACKEND_DIR / "settings.db"
    APP_DATA_DB = BACKEND_DIR / "app_data.db"
    
    # Schema files
    SETTINGS_SCHEMA = Path(__file__).parent / "schema.sql"
    AI_TEMPLATES_SCHEMA = Path(__file__).parent / "ai_templates_schema.sql"

class DatabaseManager:
    """Unified database manager for all database operations"""
    
    def __init__(self):
        self.config = DatabaseConfig()
        self._ensure_databases_exist()
    
    def _ensure_databases_exist(self):
        """Ensure all required databases exist with proper schemas"""
        try:
            # Initialize settings database
            self._init_settings_db()
            # Initialize app data database  
            self._init_app_data_db()
            logger.info("All databases initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize databases: {e}")
            raise
    
    def _init_settings_db(self):
        """Initialize settings database"""
        if not self.config.SETTINGS_SCHEMA.exists():
            logger.warning(f"Settings schema not found: {self.config.SETTINGS_SCHEMA}")
            self._create_default_settings_schema()
        else:
            with open(self.config.SETTINGS_SCHEMA, 'r', encoding='utf-8') as f:
                schema = f.read()
            
            with sqlite3.connect(self.config.SETTINGS_DB) as conn:
                conn.executescript(schema)
                conn.commit()
        
        # Initialize AI templates schema if exists
        if self.config.AI_TEMPLATES_SCHEMA.exists():
            with open(self.config.AI_TEMPLATES_SCHEMA, 'r', encoding='utf-8') as f:
                ai_schema = f.read()
            
            with sqlite3.connect(self.config.SETTINGS_DB) as conn:
                conn.executescript(ai_schema)
                conn.commit()
    
    def _create_default_settings_schema(self):
        """Create default settings schema if file doesn't exist"""
        schema = """
        CREATE TABLE IF NOT EXISTS library_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            library_name TEXT UNIQUE NOT NULL,
            prompt_template TEXT,
            temperature REAL DEFAULT 0.7,
            max_tokens INTEGER DEFAULT 800,
            semantic_ranker BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS ai_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            template_name TEXT UNIQUE NOT NULL,
            display_name TEXT NOT NULL,
            description TEXT,
            category TEXT NOT NULL,
            prompt_template TEXT NOT NULL,
            temperature REAL DEFAULT 0.7,
            max_tokens INTEGER DEFAULT 800,
            semantic_ranker BOOLEAN DEFAULT 1,
            is_system_default BOOLEAN DEFAULT 0,
            created_by TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        with sqlite3.connect(self.config.SETTINGS_DB) as conn:
            conn.executescript(schema)
            conn.commit()
    
    def _init_app_data_db(self):
        """Initialize application data database"""
        schema = """
        CREATE TABLE IF NOT EXISTS tasks (
            task_id TEXT PRIMARY KEY,
            task_type TEXT NOT NULL,
            status TEXT NOT NULL,
            progress INTEGER DEFAULT 0,
            current_step TEXT,
            filename TEXT,
            library_name TEXT,
            file_path TEXT,
            created_at TEXT,
            started_at TEXT,
            completed_at TEXT,
            error_message TEXT,
            metadata TEXT
        );
        
        CREATE TABLE IF NOT EXISTS video_index (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            original_path TEXT,
            library_name TEXT NOT NULL,
            video_id TEXT,
            status TEXT DEFAULT 'indexed',
            file_size INTEGER,
            duration TEXT,
            created_at TEXT,
            indexed_at TEXT,
            metadata TEXT
        );
        
        CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
        CREATE INDEX IF NOT EXISTS idx_tasks_type ON tasks(task_type);
        CREATE INDEX IF NOT EXISTS idx_video_library ON video_index(library_name);
        CREATE INDEX IF NOT EXISTS idx_video_status ON video_index(status);
        """
        
        with sqlite3.connect(self.config.APP_DATA_DB) as conn:
            conn.executescript(schema)
            conn.commit()
    
    @contextmanager
    def get_settings_connection(self):
        """Get connection to settings database"""
        conn = sqlite3.connect(self.config.SETTINGS_DB)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    @contextmanager
    def get_app_data_connection(self):
        """Get connection to app data database"""
        conn = sqlite3.connect(self.config.APP_DATA_DB)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

# Global database manager instance
db_manager = DatabaseManager()

# Backwards compatibility functions
def get_connection():
    """Get settings database connection (backwards compatibility)"""
    return sqlite3.connect(db_manager.config.SETTINGS_DB)

def get_db_path():
    """Get settings database path (backwards compatibility)"""
    return db_manager.config.SETTINGS_DB

def init_database():
    """Initialize database (backwards compatibility)"""
    db_manager._ensure_databases_exist()
