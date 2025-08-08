# Database Manager - Unified Database Management System

This module provides centralized database management for the VideoQnA application.

## Database Structure

1. **Main Application Database** (`app_data.db`)
   - Tasks management
   - Video records
   - Application state

2. **Settings Database** (`settings.db`)
   - Library settings
   - AI templates
   - User preferences

## Usage

```python
from database_manager import DatabaseManager, SettingsManager

# For application data
db_manager = DatabaseManager()
db_manager.save_task(task_data)

# For settings
settings_manager = SettingsManager()
settings_manager.save_library_settings(library_name, settings)
```
