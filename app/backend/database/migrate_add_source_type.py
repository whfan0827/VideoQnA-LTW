#!/usr/bin/env python3
"""
Database migration to add source_type and blob-related fields to video_index table.
This migration maintains backward compatibility with existing records.
"""

import sqlite3
import logging
from pathlib import Path
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_database(db_path: str = None):
    """
    Add new columns to support both local file and blob storage sources.
    
    Args:
        db_path: Path to the SQLite database file. If None, uses default location.
    """
    if db_path is None:
        backend_dir = Path(__file__).parent.parent
        db_path = backend_dir / "app_data.db"
    else:
        db_path = Path(db_path)
    
    if not db_path.exists():
        logger.error(f"Database file not found: {db_path}")
        return False
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Check if migration is needed
            cursor.execute("PRAGMA table_info(video_index)")
            columns = [column[1] for column in cursor.fetchall()]
            
            migration_needed = False
            new_columns = []
            
            if 'source_type' not in columns:
                new_columns.append(('source_type', 'TEXT DEFAULT "local_file"'))
                migration_needed = True
                
            if 'blob_url' not in columns:
                new_columns.append(('blob_url', 'TEXT NULL'))
                migration_needed = True
                
            if 'blob_container' not in columns:
                new_columns.append(('blob_container', 'TEXT NULL'))
                migration_needed = True
                
            if 'blob_name' not in columns:
                new_columns.append(('blob_name', 'TEXT NULL'))
                migration_needed = True
                
            if 'blob_metadata' not in columns:
                new_columns.append(('blob_metadata', 'TEXT NULL'))
                migration_needed = True
            
            if not migration_needed:
                logger.info("Database is already up to date")
                return True
            
            logger.info(f"Adding {len(new_columns)} new columns to video_index table")
            
            # Add new columns
            for column_name, column_def in new_columns:
                sql = f"ALTER TABLE video_index ADD COLUMN {column_name} {column_def}"
                logger.info(f"Executing: {sql}")
                cursor.execute(sql)
            
            # Update existing records to have source_type = 'local_file'
            cursor.execute("UPDATE video_index SET source_type = 'local_file' WHERE source_type IS NULL")
            updated_rows = cursor.rowcount
            
            # Create new indexes for blob-related columns
            try:
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_video_source_type ON video_index(source_type)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_video_blob ON video_index(blob_container, blob_name)")
                logger.info("Created indexes for new columns")
            except Exception as e:
                logger.warning(f"Could not create indexes: {e}")
            
            conn.commit()
            
            logger.info(f"Migration completed successfully")
            logger.info(f"Updated {updated_rows} existing records with source_type='local_file'")
            
            # Verify the migration
            cursor.execute("SELECT COUNT(*) FROM video_index")
            total_records = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM video_index WHERE source_type = 'local_file'")
            local_file_records = cursor.fetchone()[0]
            
            logger.info(f"Total records: {total_records}, Local file records: {local_file_records}")
            
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