-- Library Settings Database Schema
CREATE TABLE IF NOT EXISTS library_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    library_name TEXT UNIQUE NOT NULL,
    prompt_template TEXT,
    temperature REAL DEFAULT 0.7,
    max_tokens INTEGER DEFAULT 800,
    semantic_ranker BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_library_name ON library_settings(library_name);

-- Trigger to update the updated_at timestamp
CREATE TRIGGER IF NOT EXISTS update_library_settings_timestamp 
    AFTER UPDATE ON library_settings
BEGIN
    UPDATE library_settings SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;
