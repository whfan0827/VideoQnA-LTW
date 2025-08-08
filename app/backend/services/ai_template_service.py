import sqlite3
from typing import List, Optional, Dict, Any
from datetime import datetime
from database.database_manager import db_manager
from models import AITemplate
import threading
import time

class AITemplateService:
    """Service for managing AI prompt templates"""
    
    def __init__(self):
        self._cache = {}
        self._cache_lock = threading.RLock()
        self._last_updated = None
        
    def get_all_templates(self) -> List[Dict[str, Any]]:
        """Get all AI templates"""
        with self._cache_lock:
            # Check cache first
            if self._cache and self._last_updated:
                cache_age = time.time() - self._last_updated
                if cache_age < 300:  # 5 minutes cache
                    return list(self._cache.values())
            
            # Load from database
            with db_manager.get_settings_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM ai_templates 
                    ORDER BY is_system_default DESC, category, display_name
                """)
                rows = cursor.fetchall()
                
                templates = []
                self._cache = {}
                
                for row in rows:
                    template_dict = dict(row)
                    template_dict['promptTemplate'] = template_dict.pop('prompt_template')
                    template_dict['maxTokens'] = template_dict.pop('max_tokens')
                    template_dict['semanticRanker'] = bool(template_dict.pop('semantic_ranker'))
                    template_dict['isSystemDefault'] = bool(template_dict.pop('is_system_default'))
                    template_dict['templateName'] = template_dict.pop('template_name')
                    template_dict['displayName'] = template_dict.pop('display_name')
                    template_dict['createdBy'] = template_dict.pop('created_by')
                    template_dict['createdAt'] = template_dict.pop('created_at')
                    template_dict['updatedAt'] = template_dict.pop('updated_at')
                    
                    templates.append(template_dict)
                    self._cache[template_dict['templateName']] = template_dict
                
                self._last_updated = time.time()
                return templates
    
    def get_template(self, template_name: str) -> Optional[Dict[str, Any]]:
        """Get a specific template by name"""
        templates = self.get_all_templates()
        return next((t for t in templates if t['templateName'] == template_name), None)
    
    def create_template(self, template_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new AI template"""
        # Validate template data
        template = AITemplate(
            template_name=template_data['templateName'],
            display_name=template_data['displayName'],
            description=template_data.get('description'),
            category=template_data.get('category', 'Custom'),
            prompt_template=template_data['promptTemplate'],
            temperature=template_data.get('temperature', 0.7),
            max_tokens=template_data.get('maxTokens', 800),
            semantic_ranker=template_data.get('semanticRanker', True),
            is_system_default=False,  # User templates are never system defaults
            created_by=template_data.get('createdBy', 'User')
        )
        
        errors = template.validate()
        if errors:
            raise ValueError('; '.join(errors))
        
        # Save to database
        with db_manager.get_settings_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO ai_templates 
                (template_name, display_name, description, category, prompt_template, 
                 temperature, max_tokens, semantic_ranker, is_system_default, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                template.template_name,
                template.display_name,
                template.description,
                template.category,
                template.prompt_template,
                template.temperature,
                template.max_tokens,
                template.semantic_ranker,
                template.is_system_default,
                template.created_by
            ))
            
            template_id = cursor.lastrowid
            conn.commit()
        
        # Clear cache
        self._clear_cache()
        
        # Return the created template
        created_template = self.get_template(template.template_name)
        if not created_template:
            raise RuntimeError("Failed to retrieve created template")
        return created_template
    
    def update_template(self, template_name: str, template_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing template"""
        # Check if template exists and is not system default
        existing = self.get_template(template_name)
        if not existing:
            raise ValueError(f"Template '{template_name}' not found")
        
        if existing['isSystemDefault']:
            raise ValueError("Cannot modify system default templates")
        
        # Validate updated data
        template = AITemplate(
            template_name=template_name,  # Keep original name
            display_name=template_data['displayName'],
            description=template_data.get('description'),
            category=template_data.get('category', 'Custom'),
            prompt_template=template_data['promptTemplate'],
            temperature=template_data.get('temperature', 0.7),
            max_tokens=template_data.get('maxTokens', 800),
            semantic_ranker=template_data.get('semanticRanker', True),
            is_system_default=False,
            created_by=existing['createdBy']
        )
        
        errors = template.validate()
        if errors:
            raise ValueError('; '.join(errors))
        
        # Update in database
        with db_manager.get_settings_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE ai_templates SET
                    display_name = ?,
                    description = ?,
                    category = ?,
                    prompt_template = ?,
                    temperature = ?,
                    max_tokens = ?,
                    semantic_ranker = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE template_name = ? AND is_system_default = 0
            """, (
                template.display_name,
                template.description,
                template.category,
                template.prompt_template,
                template.temperature,
                template.max_tokens,
                template.semantic_ranker,
                template_name
            ))
            
            if cursor.rowcount == 0:
                raise ValueError(f"Template '{template_name}' not found or is system default")
            
            conn.commit()
        
        # Clear cache
        self._clear_cache()
        
        updated_template = self.get_template(template_name)
        if not updated_template:
            raise RuntimeError("Failed to retrieve updated template")
        return updated_template
    
    def delete_template(self, template_name: str):
        """Delete a template (only user templates)"""
        # Check if template exists and is not system default
        existing = self.get_template(template_name)
        if not existing:
            raise ValueError(f"Template '{template_name}' not found")
        
        if existing['isSystemDefault']:
            raise ValueError("Cannot delete system default templates")
        
        # Delete from database
        with db_manager.get_settings_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM ai_templates 
                WHERE template_name = ? AND is_system_default = 0
            """, (template_name,))
            
            if cursor.rowcount == 0:
                raise ValueError(f"Template '{template_name}' not found or is system default")
            
            conn.commit()
        
        # Clear cache
        self._clear_cache()
    
    def apply_template_to_library(self, template_name: str, library_name: str, settings_service):
        """Apply a template's settings to a specific library"""
        template = self.get_template(template_name)
        if not template:
            raise ValueError(f"Template '{template_name}' not found")
        
        # Prepare settings data
        settings_data = {
            'promptTemplate': template['promptTemplate'],
            'temperature': template['temperature'],
            'maxTokens': template['maxTokens'],
            'semanticRanker': template['semanticRanker']
        }
        
        # Save to library settings
        settings_service.save_settings(library_name, settings_data)
        
        return {"message": f"Template '{template['displayName']}' applied to library '{library_name}'"}
    
    def get_templates_by_category(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get templates grouped by category"""
        templates = self.get_all_templates()
        categories = {}
        
        for template in templates:
            category = template.get('category', 'Custom')
            if category not in categories:
                categories[category] = []
            categories[category].append(template)
        
        return categories
    
    def _clear_cache(self):
        """Clear the template cache"""
        with self._cache_lock:
            self._cache = {}
            self._last_updated = None


def init_ai_templates_database():
    """Initialize the AI templates database with schema"""
    import os
    from pathlib import Path
    
    # Get schema file path
    schema_path = Path(__file__).parent.parent / "database" / "ai_templates_schema.sql"
    
    if not schema_path.exists():
        print(f"AI templates schema file not found: {schema_path}")
        return
    
    # Read and execute schema
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema = f.read()
    
    with db_manager.get_settings_connection() as conn:
        conn.executescript(schema)
        conn.commit()
        print("AI templates database initialized successfully")
