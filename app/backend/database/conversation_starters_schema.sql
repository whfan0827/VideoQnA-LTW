-- Library Conversation Starters Database Schema
CREATE TABLE IF NOT EXISTS library_conversation_starters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    library_name TEXT NOT NULL,
    starter_text TEXT NOT NULL,
    starter_value TEXT NOT NULL,
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_library_conversation_starters ON library_conversation_starters(library_name);
CREATE INDEX IF NOT EXISTS idx_library_starters_order ON library_conversation_starters(library_name, display_order);

-- Trigger to update the updated_at timestamp
CREATE TRIGGER IF NOT EXISTS update_conversation_starters_timestamp 
    AFTER UPDATE ON library_conversation_starters
BEGIN
    UPDATE library_conversation_starters SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Insert default conversation starters for existing libraries
-- This will be populated by the migration script