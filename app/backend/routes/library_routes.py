"""
Library management routes
"""
import logging
from flask import Blueprint, request, jsonify, current_app
from utils.error_handlers import handle_api_errors, error_response, success_response, ValidationError

# Create blueprint
library_bp = Blueprint('library', __name__)
logger = logging.getLogger(__name__)


@library_bp.route("/libraries", methods=["POST"])
@handle_api_errors
def create_library():
    """Create a new video library (database)"""
    data = request.get_json()
    if not data or 'name' not in data:
        raise ValidationError("Library name is required")
    
    library_name = data['name']
    library_manager = current_app.library_manager
    
    if library_manager.library_exists(library_name):
        raise ValidationError(f"Library '{library_name}' already exists")
    
    # Create the library
    result = library_manager.create_library(library_name)
    
    return success_response({
        "library_name": library_name,
        "created": result
    }, f"Library '{library_name}' created successfully")


@library_bp.route("/libraries/<library_name>", methods=["DELETE"]) 
@handle_api_errors
def delete_library(library_name):
    """Delete a video library (database) with complete cleanup"""
    library_manager = current_app.library_manager
    
    logger.info(f"Starting complete deletion of library: {library_name}")
    
    try:
        # Use LibraryManager for complete deletion
        cleanup_result = library_manager.delete_library_completely(library_name)
        
        if cleanup_result.success:
            return success_response({
                "message": cleanup_result.message,
                "details": cleanup_result.details
            }, f"Library '{library_name}' deleted successfully")
        else:
            return error_response(f"Error deleting library: {cleanup_result.message}", 500)
    except Exception as e:
        logger.error(f"Error deleting library {library_name}: {e}")
        return error_response(f"Error deleting library: {str(e)}", 500)


@library_bp.route("/libraries/status", methods=["GET"])
@handle_api_errors
def get_libraries_status():
    """Get all libraries with their consistency status"""
    library_manager = current_app.library_manager
    
    try:
        libraries = library_manager.list_all_libraries_with_status()
        
        consistent_count = sum(1 for lib in libraries if lib['consistent'])
        inconsistent_count = len(libraries) - consistent_count
        
        return success_response({
            "libraries": libraries,
            "total": len(libraries),
            "consistent": consistent_count,
            "inconsistent": inconsistent_count
        })
    except Exception as e:
        logger.error(f"Error getting libraries status: {e}")
        return error_response(f"Error getting status: {str(e)}", 500)


@library_bp.route("/libraries/cleanup-inconsistent", methods=["POST"])
@handle_api_errors
def cleanup_inconsistent_libraries():
    """Automatically clean up all inconsistent libraries"""
    library_manager = current_app.library_manager
    
    logger.info("Starting automatic cleanup of inconsistent libraries")
    
    try:
        cleanup_results = library_manager.cleanup_inconsistent_libraries()
        
        total_cleaned = len(cleanup_results)
        successful_cleaned = sum(1 for result in cleanup_results if result.success)
        
        return success_response({
            "cleanup_results": [
                {
                    "library": result.library_name,
                    "success": result.success,
                    "message": result.message,
                    "details": result.details
                } for result in cleanup_results
            ],
            "total_cleaned": total_cleaned,
            "successful": successful_cleaned,
            "failed": total_cleaned - successful_cleaned
        }, f"Cleanup completed: {successful_cleaned}/{total_cleaned} libraries cleaned successfully")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        return error_response(f"Cleanup failed: {str(e)}", 500)


@library_bp.route("/libraries/<library_name>/cleanup-orphaned", methods=["POST"])
@handle_api_errors
def cleanup_orphaned_videos(library_name):
    """Clean up orphaned video records that no longer exist in Azure Video Indexer"""
    library_manager = current_app.library_manager
    
    if not library_manager.library_exists(library_name):
        return error_response(f"Library '{library_name}' not found", 404)
    
    try:
        result = library_manager.cleanup_orphaned_videos(library_name)
        return success_response(result, "Orphaned videos cleanup completed")
    except Exception as e:
        logger.error(f"Error cleaning up orphaned videos in {library_name}: {e}")
        return error_response(f"Cleanup failed: {str(e)}", 500)


@library_bp.route("/libraries/<library_name>/import-from-blob", methods=["POST"])
@handle_api_errors
def import_from_blob(library_name):
    """Import videos from Azure Blob Storage into a library"""
    library_manager = current_app.library_manager
    task_manager = current_app.task_manager
    
    if not library_manager.library_exists(library_name):
        return error_response(f"Library '{library_name}' not found", 404)
    
    data = request.get_json() or {}
    container_name = data.get('container_name')
    blob_prefix = data.get('blob_prefix', '')
    
    if not container_name:
        raise ValidationError("Container name is required")
    
    # Create import task
    task_id = task_manager.create_task(
        task_type='blob_import',
        library_name=library_name,
        container_name=container_name,
        blob_prefix=blob_prefix
    )
    
    return success_response({
        "task_id": task_id
    }, f"Blob import started for library '{library_name}'")