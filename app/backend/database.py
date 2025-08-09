import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any
import json

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path: str = "app_data.db"):
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
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        metadata TEXT,
                        UNIQUE(filename, library_name)
                    )
                """)
                
                conn.commit()
                logger.info("Database initialized successfully")
                
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
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
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task by ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,))
                row = cursor.fetchone()
                if row:
                    task_data = dict(row)
                    if task_data.get('metadata'):
                        task_data['metadata'] = json.loads(task_data['metadata'])
                    return task_data
                return None
        except Exception as e:
            logger.error(f"Failed to get task {task_id}: {e}")
            return None
    
    def get_all_tasks(self, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all tasks, optionally filtered by status"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                if status_filter:
                    cursor = conn.execute("SELECT * FROM tasks WHERE status = ? ORDER BY created_at DESC", (status_filter,))
                else:
                    cursor = conn.execute("SELECT * FROM tasks ORDER BY created_at DESC")
                
                tasks = []
                for row in cursor.fetchall():
                    task_data = dict(row)
                    if task_data.get('metadata'):
                        task_data['metadata'] = json.loads(task_data['metadata'])
                    tasks.append(task_data)
                return tasks
        except Exception as e:
            logger.error(f"Failed to get tasks: {e}")
            return []
    
    def delete_task(self, task_id: str) -> bool:
        """Delete task from database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM tasks WHERE task_id = ?", (task_id,))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to delete task {task_id}: {e}")
            return False
    
    def cleanup_old_tasks(self, hours: int = 24) -> int:
        """Clean up old completed tasks"""
        try:
            cutoff = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    DELETE FROM tasks 
                    WHERE status IN ('completed', 'failed', 'cancelled')
                    AND datetime(completed_at) < datetime(?, '-{} hours')
                """.format(hours), (cutoff,))
                deleted_count = cursor.rowcount
                conn.commit()
                return deleted_count
        except Exception as e:
            logger.error(f"Failed to cleanup old tasks: {e}")
            return 0
    
    def save_video_record(self, video_data: Dict[str, Any]) -> bool:
        """Save video record to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO video_index 
                    (filename, original_path, library_name, video_id, status, 
                     file_size, duration, created_at, updated_at, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    video_data.get('filename'),
                    video_data.get('original_path'),
                    video_data.get('library_name'),
                    video_data.get('video_id'),
                    video_data.get('status', 'indexed'),
                    video_data.get('file_size'),
                    video_data.get('duration'),
                    video_data.get('created_at', datetime.now().isoformat()),
                    datetime.now().isoformat(),
                    json.dumps(video_data.get('metadata', {}))
                ))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to save video record: {e}")
            return False
    
    def get_library_videos(self, library_name: str) -> List[Dict[str, Any]]:
        """Get all videos in a library"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT * FROM video_index 
                    WHERE library_name = ? AND status != 'deleted'
                    ORDER BY created_at DESC
                """, (library_name,))
                
                videos = []
                for row in cursor.fetchall():
                    video_data = dict(row)
                    if video_data.get('metadata'):
                        video_data['metadata'] = json.loads(video_data['metadata'])
                    videos.append(video_data)
                return videos
        except Exception as e:
            logger.error(f"Failed to get videos for library {library_name}: {e}")
            return []
    

    def mark_video_deleted(self, library_name: str, video_id: str) -> bool:
        """(保留) Mark a video as deleted (soft delete)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    UPDATE video_index 
                    SET status = 'deleted', updated_at = ?
                    WHERE library_name = ? AND (video_id = ? OR filename = ?)
                """, (datetime.now().isoformat(), library_name, video_id, video_id))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to mark video as deleted: {e}")
            return False

    def delete_video_record(self, library_name: str, video_id: str) -> bool:
        """Physically delete a video record from the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    DELETE FROM video_index
                    WHERE library_name = ? AND (video_id = ? OR filename = ?)
                """, (library_name, video_id, video_id))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to physically delete video: {e}")
            return False

# Global database manager instance
db_manager = DatabaseManager()
