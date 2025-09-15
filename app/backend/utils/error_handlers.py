"""
Error handling utilities for Flask API endpoints
"""
from functools import wraps
from flask import jsonify
import logging


class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass


def handle_api_errors(f):
    """Decorator to handle common API errors consistently"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValidationError as e:
            logging.warning(f"Validation error in {f.__name__}: {str(e)}")
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            logging.exception(f"Error in {f.__name__}")
            return jsonify({"error": str(e)}), 500
    return wrapper


def error_response(message: str, status_code: int = 400):
    """Create standardized error response"""
    return jsonify({"error": message}), status_code


def success_response(data=None, message: str = "Success"):
    """Create standardized success response"""
    response = {"message": message}
    if data is not None:
        response["data"] = data
    return jsonify(response), 200


def validate_required_fields(data, required_fields):
    """Validate that all required fields are present"""
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        raise ValidationError(f"Missing required fields: {', '.join(missing_fields)}")