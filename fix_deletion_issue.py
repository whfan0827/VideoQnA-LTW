#!/usr/bin/env python3
"""
Fix script for video deletion issues in production environment
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

# Import necessary modules
from database.app_data_manager import db_manager

def fix_null_video_ids():
    """Fix videos with NULL video_id which cause deletion failures"""
    print("=== Fixing NULL video_id records ===")
    
    library_variants = [
        'vi-machine-instruction-index',
        'vi-machine-instructions-index'
    ]
    
    for lib_name in library_variants:
        try:
            videos = db_manager.get_library_videos(lib_name)
            print(f"\nChecking library: {lib_name}")
            print(f"Found {len(videos)} videos")
            
            null_video_id_count = 0
            for video in videos:
                if not video.get('video_id'):
                    null_video_id_count += 1
                    print(f"  Found NULL video_id: {video.get('filename', 'Unknown')}")
                    
                    # Delete this record as it's corrupted
                    filename = video.get('filename')
                    if filename:
                        success = db_manager.delete_video_record(lib_name, filename=filename)
                        if success:
                            print(f"    ✓ Deleted corrupted record for {filename}")
                        else:
                            print(f"    ✗ Failed to delete corrupted record for {filename}")
            
            print(f"Total NULL video_id records processed: {null_video_id_count}")
            
        except Exception as e:
            print(f"Error processing library {lib_name}: {e}")

def manual_batch_delete():
    """Manually perform batch deletion since tasks are not working"""
    print("\n=== Manual Batch Deletion ===")
    
    # Initialize vector database components directly
    try:
        import os
        from dotenv import load_dotenv
        
        # Load environment variables
        load_dotenv()
        search_db = os.environ.get("PROMPT_CONTENT_DB", "azure_search")
        
        if search_db == "chromadb":
            from vi_search.prompt_content_db.chroma_db import ChromaDB
            prompt_content_db = ChromaDB()
            print("Initialized ChromaDB for manual deletion")
        elif search_db == "azure_search":
            from vi_search.prompt_content_db.azure_search import AzureVectorSearch
            prompt_content_db = AzureVectorSearch()
            print("Initialized Azure Search for manual deletion")
        else:
            raise ValueError(f"Unknown search_db: {search_db}")
            
    except Exception as e:
        print(f"Failed to initialize vector database: {e}")
        prompt_content_db = None
    
    library_name = 'vi-machine-instructions-index'
    
    try:
        videos = db_manager.get_library_videos(library_name)
        print(f"Found {len(videos)} videos in {library_name}")
        
        deleted_count = 0
        for video in videos:
            filename = video.get('filename', 'Unknown')
            video_id = video.get('video_id')
            
            print(f"\nProcessing: {filename}")
            print(f"Video ID: {video_id}")
            
            try:
                # Remove from vector database
                if prompt_content_db is not None:
                    try:
                        prompt_content_db.set_db(library_name)
                        success = False
                        
                        if video_id:
                            success = prompt_content_db.delete_video_documents(video_id)
                            if success:
                                print(f"  ✓ Removed vector documents for video_id: {video_id}")
                            else:
                                print(f"  ⚠ No vector documents found for video_id: {video_id}")
                        
                        if not success and hasattr(prompt_content_db, 'delete_video_documents_by_filename'):
                            success = prompt_content_db.delete_video_documents_by_filename(filename)
                            if success:
                                print(f"  ✓ Removed vector documents for filename: {filename}")
                            else:
                                print(f"  ⚠ No vector documents found for filename: {filename}")
                        
                    except Exception as e:
                        print(f"  ⚠ Failed to remove vector documents: {e}")
                else:
                    print("  ⚠ Vector database not available, skipping vector deletion")
                
                # Remove from database
                if video_id:
                    success = db_manager.delete_video_record(library_name, video_id=video_id)
                    if success:
                        print(f"  ✓ Deleted database record by video_id: {video_id}")
                        deleted_count += 1
                        continue
                
                # Fallback: delete by filename
                success = db_manager.delete_video_record(library_name, filename=filename)
                if success:
                    print(f"  ✓ Deleted database record by filename: {filename}")
                    deleted_count += 1
                else:
                    print(f"  ✗ Failed to delete database record: {filename}")
                
            except Exception as e:
                print(f"  ✗ Error processing {filename}: {e}")
        
        print(f"\n=== Manual Deletion Summary ===")
        print(f"Total videos processed: {len(videos)}")
        print(f"Successfully deleted: {deleted_count}")
        print(f"Failed: {len(videos) - deleted_count}")
        
    except Exception as e:
        print(f"Error during manual batch deletion: {e}")

def verify_cleanup():
    """Verify that the cleanup was successful"""
    print("\n=== Verification ===")
    
    library_variants = [
        'vi-machine-instruction-index',
        'vi-machine-instructions-index'
    ]
    
    for lib_name in library_variants:
        try:
            videos = db_manager.get_library_videos(lib_name)
            print(f"{lib_name}: {len(videos)} videos remaining")
            
            for video in videos:
                print(f"  - {video.get('filename', 'Unknown')} (ID: {video.get('video_id', 'None')})")
                
        except Exception as e:
            print(f"Error checking {lib_name}: {e}")

def main():
    print("=== VideoQnA-LTW Deletion Issue Fix Script ===")
    print(f"Started at: {datetime.now()}")
    print()
    
    # Step 1: Fix NULL video_id records
    fix_null_video_ids()
    
    # Step 2: Manual batch deletion
    manual_batch_delete()
    
    # Step 3: Verify cleanup
    verify_cleanup()
    
    print(f"\n=== Fix Script Completed at: {datetime.now()} ===")

if __name__ == "__main__":
    main()