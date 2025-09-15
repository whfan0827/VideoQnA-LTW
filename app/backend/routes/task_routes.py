"""
Task management routes
"""
import logging
from flask import Blueprint, request, jsonify, current_app
from utils.error_handlers import handle_api_errors, error_response, success_response

# Create blueprint
task_bp = Blueprint('task', __name__)
logger = logging.getLogger(__name__)


@task_bp.route("/tasks/<task_id>", methods=["GET"])
@handle_api_errors
def get_task_status(task_id):
    """Get status of a specific task"""
    task_manager = current_app.task_manager
    
    task = task_manager.get_task_status(task_id)
    if not task:
        return error_response(f"Task {task_id} not found", 404)
    
    return jsonify(task)


@task_bp.route("/tasks", methods=["GET"])
@handle_api_errors
def get_all_tasks():
    """Get all tasks with optional filtering"""
    task_manager = current_app.task_manager
    
    # Get filter parameters
    status = request.args.get('status')
    task_type = request.args.get('type')
    limit = request.args.get('limit', type=int)
    
    tasks = task_manager.get_all_tasks(
        status_filter=status,
        task_type_filter=task_type,
        limit=limit
    )
    
    return jsonify({
        "tasks": tasks,
        "total": len(tasks)
    })


@task_bp.route("/tasks/<task_id>/cancel", methods=["POST"])
@handle_api_errors
def cancel_task(task_id):
    """Cancel a running task"""
    task_manager = current_app.task_manager
    
    task = task_manager.get_task_status(task_id)
    if not task:
        return error_response(f"Task {task_id} not found", 404)
    
    if task['status'] not in ['pending', 'running']:
        return error_response(f"Task {task_id} cannot be cancelled (status: {task['status']})", 400)
    
    result = task_manager.cancel_task(task_id)
    
    if result:
        return success_response(message=f"Task {task_id} cancelled successfully")
    else:
        return error_response(f"Failed to cancel task {task_id}", 500)


@task_bp.route("/tasks/<task_id>", methods=["DELETE"])
@handle_api_errors
def delete_task(task_id):
    """Delete a completed or failed task"""
    task_manager = current_app.task_manager
    
    task = task_manager.get_task_status(task_id)
    if not task:
        return error_response(f"Task {task_id} not found", 404)
    
    if task['status'] in ['pending', 'running']:
        return error_response(f"Cannot delete running task {task_id}. Cancel it first.", 400)
    
    result = task_manager.delete_task(task_id)
    
    if result:
        return success_response(message=f"Task {task_id} deleted successfully")
    else:
        return error_response(f"Failed to delete task {task_id}", 500)