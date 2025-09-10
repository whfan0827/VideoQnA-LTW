#!/usr/bin/env python3
"""
診斷工具：檢查 Azure Video Indexer 的實際狀態
"""

import sys
import os
sys.path.append('.')

from dotenv import load_dotenv
load_dotenv()

from vi_search.vi_client.video_indexer_client import get_video_indexer_client_by_index
from vi_search.constants import BASE_DIR, BACKEND_DIR
from dotenv import dotenv_values

def debug_video_status():
    """檢查卡住的視頻狀態"""
    
    # First get the stuck task info
    from task_manager import TaskManager
    tm = TaskManager()
    all_tasks = tm.list_all_tasks()
    
    stuck_task = None
    for task in all_tasks:
        if task.status.value == 'processing' and 'YT2' in (task.file_info.filename if task.file_info else ''):
            stuck_task = task
            break
    
    if not stuck_task:
        print("No stuck YT2 task found")
        return
    
    print(f"Found stuck task: {stuck_task.task_id}")
    print(f"File: {stuck_task.file_info.filename}")
    print(f"Step: {stuck_task.execution.current_step}")
    
    # Load configuration
    env_path = BACKEND_DIR / ".env"
    print(f"Loading config from: {env_path}")
    config = dotenv_values(env_path)
    
    if not config.get('AccountName'):
        print("ERROR: AccountName not found in config!")
        return
        
    client = get_video_indexer_client_by_index(config)
    
    # Now we need to figure out the video ID for this task
    # The task is stuck in wait_for_videos_processing, which means it has a video_id
    # Let's check if we can get it from the database or logs
    print("Checking video processing status...")
    
    try:
        # Try to get the video by calling the same prepare_db logic but with debugging
        
        target_videos = []
        for video in videos:
            name = video.get('name', '')
            video_id = video.get('id', '')
            state = video.get('state', 'Unknown')
            created = video.get('created', 'Unknown')
            
            if 'YT2' in name or 'talkshow' in name.lower() or any(char in name for char in ['\u5927', '\u6230', '\u7dda']):
                target_videos.append({
                    'name': name,
                    'id': video_id, 
                    'state': state,
                    'created': created
                })
                print(f"Found: {name} (ID: {video_id}) - State: {state}")
        
        if not target_videos:
            print("No matching videos found. Showing all recent videos:")
            for video in videos[:10]:  # Show first 10
                name = video.get('name', 'Unknown')
                video_id = video.get('id', '')
                state = video.get('state', 'Unknown')
                print(f"  {name} (ID: {video_id}) - State: {state}")
        else:
            # Check detailed status for each target video
            print("\nDetailed status check:")
            for video in target_videos:
                video_id = video['id']
                print(f"\nChecking video ID: {video_id}")
                try:
                    is_processed = client.is_video_processed(video_id)
                    print(f"  is_video_processed() result: {is_processed}")
                    
                    # Get raw index data
                    print(f"  Getting raw index data...")
                    raw_data = client.get_video_async(video_id)
                    if raw_data:
                        actual_state = raw_data.get('state', 'Unknown')
                        processing_progress = raw_data.get('processingProgress', 'Unknown')
                        print(f"  Raw state: {actual_state}")
                        print(f"  Processing progress: {processing_progress}")
                        
                        # Show insights availability
                        if 'insights' in raw_data:
                            insights = raw_data['insights']
                            print(f"  Has insights: Yes")
                            print(f"  Insights keys: {list(insights.keys()) if insights else 'None'}")
                        else:
                            print(f"  Has insights: No")
                    
                except Exception as e:
                    print(f"  Error checking video {video_id}: {e}")
                    
    except Exception as e:
        print(f"Error getting videos: {e}")
        return
    
    print(f"\n=== Diagnosis Complete ===")

if __name__ == "__main__":
    debug_video_status()