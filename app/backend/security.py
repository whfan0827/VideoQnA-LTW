# Security configuration for production environment
import os
from flask_talisman import Talisman
from flask_cors import CORS


def configure_security(app):
    """Configure security settings for production environment"""
    
    # Only apply in production
    if os.environ.get('FLASK_ENV') != 'production':
        return app
    
    # CORS configuration
    CORS(app, 
         origins=os.environ.get('ALLOWED_ORIGINS', '*').split(','),
         allow_headers=['Content-Type', 'Authorization'],
         methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
    
    # Security headers with Talisman - CSP optimized for Fluent UI
    csp = {
        'default-src': "'self'",
        'script-src': [
            "'self'",
            "'unsafe-inline'",  # Needed for Fluent UI and React
            'https://cdn.jsdelivr.net',
        ],
        'style-src': [
            "'self'",
            "'unsafe-inline'",  # Needed for Fluent UI dynamic styles
            'https://fonts.googleapis.com',
        ],
        'font-src': [
            "'self'",
            'https://fonts.gstatic.com',
        ],
        'img-src': [
            "'self'",
            'data:',
            'https:',  # Allow external images (for video thumbnails)
        ],
        'connect-src': [
            "'self'",
            'https://*.azure.com',
            'https://*.openai.azure.com',
        ],
        'media-src': [
            "'self'",
            'https:',  # Allow external video sources
        ],
    }
    
    Talisman(
        app,
        force_https=os.environ.get('FORCE_HTTPS', 'true').lower() == 'true',
        strict_transport_security=True,
        strict_transport_security_max_age=31536000,  # 1 year
        content_security_policy=csp,
        # Remove nonce to avoid conflict with 'unsafe-inline'
        content_security_policy_nonce_in=[],
        referrer_policy='strict-origin-when-cross-origin',
        permissions_policy={
            'geolocation': '()',
            'microphone': '()',
            'camera': '()',
        }
    )
    
    return app


def configure_logging_security():
    """Configure logging to avoid sensitive data exposure"""
    import logging
    
    class SensitiveDataFilter(logging.Filter):
        """Filter to remove sensitive data from logs"""
        
        SENSITIVE_PATTERNS = [
            'api_key', 'password', 'secret', 'token', 'auth',
            'AZURE_OPENAI_API_KEY', 'AZURE_SEARCH_KEY', 'AZURE_CLIENT_SECRET'
        ]
        
        def filter(self, record):
            if hasattr(record, 'msg'):
                msg = str(record.msg)
                for pattern in self.SENSITIVE_PATTERNS:
                    if pattern.lower() in msg.lower():
                        record.msg = msg.replace(pattern, '[REDACTED]')
            return True
    
    # Apply filter to all loggers
    for logger_name in ['', 'app', 'gunicorn', 'flask']:
        logger = logging.getLogger(logger_name)
        logger.addFilter(SensitiveDataFilter())