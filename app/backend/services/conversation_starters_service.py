"""
ConversationStartersService - Manages library-specific conversation starters
"""

from typing import List, Dict, Any, Optional
import logging
import threading
import time
from database.database_manager import db_manager

logger = logging.getLogger(__name__)

DEFAULT_CONVERSATION_STARTERS = [
    {
        "text": "What insights are included with Azure AI Video Indexer?",
        "value": "What insights are included with Azure AI Video Indexer?"
    },
    {
        "text": "What is OCR?",
        "value": "What is OCR?"
    },
    {
        "text": "What is the distance to Mars?",
        "value": "What is the distance to Mars?"
    }
]

class ConversationStartersService:
    """Service for managing library-specific conversation starters"""
    
    def __init__(self):
        self._cache = {}
        self._cache_lock = threading.RLock()
        self._last_updated = {}
        
    def get_library_starters(self, library_name: str) -> List[Dict[str, str]]:
        """Get conversation starters for a specific library"""
        with self._cache_lock:
            # Check cache first
            if library_name in self._cache:
                cached_starters, cache_time = self._cache[library_name]
                # Check if cache is still valid (5 minutes)
                if time.time() - cache_time < 300:
                    return cached_starters
            
            # Load from database
            try:
                with db_manager.get_settings_connection() as conn:
                    cursor = conn.execute("""
                        SELECT starter_text, starter_value 
                        FROM library_conversation_starters 
                        WHERE library_name = ? 
                        ORDER BY display_order, created_at
                    """, (library_name,))
                    
                    rows = cursor.fetchall()
                    
                    if rows:
                        starters = [{"text": row[0], "value": row[1]} for row in rows]
                    else:
                        # No library-specific starters found, return defaults
                        starters = DEFAULT_CONVERSATION_STARTERS.copy()
                        logger.info(f"No conversation starters found for library {library_name}, using defaults")
                    
                    # Cache the result
                    self._cache[library_name] = (starters, time.time())
                    return starters
                    
            except Exception as e:
                logger.error(f"Error loading conversation starters for library {library_name}: {e}")
                return DEFAULT_CONVERSATION_STARTERS.copy()
    
    def save_library_starters(self, library_name: str, starters: List[Dict[str, str]]) -> None:
        """Save conversation starters for a specific library"""
        try:
            # Validate input
            if not isinstance(starters, list):
                raise ValueError("Starters must be a list")
            
            for i, starter in enumerate(starters):
                if not isinstance(starter, dict) or "text" not in starter or "value" not in starter:
                    raise ValueError(f"Invalid starter format at index {i}")
                if not starter["text"].strip():
                    raise ValueError(f"Empty starter text at index {i}")
            
            with db_manager.get_settings_connection() as conn:
                # Delete existing starters for this library
                conn.execute("""
                    DELETE FROM library_conversation_starters 
                    WHERE library_name = ?
                """, (library_name,))
                
                # Insert new starters
                for i, starter in enumerate(starters):
                    conn.execute("""
                        INSERT INTO library_conversation_starters 
                        (library_name, starter_text, starter_value, display_order)
                        VALUES (?, ?, ?, ?)
                    """, (library_name, starter["text"].strip(), starter["value"].strip(), i))
                
                conn.commit()
                logger.info(f"Saved {len(starters)} conversation starters for library {library_name}")
            
            # Clear cache for this library
            with self._cache_lock:
                if library_name in self._cache:
                    del self._cache[library_name]
            
        except Exception as e:
            logger.error(f"Error saving conversation starters for library {library_name}: {e}")
            raise
    
    def get_default_starters(self) -> List[Dict[str, str]]:
        """Get default conversation starters"""
        return DEFAULT_CONVERSATION_STARTERS.copy()
    
    def get_all_libraries_starters(self) -> Dict[str, List[Dict[str, str]]]:
        """Get conversation starters for all libraries"""
        try:
            result = {}
            
            with db_manager.get_settings_connection() as conn:
                # Get all libraries that have conversation starters
                cursor = conn.execute("""
                    SELECT DISTINCT library_name 
                    FROM library_conversation_starters 
                    ORDER BY library_name
                """)
                
                libraries = [row[0] for row in cursor.fetchall()]
                
                # Get starters for each library
                for library_name in libraries:
                    result[library_name] = self.get_library_starters(library_name)
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting all libraries starters: {e}")
            return {}
    
    def delete_library_starters(self, library_name: str) -> None:
        """Delete all conversation starters for a specific library"""
        try:
            with db_manager.get_settings_connection() as conn:
                cursor = conn.execute("""
                    DELETE FROM library_conversation_starters 
                    WHERE library_name = ?
                """, (library_name,))
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                logger.info(f"Deleted {deleted_count} conversation starters for library {library_name}")
            
            # Clear cache
            with self._cache_lock:
                if library_name in self._cache:
                    del self._cache[library_name]
                    
        except Exception as e:
            logger.error(f"Error deleting conversation starters for library {library_name}: {e}")
            raise
    
    def clear_cache(self, library_name: Optional[str] = None) -> None:
        """Clear conversation starters cache"""
        with self._cache_lock:
            if library_name:
                if library_name in self._cache:
                    del self._cache[library_name]
            else:
                self._cache.clear()
    
    def get_library_starter_count(self, library_name: str) -> int:
        """Get the number of conversation starters for a library"""
        try:
            with db_manager.get_settings_connection() as conn:
                cursor = conn.execute("""
                    SELECT COUNT(*) 
                    FROM library_conversation_starters 
                    WHERE library_name = ?
                """, (library_name,))
                
                return cursor.fetchone()[0]
                
        except Exception as e:
            logger.error(f"Error getting starter count for library {library_name}: {e}")
            return 0

# Global instance
conversation_starters_service = ConversationStartersService()