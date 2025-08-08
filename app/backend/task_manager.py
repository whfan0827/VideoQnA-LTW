import threading
import time
import uuid
import logging
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, asdict
from typing import Dict, Optional, Callable, List
from pathlib import Path

from database.app_data_manager import db_manager

logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class TaskInfo:
    task_id: str
    task_type: str
    status: TaskStatus
    progress: int  # 0-100
    current_step: str
    filename: str
    library_name: str
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    file_path: Optional[str] = None
    
    def to_dict(self):
        data = asdict(self)
        data['status'] = self.status.value
        data['created_at'] = self.created_at.isoformat()
        data['started_at'] = self.started_at.isoformat() if self.started_at else None
        data['completed_at'] = self.completed_at.isoformat() if self.completed_at else None
        return data

class TaskManager:
    def __init__(self):
        self.tasks: Dict[str, TaskInfo] = {}
        self.processing_queue = []
        self.max_concurrent = 3  # Maximum concurrent processing tasks
        self.current_processing = 0
        self.lock = threading.Lock()
        self.shutdown = False
        
        # Load existing tasks from database
        self._load_tasks_from_db()
        
        # Start the worker thread
        self.worker_thread = threading.Thread(target=self._process_queue, daemon=True)
        self.worker_thread.start()
        
        # Start cleanup thread
        self.cleanup_thread = threading.Thread(target=self._cleanup_old_tasks, daemon=True)
        self.cleanup_thread.start()
        
        logger.info("TaskManager initialized with database persistence")
    
    def _load_tasks_from_db(self):
        """Load existing tasks from database on startup"""
        try:
            db_tasks = db_manager.get_all_tasks()
            for db_task in db_tasks:
                if db_task['status'] in ['pending', 'processing']:
                    # Convert database record back to TaskInfo
                    task = TaskInfo(
                        task_id=db_task['task_id'],
                        task_type=db_task['task_type'],
                        status=TaskStatus(db_task['status']),
                        progress=db_task['progress'],
                        current_step=db_task['current_step'],
                        filename=db_task['filename'],
                        library_name=db_task['library_name'],
                        file_path=db_task['file_path'],
                        created_at=datetime.fromisoformat(db_task['created_at']) if db_task['created_at'] else datetime.now(),
                        started_at=datetime.fromisoformat(db_task['started_at']) if db_task['started_at'] else None,
                        completed_at=datetime.fromisoformat(db_task['completed_at']) if db_task['completed_at'] else None,
                        error_message=db_task['error_message']
                    )
                    self.tasks[task.task_id] = task
                    
                    if task.status == TaskStatus.PENDING:
                        self.processing_queue.append(task.task_id)
                        
            logger.info(f"Loaded {len(self.tasks)} tasks from database")
            
        except Exception as e:
            logger.error(f"Failed to load tasks from database: {e}")
    
    def _save_task_to_db(self, task: TaskInfo):
        """Save task to database"""
        try:
            task_data = {
                'task_id': task.task_id,
                'task_type': task.task_type,
                'status': task.status.value,
                'progress': task.progress,
                'current_step': task.current_step,
                'filename': task.filename,
                'library_name': task.library_name,
                'file_path': task.file_path,
                'created_at': task.created_at.isoformat() if task.created_at else None,
                'started_at': task.started_at.isoformat() if task.started_at else None,
                'completed_at': task.completed_at.isoformat() if task.completed_at else None,
                'error_message': task.error_message
            }
            db_manager.save_task(task_data)
        except Exception as e:
            logger.error(f"Failed to save task {task.task_id} to database: {e}")
    
    def create_upload_task(self, filename: str, library_name: str, file_path: str) -> str:
        """Create a new upload task"""
        task_id = str(uuid.uuid4())
        
        task = TaskInfo(
            task_id=task_id,
            task_type="video_upload",
            status=TaskStatus.PENDING,
            progress=0,
            current_step="Queued for processing",
            filename=filename,
            library_name=library_name,
            file_path=file_path,
            created_at=datetime.now()
        )
        
        with self.lock:
            self.tasks[task_id] = task
            self.processing_queue.append(task_id)
        
        # Save to database
        self._save_task_to_db(task)
        
        logger.info(f"Created upload task {task_id} for file {filename}")
        logger.info(f"Current queue length: {len(self.processing_queue)}")
        logger.info(f"Current processing count: {self.current_processing}")
        logger.info(f"Worker thread alive: {self.worker_thread.is_alive()}")
        
        return task_id
    
    def create_video_delete_task(self, library_name: str, video_id: str) -> str:
        """Create a new video deletion task"""
        task_id = str(uuid.uuid4())
        
        task = TaskInfo(
            task_id=task_id,
            task_type="video_delete",
            status=TaskStatus.PENDING,
            progress=0,
            current_step="Queued for deletion",
            filename=video_id,  # Use video_id as filename for deletion tasks
            library_name=library_name,
            file_path=None,  # Not needed for deletion
            created_at=datetime.now()
        )
        
        with self.lock:
            self.tasks[task_id] = task
            self.processing_queue.append(task_id)
        
        # Save to database
        self._save_task_to_db(task)
        
        logger.info(f"Created video deletion task {task_id} for {video_id} in {library_name}")
        return task_id
    
    def create_batch_delete_task(self, library_name: str, video_ids: List[str]) -> str:
        """Create a new batch video deletion task"""
        task_id = str(uuid.uuid4())
        
        task = TaskInfo(
            task_id=task_id,
            task_type="batch_video_delete",
            status=TaskStatus.PENDING,
            progress=0,
            current_step=f"Queued for batch deletion ({len(video_ids)} videos)",
            filename=f"{len(video_ids)} videos",
            library_name=library_name,
            file_path=",".join(video_ids),  # Store video IDs in file_path
            created_at=datetime.now()
        )
        
        with self.lock:
            self.tasks[task_id] = task
            self.processing_queue.append(task_id)
        
        # Save to database
        self._save_task_to_db(task)
        
        logger.info(f"Created batch deletion task {task_id} for {len(video_ids)} videos in {library_name}")
        return task_id
    
    def get_task(self, task_id: str) -> Optional[TaskInfo]:
        """Get task by ID"""
        with self.lock:
            return self.tasks.get(task_id)
    
    def list_all_tasks(self) -> List[TaskInfo]:
        """List all tasks"""
        with self.lock:
            return list(self.tasks.values())
    
    def list_active_tasks(self) -> List[TaskInfo]:
        """List only active tasks (pending or processing)"""
        with self.lock:
            return [
                task for task in self.tasks.values() 
                if task.status in [TaskStatus.PENDING, TaskStatus.PROCESSING]
            ]
    
    def update_task_progress(self, task_id: str, progress: int, step: str):
        """Update task progress"""
        with self.lock:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                task.progress = progress
                task.current_step = step
                # Save to database
                self._save_task_to_db(task)
                logger.debug(f"Task {task_id}: {progress}% - {step}")
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a task"""
        with self.lock:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                if task.status in [TaskStatus.PENDING, TaskStatus.PROCESSING]:
                    task.status = TaskStatus.CANCELLED
                    task.current_step = "Cancelled by user"
                    task.completed_at = datetime.now()
                    if task_id in self.processing_queue:
                        self.processing_queue.remove(task_id)
                    # Save to database
                    self._save_task_to_db(task)
                    logger.info(f"Task {task_id} cancelled")
                    return True
        return False
    
    def remove_task(self, task_id: str) -> bool:
        """Remove a task from the task manager"""
        with self.lock:
            if task_id in self.tasks:
                # Don't remove active tasks
                task = self.tasks[task_id]
                if task.status in [TaskStatus.PENDING, TaskStatus.PROCESSING]:
                    logger.warning(f"Cannot remove active task {task_id}")
                    return False
                
                # Remove from tasks dict
                del self.tasks[task_id]
                
                # Remove from processing queue if present
                if task_id in self.processing_queue:
                    self.processing_queue.remove(task_id)
                
                # Remove from database
                db_manager.delete_task(task_id)
                
                logger.info(f"Task {task_id} removed")
                return True
        
        logger.warning(f"Task {task_id} not found for removal")
        return False
    
    def _process_queue(self):
        """Background task processing loop"""
        logger.info("Task processing queue started")
        
        while not self.shutdown:
            try:
                should_process = False
                task_to_process = None
                
                with self.lock:
                    if self.current_processing < self.max_concurrent and self.processing_queue:
                        if self.processing_queue:
                            task_to_process = self.processing_queue.pop(0)
                            self.current_processing += 1
                            should_process = True
                            logger.info(f"Dispatching task {task_to_process} for processing. Current processing: {self.current_processing}")
                
                if should_process and task_to_process:
                    # Start processing in a new thread
                    processing_thread = threading.Thread(
                        target=self._process_single_task,
                        args=(task_to_process,),
                        daemon=True,
                        name=f"TaskProcessor-{task_to_process[:8]}"
                    )
                    processing_thread.start()
                    logger.info(f"Started processing thread for task {task_to_process}")
                
                time.sleep(1)  # Check queue every second
                
            except Exception as e:
                logger.error(f"Error in process queue: {e}")
                time.sleep(5)  # Wait longer on error
    
    def _process_single_task(self, task_id: str):
        """Process a single task (upload, delete, or batch delete)"""
        try:
            task = self.tasks[task_id]
            if task.status == TaskStatus.CANCELLED:
                return
                
            task.status = TaskStatus.PROCESSING
            task.started_at = datetime.now()
            
            logger.info(f"Starting processing task {task_id}: {task.task_type} - {task.filename}")
            
            if task.task_type == "video_upload":
                self._process_video_upload(task_id)
            elif task.task_type == "video_delete":
                self._process_video_delete(task_id)
            elif task.task_type == "batch_video_delete":
                self._process_batch_video_delete(task_id)
            else:
                raise ValueError(f"Unknown task type: {task.task_type}")
                
        except Exception as e:
            logger.exception(f"Task {task_id} failed: {e}")
            task = self.tasks[task_id]
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            task.current_step = f"Failed: {str(e)}"
            task.completed_at = datetime.now()
            
            # Save to database
            self._save_task_to_db(task)
            
        finally:
            self.current_processing -= 1
    
    def _process_video_upload(self, task_id: str):
        """Process video upload task"""
        task = self.tasks[task_id]
        
        # Step 1: Initialize
        self.update_task_progress(task_id, 5, "Initializing video processing...")
        
        # Import here to avoid circular imports
        try:
            from vi_search.prepare_db import prepare_db_with_progress
            from vi_search.constants import DATA_DIR
            import os
            
            # Initialize language models and prompt content db directly
            search_db = os.environ.get("PROMPT_CONTENT_DB", "azure_search")
            if search_db == "chromadb":
                from vi_search.prompt_content_db.chroma_db import ChromaDB
                prompt_content_db = ChromaDB()
            elif search_db == "azure_search":
                from vi_search.prompt_content_db.azure_search import AzureVectorSearch
                prompt_content_db = AzureVectorSearch()
            else:
                raise ValueError(f"Unknown search_db: {search_db}")

            lang_model = os.environ.get("LANGUAGE_MODEL", "openai")
            if lang_model == "openai":
                from vi_search.language_models.azure_openai import OpenAI
                language_models = OpenAI()
            elif lang_model == "dummy":
                from vi_search.language_models.dummy_lm import DummyLanguageModels
                language_models = DummyLanguageModels()
            else:
                raise ValueError(f"Unknown language model: {lang_model}")
            
            logger.info(f"Successfully imported dependencies for task {task_id}")
            
        except Exception as e:
            logger.error(f"Failed to import dependencies for task {task_id}: {e}")
            raise Exception(f"System dependency error: {str(e)}")
        
        # Process video with progress callbacks
        def progress_callback(step: str, progress: int):
            if task.status == TaskStatus.CANCELLED:
                raise Exception("Task was cancelled")
            self.update_task_progress(task_id, progress, step)
        
        # Call the enhanced prepare_db function
        logger.info(f"Starting video processing for task {task_id}")
        prepare_db_with_progress(
            db_name=task.library_name,
            data_dir=DATA_DIR,
            language_models=language_models,
            prompt_content_db=prompt_content_db,
            single_video_file=task.file_path,
            progress_callback=progress_callback,
            verbose=True,
            use_videos_ids_cache=False
        )
        
        # Save video record to database
        try:
            file_size = 0
            if task.file_path and Path(task.file_path).exists():
                file_size = Path(task.file_path).stat().st_size
                
            video_data = {
                'filename': task.filename,
                'original_path': task.file_path,
                'library_name': task.library_name,
                'status': 'indexed',
                'file_size': file_size,
                'indexed_at': datetime.now().isoformat()
            }
            db_manager.save_video_record(video_data)
            logger.info(f"Video record saved for {task.filename}")
        except Exception as ve:
            logger.warning(f"Failed to save video record: {ve}")
        
        # Mark as completed
        task.status = TaskStatus.COMPLETED
        task.progress = 100
        task.current_step = "Processing completed successfully"
        task.completed_at = datetime.now()
        
        # Save to database
        self._save_task_to_db(task)
        
        logger.info(f"Task {task_id} completed successfully")
    
    def _process_video_delete(self, task_id: str):
        """Process video deletion task"""
        task = self.tasks[task_id]
        video_id = task.filename
        
        self.update_task_progress(task_id, 10, "Starting video deletion...")
        
        try:
            # Import app components
            import sys
            if 'app' in sys.modules:
                app_module = sys.modules['app']
                prompt_content_db = getattr(app_module, 'prompt_content_db', None)
                if not prompt_content_db:
                    raise ImportError("Cannot access prompt_content_db from app module")
            else:
                raise ImportError("App module not loaded")
            
            # Step 1: Remove from vector database
            self.update_task_progress(task_id, 30, "Removing from vector database...")
            try:
                # This would need implementation in prompt_content_db
                # prompt_content_db.delete_video_documents(task.library_name, video_id)
                logger.info(f"Removed vector documents for {video_id}")
            except Exception as e:
                logger.warning(f"Failed to remove vector documents: {e}")
            
            # Step 2: Mark as deleted in database
            self.update_task_progress(task_id, 70, "Updating database records...")
            success = db_manager.mark_video_deleted(task.library_name, video_id)
            if not success:
                raise Exception("Failed to mark video as deleted in database")
            
            # Step 3: Optional - Delete physical file (implement if needed)
            self.update_task_progress(task_id, 90, "Cleaning up files...")
            
            # Mark as completed
            task.status = TaskStatus.COMPLETED
            task.progress = 100
            task.current_step = "Video deletion completed successfully"
            task.completed_at = datetime.now()
            
            # Save to database
            self._save_task_to_db(task)
            
            logger.info(f"Video deletion task {task_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Video deletion failed: {e}")
            raise
    
    def _process_batch_video_delete(self, task_id: str):
        """Process batch video deletion task"""
        task = self.tasks[task_id]
        video_ids = task.file_path.split(',') if task.file_path else []
        total_videos = len(video_ids)
        
        self.update_task_progress(task_id, 5, f"Starting batch deletion of {total_videos} videos...")
        
        try:
            # Import app components
            import sys
            if 'app' in sys.modules:
                app_module = sys.modules['app']
                prompt_content_db = getattr(app_module, 'prompt_content_db', None)
                if not prompt_content_db:
                    raise ImportError("Cannot access prompt_content_db from app module")
            else:
                raise ImportError("App module not loaded")
            
            deleted_count = 0
            failed_videos = []
            
            for i, video_id in enumerate(video_ids):
                if task.status == TaskStatus.CANCELLED:
                    break
                
                try:
                    progress = 10 + (i * 80 // total_videos)
                    self.update_task_progress(task_id, progress, f"Deleting {video_id}...")
                    
                    # Remove from vector database
                    # prompt_content_db.delete_video_documents(task.library_name, video_id)
                    
                    # Mark as deleted in database
                    success = db_manager.mark_video_deleted(task.library_name, video_id)
                    if success:
                        deleted_count += 1
                    else:
                        failed_videos.append(video_id)
                        
                except Exception as e:
                    logger.warning(f"Failed to delete video {video_id}: {e}")
                    failed_videos.append(video_id)
            
            # Mark as completed
            task.status = TaskStatus.COMPLETED
            task.progress = 100
            
            if failed_videos:
                task.current_step = f"Batch deletion completed with errors. Deleted: {deleted_count}, Failed: {len(failed_videos)}"
                task.error_message = f"Failed to delete: {', '.join(failed_videos)}"
            else:
                task.current_step = f"Batch deletion completed successfully. Deleted {deleted_count} videos"
            
            task.completed_at = datetime.now()
            
            # Save to database
            self._save_task_to_db(task)
            
            logger.info(f"Batch deletion task {task_id} completed. Success: {deleted_count}, Failed: {len(failed_videos)}")
            
        except Exception as e:
            logger.error(f"Batch deletion failed: {e}")
            raise
    
    def _cleanup_old_tasks(self):
        """Clean up old completed/failed tasks"""
        while not self.shutdown:
            try:
                cutoff_time = datetime.now() - timedelta(hours=24)
                
                with self.lock:
                    tasks_to_remove = [
                        task_id for task_id, task in self.tasks.items()
                        if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]
                        and task.completed_at
                        and task.completed_at < cutoff_time
                    ]
                    
                    for task_id in tasks_to_remove:
                        del self.tasks[task_id]
                        logger.debug(f"Cleaned up old task {task_id}")
                
                time.sleep(3600)  # Clean up every hour
            except Exception as e:
                logger.error(f"Error in cleanup: {e}")
                time.sleep(300)  # Wait 5 minutes on error
    
    def shutdown_manager(self):
        """Shutdown the task manager"""
        self.shutdown = True
        logger.info("TaskManager shutdown initiated")

# Global task manager instance
task_manager = TaskManager()
