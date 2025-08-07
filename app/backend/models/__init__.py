from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class LibrarySettings:
    """Data model for library settings"""
    library_name: str
    prompt_template: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 800
    semantic_ranker: bool = True
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'library_name': self.library_name,
            'prompt_template': self.prompt_template,
            'temperature': self.temperature,
            'max_tokens': self.max_tokens,
            'semantic_ranker': self.semantic_ranker,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        """Create instance from dictionary"""
        return cls(
            id=data.get('id'),
            library_name=data['library_name'],
            prompt_template=data.get('prompt_template'),
            temperature=data.get('temperature', 0.7),
            max_tokens=data.get('max_tokens', 800),
            semantic_ranker=data.get('semantic_ranker', True),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None,
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else None
        )
    
    def validate(self):
        """Validate settings values"""
        errors = []
        
        if not self.library_name or not self.library_name.strip():
            errors.append("Library name is required")
        
        if self.temperature < 0.0 or self.temperature > 1.0:
            errors.append("Temperature must be between 0.0 and 1.0")
        
        if self.max_tokens < 100 or self.max_tokens > 4000:
            errors.append("Max tokens must be between 100 and 4000")
        
        if self.prompt_template and '{context}' not in self.prompt_template:
            errors.append("Prompt template must contain {context} placeholder")
        
        if self.prompt_template and '{q}' not in self.prompt_template and '{question}' not in self.prompt_template:
            errors.append("Prompt template must contain {q} or {question} placeholder")
        
        return errors


@dataclass
class AITemplate:
    """Data model for AI prompt templates"""
    template_name: str
    display_name: str
    description: Optional[str] = None
    category: str = "Custom"
    prompt_template: str = ""
    temperature: float = 0.7
    max_tokens: int = 800
    semantic_ranker: bool = True
    is_system_default: bool = False
    created_by: str = "User"
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'template_name': self.template_name,
            'display_name': self.display_name,
            'description': self.description,
            'category': self.category,
            'prompt_template': self.prompt_template,
            'temperature': self.temperature,
            'max_tokens': self.max_tokens,
            'semantic_ranker': self.semantic_ranker,
            'is_system_default': self.is_system_default,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        """Create instance from dictionary"""
        return cls(
            id=data.get('id'),
            template_name=data['template_name'],
            display_name=data['display_name'],
            description=data.get('description'),
            category=data.get('category', 'Custom'),
            prompt_template=data.get('prompt_template', ''),
            temperature=data.get('temperature', 0.7),
            max_tokens=data.get('max_tokens', 800),
            semantic_ranker=data.get('semantic_ranker', True),
            is_system_default=data.get('is_system_default', False),
            created_by=data.get('created_by', 'User'),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None,
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else None
        )
    
    def validate(self):
        """Validate template values"""
        errors = []
        
        if not self.template_name or not self.template_name.strip():
            errors.append("Template name is required")
        
        if not self.display_name or not self.display_name.strip():
            errors.append("Display name is required")
            
        if not self.prompt_template or not self.prompt_template.strip():
            errors.append("Prompt template is required")
        
        if self.temperature < 0.1 or self.temperature > 2.0:
            errors.append("Temperature must be between 0.1 and 2.0")
        
        if self.max_tokens < 100 or self.max_tokens > 4000:
            errors.append("Max tokens must be between 100 and 4000")
        
        if len(self.prompt_template) > 5000:
            errors.append("Prompt template must be less than 5000 characters")
        
        return errors
