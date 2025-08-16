"""
Migration script for Library Conversation Starters
Migrates existing global conversation starters to library-specific starters
"""

import sqlite3
import json
import logging
from pathlib import Path
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

def migrate_conversation_starters():
    """Migrate conversation starters to library-specific format"""
    try:
        # 1. Create the conversation starters table
        schema_path = Path(__file__).parent / "conversation_starters_schema.sql"
        if schema_path.exists():
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema = f.read()
            
            with db_manager.get_settings_connection() as conn:
                conn.executescript(schema)
                conn.commit()
                logger.info("Conversation starters table created successfully")
        
        # 2. Get all existing libraries
        libraries = []
        with db_manager.get_settings_connection() as conn:
            cursor = conn.execute("SELECT DISTINCT library_name FROM library_settings")
            libraries = [row[0] for row in cursor.fetchall()]
        
        logger.info(f"Found {len(libraries)} existing libraries")
        
        # 3. Check if any library already has conversation starters
        existing_count = 0
        with db_manager.get_settings_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM library_conversation_starters")
            existing_count = cursor.fetchone()[0]
        
        if existing_count > 0:
            logger.info(f"Found {existing_count} existing conversation starters, skipping migration")
            return
        
        # 4. For each library, insert default conversation starters
        with db_manager.get_settings_connection() as conn:
            for library_name in libraries:
                for i, starter in enumerate(DEFAULT_CONVERSATION_STARTERS):
                    conn.execute("""
                        INSERT INTO library_conversation_starters 
                        (library_name, starter_text, starter_value, display_order)
                        VALUES (?, ?, ?, ?)
                    """, (library_name, starter["text"], starter["value"], i))
                
                logger.info(f"Migrated conversation starters for library: {library_name}")
            
            conn.commit()
        
        logger.info("Conversation starters migration completed successfully")
        
    except Exception as e:
        logger.error(f"Failed to migrate conversation starters: {e}")
        raise

def rollback_migration():
    """Rollback conversation starters migration"""
    try:
        with db_manager.get_settings_connection() as conn:
            conn.execute("DROP TABLE IF EXISTS library_conversation_starters")
            conn.commit()
        logger.info("Conversation starters migration rolled back")
    except Exception as e:
        logger.error(f"Failed to rollback migration: {e}")
        raise

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    migrate_conversation_starters()