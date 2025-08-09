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
            errors.append("Temperature must be between 0.0 and 1.0 (inclusive)")
        
        if self.max_tokens < 100 or self.max_tokens > 4000:
            errors.append("Max tokens must be between 100 and 4000")
        
        if self.prompt_template and '{context}' not in self.prompt_template:
            errors.append("Prompt template must contain {context} placeholder")
        
        if self.prompt_template and '{q}' not in self.prompt_template and '{question}' not in self.prompt_template:
            errors.append("Prompt template must contain {q} or {question} placeholder")
        
        return errors
