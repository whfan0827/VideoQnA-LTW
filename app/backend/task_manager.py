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
from config import AppConfig
from models.task_models import TaskInfo, TaskStatus, Task, TaskExecution

logger = logging.getLogger(__name__)

class TaskManager:
    def __init__(self):
        self.tasks: Dict[str, TaskInfo] = {}
        self.processing_queue = []
        self.max_concurrent = AppConfig.MAX_CONCURRENT_TASKS
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
                    # Convert database record back to TaskInfo using new model
                    task = TaskInfo.from_dict(db_task)
                    self.tasks[task.task_id] = task
                    
                    if task.status == TaskStatus.PENDING:
                        self.processing_queue.append(task.task_id)
                        
            logger.info(f"Loaded {len(self.tasks)} tasks from database")
            
        except Exception as e:
            logger.error(f"Failed to load tasks from database: {e}")
    
    def _save_task_to_db(self, task: TaskInfo):
        """Save task to database"""
        try:
            # Use the to_dict() method to get all data in the correct format
            task_data = task.to_dict()
            db_manager.save_task(task_data)
        except Exception as e:
            logger.error(f"Failed to save task {task.task_id} to database: {e}")
    
    def create_upload_task(self, filename: str, library_name: str, file_path: str, source_language: str = "auto", source_type: str = "local_file", file_size: int = None) -> str:
        """Create a new file upload task"""
        task_id = str(uuid.uuid4())
        
        task = TaskInfo.create_file_task(
            task_id=task_id,
            task_type="video_upload",
            filename=filename,
            library_name=library_name,
            file_path=file_path,
            source_type=source_type,
            file_size_metadata=file_size,
            source_language=source_language
        )
        
        # Set initial execution state
        task.execution.current_step = "Queued for processing"
        
        with self.lock:
            self.tasks[task_id] = task
            self.processing_queue.append(task_id)
        
        # Save to database
        self._save_task_to_db(task)
        
        logger.info(f"Created file upload task {task_id} for file '{filename}' in library '{library_name}' (queue position: {len(self.processing_queue)})")
        return task_id
    
    def create_blob_import_task(self, filename: str, blob_url: str, library_name: str, file_size: int = None, source_language: str = "auto") -> str:
        """Create a new blob import task"""
        return self.create_upload_task(
            filename=filename,
            library_name=library_name,
            file_path=blob_url,
            source_type="blob_storage",
            file_size=file_size,
            source_language=source_language
        )
    
    def create_url_upload_task(self, filename: str, library_name: str, video_url: str, source_language: str = "auto") -> str:
        """Create a new URL upload task"""
        task_id = str(uuid.uuid4())
        
        task = TaskInfo.create_url_task(
            task_id=task_id,
            filename=filename,
            library_name=library_name,
            video_url=video_url,
            source_language=source_language
        )
        
        # Set initial execution state
        task.execution.current_step = "Queued for URL processing"
        
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
        
        task = TaskInfo.create_file_task(
            task_id=task_id,
            task_type="video_delete",
            filename=video_id,  # Use video_id as filename for deletion tasks
            library_name=library_name,
            file_path=None  # Not needed for deletion
        )
        
        # Set initial execution state
        task.execution.current_step = "Queued for deletion"
        
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
        
        task = TaskInfo.create_file_task(
            task_id=task_id,
            task_type="batch_video_delete",
            filename=f"{len(video_ids)} videos",
            library_name=library_name,
            file_path=",".join(video_ids)  # Store video IDs in file_path
        )
        
        # Set initial execution state
        task.execution.current_step = f"Queued for batch deletion ({len(video_ids)} videos)"
        
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
                # Update using new model structure
                task.execution.progress = progress
                task.execution.current_step = step
                # Save to database
                self._save_task_to_db(task)
                logger.debug(f"Task {task_id}: {progress}% - {step}")
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a task"""
        with self.lock:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                if task.status in [TaskStatus.PENDING, TaskStatus.PROCESSING]:
                    task.task.status = TaskStatus.CANCELLED
                    task.execution.current_step = "Cancelled by user"
                    task.execution.completed_at = datetime.now()
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
                
            task.task.status = TaskStatus.PROCESSING
            task.execution.started_at = datetime.now()
            
            logger.info(f"Starting processing task {task_id}: {task.task.task_type} - {task.file_info.filename if task.file_info else 'N/A'}")
            
            if task.task.task_type == "video_upload":
                self._process_video_upload(task_id)
            elif task.task.task_type == "video_url_upload":
                self._process_video_url_upload(task_id)
            elif task.task.task_type == "video_delete":
                self._process_video_delete(task_id)
            elif task.task.task_type == "batch_video_delete":
                self._process_batch_video_delete(task_id)
            else:
                raise ValueError(f"Unknown task type: {task.task.task_type}")
                
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
            
            if is_retryable and task.retry_policy.can_retry():
                task.retry_policy.increment_retry()
                retry_delay = task.retry_policy.retry_count * 60  # 1, 2, 3 minutes
                task.task.status = TaskStatus.PENDING  # Reset to pending for retry
                task.execution.current_step = f"Retrying in {retry_delay}s (attempt {task.retry_policy.retry_count + 1}/{task.retry_policy.max_retries + 1}): {str(e)}"
                task.execution.error_message = f"Retry {task.retry_policy.retry_count}: {str(e)}"
                
                logger.info(f"Task {task_id} will retry in {retry_delay}s (attempt {task.retry_policy.retry_count + 1}/{task.retry_policy.max_retries + 1})")
                
                # Schedule retry by adding back to queue with delay
                import threading
                def delayed_retry():
                    time.sleep(retry_delay)
                    with self.lock:
                        if task.task.status == TaskStatus.PENDING:  # Only if not cancelled
                            self.processing_queue.append(task_id)
                            logger.info(f"Task {task_id} added back to queue for retry")
                
                retry_thread = threading.Thread(target=delayed_retry, daemon=True)
                retry_thread.start()
            else:
                # Final failure after all retries
                task.task.status = TaskStatus.FAILED
                if task.retry_policy.retry_count > 0:
                    task.execution.error_message = f"Failed after {task.retry_policy.retry_count} retries: {str(e)}"
                    task.execution.current_step = f"Failed after {task.retry_policy.retry_count} retries: {str(e)}"
                else:
                    task.execution.error_message = str(e)
                    task.execution.current_step = f"Failed: {str(e)}"
                task.execution.completed_at = datetime.now()
            
            # Save to database
            self._save_task_to_db(task)
            
        finally:
            self.current_processing -= 1
    
    def _process_video_upload(self, task_id: str):
        """Process video upload task with enhanced timeout and error handling"""
        task = self.tasks[task_id]
        
        # Add timeout monitoring
        import time
        start_time = time.time()
        max_processing_time = 7200  # 2 hours maximum processing time
        
        def check_timeout():
            elapsed = time.time() - start_time
            if elapsed > max_processing_time:
                raise TimeoutError(f"Task processing timeout after {elapsed/60:.1f} minutes (max: {max_processing_time/60} minutes)")
            return elapsed
        
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
        if task.file_info.file_path and Path(task.file_info.file_path).exists():
            cached_info = file_cache.get_cached_video_info(Path(task.file_info.file_path))
            if cached_info:
                self.update_task_progress(task_id, 50, f"Duplicate detected - using cached video_id {cached_info['video_id']}")
                logger.info(f"Skipping duplicate file upload for {task.file_info.filename} - using cached video_id {cached_info['video_id']}")
                
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
                    
                    videos_ids = prepare_db_with_progress(
                        db_name=task.file_info.library_name,
                        data_dir=DATA_DIR,
                        language_models=language_models,
                        prompt_content_db=prompt_content_db,
                        single_video_file=task.file_info.file_path,
                        progress_callback=progress_callback,
                        verbose=True,
                        use_videos_ids_cache=True,  # Use cache for fast processing
                        original_filename=task.file_info.filename,
                        source_language=task.file_info.source_language or 'auto'
                    )
                    
                    # Save video record to target library database
                    file_size = 0
                    if hasattr(task, 'file_size_metadata') and task.file_info.file_size_metadata:
                        # Use blob size metadata if available
                        file_size = task.file_info.file_size_metadata
                    elif task.file_info.file_path and Path(task.file_info.file_path).exists():
                        # Use local file size for local files
                        file_size = Path(task.file_info.file_path).stat().st_size
                        
                    video_data = {
                        'filename': task.file_info.filename,
                        'original_path': task.file_info.file_path,
                        'library_name': task.file_info.library_name,
                        'video_id': cached_info['video_id'],
                        'status': 'indexed',
                        'file_size': file_size,
                        'source_type': task.file_info.source_type,
                        'blob_url': task.file_info.file_path if task.file_info.source_type == 'blob_storage' else None,
                        'blob_container': self._extract_container_from_url(task.file_info.file_path) if task.file_info.source_type == 'blob_storage' else None,
                        'blob_name': self._extract_blob_name_from_url(task.file_info.file_path) if task.file_info.source_type == 'blob_storage' else None,
                        'source_language': task.file_info.source_language
                    }
                    
                    db_manager.save_video_record(video_data)
                    logger.info(f"Video record saved for {task.file_info.filename} in library {task.file_info.library_name}")
                    
                    # Mark as completed
                    task.task.status = TaskStatus.COMPLETED
                    task.execution.progress = 100
                    task.execution.current_step = f"Duplicate processed - video indexed as {cached_info['video_id']} in {task.file_info.library_name}"
                    task.execution.completed_at = datetime.now()
                    self._save_task_to_db(task)
                    return
                    
                except Exception as e:
                    logger.error(f"Failed to process cached video: {e}")
                    # Fall through to normal processing if cached processing fails

        # Process video with progress callbacks
        def progress_callback(step: str, progress: int):
            if task.task.status == TaskStatus.CANCELLED:
                raise Exception("Task was cancelled")
            
            # Check for timeout during long processing
            try:
                elapsed = check_timeout()
                # Add elapsed time info to progress updates during long waits
                if progress == 30 and "waiting" in step.lower():
                    step = f"{step} (elapsed: {elapsed/60:.1f}min)"
            except TimeoutError as te:
                logger.error(f"Timeout during progress callback: {te}")
                raise te
                
            self.update_task_progress(task_id, progress, step)
        
        # Call the enhanced prepare_db function with timeout monitoring
        logger.info(f"Starting video processing for task {task_id}")
        check_timeout()  # Check before starting heavy processing
        
        try:
            videos_ids = prepare_db_with_progress(
                db_name=task.file_info.library_name,
                data_dir=DATA_DIR,
                language_models=language_models,
                prompt_content_db=prompt_content_db,
                single_video_file=task.file_info.file_path,
                progress_callback=progress_callback,
                verbose=True,
                use_videos_ids_cache=False,
                original_filename=task.file_info.filename,
                source_language=task.file_info.source_language or 'auto'
            )
        except TimeoutError as te:
            logger.error(f"Video processing timeout for task {task_id}: {te}")
            raise te
        except Exception as e:
            elapsed = check_timeout()
            logger.error(f"Video processing failed for task {task_id} after {elapsed/60:.1f} minutes: {e}")
            raise e
        
        # Extract video_id from the results
        # Linus principle: eliminate special cases with proper key normalization
        video_id = None
        if videos_ids:
            # Try multiple key formats to handle path normalization inconsistencies
            possible_keys = [
                task.file_info.file_path,  # Original path
                str(Path(task.file_info.file_path)),  # Path object string
                str(Path(task.file_info.file_path).resolve()),  # Resolved path
                Path(task.file_info.file_path).as_posix(),  # POSIX format
            ]
            
            for key in possible_keys:
                if key in videos_ids:
                    video_id = videos_ids[key]
                    logger.info(f"Successfully obtained video_id: {video_id} for file: {task.file_info.filename} (key: {key})")
                    break
            
            if not video_id:
                logger.warning(f"No video_id returned for file: {task.file_info.filename}")
                logger.debug(f"videos_ids returned: {videos_ids}")
                logger.debug(f"Looking for file_path: {task.file_info.file_path}")
                logger.debug(f"Tried keys: {possible_keys}")
        
        # Linus principle: Fail fast - don't save invalid records
        if not video_id:
            error_msg = f"No video_id obtained for {task.file_info.filename}. This indicates processing failed."
            logger.error(error_msg)
            raise Exception(error_msg)

        # Save video record to database
        try:
            file_size = 0
            if hasattr(task, 'file_size_metadata') and task.file_info.file_size_metadata:
                # Use blob size metadata if available
                file_size = task.file_info.file_size_metadata
            elif task.file_info.file_path and Path(task.file_info.file_path).exists():
                # Use local file size for local files
                file_size = Path(task.file_info.file_path).stat().st_size
                
            video_data = {
                'filename': task.file_info.filename,
                'original_path': task.file_info.file_path,
                'library_name': task.file_info.library_name,
                'video_id': video_id,  # Now guaranteed to be not None
                'status': 'indexed',
                'file_size': file_size,
                'source_type': task.file_info.source_type,
                'blob_url': task.file_info.file_path if task.file_info.source_type == 'blob_storage' else None,
                'blob_container': self._extract_container_from_url(task.file_info.file_path) if task.file_info.source_type == 'blob_storage' else None,
                'blob_name': self._extract_blob_name_from_url(task.file_info.file_path) if task.file_info.source_type == 'blob_storage' else None,
                'indexed_at': datetime.now().isoformat(),
                'source_language': task.file_info.source_language
            }
            db_manager.save_video_record(video_data)
            logger.info(f"Video record saved for {task.file_info.filename} with video_id: {video_id}")
        except Exception as ve:
            logger.error(f"Failed to save video record: {ve}")
            raise ve  # Re-raise to fail the task
        
        # Mark as completed
        task.task.status = TaskStatus.COMPLETED
        task.execution.progress = 100
        task.execution.current_step = "Processing completed successfully"
        task.execution.completed_at = datetime.now()
        
        # Save to database
        self._save_task_to_db(task)
        
        logger.info(f"File upload task {task_id} completed successfully")
    
    def _process_video_url_upload(self, task_id: str):
        """Process video URL upload task"""
        task = self.tasks[task_id]
        video_url = task.file_info.file_path  # URL is stored in file_path
        
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
            actual_language = task.file_info.source_language or 'auto'
            logger.info(f"Calling Azure Video Indexer with source_language: {actual_language}")
            video_id = client.upload_url_async(task.file_info.filename, video_url, wait_for_index=False, source_language=actual_language)
            
            # Wait for indexing
            self.update_task_progress(task_id, 50, "Waiting for video indexing...")
            client.wait_for_index_async(video_id)
            
            # Generate prompt content and index to vector DB
            self.update_task_progress(task_id, 70, "Processing video content...")
            sections = client.get_prompt_content_async(video_id)
            
            # Add to vector database
            prompt_content_db.set_db(task.file_info.library_name)
            prompt_content_db.add_sections_to_db(sections, upload_batch_size=100)
            
        except Exception as e:
            logger.error(f"URL processing failed for task {task_id}: {e}")
            raise
        
        # Save video record to database
        try:
            video_data = {
                'filename': task.file_info.filename,
                'original_path': video_url,
                'library_name': task.file_info.library_name,
                'status': 'indexed',
                'file_size': 0,  # Unknown for URL uploads
                'indexed_at': datetime.now().isoformat(),
                'source_language': getattr(task, 'source_language', 'auto')
            }
            db_manager.save_video_record(video_data)
            logger.info(f"Video record saved for {task.file_info.filename}")
        except Exception as ve:
            logger.warning(f"Failed to save video record: {ve}")
        
        # Mark as completed
        task.task.status = TaskStatus.COMPLETED
        task.execution.progress = 100
        task.execution.current_step = "URL processing completed successfully"
        task.execution.completed_at = datetime.now()
        
        # Save to database
        self._save_task_to_db(task)
        
        logger.info(f"URL upload task {task_id} completed successfully")
    
    def _process_video_delete(self, task_id: str):
        """Process video deletion task"""
        task = self.tasks[task_id]
        filename = task.file_info.filename
        
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
            
            # Step 1: Identify if filename is actually a video_id
            self.update_task_progress(task_id, 20, "Looking up video information...")
            real_video_id = None
            actual_filename = None
            
            # Check if the filename is actually a video_id (common case)
            library_variants = [
                task.file_info.library_name,
                task.file_info.library_name.replace('-instructions-', '-instruction-'),
                task.file_info.library_name.replace('-instruction-', '-instructions-')
            ]
            
            # First, try to find by video_id (since filename might actually be video_id)
            found_video = False
            for lib_name in library_variants:
                videos = db_manager.get_library_videos(lib_name)
                for video in videos:
                    if video.get('video_id') == filename:
                        real_video_id = video.get('video_id')
                        actual_filename = video.get('filename')
                        print(f"Found video by video_id: {real_video_id}, filename: {actual_filename}")
                        found_video = True
                        break
                    elif video.get('filename') == filename:
                        real_video_id = video.get('video_id')  # This can be None
                        actual_filename = video.get('filename')
                        print(f"Found video by filename: {actual_filename}, video_id: {real_video_id}")
                        found_video = True
                        break
                if found_video:
                    break
            
            # Step 2: Remove from vector database
            self.update_task_progress(task_id, 40, "Removing from vector database...")
            if prompt_content_db is not None:
                try:
                    # Set the database to the correct library
                    prompt_content_db.set_db(task.file_info.library_name)
                    success = False
                    
                    if real_video_id:
                        # Try deletion by video_id first
                        success = prompt_content_db.delete_video_documents(real_video_id)
                        if success:
                            logger.info(f"Successfully removed vector documents for video '{filename}' (video_id: {real_video_id})")
                        else:
                            logger.warning(f"No vector documents found for video '{filename}' (video_id: {real_video_id})")
                    
                    if not success and hasattr(prompt_content_db, 'delete_video_documents_by_filename'):
                        # Try deletion by filename if video_id deletion failed or no video_id
                        success = prompt_content_db.delete_video_documents_by_filename(filename)
                        if success:
                            logger.info(f"Successfully removed vector documents for video '{filename}' by filename")
                        else:
                            logger.warning(f"No vector documents found for video '{filename}' by filename")
                    
                except Exception as e:
                    logger.warning(f"Failed to remove vector documents for '{filename}': {e}")
                    # Don't fail the entire task if vector deletion fails
            else:
                logger.warning("Vector database not available, skipping vector deletion")
            
            # Step 3: Physically delete from database
            self.update_task_progress(task_id, 70, "Physically deleting database records...")
            success = False
            
            # Only raise exception if we couldn't find the video at all
            if not found_video:
                raise Exception(f"Cannot delete video '{filename}' - not found in any library: {library_variants}")
            
            # Delete by video_id first (if available)
            if real_video_id:
                for lib_name in library_variants:
                    success = db_manager.delete_video_record(lib_name, video_id=real_video_id)
                    if success:
                        logger.info(f"Successfully deleted video '{actual_filename or filename}' (video_id: {real_video_id}) from library '{lib_name}'")
                        break
                        
            # Fallback: try delete by filename if video_id deletion failed or no video_id
            if not success and actual_filename:
                for lib_name in library_variants:
                    success = db_manager.delete_video_record(lib_name, filename=actual_filename)
                    if success:
                        logger.info(f"Successfully deleted video '{actual_filename}' by filename from library '{lib_name}'")
                        break
            
            # Final fallback: try delete by the original filename parameter
            if not success:
                for lib_name in library_variants:
                    success = db_manager.delete_video_record(lib_name, filename=filename)
                    if success:
                        logger.info(f"Successfully deleted video '{filename}' by original filename from library '{lib_name}'")
                        break
            
            if not success:
                raise Exception(f"Failed to physically delete video '{actual_filename or filename}' (video_id: {real_video_id or 'None'}) in database. Tried library names: {library_variants}")
            
            # Step 4: Optional - Delete physical file (implement if needed)
            self.update_task_progress(task_id, 90, "Cleaning up files...")
            
            # Mark as completed
            task.task.status = TaskStatus.COMPLETED
            task.execution.progress = 100
            task.execution.current_step = "Video deletion completed successfully"
            task.execution.completed_at = datetime.now()
            
            # Save to database
            self._save_task_to_db(task)
            
            logger.info(f"Video deletion task {task_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Video deletion failed: {e}")
            raise
    
    def _process_batch_video_delete(self, task_id: str):
        """Process batch video deletion task"""
        task = self.tasks[task_id]
        video_ids = task.file_info.file_path.split(',') if task.file_info.file_path else []
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
                if task.task.status == TaskStatus.CANCELLED:
                    break
                
                try:
                    progress = 10 + (i * 80 // total_videos)
                    self.update_task_progress(task_id, progress, f"Deleting {video_id}...")
                    
                    # Remove from vector database
                    if prompt_content_db is not None:
                        try:
                            # Set the database to the correct library
                            prompt_content_db.set_db(task.file_info.library_name)
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
                        task.file_info.library_name,
                        task.file_info.library_name.replace('-instructions-', '-instruction-'),
                        task.file_info.library_name.replace('-instruction-', '-instructions-')
                    ]
                    success = False
                    
                    # Find all matching video records across all libraries (to handle duplicates)
                    matching_videos = []
                    for lib_name in library_variants:
                        videos = db_manager.get_library_videos(lib_name)
                        for video in videos:
                            if video.get('video_id') == video_id or video.get('filename') == video_id:
                                matching_videos.append({
                                    'library': lib_name,
                                    'video_id': video.get('video_id'),
                                    'filename': video.get('filename')
                                })
                    
                    if matching_videos:
                        deleted_any = False
                        for match in matching_videos:
                            lib_name = match['library']
                            real_video_id = match['video_id']
                            actual_filename = match['filename']
                            local_success = False
                            
                            # Try deletion by video_id first (if available)
                            if real_video_id:
                                local_success = db_manager.delete_video_record(lib_name, video_id=real_video_id)
                                if local_success:
                                    logger.info(f"Batch delete: Successfully deleted {actual_filename} (video_id: {real_video_id}) from {lib_name}")
                            
                            # Fallback: try deletion by filename if video_id deletion failed or no video_id
                            if not local_success and actual_filename:
                                local_success = db_manager.delete_video_record(lib_name, filename=actual_filename)
                                if local_success:
                                    logger.info(f"Batch delete: Successfully deleted {actual_filename} by filename from {lib_name}")
                            
                            # Final fallback: try deletion by the original video_id parameter
                            if not local_success:
                                local_success = db_manager.delete_video_record(lib_name, filename=video_id)
                                if local_success:
                                    logger.info(f"Batch delete: Successfully deleted {video_id} by original parameter from {lib_name}")
                            
                            if local_success:
                                deleted_any = True
                        
                        success = deleted_any
                    
                    if success:
                        deleted_count += 1
                    else:
                        logger.warning(f"Batch delete: Failed to delete {video_id} - not found or could not delete")
                        failed_videos.append(video_id)
                        
                except Exception as e:
                    logger.warning(f"Failed to delete video {video_id}: {e}")
                    failed_videos.append(video_id)
            
            # Mark as completed
            task.task.status = TaskStatus.COMPLETED
            task.execution.progress = 100
            
            if failed_videos:
                task.execution.current_step = f"Batch deletion completed with errors. Deleted: {deleted_count}, Failed: {len(failed_videos)}"
                task.execution.error_message = f"Failed to delete: {', '.join(failed_videos)}"
            else:
                task.execution.current_step = f"Batch deletion completed successfully. Deleted {deleted_count} videos"
            
            task.execution.completed_at = datetime.now()
            
            # Save to database
            self._save_task_to_db(task)
            
            logger.info(f"Batch deletion task {task_id} completed. Success: {deleted_count}, Failed: {len(failed_videos)}")
            
        except Exception as e:
            logger.error(f"Batch deletion failed: {e}")
            raise
    
    def _extract_container_from_url(self, url: str) -> str:
        """Extract container name from blob storage URL"""
        if not url or 'blob.core.windows.net' not in url:
            return None
        try:
            # URL format: https://account.blob.core.windows.net/container/blob/path?sas_token
            parts = url.split('blob.core.windows.net/')[1].split('/')
            return parts[0] if parts else None
        except:
            return None
    
    def _extract_blob_name_from_url(self, url: str) -> str:
        """Extract blob name from blob storage URL"""
        if not url or 'blob.core.windows.net' not in url:
            return None
        try:
            # URL format: https://account.blob.core.windows.net/container/blob/path?sas_token
            url_without_sas = url.split('?')[0]  # Remove SAS token
            parts = url_without_sas.split('blob.core.windows.net/')[1].split('/')
            if len(parts) > 1:
                return '/'.join(parts[1:])  # Join all parts after container name
            return None
        except:
            return None

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
