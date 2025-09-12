#!/usr/bin/env python3
"""
Debugging script to check task status and identify deletion issues
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add backend to path
backend_dir = Path(__file__).parent / "app" / "backend"
sys.path.append(str(backend_dir))
os.chdir(str(backend_dir))

# Load environment
from dotenv import load_dotenv
load_dotenv()

# Import database manager
from database.app_data_manager import db_manager
from task_manager import task_manager

def main():
    print("=== Task Manager Debug Report ===")
    print(f"Generated at: {datetime.now()}")
    print()
    
    # Check active tasks
    print("1. Active Tasks:")
    active_tasks = task_manager.list_active_tasks()
    if active_tasks:
        for task in active_tasks:
            print(f"  Task ID: {task.task.task_id}")
            print(f"  Type: {task.task.task_type}")
            print(f"  Status: {task.task.status}")
            print(f"  Progress: {task.execution.progress}%")
            print(f"  Current Step: {task.execution.current_step}")
            print(f"  Created: {task.task.created_at}")
            if task.execution.error_message:
                print(f"  Error: {task.execution.error_message}")
            print()
    else:
        print("  No active tasks found")
    
    print()
    
    # Check all tasks
    print("2. All Tasks (Last 10):")
    all_tasks = task_manager.list_all_tasks()
    recent_tasks = sorted(all_tasks, key=lambda t: t.task.created_at, reverse=True)[:10]
    
    if recent_tasks:
        for task in recent_tasks:
            print(f"  Task ID: {task.task.task_id[:8]}...")
            print(f"  Type: {task.task.task_type}")
            print(f"  Status: {task.task.status}")
            print(f"  Library: {task.file_info.library_name if task.file_info else 'N/A'}")
            print(f"  Created: {task.task.created_at}")
            if task.task.status in ['completed', 'failed']:
                print(f"  Completed: {task.execution.completed_at}")
            if task.execution.error_message:
                print(f"  Error: {task.execution.error_message}")
            print()
    else:
        print("  No tasks found")
    
    print()
    
    # Check machine instruction library
    print("3. Machine Instruction Library Status:")
    try:
        # Try different library name variants
        library_variants = [
            'vi-machine-instruction-index',
            'vi-machine-instructions-index'
        ]
        
        for lib_name in library_variants:
            try:
                videos = db_manager.get_library_videos(lib_name)
                print(f"  {lib_name}: {len(videos)} videos")
                for i, video in enumerate(videos[:3], 1):
                    print(f"    {i}. {video.get('filename', 'N/A')} (ID: {video.get('video_id', 'N/A')})")
                if len(videos) > 3:
                    print(f"    ... and {len(videos) - 3} more videos")
                print()
            except Exception as e:
                print(f"  Error accessing {lib_name}: {e}")
                
    except Exception as e:
        print(f"  Error checking machine instruction library: {e}")
    
    print()
    
    # Check processing queue
    print("4. Task Manager Status:")
    print(f"  Current processing: {task_manager.current_processing}/{task_manager.max_concurrent}")
    print(f"  Queue length: {len(task_manager.processing_queue)}")
    print(f"  Worker thread alive: {task_manager.worker_thread.is_alive()}")
    print(f"  Cleanup thread alive: {task_manager.cleanup_thread.is_alive()}")
    print()
    
    # Check recent batch delete tasks specifically
    print("5. Recent Batch Delete Tasks:")
    batch_delete_tasks = [t for t in recent_tasks if t.task.task_type == 'batch_video_delete']
    if batch_delete_tasks:
        for task in batch_delete_tasks[:5]:
            print(f"  Task ID: {task.task.task_id}")
            print(f"  Status: {task.task.status}")
            print(f"  Library: {task.file_info.library_name}")
            print(f"  Videos: {task.file_info.filename}")
            print(f"  Video IDs: {task.file_info.file_path}")
            print(f"  Progress: {task.execution.progress}%")
            print(f"  Step: {task.execution.current_step}")
            if task.execution.error_message:
                print(f"  Error: {task.execution.error_message}")
            print(f"  Created: {task.task.created_at}")
            if task.execution.completed_at:
                print(f"  Completed: {task.execution.completed_at}")
            print()
    else:
        print("  No batch delete tasks found")

if __name__ == "__main__":
    main()