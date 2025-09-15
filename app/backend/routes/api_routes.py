"""
API routes for core functionality
"""
import logging
from flask import Blueprint, request, jsonify, current_app
from utils.error_handlers import handle_api_errors, error_response, success_response, ValidationError

# Create blueprint
api_bp = Blueprint('api', __name__)
logger = logging.getLogger(__name__)


@api_bp.route("/ask", methods=["POST"])
@handle_api_errors
def ask_question():
    """Process question and return answer using RAG approach"""
    if not request.json:
        raise ValidationError("Request must contain JSON")
    
    # Extract and validate required fields
    approach = request.json.get("approach", "rrrv")
    question = request.json.get("question")
    library_name = request.json.get("library_name")
    
    if not question:
        raise ValidationError("Question is required")
    if not library_name:
        raise ValidationError("Library name is required")
    
    # Get approach handler
    ask_approaches = current_app.ask_approaches
    if approach not in ask_approaches:
        raise ValidationError(f"Unknown approach: {approach}")
    
    # Validate library exists
    prompt_content_db = current_app.prompt_content_db
    available_dbs = prompt_content_db.get_available_dbs()
    if library_name not in available_dbs:
        raise ValidationError(f"Library '{library_name}' not found")
    
    # Process the question
    try:
        r = ask_approaches[approach].run(question, request.json)
        return jsonify(r)
    except Exception as e:
        logger.error(f"Error processing question: {e}")
        return error_response(f"Error processing question: {str(e)}", 500)


@api_bp.route("/indexes", methods=["GET"])
@handle_api_errors
def get_available_indexes():
    """Get list of available search indexes/databases"""
    prompt_content_db = current_app.prompt_content_db
    
    try:
        available_dbs = prompt_content_db.get_available_dbs()
        return success_response({
            "indexes": available_dbs,
            "count": len(available_dbs)
        })
    except Exception as e:
        logger.error(f"Error getting available indexes: {e}")
        return error_response(f"Error getting indexes: {str(e)}", 500)


@api_bp.route("/api/libraries/<library_name>/ai-parameters", methods=["GET"])
@handle_api_errors
def get_library_ai_parameters(library_name):
    """Get AI parameters for a specific library"""
    settings_service = current_app.settings_service
    
    try:
        settings = settings_service.get_settings(library_name)
        
        # Extract AI parameters
        ai_parameters = {
            "temperature": settings.get("temperature", 0.3),
            "max_tokens": settings.get("max_tokens", 1024),
            "semantic_ranker": settings.get("semantic_ranker", True)
        }
        
        return success_response(ai_parameters)
    except Exception as e:
        logger.error(f"Error getting AI parameters for {library_name}: {e}")
        return error_response(f"Error getting AI parameters: {str(e)}", 500)


@api_bp.route("/api/libraries/<library_name>/ai-parameters", methods=["PUT"])
@handle_api_errors
def update_library_ai_parameters(library_name):
    """Update AI parameters for a specific library"""
    if not request.json:
        raise ValidationError("Invalid JSON")
    
    settings_service = current_app.settings_service
    
    # Validate parameters
    valid_params = ['temperature', 'max_tokens', 'semantic_ranker']
    invalid_params = [key for key in request.json.keys() if key not in valid_params]
    if invalid_params:
        raise ValidationError(f"Invalid parameters: {', '.join(invalid_params)}")
    
    # Validate ranges
    if 'temperature' in request.json:
        temp = request.json['temperature']
        if not isinstance(temp, (int, float)) or temp < 0 or temp > 2:
            raise ValidationError("Temperature must be between 0 and 2")
    
    if 'max_tokens' in request.json:
        tokens = request.json['max_tokens']
        if not isinstance(tokens, int) or tokens < 1 or tokens > 8000:
            raise ValidationError("Max tokens must be between 1 and 8000")
    
    try:
        # Update settings
        settings_service.update_library_settings(library_name, request.json)
        
        return success_response(message=f"AI parameters updated for library '{library_name}'")
    except Exception as e:
        logger.error(f"Error updating AI parameters for {library_name}: {e}")
        return error_response(f"Error updating AI parameters: {str(e)}", 500)


@api_bp.route("/api/libraries/<library_name>/conversation-starters", methods=["GET"])
@handle_api_errors
def get_library_conversation_starters(library_name):
    """Get conversation starters for a specific library"""
    conversation_starters_service = current_app.conversation_starters_service
    
    try:
        starters = conversation_starters_service.get_library_starters(library_name)
        return success_response({"starters": starters})
    except Exception as e:
        logger.error(f"Error getting conversation starters for {library_name}: {e}")
        return error_response(f"Error getting conversation starters: {str(e)}", 500)


@api_bp.route("/api/libraries/<library_name>/conversation-starters", methods=["PUT"])
@handle_api_errors
def save_library_conversation_starters(library_name):
    """Save conversation starters for a specific library"""
    if not request.json or "starters" not in request.json:
        raise ValidationError("Invalid request: 'starters' field required")
    
    conversation_starters_service = current_app.conversation_starters_service
    starters = request.json["starters"]
    
    if not isinstance(starters, list):
        raise ValidationError("Starters must be a list")
    
    try:
        conversation_starters_service.save_library_starters(library_name, starters)
        return success_response(message=f"Conversation starters saved for library '{library_name}'")
    except Exception as e:
        logger.error(f"Error saving conversation starters for {library_name}: {e}")
        return error_response(f"Error saving conversation starters: {str(e)}", 500)