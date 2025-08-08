"""
Legacy Application Data Manager

This module is moved from the root backend directory for better organization.
It provides task and video management functionality.
"""

import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any
import json

logger = logging.getLogger(__name__)

class TaskDatabase:
    """Database manager for task-related operations"""
    
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            backend_dir = Path(__file__).parent.parent
            self.db_path = backend_dir / "app_data.db"
        else:
            self.db_path = Path(db_path)
        self._init_database()
    
    def _init_database(self):
        """Initialize database and create tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("PRAGMA foreign_keys = ON")
                
                # Create tasks table
                conn.execute("""
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
                    )
                """)
                
                conn.commit()
                logger.info("Task database initialized successfully")
                
        except Exception as e:
            logger.error(f"Failed to initialize task database: {e}")
            raise
    
    def save_task(self, task_data: Dict[str, Any]) -> bool:
        """Save or update task in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO tasks 
                    (task_id, task_type, status, progress, current_step, filename, 
                     library_name, file_path, created_at, started_at, completed_at, 
                     error_message, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    task_data.get('task_id'),
                    task_data.get('task_type'),
                    task_data.get('status'),
                    task_data.get('progress', 0),
                    task_data.get('current_step'),
                    task_data.get('filename'),
                    task_data.get('library_name'),
                    task_data.get('file_path'),
                    task_data.get('created_at'),
                    task_data.get('started_at'),
                    task_data.get('completed_at'),
                    task_data.get('error_message'),
                    json.dumps(task_data.get('metadata', {}))
                ))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to save task {task_data.get('task_id')}: {e}")
            return False

    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """Get all tasks from database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("SELECT * FROM tasks ORDER BY created_at DESC")
                
                tasks = []
                for row in cursor.fetchall():
                    task = dict(row)
                    # Parse metadata JSON
                    if task['metadata']:
                        try:
                            task['metadata'] = json.loads(task['metadata'])
                        except json.JSONDecodeError:
                            task['metadata'] = {}
                    else:
                        task['metadata'] = {}
                    tasks.append(task)
                
                return tasks
        except Exception as e:
            logger.error(f"Failed to get all tasks: {e}")
            return []

class VideoDatabase:
    """Database manager for video-related operations"""
    
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            backend_dir = Path(__file__).parent.parent
            self.db_path = backend_dir / "app_data.db"
        else:
            self.db_path = Path(db_path)
        self._init_database()
    
    def _init_database(self):
        """Initialize database and create tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("PRAGMA foreign_keys = ON")
                
                # Create video_index table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS video_index (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        filename TEXT NOT NULL,
                        original_path TEXT,
                        library_name TEXT NOT NULL,
                        video_id TEXT,
                        status TEXT DEFAULT 'indexed',
                        file_size INTEGER,
                        duration TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        indexed_at TEXT,
                        metadata TEXT,
                        UNIQUE(filename, library_name)
                    )
                """)
                
                # Create indexes
                conn.execute("CREATE INDEX IF NOT EXISTS idx_video_library ON video_index(library_name)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_video_status ON video_index(status)")
                
                conn.commit()
                logger.info("Video database initialized successfully")
                
        except Exception as e:
            logger.error(f"Failed to initialize video database: {e}")
            raise

    def get_library_videos(self, library_name: str) -> List[Dict[str, Any]]:
        """Get all videos for a library"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    "SELECT * FROM video_index WHERE library_name = ? ORDER BY created_at DESC",
                    (library_name,)
                )
                
                videos = []
                for row in cursor.fetchall():
                    video = dict(row)
                    # Parse metadata JSON
                    if video['metadata']:
                        try:
                            video['metadata'] = json.loads(video['metadata'])
                        except json.JSONDecodeError:
                            video['metadata'] = {}
                    else:
                        video['metadata'] = {}
                    videos.append(video)
                
                return videos
        except Exception as e:
            logger.error(f"Failed to get videos for library {library_name}: {e}")
            return []

# Backwards compatibility - create global instance
class DatabaseManager:
    """Legacy wrapper for backwards compatibility"""
    
    def __init__(self, db_path: str = "app_data.db"):
        backend_dir = Path(__file__).parent.parent
        self.db_path = backend_dir / db_path
        self.task_db = TaskDatabase(str(self.db_path))
        self.video_db = VideoDatabase(str(self.db_path))
    
    def save_task(self, task_data: Dict[str, Any]) -> bool:
        return self.task_db.save_task(task_data)
    
    def get_all_tasks(self) -> List[Dict[str, Any]]:
        return self.task_db.get_all_tasks()
    
    def get_library_videos(self, library_name: str) -> List[Dict[str, Any]]:
        return self.video_db.get_library_videos(library_name)
    
    def delete_task(self, task_id: str) -> bool:
        """Delete task from database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("DELETE FROM tasks WHERE task_id = ?", (task_id,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Failed to delete task {task_id}: {e}")
            return False
    
    def save_video_record(self, video_data: Dict[str, Any]) -> bool:
        """Save video record to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO video_index 
                    (filename, original_path, library_name, video_id, status, 
                     file_size, duration, created_at, indexed_at, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    video_data.get('filename'),
                    video_data.get('original_path'),
                    video_data.get('library_name'),
                    video_data.get('video_id'),
                    video_data.get('status', 'indexed'),
                    video_data.get('file_size'),
                    video_data.get('duration'),
                    video_data.get('created_at'),
                    video_data.get('indexed_at'),
                    json.dumps(video_data.get('metadata', {}))
                ))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to save video record: {e}")
            return False
    
    def mark_video_deleted(self, library_name: str, video_id: str) -> bool:
        """Mark video as deleted in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    UPDATE video_index 
                    SET status = 'deleted', indexed_at = CURRENT_TIMESTAMP 
                    WHERE library_name = ? AND video_id = ?
                """, (library_name, video_id))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Failed to mark video as deleted {video_id}: {e}")
            return False

# Global instances
db_manager = DatabaseManager()
task_db = TaskDatabase()
video_db = VideoDatabase()
