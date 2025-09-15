"""
Flask Blueprint routes package
"""
from .video_routes import video_bp
from .library_routes import library_bp
from .task_routes import task_bp
from .api_routes import api_bp
from .system_routes import system_bp

# List of all blueprints to register
BLUEPRINTS = [
    video_bp,
    library_bp, 
    task_bp,
    api_bp,
    system_bp
]