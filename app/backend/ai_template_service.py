import sqlite3
import os
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'library.db')

@dataclass
class AITemplate:
    template_name: str
    display_name: str
    description: str
    category: str
    prompt_template: str
    temperature: float
    max_tokens: int
    semantic_ranker: bool
    is_system_default: bool
    created_by: str
    id: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class AITemplateService:
    def __init__(self):
        self._init_database()
        self._init_system_templates()
    
    def _init_database(self):
        """Initialize the database with required tables"""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        try:
            # Create ai_templates table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    template_name TEXT UNIQUE NOT NULL,
                    display_name TEXT NOT NULL,
                    description TEXT,
                    category TEXT NOT NULL,
                    prompt_template TEXT NOT NULL,
                    temperature REAL DEFAULT 0.7,
                    max_tokens INTEGER DEFAULT 800,
                    semantic_ranker BOOLEAN DEFAULT 1,
                    is_system_default BOOLEAN DEFAULT 0,
                    created_by TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create library_settings table if not exists
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS library_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    library_name TEXT UNIQUE NOT NULL,
                    prompt_template TEXT,
                    temperature REAL DEFAULT 0.7,
                    max_tokens INTEGER DEFAULT 800,
                    semantic_ranker BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            print("Database initialized successfully")
            
        except Exception as e:
            print(f"Error initializing database: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def _init_system_templates(self):
        """Initialize system default templates"""
        system_templates = [
            AITemplate(
                template_name='hr-recruitment',
                display_name='HR Recruitment Assistant',
                description='Professional HR recruitment and candidate evaluation assistant',
                category='HR',
                prompt_template='''You are a professional HR recruitment assistant specialized in candidate evaluation and interview processes.

Your role:
- Analyze candidate profiles and qualifications objectively
- Provide structured interview guidance and questions
- Evaluate skills match against job requirements
- Suggest best practices for fair and effective recruitment

Focus on:
- Professional communication standards
- Diversity and inclusion principles
- Legal compliance in hiring practices
- Evidence-based candidate assessment

Maintain a respectful, unbiased tone and provide actionable recruitment insights.

Question: {question}
Context: {context}
Answer:''',
                temperature=0.7,
                max_tokens=800,
                semantic_ranker=True,
                is_system_default=True,
                created_by='system'
            ),
            AITemplate(
                template_name='tech-support',
                display_name='Technical Support Specialist',
                description='Expert technical support for hardware and software issues',
                category='Technical',
                prompt_template='''You are an expert technical support specialist with deep knowledge across multiple technology domains.

Your expertise includes:
- Hardware and software troubleshooting
- Network connectivity and security issues
- System performance optimization
- Database and application support

Response format:
- Provide clear, step-by-step solutions
- Include relevant technical specifications
- Suggest preventive measures when applicable
- Offer alternative approaches for complex issues

Always prioritize user safety and data integrity in your recommendations.

Question: {question}
Context: {context}
Answer:''',
                temperature=0.5,
                max_tokens=1200,
                semantic_ranker=True,
                is_system_default=True,
                created_by='system'
            ),
            AITemplate(
                template_name='creative-brainstorm',
                display_name='Creative Brainstorming Partner',
                description='Innovative thinking and idea generation assistant',
                category='Creative',
                prompt_template='''You are a creative brainstorming partner designed to inspire innovative thinking and idea generation.

Your capabilities:
- Generate diverse creative concepts and approaches
- Build upon initial ideas with thoughtful extensions
- Provide cross-industry inspiration and examples
- Facilitate structured creative thinking processes

Approach:
- Ask clarifying questions to understand objectives
- Offer multiple creative directions to explore
- Combine existing concepts in novel ways
- Encourage experimentation and iteration

Foster an environment of open-minded exploration and creative risk-taking.

Question: {question}
Context: {context}
Answer:''',
                temperature=0.9,
                max_tokens=1000,
                semantic_ranker=True,
                is_system_default=True,
                created_by='system'
            ),
            AITemplate(
                template_name='training-instructor',
                display_name='Professional Training Instructor',
                description='Adult learning and professional development specialist',
                category='Education',
                prompt_template='''You are an experienced training instructor specializing in adult learning and professional development.

Your teaching philosophy:
- Adult learners bring valuable experience to the learning process
- Multiple learning styles require diverse instructional approaches
- Practical application reinforces theoretical concepts
- Continuous feedback improves learning outcomes

Instructional methods:
- Break complex topics into manageable segments
- Use real-world examples and case studies
- Encourage interactive participation and discussion
- Provide clear learning objectives and progress markers

Create engaging, professional learning experiences that respect learner expertise.

Question: {question}
Context: {context}
Answer:''',
                temperature=0.7,
                max_tokens=900,
                semantic_ranker=True,
                is_system_default=True,
                created_by='system'
            )
        ]
        
        for template in system_templates:
            self._create_template_if_not_exists(template)
    
    def _create_template_if_not_exists(self, template: AITemplate):
        """Create template if it doesn't exist"""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        try:
            # Check if template exists
            cursor.execute('SELECT id FROM ai_templates WHERE template_name = ?', (template.template_name,))
            if cursor.fetchone():
                return  # Template already exists
            
            # Create template
            cursor.execute('''
                INSERT INTO ai_templates 
                (template_name, display_name, description, category, prompt_template, 
                 temperature, max_tokens, semantic_ranker, is_system_default, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                template.template_name, template.display_name, template.description,
                template.category, template.prompt_template, template.temperature,
                template.max_tokens, template.semantic_ranker, template.is_system_default,
                template.created_by
            ))
            
            conn.commit()
            print(f"Created system template: {template.display_name}")
            
        except Exception as e:
            print(f"Error creating template {template.template_name}: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def get_all_templates(self) -> List[Dict[str, Any]]:
        """Get all templates"""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT id, template_name, display_name, description, category, 
                       prompt_template, temperature, max_tokens, semantic_ranker,
                       is_system_default, created_by, created_at, updated_at
                FROM ai_templates 
                ORDER BY is_system_default DESC, template_name
            ''')
            
            rows = cursor.fetchall()
            templates = []
            
            for row in rows:
                template = {
                    'id': row[0],
                    'templateName': row[1],
                    'displayName': row[2],
                    'description': row[3],
                    'category': row[4],
                    'promptTemplate': row[5],
                    'temperature': row[6],
                    'maxTokens': row[7],
                    'semanticRanker': bool(row[8]),
                    'isSystemDefault': bool(row[9]),
                    'createdBy': row[10],
                    'createdAt': row[11],
                    'updatedAt': row[12]
                }
                templates.append(template)
            
            return templates
            
        except Exception as e:
            print(f"Error getting templates: {e}")
            return []
        finally:
            conn.close()
    
    def create_template(self, template_data: Dict[str, Any]) -> bool:
        """Create a new template"""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO ai_templates 
                (template_name, display_name, description, category, prompt_template, 
                 temperature, max_tokens, semantic_ranker, is_system_default, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                template_data['templateName'],
                template_data['displayName'],
                template_data.get('description', ''),
                template_data['category'],
                template_data['promptTemplate'],
                template_data.get('temperature', 0.7),
                template_data.get('maxTokens', 800),
                template_data.get('semanticRanker', True),
                False,  # User templates are never system defaults
                template_data.get('createdBy', 'user')
            ))
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"Error creating template: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def apply_template_to_library(self, template_name: str, library_name: str) -> bool:
        """Apply template to library settings"""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        try:
            # Get template
            cursor.execute('''
                SELECT prompt_template, temperature, max_tokens, semantic_ranker
                FROM ai_templates 
                WHERE template_name = ?
            ''', (template_name,))
            
            template_data = cursor.fetchone()
            if not template_data:
                return False
            
            # Update or insert library settings
            cursor.execute('''
                INSERT OR REPLACE INTO library_settings 
                (library_name, prompt_template, temperature, max_tokens, semantic_ranker, updated_at)
                VALUES (?, ?, ?, ?, ?, datetime('now'))
            ''', (library_name, template_data[0], template_data[1], template_data[2], template_data[3]))
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"Error applying template: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

def main():
    """Initialize the service"""
    service = AITemplateService()
    
    print("\n" + "="*50)
    print("AI TEMPLATE SERVICE INITIALIZED")
    print("="*50)
    
    templates = service.get_all_templates()
    print(f"\nTotal templates: {len(templates)}")
    
    for template in templates:
        status = "System" if template['isSystemDefault'] else "Custom"
        print(f"• {template['displayName']} ({template['category']}) - {status}")

if __name__ == "__main__":
    main()
