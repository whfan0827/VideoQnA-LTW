from typing import Optional, Dict, Any
from datetime import datetime
from database.init_db import get_connection
from models import LibrarySettings
from vi_search.utils.ask_templates import ask_templates
import threading
import time

class SettingsService:
    """Service for managing library settings with hot reload capability"""
    
    def __init__(self):
        self._cache = {}
        self._cache_lock = threading.RLock()
        self._last_updated = {}
        
    def get_settings(self, library_name: str) -> Dict[str, Any]:
        """Get settings for a library with caching"""
        with self._cache_lock:
            # Check cache first
            if library_name in self._cache:
                cached_settings, cache_time = self._cache[library_name]
                
                # Check if cache is still valid (5 minutes)
                if time.time() - cache_time < 300:
                    return cached_settings
            
            # Load from database
            with get_connection() as conn:
                cursor = conn.execute(
                    "SELECT * FROM library_settings WHERE library_name = ?",
                    (library_name,)
                )
                row = cursor.fetchone()
                
                if row:
                    settings = LibrarySettings(
                        id=row['id'],
                        library_name=row['library_name'],
                        prompt_template=row['prompt_template'],
                        temperature=row['temperature'],
                        max_tokens=row['max_tokens'],
                        semantic_ranker=bool(row['semantic_ranker']),
                        created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
                        updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
                    )
                else:
                    # Return default settings if not found
                    settings = LibrarySettings(
                        library_name=library_name,
                        prompt_template=ask_templates['default_system_prompt'],
                        temperature=0.7,
                        max_tokens=800,
                        semantic_ranker=True
                    )
                
                # Convert to dict for API response
                settings_dict = {
                    'promptTemplate': settings.prompt_template,
                    'temperature': settings.temperature,
                    'maxTokens': settings.max_tokens,
                    'semanticRanker': settings.semantic_ranker
                }
                
                # Cache the result
                self._cache[library_name] = (settings_dict, time.time())
                
                return settings_dict
    
    def save_settings(self, library_name: str, settings_data: Dict[str, Any]) -> LibrarySettings:
        """Save settings for a library"""
        # Convert from API format to internal format
        settings = LibrarySettings(
            library_name=library_name,
            prompt_template=settings_data.get('promptTemplate'),
            temperature=settings_data.get('temperature', 0.7),
            max_tokens=settings_data.get('maxTokens', 800),
            semantic_ranker=settings_data.get('semanticRanker', True)
        )
        
        # Validate settings
        validation_errors = settings.validate()
        if validation_errors:
            raise ValueError(f"Validation errors: {', '.join(validation_errors)}")
        
        with get_connection() as conn:
            # Check if settings already exist
            cursor = conn.execute(
                "SELECT id FROM library_settings WHERE library_name = ?",
                (library_name,)
            )
            existing = cursor.fetchone()
            
            if existing:
                # Update existing settings
                conn.execute("""
                    UPDATE library_settings 
                    SET prompt_template = ?, temperature = ?, max_tokens = ?, 
                        semantic_ranker = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE library_name = ?
                """, (
                    settings.prompt_template,
                    settings.temperature,
                    settings.max_tokens,
                    settings.semantic_ranker,
                    library_name
                ))
            else:
                # Insert new settings
                cursor = conn.execute("""
                    INSERT INTO library_settings 
                    (library_name, prompt_template, temperature, max_tokens, semantic_ranker)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    library_name,
                    settings.prompt_template,
                    settings.temperature,
                    settings.max_tokens,
                    settings.semantic_ranker
                ))
                settings.id = cursor.lastrowid
            
            conn.commit()
        
        # Invalidate cache
        with self._cache_lock:
            if library_name in self._cache:
                del self._cache[library_name]
        
        # Record update time for hot reload
        self._last_updated[library_name] = time.time()
        
        return settings
    
    def clear_cache(self, library_name: Optional[str] = None):
        """Clear settings cache"""
        with self._cache_lock:
            if library_name:
                if library_name in self._cache:
                    del self._cache[library_name]
            else:
                self._cache.clear()
    
    def get_all_libraries(self):
        """Get all library names that have settings"""
        with get_connection() as conn:
            cursor = conn.execute("SELECT DISTINCT library_name FROM library_settings")
            return [row['library_name'] for row in cursor.fetchall()]
    
    def delete_settings(self, library_name: str):
        """Delete settings for a library"""
        with get_connection() as conn:
            conn.execute("DELETE FROM library_settings WHERE library_name = ?", (library_name,))
            conn.commit()
        
        # Clear from cache
        with self._cache_lock:
            if library_name in self._cache:
                del self._cache[library_name]
    
    def get_settings_for_ai(self, library_name: str) -> Dict[str, Any]:
        """Get settings formatted for AI processing"""
        settings = self.get_settings(library_name)
        
        return {
            'sys_prompt': settings.get('promptTemplate'),
            'temperature': settings.get('temperature', 0.7),
            'max_tokens': settings.get('maxTokens', 800),
            'semantic_ranker': settings.get('semanticRanker', True)
        }

# Global instance
settings_service = SettingsService()
