"""
Video upload and management routes
"""
import logging
import os
import re
import uuid
from pathlib import Path
from werkzeug.utils import secure_filename
from datetime import datetime

from flask import Blueprint, request, jsonify, current_app
from utils.error_handlers import handle_api_errors, error_response, success_response, ValidationError

# Create blueprint
video_bp = Blueprint('video', __name__)
logger = logging.getLogger(__name__)


@video_bp.route("/upload", methods=["POST"])
@handle_api_errors
def upload_video():
    """Handle video upload"""
    if 'file' not in request.files:
        raise ValidationError("No file part in the request")
    
    file = request.files['file']
    if file.filename == '':
        raise ValidationError("No file selected")
    
    library_name = request.form.get('library_name')
    if not library_name:
        raise ValidationError("Library name is required")
    
    # Get services from current_app
    task_manager = current_app.task_manager
    library_manager = current_app.library_manager
    
    # Check if library exists
    available_libs = library_manager.get_libraries()
    if library_name not in available_libs:
        raise ValidationError(f"Library '{library_name}' not found")
    
    # Validate file type
    allowed_extensions = {'.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv', '.m4v'}
    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in allowed_extensions:
        raise ValidationError(f"File type {file_extension} not allowed. Supported: {', '.join(allowed_extensions)}")
    
    # Handle Chinese filename conversion
    original_filename = file.filename
    if re.search(r'[\u4e00-\u9fff]', original_filename):
        file_extension = Path(original_filename).suffix
        uuid_name = str(uuid.uuid4())
        new_filename = f"{uuid_name}{file_extension}"
        logger.info(f"Chinese filename detected. Converting '{original_filename}' to '{new_filename}'")
    else:
        new_filename = secure_filename(original_filename)
    
    # Save file to upload directory
    from vi_search.constants import DATA_DIR
    upload_dir = Path(DATA_DIR) / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = upload_dir / new_filename
    file.save(str(file_path))
    logger.info(f"File uploaded: {file_path}")
    
    # Create upload task
    task_id = task_manager.create_task(
        task_type='video_upload',
        video_path=str(file_path),
        library_name=library_name,
        original_filename=original_filename,
        metadata={
            'file_size': file_path.stat().st_size,
            'upload_time': datetime.now().isoformat()
        }
    )
    
    return success_response({
        "task_id": task_id,
        "filename": new_filename,
        "original_filename": original_filename
    }, "Video upload started")


@video_bp.route("/libraries/<library_name>/videos", methods=["GET"])
@handle_api_errors  
def get_library_videos(library_name):
    """Get videos in a library"""
    prompt_content_db = current_app.prompt_content_db
    db_manager = current_app.db_manager
    
    # Check if library exists
    available_dbs = prompt_content_db.get_available_dbs()
    if library_name not in available_dbs:
        return error_response("Library not found", 404)
    
    try:
        # Get videos from database
        videos = db_manager.get_library_videos(library_name)
        return success_response({
            "library_name": library_name,
            "videos": videos,
            "total": len(videos)
        })
    except Exception as e:
        logger.error(f"Error getting videos for library {library_name}: {e}")
        return error_response(f"Error getting videos: {str(e)}", 500)


@video_bp.route("/libraries/<library_name>/videos/<video_id>", methods=["DELETE"])
@handle_api_errors
def delete_video(library_name, video_id):
    """Delete a video from library"""
    prompt_content_db = current_app.prompt_content_db
    task_manager = current_app.task_manager
    
    # Check if library exists
    available_dbs = prompt_content_db.get_available_dbs()
    if library_name not in available_dbs:
        return error_response("Library not found", 404)
    
    try:
        # Create deletion task
        task_id = task_manager.create_video_delete_task(library_name, video_id)
        
        return jsonify({
            "task_id": task_id,
            "message": f"Video deletion started for {video_id}",
            "status": "accepted"
        }), 202
    except Exception as e:
        logger.error(f"Error deleting video {video_id}: {e}")
        return error_response(f"Error deleting video: {str(e)}", 500)


@video_bp.route("/libraries/<library_name>/videos/batch-delete", methods=["POST"])
@handle_api_errors
def batch_delete_videos(library_name):
    """Delete multiple videos from a library"""
    prompt_content_db = current_app.prompt_content_db
    task_manager = current_app.task_manager
    
    data = request.get_json()
    if not data or 'video_ids' not in data:
        raise ValidationError("video_ids list is required")
    
    video_ids = data['video_ids']
    if not video_ids:
        raise ValidationError("At least one video_id is required")
    
    # Check if library exists
    available_dbs = prompt_content_db.get_available_dbs()
    if library_name not in available_dbs:
        return error_response("Library not found", 404)
    
    try:
        # Create deletion tasks for all videos
        task_ids = []
        for video_id in video_ids:
            task_id = task_manager.create_video_delete_task(library_name, video_id)
            task_ids.append(task_id)
        
        return success_response({
            "task_ids": task_ids,
            "video_ids": video_ids,
            "total": len(task_ids)
        }, f"Batch deletion started for {len(video_ids)} videos")
    except Exception as e:
        logger.error(f"Error in batch delete: {e}")
        return error_response(f"Error in batch deletion: {str(e)}", 500)