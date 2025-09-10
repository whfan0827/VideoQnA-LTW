"""
Unified Configuration Management for VideoQnA Application

This module provides centralized configuration management to eliminate
hardcoded values throughout the application.
"""

import os
from pathlib import Path
from typing import Optional


class AppConfig:
    """
    Centralized configuration class for the entire application.
    All configuration values should be accessed through this class.
    """
    
    # Task Management Configuration
    MAX_CONCURRENT_TASKS = int(os.getenv('MAX_CONCURRENT_TASKS', '1'))
    TASK_RETRY_MAX = int(os.getenv('TASK_RETRY_MAX', '2'))
    TASK_CLEANUP_DAYS = int(os.getenv('TASK_CLEANUP_DAYS', '7'))
    
    # File Processing Configuration
    FILE_HASH_CHUNK_SIZE = int(os.getenv('FILE_HASH_CHUNK_SIZE', '8192'))
    
    # Database Configuration
    @staticmethod
    def get_db_path(db_name: str) -> Path:
        """Get database file path"""
        backend_dir = Path(__file__).parent
        return backend_dir / f"{db_name}.db"
    
    # Retrieval Configuration
    DEFAULT_TOP_K = int(os.getenv('DEFAULT_TOP_K', '3'))
    DEFAULT_TEMPERATURE = float(os.getenv('DEFAULT_TEMPERATURE', '1.0'))
    DEFAULT_TOP_P = float(os.getenv('DEFAULT_TOP_P', '1.0'))
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
    
    # Cache Configuration
    CACHE_FILE_NAME = os.getenv('CACHE_FILE_NAME', 'file_hash_cache.json')
    
    # Network Configuration  
    REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', '30'))
    MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))
    
    @classmethod
    def validate(cls):
        """Validate configuration values"""
        if cls.MAX_CONCURRENT_TASKS < 1:
            raise ValueError("MAX_CONCURRENT_TASKS must be >= 1")
        
        if cls.FILE_HASH_CHUNK_SIZE < 1024:
            raise ValueError("FILE_HASH_CHUNK_SIZE must be >= 1024")
        
        if cls.DEFAULT_TOP_K < 1:
            raise ValueError("DEFAULT_TOP_K must be >= 1")


# Validate configuration on import
AppConfig.validate()