#!/usr/bin/env python3
"""
簡單診斷工具：檢查卡住的任務並嘗試手動完成
"""

import sys
sys.path.append('.')

from task_manager import TaskManager
from models.task_models import TaskStatus

def debug_and_fix_stuck_task():
    """找到卡住的任務並嘗試解決"""
    
    tm = TaskManager()
    all_tasks = tm.list_all_tasks()
    
    print("=== Current Tasks Status ===")
    for task in all_tasks:
        filename = task.file_info.filename if task.file_info else 'N/A'
        print(f"Task: {task.task_id[:8]}... | File: {filename} | Status: {task.status} | Progress: {task.progress}%")
        if task.status == TaskStatus.PROCESSING:
            print(f"  Current Step: {task.execution.current_step}")
            if 'YT2' in filename:
                print("  ^^ This is the stuck YT2 task!")
                
                # Since you said Azure shows it's completed, let's manually complete it
                print("\n=== Manual Task Completion ===")
                print("Since Azure Video Indexer shows the video as completed,")
                print("but our task is stuck in waiting, this suggests a bug in the waiting logic.")
                print("\nOptions:")
                print("1. Cancel the stuck task")
                print("2. Mark as completed manually") 
                print("3. Let it continue (might be stuck forever)")
                
                choice = input("Enter your choice (1/2/3): ").strip()
                
                if choice == "1":
                    print("Cancelling task...")
                    success = tm.cancel_task(task.task_id)
                    print(f"Cancel result: {success}")
                    
                elif choice == "2":
                    print("Marking task as completed...")
                    # Mark as completed
                    task.task.status = TaskStatus.COMPLETED
                    task.execution.progress = 100
                    task.execution.current_step = "Manually marked as completed (Azure shows processed)"
                    from datetime import datetime
                    task.execution.completed_at = datetime.now()
                    
                    # Save to database  
                    tm._save_task_to_db(task)
                    print("Task marked as completed!")
                    
                elif choice == "3":
                    print("Leaving task as-is...")
                else:
                    print("Invalid choice")
                    
                break
    
    print("\n=== Post-action Task Status ===")
    all_tasks = tm.list_all_tasks()
    for task in all_tasks:
        filename = task.file_info.filename if task.file_info else 'N/A'
        if 'YT2' in filename:
            print(f"YT2 Task: {task.task_id[:8]}... | Status: {task.status} | Progress: {task.progress}%")

if __name__ == "__main__":
    debug_and_fix_stuck_task()