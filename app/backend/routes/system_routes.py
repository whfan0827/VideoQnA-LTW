"""
System monitoring and maintenance routes
"""
import logging
from flask import Blueprint, request, jsonify, current_app, send_from_directory
from utils.error_handlers import handle_api_errors, error_response, success_response

# Create blueprint
system_bp = Blueprint('system', __name__)
logger = logging.getLogger(__name__)


@system_bp.route("/")
def index():
    """Serve the frontend application"""
    return send_from_directory(current_app.static_folder, 'index.html')


@system_bp.route("/assets/<path:filename>")
def serve_assets(filename):
    """Serve static assets"""
    return send_from_directory(current_app.static_folder + '/assets', filename)


@system_bp.route("/favicon.ico")
def favicon():
    """Serve favicon"""
    return send_from_directory(current_app.static_folder, 'favicon.ico')


@system_bp.route("/system/data-consistency/status", methods=["GET"])
@handle_api_errors
def get_data_consistency_status():
    """Get current data consistency status"""
    consistency_monitor = current_app.consistency_monitor
    
    try:
        status = consistency_monitor.get_overall_status()
        return jsonify({
            "status": status,
            "timestamp": status.get("last_check", "Never")
        })
    except Exception as e:
        logger.error(f"Error getting consistency status: {e}")
        return error_response(f"Error getting status: {str(e)}", 500)


@system_bp.route("/system/data-consistency/check", methods=["POST"])
@handle_api_errors
def check_data_consistency():
    """Trigger manual data consistency check"""
    consistency_monitor = current_app.consistency_monitor
    
    try:
        result = consistency_monitor.run_consistency_check()
        return success_response(result, "Data consistency check completed")
    except Exception as e:
        logger.error(f"Error running consistency check: {e}")
        return error_response(f"Consistency check failed: {str(e)}", 500)


@system_bp.route("/system/data-consistency/auto-fix", methods=["POST"])
@handle_api_errors
def auto_fix_inconsistencies():
    """Automatically fix detected inconsistencies"""
    consistency_monitor = current_app.consistency_monitor
    
    try:
        result = consistency_monitor.auto_fix_issues()
        return success_response(result, "Auto-fix completed")
    except Exception as e:
        logger.error(f"Error during auto-fix: {e}")
        return error_response(f"Auto-fix failed: {str(e)}", 500)


@system_bp.route("/system/data-consistency/monitor", methods=["POST"])
@handle_api_errors
def start_consistency_monitoring():
    """Start automatic consistency monitoring"""
    consistency_monitor = current_app.consistency_monitor
    
    data = request.get_json() or {}
    interval_minutes = data.get('interval_minutes', 60)
    
    try:
        result = consistency_monitor.start_monitoring(interval_minutes)
        return success_response(result, "Consistency monitoring started")
    except Exception as e:
        logger.error(f"Error starting monitoring: {e}")
        return error_response(f"Failed to start monitoring: {str(e)}", 500)


@system_bp.route("/system/data-consistency/monitor", methods=["DELETE"])
@handle_api_errors
def stop_consistency_monitoring():
    """Stop automatic consistency monitoring"""
    consistency_monitor = current_app.consistency_monitor
    
    try:
        result = consistency_monitor.stop_monitoring()
        return success_response(result, "Consistency monitoring stopped")
    except Exception as e:
        logger.error(f"Error stopping monitoring: {e}")
        return error_response(f"Failed to stop monitoring: {str(e)}", 500)