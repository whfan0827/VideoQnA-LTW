"""
Task Domain Models

Refactored task-related data structures following single responsibility principle.
Each class has a clear, focused purpose.
"""

from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from typing import Optional
from config import AppConfig


class TaskStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Task:
    """
    Core task entity with essential identification and status.
    Contains only the most fundamental task information.
    """
    task_id: str
    task_type: str
    status: TaskStatus
    created_at: datetime
    
    def to_dict(self):
        return {
            'task_id': self.task_id,
            'task_type': self.task_type,
            'status': self.status.value,
            'created_at': self.created_at.isoformat()
        }


@dataclass
class TaskExecution:
    """
    Task execution tracking information.
    Handles runtime state and progress.
    """
    task_id: str
    progress: int = 0  # 0-100
    current_step: str = ""
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    def to_dict(self):
        return {
            'task_id': self.task_id,
            'progress': self.progress,
            'current_step': self.current_step,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'error_message': self.error_message
        }


@dataclass
class TaskRetryPolicy:
    """
    Retry logic and failure handling.
    Separated from core task data.
    """
    task_id: str
    retry_count: int = 0
    max_retries: int = AppConfig.TASK_RETRY_MAX
    
    def can_retry(self) -> bool:
        return self.retry_count < self.max_retries
    
    def increment_retry(self):
        self.retry_count += 1


@dataclass
class FileTask:
    """
    File-specific task information.
    Only contains file-related data.
    """
    task_id: str
    filename: str
    library_name: str
    file_path: Optional[str] = None
    file_size_metadata: Optional[int] = None
    source_type: str = "local_file"
    source_language: str = "auto"
    
    def to_dict(self):
        return {
            'task_id': self.task_id,
            'filename': self.filename,
            'library_name': self.library_name,
            'file_path': self.file_path,
            'file_size_metadata': self.file_size_metadata,
            'source_type': self.source_type,
            'source_language': self.source_language
        }


@dataclass
class TaskInfo:
    """
    Composite task information for backward compatibility.
    Combines all task-related data but delegates to specialized classes.
    """
    task: Task
    execution: TaskExecution
    retry_policy: TaskRetryPolicy
    file_info: Optional[FileTask] = None
    
    @property
    def task_id(self) -> str:
        return self.task.task_id
    
    @property
    def status(self) -> TaskStatus:
        return self.task.status
    
    @property
    def progress(self) -> int:
        return self.execution.progress
    
    def to_dict(self):
        """
        Provides backward compatibility with the old flat structure
        """
        result = {}
        result.update(self.task.to_dict())
        result.update(self.execution.to_dict())
        result.update({
            'retry_count': self.retry_policy.retry_count,
            'max_retries': self.retry_policy.max_retries
        })
        
        if self.file_info:
            file_dict = self.file_info.to_dict()
            # Remove duplicate task_id
            file_dict.pop('task_id', None)
            result.update(file_dict)
        
        return result
    
    @classmethod
    def create_file_task(cls, task_id: str, task_type: str, filename: str, 
                        library_name: str, **kwargs):
        """
        Factory method for creating file processing tasks
        """
        task = Task(
            task_id=task_id,
            task_type=task_type,
            status=TaskStatus.PENDING,
            created_at=datetime.now()
        )
        
        execution = TaskExecution(task_id=task_id)
        retry_policy = TaskRetryPolicy(task_id=task_id)
        
        file_info = FileTask(
            task_id=task_id,
            filename=filename,
            library_name=library_name,
            **kwargs
        )
        
        return cls(
            task=task,
            execution=execution,
            retry_policy=retry_policy,
            file_info=file_info
        )
    
    @classmethod
    def create_generic_task(cls, task_id: str, task_type: str, current_step: str = ""):
        """
        Factory method for creating generic tasks (non-file tasks)
        """
        task = Task(
            task_id=task_id,
            task_type=task_type,
            status=TaskStatus.PENDING,
            created_at=datetime.now()
        )
        
        execution = TaskExecution(
            task_id=task_id,
            current_step=current_step
        )
        retry_policy = TaskRetryPolicy(task_id=task_id)
        
        return cls(
            task=task,
            execution=execution,
            retry_policy=retry_policy,
            file_info=None
        )
    
    @classmethod
    def create_url_task(cls, task_id: str, filename: str, library_name: str, 
                       video_url: str, source_language: str = "auto"):
        """
        Factory method for creating URL upload tasks
        """
        return cls.create_file_task(
            task_id=task_id,
            task_type="video_url_upload",
            filename=filename,
            library_name=library_name,
            file_path=video_url,
            source_type="url",
            source_language=source_language
        )
    
    @classmethod
    def from_dict(cls, data: dict):
        """
        Create TaskInfo from dictionary (backward compatibility)
        """
        task = Task(
            task_id=data['task_id'],
            task_type=data['task_type'],
            status=TaskStatus(data['status']) if isinstance(data['status'], str) else data['status'],
            created_at=datetime.fromisoformat(data['created_at']) if isinstance(data['created_at'], str) else data['created_at']
        )
        
        execution = TaskExecution(
            task_id=data['task_id'],
            progress=data.get('progress', 0),
            current_step=data.get('current_step', ''),
            started_at=datetime.fromisoformat(data['started_at']) if data.get('started_at') else None,
            completed_at=datetime.fromisoformat(data['completed_at']) if data.get('completed_at') else None,
            error_message=data.get('error_message')
        )
        
        retry_policy = TaskRetryPolicy(
            task_id=data['task_id'],
            retry_count=data.get('retry_count', 0),
            max_retries=data.get('max_retries', AppConfig.TASK_RETRY_MAX)
        )
        
        file_info = None
        if data.get('filename'):
            file_info = FileTask(
                task_id=data['task_id'],
                filename=data['filename'],
                library_name=data.get('library_name', ''),
                file_path=data.get('file_path'),
                file_size_metadata=data.get('file_size_metadata'),
                source_type=data.get('source_type', 'local_file'),
                source_language=data.get('source_language', 'auto')
            )
        
        return cls(
            task=task,
            execution=execution,
            retry_policy=retry_policy,
            file_info=file_info
        )