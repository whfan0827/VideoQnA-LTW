import os
import json
import sys
from pprint import pprint
from pathlib import Path
import time
from typing import Optional

# Fix Windows encoding issues
if sys.platform == "win32":
    # Set environment variables for subprocess calls
    os.environ["PYTHONIOENCODING"] = "utf-8"
    # Reconfigure stdout/stderr for proper encoding
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')

from dotenv import dotenv_values

from vi_search.constants import DATA_DIR
from vi_search.language_models.language_models import LanguageModels
from vi_search.prep_scenes import get_sections_generator
from vi_search.prompt_content_db.prompt_content_db import PromptContentDB, VECTOR_FIELD_NAME
from vi_search.vi_client.video_indexer_client import init_video_indexer_client, VideoIndexerClient
from vi_search.file_hash_cache import get_global_cache


def index_videos(client: VideoIndexerClient,
                 videos: list[str] | list[Path],
                 extensions: list = ['.mp4', '.mov', '.avi'],
                 privacy: str = 'private',
                 excluded_ai=None,
                 library_name: str = "",
                 original_filename_map: dict = None,
                 source_language: str = 'auto') -> dict[str, str]:
    start = time.time()
    videos_ids = {}
    file_cache = get_global_cache()
    
    for video_file in videos:
        video_str = str(video_file)
        
        # Fix URL format: replace backslashes with forward slashes for URLs
        # This handles cases where Windows path separators contaminate URLs
        if '://' in video_str or ':\\' in video_str:
            # This looks like a URL (either correct or with broken slashes), normalize all slashes
            video_str = video_str.replace('\\', '/')
            # Fix the protocol part if it was broken
            if video_str.startswith('https:/') and not video_str.startswith('https://'):
                video_str = video_str.replace('https:/', 'https://')
            elif video_str.startswith('http:/') and not video_str.startswith('http://'):
                video_str = video_str.replace('http:/', 'http://')
        
        # Check if it's a URL (for Blob Storage SAS URLs)
        from urllib.parse import urlparse
        parsed = urlparse(video_str)
        is_url = parsed.scheme in ('http', 'https')
        
        if is_url:
            print(f"Processing video URL: {video_str}")
            video_name = parsed.path.split('/')[-1] if parsed.path else f"video_{len(videos_ids)}"
            
            # For URLs, we can't check cache by file content, but we could check by URL hash
            # For now, proceed with upload (URLs are typically temporary SAS URLs anyway)
            try:
                video_id = client.upload_url_async(video_name, video_str, excluded_ai=excluded_ai, privacy=privacy, source_language=source_language)
                videos_ids[video_str] = video_id
                print(f"Successfully uploaded URL video, got video_id: {video_id}")
                
            except Exception as e:
                print(f"Failed to upload URL {video_str}: {str(e)}")
                continue
        else:
            # Handle as local file
            video_file = Path(video_file)

            if not video_file.exists():
                print(f"Video file not found: {video_file}. Skipping...")
                continue

            if (video_file).suffix not in extensions:
                print(f"Unsupported video format: {video_file}. Skipping...")
                continue

            print(f"Processing video: {video_file}")

            # Check if this file (by content hash) has already been processed
            cached_info = file_cache.get_cached_video_info(video_file)
            if cached_info:
                video_id = cached_info['video_id']
                print(f"Using cached video_id {video_id} for duplicate file: {video_file.name}")
                print(f"Original file: {cached_info.get('filename', 'unknown')} (cached at {cached_info.get('cached_at_readable', 'unknown')})")
                videos_ids[str(video_file)] = video_id
                continue

            # File is not cached, proceed with upload
            try:
                # Use original filename if provided, otherwise extract a meaningful name
                video_name = None
                video_path_str = str(video_file)
                
                if original_filename_map and video_path_str in original_filename_map:
                    # Use the original filename (without extension) as the video name
                    original_name = original_filename_map[video_path_str]
                    video_name = Path(original_name).stem
                    print(f"Using original filename for video name: '{video_name}'")
                else:
                    # Fallback to extracting from current filename
                    if hasattr(video_file, 'name'):
                        filename = video_file.name
                        # Check if this looks like a UUID filename (generated from Chinese names)
                        import re
                        if re.match(r'^[0-9a-f]{12}\.mp4$', filename):
                            # Use a generic name for UUID filenames
                            video_name = f"Video_{filename[:8]}"
                        else:
                            # Use the actual filename (without extension) as video name
                            video_name = Path(filename).stem
                
                video_id = client.file_upload_async(video_file, video_name=video_name, excluded_ai=excluded_ai, privacy=privacy, source_language=source_language)
                videos_ids[str(video_file)] = video_id
                
                # Cache the video_id for future duplicate detection
                file_cache.cache_video_info(
                    file_path=video_file,
                    video_id=video_id,
                    library_name=library_name,
                    additional_info={'privacy': privacy, 'upload_method': 'file'}
                )
                print(f"Cached video_id {video_id} for file: {video_file.name}")
                
            except Exception as e:
                print(f"Failed to upload {video_file}: {str(e)}")
                # Don't cache failed uploads
                continue

    print(f"Videos processed: {len(videos_ids)} files, took {time.time() - start} seconds")
    return videos_ids


def wait_for_videos_processing(client: VideoIndexerClient, videos_ids: dict, get_insights: bool = False,
                               timeout: int = 600) -> Optional[dict[str, dict]]:
    start = time.time()

    if not videos_ids:
        print("No videos to wait for processing (empty videos_ids)")
        return {}

    videos_left = list(videos_ids.keys())
    insights = {}
    print(f"Waiting for {len(videos_left)} videos to complete processing...")
    
    # Add a mechanism to check if we should continue processing
    def should_continue_processing():
        # This function can be extended to check task status if needed
        # For now, just continue unless there's a critical error
        return True
    
    while True:
        # Check if we should continue
        if not should_continue_processing():
            print("Processing interrupted by external signal")
            break
        # Copy the list to avoid modifying it while iterating
        for video_file in videos_left[:]:
            try:
                video_id = videos_ids[video_file]
                print(f"Checking processing status for video {video_id}...")
                res = client.is_video_processed(video_id)
                if res:
                    print(f"Video {video_file} (ID: {video_id}) processing completed.")
                    videos_left.remove(video_file)
                    if get_insights:
                        insights[video_file] = client.get_video_async(video_id)
                else:
                    print(f"Video {video_id} still processing...")
            except Exception as e:
                elapsed = time.time() - start  # Fix: Calculate elapsed time here
                error_str = str(e)
                print(f"Error checking video processing status for {video_file} (ID: {videos_ids.get(video_file, 'unknown')}): {e}")
                
                # Handle specific error cases
                if "404" in error_str or "Not Found" in error_str:
                    print(f"Video {video_id} not found in Video Indexer (404). It may have been deleted or expired.")
                    print(f"Removing {video_file} from processing queue.")
                    videos_left.remove(video_file)
                elif "400" in error_str or "Bad Request" in error_str:
                    print(f"Video {video_id} returned Bad Request (400). The video may be in an invalid state.")
                    print(f"Removing {video_file} from processing queue.")
                    videos_left.remove(video_file)
                elif "Video processing failed or unavailable" in error_str and ("Failed" in error_str or "Unavailable" in error_str):
                    print(f"Video {video_id} processing permanently failed in Azure Video Indexer.")
                    print(f"This video cannot be processed and will be removed from the queue.")
                    print(f"Error details: {error_str}")
                    print(f"Removing {video_file} from processing queue.")
                    videos_left.remove(video_file)
                elif "401" in error_str or "403" in error_str or "Unauthorized" in error_str:
                    print(f"Authentication error for video {video_id}. This might be a token expiry issue.")
                    if elapsed > 1800:  # After 30 minutes, give up on auth errors
                        print(f"Removing {video_file} due to persistent authentication errors.")
                        videos_left.remove(video_file)
                    else:
                        print("Will retry checking status in next iteration...")
                elif elapsed > 3600:  # After 1 hour of waiting, be more strict about errors
                    print(f"Marking video {video_file} as failed due to persistent connection errors after 1 hour")
                    videos_left.remove(video_file)
                else:
                    print("Will retry checking status in next iteration...")
                    # Don't remove from list, will retry

        elapsed = time.time() - start
        if elapsed > timeout:
            remaining_videos = [f"{vf} (ID: {videos_ids[vf]})" for vf in videos_left]
            raise TimeoutError(f"Timeout reached after {timeout}s. Videos left to process: {remaining_videos}")

        # Progressive reporting: more frequent initially, then less frequent
        if elapsed % 60 == 0 and elapsed > 0:  # Report every minute
            remaining_count = len(videos_left)
            remaining_videos = [f"{vf} (ID: {videos_ids[vf]})" for vf in videos_left[:3]]  # Show first 3
            print(f"Elapsed time: {elapsed/60:.1f} minutes. Videos still processing ({remaining_count}): {remaining_videos}")

        if not videos_left:
            break

        time.sleep(10)  # Check every 10 seconds instead of 1

    print(f"Videos processing completed, took {time.time() - start} seconds")

    if get_insights:
        return insights


class CustomEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Path):
            return str(o)
        return super().default(o)  # Use default serialization for other types


def prepare_db(db_name, data_dir, language_models: LanguageModels, prompt_content_db: PromptContentDB,
               use_videos_ids_cache=True, video_ids_cache_file='videos_ids_cache.json', verbose=False, 
               single_video_file=None):
    # Wrapper for backward compatibility
    return prepare_db_with_progress(
        db_name=db_name,
        data_dir=data_dir,
        language_models=language_models,
        prompt_content_db=prompt_content_db,
        use_videos_ids_cache=use_videos_ids_cache,
        video_ids_cache_file=video_ids_cache_file,
        verbose=verbose,
        single_video_file=single_video_file,
        progress_callback=None
    )


def prepare_db_with_progress(db_name, data_dir, language_models: LanguageModels, prompt_content_db: PromptContentDB,
                           use_videos_ids_cache=True, video_ids_cache_file='videos_ids_cache.json', verbose=False, 
                           single_video_file=None, progress_callback=None, original_filename=None, source_language='auto'):

    # If single_video_file is provided, process only that file
    if single_video_file:
        videos = [Path(single_video_file)]
    else:
        # Support multiple video formats
        video_extensions = ['*.mp4', '*.mov', '*.avi', '*.mkv']
        videos = []
        for ext in video_extensions:
            videos.extend(list(data_dir.glob(ext)))
    
    video_ids_cache_file = Path(video_ids_cache_file)

    if progress_callback:
        progress_callback("Initializing Video Indexer client...", 10)

    ### Initialization ###
    try:
        # .env file is in the backend directory
        env_path = Path(__file__).parent.parent / ".env"
        config = dotenv_values(env_path)
        print(f"Loading .env from: {env_path}")
        print(f"Found AccountName: {config.get('AccountName')}")
    except FileNotFoundError:
        ''' Expects a file with the following text (Taken from Azure Portal):
                AccountName='YOUR_VI_ACCOUNT_NAME'
                ResourceGroup='RESOURCE_GROUP_NAME'
                SubscriptionId='SUBSCRIPTION_ID'
        '''
        raise FileNotFoundError("Please provide .env file with Video Indexer keys")

    client = init_video_indexer_client(config)

    if progress_callback:
        progress_callback("Uploading to Azure Video Indexer...", 20)

    ### Indexing Videos or getting indexed videos IDs ###
    if use_videos_ids_cache and video_ids_cache_file.exists():
        print(f"Using cached videos IDs from {video_ids_cache_file}")
        videos_ids = json.loads(video_ids_cache_file.read_text())
    else:
        # Setting privacy to 'public' allows much simpler access to the videos by the UI (No need for VI keys),
        # this should be used with *caution*.
        
        # Create filename mapping if original filename is provided
        original_filename_map = {}
        if original_filename and single_video_file:
            original_filename_map[single_video_file] = original_filename
        
        videos_ids = index_videos(client, videos=videos, privacy='public', library_name=db_name, 
                                 original_filename_map=original_filename_map, source_language=source_language)
        if use_videos_ids_cache:
            print(f"Saving videos IDs to {video_ids_cache_file}")
            video_ids_cache_file.write_text(json.dumps(videos_ids, cls=CustomEncoder))

    if progress_callback:
        progress_callback("Waiting for Video Indexer processing... (this may take 15-60 minutes)", 30)

    wait_for_videos_processing(client, videos_ids, timeout=3600)

    if progress_callback:
        progress_callback("Generating AI-powered content analysis... (this may take 30-120 minutes for longer videos)", 50)

    ### Getting indexed videos prompt content ###
    videos_prompt_content = client.get_collection_prompt_content(list(videos_ids.values()), timeout_sec=7200)

    if verbose:
        for video_id, prompt_content in videos_prompt_content.items():
            print(f"Video ID: {video_id}")
            pprint(prompt_content)
            print()

    ### Prepare language models ###

    embeddings_size = language_models.get_embeddings_size()

    if progress_callback:
        progress_callback("Generating embeddings and preparing content...", 70)

    ### Adding prompt content sections ###
    account_details = client.get_account_details()
    sections_generator = get_sections_generator(videos_prompt_content, account_details, embedding_cb=language_models.get_text_embeddings,
                                                embeddings_col_name=VECTOR_FIELD_NAME)

    if progress_callback:
        progress_callback("Creating database and storing vectors...", 80)

    ### Creating new DB ###
    prompt_content_db.create_db(db_name, vector_search_dimensions=embeddings_size)
    
    # Enhanced section storage with progress tracking
    if progress_callback:
        sections_list = list(sections_generator)  # Convert generator to list for progress tracking
        total_sections = len(sections_list)
        
        def progress_sections_generator():
            for i, section in enumerate(sections_list):
                if i % 10 == 0:  # Update every 10 sections
                    current_progress = 80 + int((i / total_sections) * 15)  # 80-95% range
                    progress_callback(f"Storing section {i+1}/{total_sections} to database...", current_progress)
                yield section
        
        prompt_content_db.add_sections_to_db(progress_sections_generator(), upload_batch_size=100, verbose=verbose)
        progress_callback("Processing completed successfully", 100)
    else:
        prompt_content_db.add_sections_to_db(sections_generator, upload_batch_size=100, verbose=verbose)

    print("Done adding sections to DB. Exiting...")
    
    # Return the videos_ids mapping so caller can get the video_id
    return videos_ids


def main():
    '''
    Two options to run this script:
    1. Put your videos in the data directory and run the script.
    2. Create JSON file with the following structure:
           {"VIDEO_1_NAME": "VIDEO_1_ID",
            "VIDEO_2_NAME": "VIDEO_2_ID"}
       and run the script while calling `prepate_db()` with arguments:
            `use_videos_ids_cache=True`
            `video_ids_cache_file="path_to_json_file"`.

        Important note: If you choose ChromaDB as a your prompt content DB, you need to make sure the DB location which
                        is by default on local disk is accessible by the Azure Function App.
    '''
    print("This program will prepare a vector DB for LLM queries using the Video Indexer prompt content API")

    verbose = True

    # For UI parsing keep the name in the format: "vi-<your-name>-index"
    db_name = os.environ.get("PROMPT_CONTENT_DB_NAME", "vi-prompt-content-example-index")

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

    prepare_db(db_name, DATA_DIR, language_models, prompt_content_db, verbose=verbose)


if __name__ == "__main__":
    main()
