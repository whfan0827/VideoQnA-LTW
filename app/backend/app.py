import logging
import os
import re
import uuid
import sys
from pathlib import Path
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from datetime import datetime

# Fix Windows encoding issues
if sys.platform == "win32":
    # Set environment variables for subprocess calls
    os.environ["PYTHONIOENCODING"] = "utf-8"
    # Reconfigure stdout/stderr for proper encoding
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')

from flask import Flask, request, jsonify

# Import security configuration
try:
    from security import configure_security, configure_logging_security
    configure_logging_security()
except ImportError:
    # Security module not available in development
    def configure_security(app):
        return app

# Setup logging system
log_dir = Path(__file__).parent / "logs"
log_dir.mkdir(exist_ok=True)

# Configure log format and handlers
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(
            log_dir / f"app_{datetime.now().strftime('%Y%m%d')}.log",
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)

# Set log levels for specific modules
logging.getLogger('task_manager').setLevel(logging.INFO)
logging.getLogger('database.app_data_manager').setLevel(logging.INFO)
logging.getLogger('vi_search').setLevel(logging.INFO)

logger = logging.getLogger(__name__)
logger.info("Application starting with enhanced logging system")

# Load environment variables from .env file
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from vi_search.ask import RetrieveThenReadVectorApproach
from vi_search.constants import DATA_DIR
from services.settings_service import SettingsService
from services.ai_template_service import AITemplateService, init_ai_templates_database
from services.conversation_starters_service import conversation_starters_service
from task_manager import task_manager
from database.app_data_manager import db_manager
from database.init_db import init_database


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


ask_approaches = {
    "rrrv": RetrieveThenReadVectorApproach(prompt_content_db=prompt_content_db, language_models=language_models)
}

# Initialize settings service
settings_service = SettingsService()

# Initialize AI template service
ai_template_service = AITemplateService()

app = Flask(__name__, static_folder='static', static_url_path='')

# Apply security configuration
app = configure_security(app)

# Initialize database on startup
try:
    init_database()
    print("Database initialized successfully")
    init_ai_templates_database()
    print("AI templates database initialized successfully")
    
    # Initialize conversation starters
    from database.migrate_conversation_starters import migrate_conversation_starters
    migrate_conversation_starters()
    print("Conversation starters database initialized successfully")
except Exception as e:
    print(f"Database initialization error: {e}")
    # Continue anyway as the database might already exist

# The limiter is used to prevent abuse of the API, you can adjust the limits as needed
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["300000 per day", "20000 per hour"],
    storage_uri="memory://",
)
ASK_RATE_LIMIT_PER_DAY = 1000
ASK_RATE_LIMIT_PER_MIN = 50


@app.route("/")
def index():
    return app.send_static_file('index.html')

@app.route("/assets/<path:filename>")
def assets(filename):
    return app.send_static_file(f'assets/{filename}')

@app.route("/favicon.ico")
def favicon():
    return app.send_static_file('favicon.ico')


@app.route("/ask", methods=["POST"])
@limiter.limit(f"{ASK_RATE_LIMIT_PER_DAY}/day;{ASK_RATE_LIMIT_PER_MIN}/minute", override_defaults=True)
def ask():
    if not request.json:
        return jsonify({"error": "Invalid JSON"}), 400
        
    approach = request.json.get("approach")
    if not approach:
        return jsonify({"error": "Approach is required"}), 400
        
    try:
        impl = ask_approaches.get(approach)
        if impl is None:
            return jsonify({"error": "unknown approach"}), 400

        # Get overrides from request
        overrides = request.json.get("overrides") or {}
        
        # Get library name from overrides (the index name corresponds to library)
        library_name = overrides.get("index", "default")
        print(f"[DEBUG] Received library_name from overrides: {library_name}")
        
        # Load library settings and merge with overrides
        try:
            library_settings = settings_service.get_settings(library_name)
            # Library settings take precedence over defaults, but request overrides take precedence over both
            merged_overrides = {**library_settings, **overrides}
            print(f"[DEBUG] Merged overrides keys: {list(merged_overrides.keys())}")
        except Exception as e:
            print(f"Warning: Could not load settings for library '{library_name}': {e}")
            merged_overrides = overrides

        # print(f"question: {request.json['question']}")
        r = impl.run(request.json.get("question", ""), merged_overrides)
        print(f"response: {r['answer']}\n\n")
        # print(f"response: {r}\n\n")
        return jsonify(r)

    except Exception as e:
        logging.exception("Exception in /ask")
        return jsonify({"error": str(e)}), 500


@app.route("/indexes", methods=["GET"])
def get_indexes():
    indexes = prompt_content_db.get_available_dbs()
    return jsonify(indexes)


@app.route("/libraries", methods=["POST"])
def create_library():
    """Create a new video library (database)"""
    try:
        data = request.get_json()
        if not data or 'name' not in data:
            return jsonify({"error": "Library name is required"}), 400
        
        library_name = data['name']
        
        # Validate library name format
        if not library_name.startswith('vi-') or not library_name.endswith('-index'):
            return jsonify({"error": "Library name must start with 'vi-' and end with '-index'"}), 400
        
        # Create empty database
        embeddings_size = language_models.get_embeddings_size()
        prompt_content_db.create_db(library_name, embeddings_size)
        
        return jsonify({"message": f"Library '{library_name}' created successfully"}), 201
        
    except Exception as e:
        logging.exception("Exception in /libraries POST")
        return jsonify({"error": str(e)}), 500


@app.route("/libraries/<library_name>", methods=["DELETE"]) 
def delete_library(library_name):
    """Delete a video library (database)"""
    try:
        # Check if library exists
        available_dbs = prompt_content_db.get_available_dbs()
        if library_name not in available_dbs:
            return jsonify({"error": "Library not found"}), 404
        
        # Delete the database
        prompt_content_db.remove_db(library_name)
        
        return jsonify({"message": f"Library '{library_name}' deleted successfully"}), 200
        
    except Exception as e:
        logging.exception("Exception in /libraries DELETE")
        return jsonify({"error": str(e)}), 500


@app.route("/upload", methods=["POST"])
def upload_video():
    """Upload video to a specific library - Supports both file and URL upload"""
    try:
        # Check if this is a JSON request (URL upload) or form data (file upload)
        if request.is_json:
            # Handle URL upload
            data = request.get_json()
            
            if 'video_url' not in data:
                return jsonify({"error": "No video URL provided"}), 400
            if 'library' not in data:
                return jsonify({"error": "Library name is required"}), 400
                
            video_url = data['video_url']
            library_name = data['library']
            video_name = data.get('video_name', video_url.split('/')[-1])
            source_language = data.get('source_language', 'auto')
            logging.info(f"URL upload received source_language: {source_language}")
            
            # Validate URL format
            from urllib.parse import urlparse
            parsed_url = urlparse(video_url)
            if not parsed_url.scheme or not parsed_url.netloc:
                return jsonify({"error": "Invalid video URL format"}), 400
            
            # Check if library exists
            available_dbs = prompt_content_db.get_available_dbs()
            if library_name not in available_dbs:
                return jsonify({"error": "Library not found"}), 404
            
            # Create URL upload task
            task_id = task_manager.create_url_upload_task(video_name, library_name, video_url, source_language)
            
            return jsonify({
                "task_id": task_id,
                "message": f"URL upload started for {video_name}",
                "status": "accepted"
            }), 202  # HTTP 202 Accepted
        
        else:
            # Handle file upload (existing logic)
            if 'video' not in request.files:
                return jsonify({"error": "No video file provided"}), 400
                
            if 'library' not in request.form:
                return jsonify({"error": "Library name is required"}), 400
                
            video_file = request.files['video']
            library_name = request.form['library']
            source_language = request.form.get('source_language', 'auto')
            logging.info(f"File upload received source_language: {source_language}")
        
        if video_file.filename == '' or video_file.filename is None:
            return jsonify({"error": "No video file selected"}), 400
        
        # Check if library exists
        available_dbs = prompt_content_db.get_available_dbs()
        if library_name not in available_dbs:
            return jsonify({"error": "Library not found"}), 404
        
        # Handle filename processing - Chinese filenames get UUID, English keep secure_filename
        original_filename = video_file.filename
        file_extension = Path(original_filename).suffix.lower()
        
        # Check if filename contains Chinese characters
        if re.search(r'[\u4e00-\u9fff]', original_filename):
            # Chinese filename: use UUID + extension
            safe_filename = f"{uuid.uuid4().hex[:12]}{file_extension}"
            logging.info(f"Chinese filename detected: '{original_filename}' -> '{safe_filename}'")
        else:
            # English filename: use secure_filename
            safe_filename = secure_filename(original_filename)
            logging.info(f"English filename processed: '{original_filename}' -> '{safe_filename}'")
        
        # Save uploaded file
        upload_path = DATA_DIR / safe_filename
        video_file.save(upload_path)
        
        # Create task (async processing) - pass both original and safe filenames
        task_id = task_manager.create_upload_task(original_filename, library_name, str(upload_path), source_language)
        
        return jsonify({
            "task_id": task_id,
            "message": f"Upload started for {original_filename}",
            "status": "accepted"
        }), 202  # HTTP 202 Accepted
        
    except Exception as e:
        logging.exception("Exception in /upload")
        return jsonify({"error": str(e)}), 500


@app.route("/tasks/<task_id>", methods=["GET"])
def get_task_status(task_id: str):
    """Get status of a specific task"""
    task = task_manager.get_task(task_id)
    if not task:
        return jsonify({"error": "Task not found"}), 404
    
    return jsonify(task.to_dict())


@app.route("/tasks", methods=["GET"])
def list_tasks():
    """List all tasks"""
    # Get query parameters
    status_filter = request.args.get('status')  # Optional status filter
    active_only = request.args.get('active') == 'true'  # Show only active tasks
    
    if active_only:
        tasks = task_manager.list_active_tasks()
    else:
        tasks = task_manager.list_all_tasks()
    
    # Apply status filter if provided
    if status_filter:
        tasks = [task for task in tasks if task.status.value == status_filter]
    
    return jsonify({
        "tasks": [task.to_dict() for task in tasks],
        "total": len(tasks)
    })


@app.route("/tasks/<task_id>/cancel", methods=["POST"])
def cancel_task(task_id: str):
    """Cancel a specific task"""
    logging.info(f"Attempting to cancel task: {task_id}")
    
    # Check if task exists
    task = task_manager.get_task(task_id)
    if not task:
        logging.warning(f"Task {task_id} not found for cancellation")
        return jsonify({"error": "Task not found"}), 404
    
    logging.info(f"Task {task_id} current status: {task.status}")
    
    success = task_manager.cancel_task(task_id)
    if success:
        logging.info(f"Task {task_id} cancelled successfully")
        return jsonify({"message": "Task cancelled successfully"})
    else:
        logging.warning(f"Failed to cancel task {task_id}")
        return jsonify({"error": "Cannot cancel task or task not found"}), 400


@app.route("/tasks/<task_id>", methods=["DELETE"])
def delete_task(task_id: str):
    """Delete/Remove a specific task"""
    success = task_manager.remove_task(task_id)
    if success:
        return jsonify({"message": "Task removed successfully"})
    else:
        return jsonify({"error": "Task not found"}), 404


@app.route("/libraries/<library_name>/videos", methods=["GET"])
def list_library_videos(library_name):
    """Get all videos in a specific library"""
    try:
        # Check if library exists
        available_dbs = prompt_content_db.get_available_dbs()
        if library_name not in available_dbs:
            return jsonify({"error": "Library not found"}), 404
        
        # Get videos from database
        videos = db_manager.get_library_videos(library_name)
        
        return jsonify({
            "library_name": library_name,
            "videos": videos,
            "total": len(videos)
        }), 200
        
    except Exception as e:
        logging.exception("Exception in /libraries/<library>/videos GET")
        return jsonify({"error": str(e)}), 500


@app.route("/libraries/<library_name>/videos/<video_id>", methods=["DELETE"])
def delete_video(library_name, video_id):
    """Delete a specific video from a library"""
    try:
        # Check if library exists
        available_dbs = prompt_content_db.get_available_dbs()
        if library_name not in available_dbs:
            return jsonify({"error": "Library not found"}), 404
        
        # Create deletion task
        task_id = task_manager.create_video_delete_task(library_name, video_id)
        
        return jsonify({
            "task_id": task_id,
            "message": f"Video deletion started for {video_id}",
            "status": "accepted"
        }), 202
        
    except Exception as e:
        logging.exception(f"Exception in delete video {video_id}")
        return jsonify({"error": str(e)}), 500


@app.route("/libraries/<library_name>/videos/batch-delete", methods=["POST"])
def batch_delete_videos(library_name):
    """Delete multiple videos from a library"""
    try:
        data = request.get_json()
        if not data or 'video_ids' not in data:
            return jsonify({"error": "video_ids list is required"}), 400
        
        video_ids = data['video_ids']
        if not video_ids:
            return jsonify({"error": "At least one video_id is required"}), 400
        
        # Check if library exists
        available_dbs = prompt_content_db.get_available_dbs()
        if library_name not in available_dbs:
            return jsonify({"error": "Library not found"}), 404
        
        # Create batch deletion task
        task_id = task_manager.create_batch_delete_task(library_name, video_ids)
        
        return jsonify({
            "task_id": task_id,
            "message": f"Batch deletion started for {len(video_ids)} videos",
            "status": "accepted"
        }), 202
        
    except Exception as e:
        logging.exception(f"Exception in batch delete videos")
        return jsonify({"error": str(e)}), 500


@app.route("/libraries/<library_name>/videos/<video_id>/captions/<format>", methods=["GET"])
def download_video_captions(library_name, video_id, format):
    """Download caption/subtitle files for a specific video with language support"""
    try:
        # Get language parameter from query string
        language = request.args.get('language', 'auto')  # Default to auto-detect
        
        # Validate format
        supported_formats = ['srt', 'vtt', 'ttml']
        if format.lower() not in supported_formats:
            return jsonify({"error": f"Unsupported format '{format}'. Supported formats: {', '.join(supported_formats)}"}), 400
        
        # Check if library exists
        available_dbs = prompt_content_db.get_available_dbs()
        if library_name not in available_dbs:
            return jsonify({"error": "Library not found"}), 404
        
        # Get video information from database
        videos = db_manager.get_library_videos(library_name)
        video = next((v for v in videos if v['video_id'] == video_id), None)
        
        if not video:
            return jsonify({"error": "Video not found in library"}), 404
        
        if video['status'] != 'indexed':
            return jsonify({"error": "Video must be indexed to export captions"}), 400
        
        # Get video indexer client using environment variables
        from vi_search.vi_client.video_indexer_client import init_video_indexer_client
        from dotenv import dotenv_values
        from pathlib import Path
        
        try:
            # Load configuration from .env file
            env_path = Path(__file__).parent / ".env"
            config = dotenv_values(env_path)
            vi_client = init_video_indexer_client(config)
            
            # Map language codes for Azure Video Indexer
            azure_language = language
            if language == 'auto':
                azure_language = 'en-US'  # Default fallback
            elif language == 'zh-Hant':
                azure_language = 'zh-Hant'  # Traditional Chinese
            elif language == 'zh-Hans':
                azure_language = 'zh-Hans'  # Simplified Chinese
            elif language == 'zh-HK':
                azure_language = 'zh-HK'  # Cantonese Traditional
            elif language == 'vi-VN':
                azure_language = 'vi-VN'  # Vietnamese
            
            # Download captions from Azure Video Indexer
            caption_content = vi_client.download_captions(
                video_id=video_id, 
                format=format.lower(),
                language=azure_language,
                include_speakers=True
            )
            
            # Generate filename: use original filename without extension + format + language
            base_filename = video['filename']
            if '.' in base_filename:
                base_filename = base_filename.rsplit('.', 1)[0]
            
            # Add language suffix if not auto-detect
            language_suffix = "" if language == 'auto' else f".{language}"
            filename = f"{base_filename}{language_suffix}.{format.lower()}"
            
            # URL-encode filename for HTTP header compatibility (handles Chinese characters)
            from urllib.parse import quote
            encoded_filename = quote(filename.encode('utf-8'))
            
            # Return file as download
            from flask import Response
            response = Response(
                caption_content,
                mimetype='text/plain',
                headers={
                    'Content-Disposition': f'attachment; filename*=UTF-8\'\'{encoded_filename}',
                    'Content-Type': f'text/{format.lower()}' if format.lower() in ['srt', 'vtt'] else 'text/plain'
                }
            )
            
            logger.info(f"Successfully downloaded {format.upper()} captions for video {video_id} in library {library_name} (Language: {language})")
            return response
            
        except Exception as vi_error:
            logger.error(f"Azure Video Indexer error for video {video_id}: {str(vi_error)}")
            return jsonify({"error": f"Failed to download captions from Azure Video Indexer: {str(vi_error)}"}), 500
            
    except Exception as e:
        logger.exception(f"Exception in download video captions for video {video_id}")
        return jsonify({"error": str(e)}), 500


@app.route("/libraries/<library_name>/cleanup-orphaned", methods=["POST"])
def cleanup_orphaned_videos(library_name):
    """Clean up orphaned video records that no longer exist in Azure Video Indexer"""
    try:
        from vi_search.vi_client.video_indexer_client import init_video_indexer_client
        from dotenv import dotenv_values
        from pathlib import Path
        
        # Get all videos in the library
        videos = db_manager.get_library_videos(library_name)
        if not videos:
            return jsonify({"message": "No videos found in library", "orphaned": [], "total": 0}), 200
        
        # Initialize Video Indexer client
        env_path = Path(__file__).parent / ".env"
        config = dotenv_values(env_path)
        client = init_video_indexer_client(config)
        
        orphaned_videos = []
        checked_count = 0
        
        for video in videos:
            video_id = video.get('video_id')
            filename = video.get('filename', 'Unknown')
            
            if not video_id:
                # No video_id means it's definitely orphaned
                orphaned_videos.append({
                    'id': video.get('id'),
                    'filename': filename,
                    'video_id': None,
                    'reason': 'No video_id'
                })
                continue
            
            checked_count += 1
            try:
                # Check if video exists in Azure Video Indexer
                client.is_video_processed(video_id)
                # If no exception, video exists
            except Exception as e:
                error_str = str(e)
                if "404" in error_str or "not found" in error_str.lower():
                    orphaned_videos.append({
                        'id': video.get('id'),
                        'filename': filename,
                        'video_id': video_id,
                        'reason': 'Not found in Azure Video Indexer (404)'
                    })
                elif "400" in error_str:
                    orphaned_videos.append({
                        'id': video.get('id'),
                        'filename': filename,
                        'video_id': video_id,
                        'reason': 'Invalid state in Azure Video Indexer (400)'
                    })
                # Other errors might be temporary, so don't mark as orphaned
        
        # Get option to actually delete
        should_delete = request.json and request.json.get('delete', False)
        
        if should_delete and orphaned_videos:
            deleted_count = 0
            for orphaned in orphaned_videos:
                try:
                    if db_manager.delete_video_record(library_name, video_id=orphaned['video_id']):
                        deleted_count += 1
                        orphaned['deleted'] = True
                    else:
                        orphaned['deleted'] = False
                        orphaned['delete_error'] = 'Database deletion failed'
                except Exception as e:
                    orphaned['deleted'] = False
                    orphaned['delete_error'] = str(e)
            
            return jsonify({
                "message": f"Cleanup completed. Deleted {deleted_count} orphaned records.",
                "orphaned": orphaned_videos,
                "total_checked": checked_count,
                "total_orphaned": len(orphaned_videos),
                "deleted": deleted_count
            }), 200
        else:
            return jsonify({
                "message": f"Found {len(orphaned_videos)} orphaned video records",
                "orphaned": orphaned_videos,
                "total_checked": checked_count,
                "total_orphaned": len(orphaned_videos),
                "note": "To actually delete these records, send POST with {\"delete\": true}"
            }), 200
        
    except Exception as e:
        logging.exception(f"Exception in cleanup orphaned videos")
        return jsonify({"error": str(e)}), 500


@app.route("/settings/<library_name>", methods=["GET"])
def get_library_settings(library_name):
    """Get settings for a specific library"""
    try:
        settings = settings_service.get_settings(library_name)
        return jsonify(settings), 200
        
    except Exception as e:
        logging.exception("Exception in /settings GET")
        return jsonify({"error": str(e)}), 500


@app.route("/settings/<library_name>", methods=["POST"])
def save_library_settings(library_name):
    """Save settings for a specific library"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Settings data is required"}), 400
        
        # Save settings using the service
        settings_service.save_settings(library_name, data)
        
        return jsonify({"message": f"Settings for '{library_name}' saved successfully"}), 200
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logging.exception("Exception in /settings POST")
        return jsonify({"error": str(e)}), 500


# AI Parameters Management API endpoints
@app.route("/api/libraries/<library_name>/ai-parameters", methods=["GET"])
def get_library_ai_parameters(library_name):
    """Get AI parameters for a specific library"""
    try:
        settings = settings_service.get_settings(library_name)
        
        # Return AI parameters with default values if not set
        ai_parameters = {
            "model": settings.get("model", "gpt-4o"),
            "temperature": settings.get("temperature", 0.7),
            "maxTokens": settings.get("maxTokens", 2000),
            "topP": settings.get("topP", 0.9),
            "frequencyPenalty": settings.get("frequencyPenalty", 0),
            "presencePenalty": settings.get("presencePenalty", 0),
            "stopSequences": settings.get("stopSequences", []),
            "systemPrompt": settings.get("promptTemplate", ""),
            "conversationStarters": settings.get("conversationStarters", []),
            "timeoutSeconds": settings.get("timeoutSeconds", 30),
            "enableStreaming": settings.get("enableStreaming", True),
            "enableFunctionCalling": settings.get("enableFunctionCalling", False),
            "maxRetries": settings.get("maxRetries", 3),
        }
        
        return jsonify(ai_parameters)
        
    except Exception as e:
        logging.exception(f"Exception in get AI parameters for library {library_name}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/libraries/<library_name>/ai-parameters", methods=["PUT"])
def update_library_ai_parameters(library_name):
    """Update AI parameters for a specific library"""
    if not request.json:
        return jsonify({"error": "Invalid JSON"}), 400
        
    try:
        # Get existing settings
        existing_settings = settings_service.get_settings(library_name)
        
        # Map AI parameters to settings format
        ai_params = request.json
        updated_settings = {
            **existing_settings,  # Keep existing settings
            "model": ai_params.get("model", existing_settings.get("model", "gpt-4o")),
            "temperature": ai_params.get("temperature", existing_settings.get("temperature", 0.7)),
            "maxTokens": ai_params.get("maxTokens", existing_settings.get("maxTokens", 2000)),
            "topP": ai_params.get("topP", existing_settings.get("topP", 0.9)),
            "frequencyPenalty": ai_params.get("frequencyPenalty", existing_settings.get("frequencyPenalty", 0)),
            "presencePenalty": ai_params.get("presencePenalty", existing_settings.get("presencePenalty", 0)),
            "stopSequences": ai_params.get("stopSequences", existing_settings.get("stopSequences", [])),
            "promptTemplate": ai_params.get("systemPrompt", existing_settings.get("promptTemplate", "")),
            "conversationStarters": ai_params.get("conversationStarters", existing_settings.get("conversationStarters", [])),
            "timeoutSeconds": ai_params.get("timeoutSeconds", existing_settings.get("timeoutSeconds", 30)),
            "enableStreaming": ai_params.get("enableStreaming", existing_settings.get("enableStreaming", True)),
            "enableFunctionCalling": ai_params.get("enableFunctionCalling", existing_settings.get("enableFunctionCalling", False)),
            "maxRetries": ai_params.get("maxRetries", existing_settings.get("maxRetries", 3)),
        }
        
        # Save updated settings
        settings_service.save_settings(library_name, updated_settings)
        
        return jsonify({"message": f"AI parameters for '{library_name}' updated successfully"}), 200
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logging.exception(f"Exception in update AI parameters for library {library_name}")
        return jsonify({"error": str(e)}), 500


# AI Templates API endpoints
@app.route("/api/templates", methods=["GET"])
def get_all_templates():
    """Get all AI templates"""
    try:
        templates = ai_template_service.get_all_templates()
        return jsonify(templates)
    
    except Exception as e:
        logging.exception("Exception in get all templates")
        return jsonify({"error": str(e)}), 500


@app.route("/api/templates/<template_name>", methods=["GET"])
def get_template(template_name):
    """Get a specific template"""
    try:
        template = ai_template_service.get_template(template_name)
        if not template:
            return jsonify({"error": "Template not found"}), 404
        
        return jsonify(template)
    
    except Exception as e:
        logging.exception("Exception in get template")
        return jsonify({"error": str(e)}), 500


@app.route("/api/templates", methods=["POST"])
def create_template():
    """Create a new AI template"""
    if not request.json:
        return jsonify({"error": "Invalid JSON"}), 400
    
    try:
        template = ai_template_service.create_template(request.json)
        return jsonify(template), 201
    
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logging.exception("Exception in create template")
        return jsonify({"error": str(e)}), 500


@app.route("/api/templates/<template_name>", methods=["PUT"])
def update_template(template_name):
    """Update an existing template"""
    if not request.json:
        return jsonify({"error": "Invalid JSON"}), 400
    
    try:
        template = ai_template_service.update_template(template_name, request.json)
        return jsonify(template)
    
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logging.exception("Exception in update template")
        return jsonify({"error": str(e)}), 500


@app.route("/api/templates/<template_name>", methods=["DELETE"])
def delete_template(template_name):
    """Delete a template"""
    try:
        ai_template_service.delete_template(template_name)
        return jsonify({"message": "Template deleted successfully"})
    
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logging.exception("Exception in delete template")
        return jsonify({"error": str(e)}), 500


@app.route("/api/templates/<template_name>/apply-to/<library_name>", methods=["POST"])
def apply_template_to_library(template_name, library_name):
    """Apply a template to a specific library"""
    try:
        result = ai_template_service.apply_template_to_library(
            template_name, library_name, settings_service
        )
        return jsonify(result)
    
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logging.exception("Exception in apply template to library")
        return jsonify({"error": str(e)}), 500


@app.route("/api/templates/categories", methods=["GET"])
def get_templates_by_category():
    """Get templates grouped by category"""
    try:
        categories = ai_template_service.get_templates_by_category()
        return jsonify(categories)
    
    except Exception as e:
        logging.exception("Exception in get templates by category")
        return jsonify({"error": str(e)}), 500


@app.route("/api/libraries/<library_name>/conversation-starters", methods=["GET"])
def get_library_conversation_starters(library_name):
    """Get conversation starters for a specific library"""
    try:
        starters = conversation_starters_service.get_library_starters(library_name)
        return jsonify({"starters": starters})
    
    except Exception as e:
        logging.exception("Exception in get library conversation starters")
        return jsonify({"error": str(e)}), 500


@app.route("/api/libraries/<library_name>/conversation-starters", methods=["PUT"])
def save_library_conversation_starters(library_name):
    """Save conversation starters for a specific library"""
    if not request.json or "starters" not in request.json:
        return jsonify({"error": "Invalid request: 'starters' field required"}), 400
    
    try:
        starters = request.json["starters"]
        conversation_starters_service.save_library_starters(library_name, starters)
        return jsonify({"message": "Conversation starters saved successfully"})
    
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logging.exception("Exception in save library conversation starters")
        return jsonify({"error": str(e)}), 500


@app.route("/api/conversation-starters", methods=["GET"])
def get_all_conversation_starters():
    """Get conversation starters for all libraries"""
    try:
        all_starters = conversation_starters_service.get_all_libraries_starters()
        defaults = conversation_starters_service.get_default_starters()
        return jsonify({
            "libraries": all_starters,
            "defaults": defaults
        })
    
    except Exception as e:
        logging.exception("Exception in get all conversation starters")
        return jsonify({"error": str(e)}), 500


@app.route("/api/system/logs", methods=["GET"])
def get_system_logs():
    """Get system logs for debugging"""
    try:
        log_type = request.args.get('type', 'app')
        lines = int(request.args.get('lines', 100))
        
        log_dir = Path(__file__).parent / "logs"
        today = datetime.now().strftime('%Y%m%d')
        
        if log_type == 'app':
            log_file = log_dir / f"app_{today}.log"
        else:
            return jsonify({"error": "Invalid log type"}), 400
        
        if not log_file.exists():
            return jsonify({"logs": [], "message": f"Log file not found: {log_file.name}"})
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                # Get last N lines
                recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
                
            return jsonify({
                "logs": [line.strip() for line in recent_lines],
                "total_lines": len(all_lines),
                "file": log_file.name,
                "showing": len(recent_lines)
            })
            
        except Exception as e:
            return jsonify({"error": f"Failed to read log file: {str(e)}"}), 500
        
    except Exception as e:
        logging.exception("Exception in get system logs")
        return jsonify({"error": str(e)}), 500


@app.route("/api/system/tasks-history", methods=["GET"])
def get_tasks_history():
    """Get all tasks history from database"""
    try:
        # Get query parameters
        status_filter = request.args.get('status')  # Optional status filter
        days = int(request.args.get('days', 7))  # Default to recent 7 days
        limit = int(request.args.get('limit', 100))  # Limit number of results
        
        # Get task history from database
        all_tasks = db_manager.get_all_tasks()
        
        # Filter tasks from recent N days
        from datetime import datetime, timedelta
        cutoff_date = datetime.now() - timedelta(days=days)
        
        filtered_tasks = []
        for task in all_tasks:
            try:
                task_date = datetime.fromisoformat(task['created_at']) if task['created_at'] else datetime.min
                if task_date >= cutoff_date:
                    # Apply status filter
                    if not status_filter or task['status'] == status_filter:
                        filtered_tasks.append(task)
            except (ValueError, KeyError):
                continue
        
        # Sort by creation time (newest first)
        filtered_tasks.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        # Apply limit
        result_tasks = filtered_tasks[:limit]
        
        return jsonify({
            "tasks": result_tasks,
            "total_found": len(filtered_tasks),
            "total_in_db": len(all_tasks),
            "showing": len(result_tasks),
            "filter": {
                "status": status_filter,
                "days": days,
                "limit": limit
            }
        })
        
    except Exception as e:
        logging.exception("Exception in get tasks history")
        return jsonify({"error": str(e)}), 500


# Blob Storage API endpoints
@app.route("/blob-storage/containers", methods=["GET"])
def list_blob_containers():
    """List all blob storage containers"""
    try:
        from services.blob_storage_service import get_blob_storage_service
        blob_service = get_blob_storage_service()
        containers = blob_service.list_containers()
        
        return jsonify({
            "containers": containers,
            "total": len(containers)
        })
        
    except ImportError:
        return jsonify({"error": "Azure Storage SDK not available"}), 501
    except Exception as e:
        logging.exception("Exception in list blob containers")
        return jsonify({"error": str(e)}), 500


@app.route("/blob-storage/containers/<container_name>/blobs", methods=["GET"])
def list_container_blobs(container_name):
    """List blobs in a specific container"""
    try:
        from services.blob_storage_service import get_blob_storage_service
        blob_service = get_blob_storage_service()
        
        # Get query parameters
        prefix = request.args.get('prefix')
        pattern = request.args.get('pattern')
        metadata_filter = request.args.get('metadata')
        
        if pattern:
            blobs = blob_service.list_blobs_by_pattern(container_name, pattern)
        elif metadata_filter:
            try:
                metadata_dict = json.loads(metadata_filter)
                blobs = blob_service.list_blobs_by_metadata(container_name, metadata_dict)
            except json.JSONDecodeError:
                return jsonify({"error": "Invalid metadata filter JSON"}), 400
        else:
            blobs = blob_service.list_blobs(container_name, prefix)
        
        # Convert BlobInfo objects to dictionaries
        blob_list = []
        for blob in blobs:
            blob_dict = {
                'name': blob.name,
                'container': blob.container,
                'size': blob.size,
                'last_modified': blob.last_modified.isoformat(),
                'content_type': blob.content_type,
                'md5_hash': blob.md5_hash,
                'metadata': blob.metadata
            }
            blob_list.append(blob_dict)
        
        return jsonify({
            "container": container_name,
            "blobs": blob_list,
            "total": len(blob_list)
        })
        
    except ImportError:
        return jsonify({"error": "Azure Storage SDK not available"}), 501
    except Exception as e:
        logging.exception("Exception in list container blobs")
        return jsonify({"error": str(e)}), 500


@app.route("/blob-storage/generate-sas", methods=["POST"])
def generate_blob_sas():
    """Generate SAS URL for a blob"""
    try:
        from services.blob_storage_service import get_blob_storage_service
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        container_name = data.get('container_name')
        blob_name = data.get('blob_name')
        expiry_hours = data.get('expiry_hours', 24)
        
        if not container_name or not blob_name:
            return jsonify({"error": "container_name and blob_name are required"}), 400
        
        blob_service = get_blob_storage_service()
        sas_url = blob_service.generate_sas_url(container_name, blob_name, expiry_hours)
        
        return jsonify({
            "sas_url": sas_url,
            "container": container_name,
            "blob": blob_name,
            "expires_in_hours": expiry_hours
        })
        
    except ImportError:
        return jsonify({"error": "Azure Storage SDK not available"}), 501
    except Exception as e:
        logging.exception("Exception in generate blob SAS")
        return jsonify({"error": str(e)}), 500


@app.route("/libraries/<library_name>/import-from-blob", methods=["POST"])
def import_from_blob(library_name):
    """Import videos from Azure Blob Storage into a library"""
    try:
        from services.blob_storage_service import get_blob_storage_service
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        # Check if library exists
        available_dbs = prompt_content_db.get_available_dbs()
        if library_name not in available_dbs:
            return jsonify({"error": f"Library '{library_name}' not found"}), 404
        
        blob_service = get_blob_storage_service()
        task_ids = []
        
        # Handle different import modes
        if 'blob_url' in data:
            # Single blob URL
            blob_url = data['blob_url']
            blob_info = blob_service.extract_blob_info_from_url(blob_url)
            blob_name = blob_info['blob_name']
            container_name = blob_info['container']
            filename = blob_name.split('/')[-1]  # Extract filename from path
            
            # Get blob details to retrieve file size
            blobs = blob_service.list_blobs(container_name, prefix=blob_name)
            file_size = None
            if blobs:
                matching_blob = next((b for b in blobs if b.name == blob_name), None)
                if matching_blob:
                    file_size = matching_blob.size
            
            task_id = task_manager.create_blob_import_task(filename, blob_url, library_name, file_size)
            task_ids.append(task_id)
            
        elif 'blob_path' in data:
            # Pattern-based selection
            container_name = data.get('container_name', 'videoqna-videos')
            pattern = data['blob_path']
            
            blobs = blob_service.list_blobs_by_pattern(container_name, pattern)
            for blob in blobs:
                sas_url = blob_service.generate_sas_url(container_name, blob.name)
                filename = blob.name.split('/')[-1]  # Extract filename from path
                task_id = task_manager.create_blob_import_task(filename, sas_url, library_name, blob.size)
                task_ids.append(task_id)
                
        elif 'blob_metadata' in data:
            # Metadata-based selection
            container_name = data.get('container_name', 'videoqna-videos')
            metadata_filter = data['blob_metadata']
            
            blobs = blob_service.list_blobs_by_metadata(container_name, metadata_filter)
            for blob in blobs:
                sas_url = blob_service.generate_sas_url(container_name, blob.name)
                filename = blob.name.split('/')[-1]  # Extract filename from path
                task_id = task_manager.create_blob_import_task(filename, sas_url, library_name, blob.size)
                task_ids.append(task_id)
                
        elif 'blob_list' in data:
            # Explicit blob list - supports both string array and object array formats
            blob_list = data['blob_list']
            
            for blob_item in blob_list:
                # Handle both string format and object format
                if isinstance(blob_item, dict):
                    container_name = blob_item.get('container_name', data.get('container_name', 'videoqna-videos'))
                    blob_name = blob_item.get('blob_name')
                else:
                    # String format
                    container_name = data.get('container_name', 'videoqna-videos')
                    blob_name = blob_item
                
                if not blob_name:
                    continue
                    
                # Get blob size for explicit blob list
                blob_info = blob_service.get_blob_properties(container_name, blob_name)
                file_size = blob_info.size if blob_info else None
                
                sas_url = blob_service.generate_sas_url(container_name, blob_name)
                filename = blob_name.split('/')[-1]  # Extract filename from path
                task_id = task_manager.create_blob_import_task(filename, sas_url, library_name, file_size)
                task_ids.append(task_id)
        else:
            return jsonify({"error": "No valid import method specified. Use one of: blob_url, blob_path, blob_metadata, blob_list"}), 400
        
        return jsonify({
            "task_ids": task_ids,
            "total_videos": len(task_ids),
            "message": f"Started importing {len(task_ids)} videos from blob storage into library '{library_name}'"
        }), 202  # HTTP 202 Accepted
        
    except ImportError:
        return jsonify({"error": "Azure Storage SDK not available"}), 501
    except Exception as e:
        logging.exception("Exception in import from blob")
        return jsonify({"error": str(e)}), 500


# Handle the rate limit exceeded exception
@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({"error": "Rate limit: Exceeded the number of asks per day", "message": e.description}), 429


if __name__ == "__main__":
    # Check if running in container environment
    is_docker = os.path.exists('/.dockerenv')
    is_development = os.environ.get('FLASK_ENV') == 'development'
    is_production = os.environ.get('FLASK_ENV') == 'production'
    
    if is_production:
        # Production environment should use Gunicorn
        logger.warning("Running in production mode with Flask dev server. Use Gunicorn instead: gunicorn -c gunicorn.conf.py app:app")
        app.run(
            host='0.0.0.0',
            port=int(os.environ.get('PORT', 5000)),
            debug=False,     # Never enable debug in production
            threaded=True
        )
    elif is_docker:
        # Docker environment configuration
        app.run(
            host='0.0.0.0',  # Must bind to 0.0.0.0 in container
            port=int(os.environ.get('PORT', 5000)),
            debug=is_development,
            threaded=True
        )
    else:
        # Local development configuration
        app.run(
            host='0.0.0.0',  # Allow external connections
            port=int(os.environ.get('PORT', 5000)),
            debug=True,      # Enable debug mode
            threaded=True    # Enable multi-threading
        )
