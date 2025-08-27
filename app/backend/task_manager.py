import threading
import time
import uuid
import logging
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, asdict
from typing import Dict, Optional, List
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
    retry_count: int = 0
    max_retries: int = 2
    
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
        self.max_concurrent = 1  # Maximum concurrent processing tasks
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
        """Create a new file upload task"""
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
        
        logger.info(f"Created file upload task {task_id} for file '{filename}' in library '{library_name}' (queue position: {len(self.processing_queue)})")
        return task_id
    
    def create_url_upload_task(self, filename: str, library_name: str, video_url: str) -> str:
        """Create a new URL upload task"""
        task_id = str(uuid.uuid4())
        
        task = TaskInfo(
            task_id=task_id,
            task_type="video_url_upload",
            status=TaskStatus.PENDING,
            progress=0,
            current_step="Queued for URL processing",
            filename=filename,
            library_name=library_name,
            file_path=video_url,  # Store URL in file_path field
            created_at=datetime.now()
        )
        
        with self.lock:
            self.tasks[task_id] = task
            self.processing_queue.append(task_id)
        
        # Save to database
        self._save_task_to_db(task)
        
        logger.info(f"Created URL upload task {task_id} for URL {video_url}")
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
                try:
                    db_manager.delete_task(task_id)
                except Exception as e:
                    logger.warning(f"Failed to delete task {task_id} from database: {e}")
                
                logger.info(f"Task {task_id} removed")
                return True
        
        # Task not found in memory, try to delete from database anyway
        try:
            success = db_manager.delete_task(task_id)
            if success:
                logger.info(f"Task {task_id} found in database and removed")
                return True
        except Exception as e:
            logger.warning(f"Error trying to delete task {task_id} from database: {e}")
        
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
            elif task.task_type == "video_url_upload":
                self._process_video_url_upload(task_id)
            elif task.task_type == "video_delete":
                self._process_video_delete(task_id)
            elif task.task_type == "batch_video_delete":
                self._process_batch_video_delete(task_id)
            else:
                raise ValueError(f"Unknown task type: {task.task_type}")
                
        except Exception as e:
            logger.exception(f"Task {task_id} failed: {e}")
            task = self.tasks[task_id]
            
            # Check if this is a retryable error (connection issues)
            is_retryable = (
                "10054" in str(e) or 
                "Connection aborted" in str(e) or
                "Connection reset" in str(e) or
                "timeout" in str(e).lower()
            )
            
            if is_retryable and task.retry_count < task.max_retries:
                task.retry_count += 1
                retry_delay = task.retry_count * 60  # 1, 2, 3 minutes
                task.status = TaskStatus.PENDING  # Reset to pending for retry
                task.current_step = f"Retrying in {retry_delay}s (attempt {task.retry_count + 1}/{task.max_retries + 1}): {str(e)}"
                task.error_message = f"Retry {task.retry_count}: {str(e)}"
                
                logger.info(f"Task {task_id} will retry in {retry_delay}s (attempt {task.retry_count + 1}/{task.max_retries + 1})")
                
                # Schedule retry by adding back to queue with delay
                import threading
                def delayed_retry():
                    time.sleep(retry_delay)
                    with self.lock:
                        if task.status == TaskStatus.PENDING:  # Only if not cancelled
                            self.processing_queue.append(task_id)
                            logger.info(f"Task {task_id} added back to queue for retry")
                
                retry_thread = threading.Thread(target=delayed_retry, daemon=True)
                retry_thread.start()
            else:
                # Final failure after all retries
                task.status = TaskStatus.FAILED
                if task.retry_count > 0:
                    task.error_message = f"Failed after {task.retry_count} retries: {str(e)}"
                    task.current_step = f"Failed after {task.retry_count} retries: {str(e)}"
                else:
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
        
        # Brief delay to avoid API rate limiting - reduced due to optimized connection handling
        import time
        # Short delay since we now have token caching and optimized connections
        wait_time = 5  # Wait 5 seconds between uploads - much faster with our optimizations
        self.update_task_progress(task_id, 5, f"Preparing upload (waiting {wait_time}s)...")
        time.sleep(wait_time)
        self.update_task_progress(task_id, 10, "Preparing Azure Video Indexer connection...")
        
        # Import here to avoid circular imports
        try:
            from vi_search.prepare_db import prepare_db_with_progress
            from vi_search.constants import DATA_DIR
            from vi_search.file_hash_cache import get_global_cache
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
        
        # Fast duplicate check before processing
        file_cache = get_global_cache()
        if task.file_path and Path(task.file_path).exists():
            cached_info = file_cache.get_cached_video_info(Path(task.file_path))
            if cached_info:
                self.update_task_progress(task_id, 50, f"Duplicate detected - using cached video_id {cached_info['video_id']}")
                logger.info(f"Skipping duplicate file upload for {task.filename} - using cached video_id {cached_info['video_id']}")
                
                # Still need to process the video to add it to the target library
                # Use the cached video_id to quickly generate vectors and add to database
                try:
                    # Import dependencies for cached processing
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

                    self.update_task_progress(task_id, 70, "Processing cached video for target library...")
                    
                    # Process the cached video with the target library
                    from vi_search.prepare_db import prepare_db_with_progress
                    from vi_search.constants import DATA_DIR
                    
                    def progress_callback(step: str, progress: int):
                        if task.status == TaskStatus.CANCELLED:
                            raise Exception("Task was cancelled")
                        # Scale progress from 70-95
                        scaled_progress = 70 + int((progress / 100) * 25)
                        self.update_task_progress(task_id, scaled_progress, step)
                    
                    prepare_db_with_progress(
                        db_name=task.library_name,
                        data_dir=DATA_DIR,
                        language_models=language_models,
                        prompt_content_db=prompt_content_db,
                        single_video_file=task.file_path,
                        progress_callback=progress_callback,
                        verbose=True,
                        use_videos_ids_cache=True  # Use cache for fast processing
                    )
                    
                    # Save video record to target library database
                    file_size = 0
                    if task.file_path and Path(task.file_path).exists():
                        file_size = Path(task.file_path).stat().st_size
                        
                    video_data = {
                        'filename': task.filename,
                        'original_path': task.file_path,
                        'library_name': task.library_name,
                        'video_id': cached_info['video_id'],
                        'status': 'indexed',
                        'file_size': file_size,
                    }
                    
                    db_manager.save_video_record(video_data)
                    logger.info(f"Video record saved for {task.filename} in library {task.library_name}")
                    
                    # Mark as completed
                    task.status = TaskStatus.COMPLETED
                    task.progress = 100
                    task.current_step = f"Duplicate processed - video indexed as {cached_info['video_id']} in {task.library_name}"
                    task.completed_at = datetime.now()
                    self._save_task_to_db(task)
                    return
                    
                except Exception as e:
                    logger.error(f"Failed to process cached video: {e}")
                    # Fall through to normal processing if cached processing fails

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
        
        logger.info(f"File upload task {task_id} completed successfully")
    
    def _process_video_url_upload(self, task_id: str):
        """Process video URL upload task"""
        task = self.tasks[task_id]
        video_url = task.file_path  # URL is stored in file_path
        
        # Step 1: Initialize
        self.update_task_progress(task_id, 5, "Initializing URL video processing...")
        
        # Brief delay for URL uploads - reduced due to optimized connection handling
        import time
        wait_time = 3  # Wait 3 seconds between URL uploads (optimized with token caching)
        self.update_task_progress(task_id, 8, f"Preparing URL upload (waiting {wait_time}s)...")
        time.sleep(wait_time)
        self.update_task_progress(task_id, 15, "Preparing Azure Video Indexer connection...")
        
        # Import necessary components
        try:
            from vi_search.vi_client.video_indexer_client import get_video_indexer_client_by_index
            from vi_search.constants import BASE_DIR
            from dotenv import dotenv_values
            import os
            
            # Initialize language models and prompt content db
            search_db = os.environ.get("PROMPT_CONTENT_DB", "azure_search")
            if search_db == "chromadb":
                from vi_search.prompt_content_db.chroma_db import ChromaDB
                prompt_content_db = ChromaDB()
            elif search_db == "azure_search":
                from vi_search.prompt_content_db.azure_search import AzureVectorSearch
                prompt_content_db = AzureVectorSearch()
            else:
                raise ValueError(f"Unknown search_db: {search_db}")

            # Language models not needed for URL upload (would be used for text processing)
            logger.info(f"Successfully imported dependencies for URL task {task_id}")
            
        except Exception as e:
            logger.error(f"Failed to import dependencies for task {task_id}: {e}")
            raise Exception(f"System dependency error: {str(e)}")
        
        # Call URL processing function (we'll need to create this)
        logger.info(f"Starting URL video processing for task {task_id}")
        try:
            # Load VI configuration
            config = dotenv_values(BASE_DIR / ".env")
            client = get_video_indexer_client_by_index(config)
            
            # Upload video from URL
            self.update_task_progress(task_id, 30, "Uploading video from URL...")
            if video_url is None:
                raise ValueError("Video URL is None")
            video_id = client.upload_url_async(task.filename, video_url, wait_for_index=False)
            
            # Wait for indexing
            self.update_task_progress(task_id, 50, "Waiting for video indexing...")
            client.wait_for_index_async(video_id)
            
            # Generate prompt content and index to vector DB
            self.update_task_progress(task_id, 70, "Processing video content...")
            sections = client.get_prompt_content_async(video_id)
            
            # Add to vector database
            prompt_content_db.set_db(task.library_name)
            prompt_content_db.add_sections_to_db(sections, upload_batch_size=100)
            
        except Exception as e:
            logger.error(f"URL processing failed for task {task_id}: {e}")
            raise
        
        # Save video record to database
        try:
            video_data = {
                'filename': task.filename,
                'original_path': video_url,
                'library_name': task.library_name,
                'status': 'indexed',
                'file_size': 0,  # Unknown for URL uploads
                'indexed_at': datetime.now().isoformat()
            }
            db_manager.save_video_record(video_data)
            logger.info(f"Video record saved for {task.filename}")
        except Exception as ve:
            logger.warning(f"Failed to save video record: {ve}")
        
        # Mark as completed
        task.status = TaskStatus.COMPLETED
        task.progress = 100
        task.current_step = "URL processing completed successfully"
        task.completed_at = datetime.now()
        
        # Save to database
        self._save_task_to_db(task)
        
        logger.info(f"URL upload task {task_id} completed successfully")
    
    def _process_video_delete(self, task_id: str):
        """Process video deletion task"""
        task = self.tasks[task_id]
        video_id = task.filename
        
        self.update_task_progress(task_id, 10, "Starting video deletion...")
        
        try:
            # Import vector database components directly
            try:
                import os
                from dotenv import load_dotenv
                
                # Load environment variables
                load_dotenv()
                search_db = os.environ.get("PROMPT_CONTENT_DB", "azure_search")
                
                if search_db == "chromadb":
                    from vi_search.prompt_content_db.chroma_db import ChromaDB
                    prompt_content_db = ChromaDB()
                    logger.info("Initialized ChromaDB for video deletion")
                elif search_db == "azure_search":
                    from vi_search.prompt_content_db.azure_search import AzureVectorSearch
                    prompt_content_db = AzureVectorSearch()
                    logger.info("Initialized Azure Search for video deletion")
                else:
                    raise ValueError(f"Unknown search_db: {search_db}")
                    
            except Exception as e:
                logger.error(f"Failed to initialize vector database: {e}")
                # If vector database fails, continue without it
                prompt_content_db = None
            
            # Step 1: Remove from vector database
            self.update_task_progress(task_id, 30, "Removing from vector database...")
            if prompt_content_db is not None:
                try:
                    # Set the database to the correct library
                    prompt_content_db.set_db(task.library_name)
                    success = prompt_content_db.delete_video_documents(video_id)
                    if success:
                        logger.info(f"Successfully removed vector documents for {video_id}")
                    else:
                        logger.warning(f"No vector documents found for {video_id}")
                except Exception as e:
                    logger.warning(f"Failed to remove vector documents: {e}")
                    # Don't fail the entire task if vector deletion fails
            else:
                logger.warning("Vector database not available, skipping vector deletion")
            
            # Step 2: Physically delete from database
            self.update_task_progress(task_id, 70, "Physically deleting database records...")
            library_variants = [
                task.library_name,
                task.library_name.replace('-instructions-', '-instruction-'),
                task.library_name.replace('-instruction-', '-instructions-')
            ]
            success = False
            for lib_name in library_variants:
                success = db_manager.delete_video_record(lib_name, video_id)
                if success:
                    logger.info(f"Physically deleted video using library name: {lib_name}")
                    break
            if not success:
                raise Exception(f"Failed to physically delete video in database. Tried library names: {library_variants}")
            
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
            # Import vector database components directly (same as single video delete)
            try:
                import os
                from dotenv import load_dotenv
                
                # Load environment variables
                load_dotenv()
                search_db = os.environ.get("PROMPT_CONTENT_DB", "azure_search")
                
                if search_db == "chromadb":
                    from vi_search.prompt_content_db.chroma_db import ChromaDB
                    prompt_content_db = ChromaDB()
                    logger.info("Initialized ChromaDB for batch video deletion")
                elif search_db == "azure_search":
                    from vi_search.prompt_content_db.azure_search import AzureVectorSearch
                    prompt_content_db = AzureVectorSearch()
                    logger.info("Initialized Azure Search for batch video deletion")
                else:
                    raise ValueError(f"Unknown search_db: {search_db}")
                    
            except Exception as e:
                logger.error(f"Failed to initialize vector database: {e}")
                # If vector database fails, continue without it
                prompt_content_db = None
            
            deleted_count = 0
            failed_videos = []
            
            for i, video_id in enumerate(video_ids):
                if task.status == TaskStatus.CANCELLED:
                    break
                
                try:
                    progress = 10 + (i * 80 // total_videos)
                    self.update_task_progress(task_id, progress, f"Deleting {video_id}...")
                    
                    # Remove from vector database
                    if prompt_content_db is not None:
                        try:
                            # Set the database to the correct library
                            prompt_content_db.set_db(task.library_name)
                            success = prompt_content_db.delete_video_documents(video_id)
                            if success:
                                logger.info(f"Successfully removed vector documents for {video_id}")
                            else:
                                logger.warning(f"No vector documents found for {video_id}")
                        except Exception as e:
                            logger.warning(f"Failed to remove vector documents for {video_id}: {e}")
                            # Don't fail the entire task if vector deletion fails
                    else:
                        logger.warning(f"Vector database not available, skipping vector deletion for {video_id}")
                    
                    # Physically delete in database
                    library_variants = [
                        task.library_name,
                        task.library_name.replace('-instructions-', '-instruction-'),
                        task.library_name.replace('-instruction-', '-instructions-')
                    ]
                    success = False
                    for lib_name in library_variants:
                        success = db_manager.delete_video_record(lib_name, video_id)
                        if success:
                            break
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
        """Clean up old completed/failed tasks (extended retention period)"""
        while not self.shutdown:
            try:
                # Extended retention period to 7 days instead of 24 hours
                cutoff_time = datetime.now() - timedelta(days=7)
                
                with self.lock:
                    tasks_to_remove = [
                        task_id for task_id, task in self.tasks.items()
                        if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]
                        and task.completed_at
                        and task.completed_at < cutoff_time
                    ]
                    
                    for task_id in tasks_to_remove:
                        logger.info(f"Cleaning up old task {task_id} (completed {(datetime.now() - self.tasks[task_id].completed_at).days} days ago)")
                        del self.tasks[task_id]
                
                # Check every 6 hours instead of every hour to reduce frequency
                time.sleep(6 * 3600)  # Clean up every 6 hours
            except Exception as e:
                logger.error(f"Error in cleanup: {e}")
                time.sleep(300)  # Wait 5 minutes on error
    
    def shutdown_manager(self):
        """Shutdown the task manager"""
        self.shutdown = True
        logger.info("TaskManager shutdown initiated")

# Global task manager instance
task_manager = TaskManager()
