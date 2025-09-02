#!/usr/bin/env python3
"""
Database migration to add source_language field to video_index table.
This migration maintains backward compatibility with existing records.
"""

import sqlite3
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_database(db_path: str = None):
    """
    Add source_language column to support storing the language used during video upload.
    
    Args:
        db_path: Path to the SQLite database file. If None, uses default location.
    """
    if db_path is None:
        backend_dir = Path(__file__).parent.parent
        db_path = backend_dir / "app_data.db"
    else:
        db_path = Path(db_path)
    
    if not db_path.exists():
        logger.warning(f"Database file not found: {db_path}. It will be created when the app starts.")
        return True
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Check if migration is needed
            cursor.execute("PRAGMA table_info(video_index)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'source_language' in columns:
                logger.info("source_language column already exists")
                return True
                
            logger.info("Adding source_language column to video_index table")
            
            # Add source_language column
            sql = "ALTER TABLE video_index ADD COLUMN source_language TEXT DEFAULT 'auto'"
            logger.info(f"Executing: {sql}")
            cursor.execute(sql)
            
            # Update existing records to have source_language = 'auto'
            cursor.execute("UPDATE video_index SET source_language = 'auto' WHERE source_language IS NULL")
            updated_rows = cursor.rowcount
            
            # Create index for source_language column
            try:
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_video_source_language ON video_index(source_language)")
                logger.info("Created index for source_language column")
            except Exception as e:
                logger.warning(f"Could not create index: {e}")
            
            conn.commit()
            
            logger.info(f"Migration completed successfully")
            logger.info(f"Updated {updated_rows} existing records with source_language='auto'")
            
            # Verify the migration
            cursor.execute("SELECT COUNT(*) FROM video_index")
            total_records = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM video_index WHERE source_language = 'auto'")
            auto_language_records = cursor.fetchone()[0]
            
            logger.info(f"Total records: {total_records}, Auto language records: {auto_language_records}")
            
            return True
            
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = migrate_database()
    if success:
        print("Database migration completed successfully")
    else:
        print("Database migration failed")
        exit(1)