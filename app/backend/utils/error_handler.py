"""
Unified Error Handling for VideoQnA Application

Provides consistent error handling patterns throughout the application.
"""

import logging
from typing import Optional, Dict, Any
from flask import jsonify
from werkzeug.exceptions import HTTPException


logger = logging.getLogger(__name__)


class AppError(Exception):
    """
    Base application error class with structured error information.
    """
    
    def __init__(self, message: str, error_code: str = "GENERAL_ERROR", 
                 status_code: int = 500, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            'error': self.message,
            'error_code': self.error_code,
            'details': self.details
        }


class ValidationError(AppError):
    """Validation errors (400 status)"""
    
    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR", 
            status_code=400,
            details={'field': field} if field else {}
        )


class NotFoundError(AppError):
    """Resource not found errors (404 status)"""
    
    def __init__(self, message: str, resource_type: Optional[str] = None):
        super().__init__(
            message=message,
            error_code="NOT_FOUND",
            status_code=404,
            details={'resource_type': resource_type} if resource_type else {}
        )


class ConfigurationError(AppError):
    """Configuration errors (500 status)"""
    
    def __init__(self, message: str, config_key: Optional[str] = None):
        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            status_code=500,
            details={'config_key': config_key} if config_key else {}
        )


class ExternalServiceError(AppError):
    """External service errors (502 status)"""
    
    def __init__(self, message: str, service_name: str):
        super().__init__(
            message=message,
            error_code="EXTERNAL_SERVICE_ERROR",
            status_code=502,
            details={'service': service_name}
        )


class ErrorHandler:
    """
    Centralized error handling utilities
    """
    
    @staticmethod
    def handle_flask_error(error) -> tuple:
        """
        Handle Flask application errors and return appropriate JSON response
        """
        if isinstance(error, AppError):
            logger.error(f"Application error: {error.message}", extra={'details': error.details})
            return jsonify(error.to_dict()), error.status_code
        
        elif isinstance(error, HTTPException):
            logger.error(f"HTTP error: {error.description}")
            return jsonify({
                'error': error.description,
                'error_code': 'HTTP_ERROR'
            }), error.code
        
        else:
            # Unexpected error
            logger.exception(f"Unexpected error: {str(error)}")
            return jsonify({
                'error': 'Internal server error',
                'error_code': 'INTERNAL_ERROR'
            }), 500
    
    @staticmethod
    def log_and_raise(error_class, message: str, **kwargs):
        """
        Log an error and raise the specified exception class
        """
        logger.error(message, extra={'kwargs': kwargs})
        raise error_class(message, **kwargs)
    
    @staticmethod
    def safe_execute(func, *args, **kwargs):
        """
        Execute a function with error handling, returning (result, error) tuple
        """
        try:
            result = func(*args, **kwargs)
            return result, None
        except Exception as e:
            logger.exception(f"Error executing {func.__name__}: {str(e)}")
            return None, e


# Error handling decorators
def handle_api_errors(func):
    """
    Decorator for API endpoints to handle errors consistently
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except AppError as e:
            return jsonify(e.to_dict()), e.status_code
        except Exception as e:
            logger.exception(f"Unexpected error in {func.__name__}: {str(e)}")
            return jsonify({
                'error': 'Internal server error',
                'error_code': 'INTERNAL_ERROR'
            }), 500
    
    wrapper.__name__ = func.__name__
    return wrapper