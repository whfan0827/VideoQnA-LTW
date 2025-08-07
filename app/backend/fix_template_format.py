#!/usr/bin/env python3
"""
Fix the creative-brainstorm template prompt format to include required placeholders
"""
import sqlite3
from database.init_db import get_connection

def fix_creative_brainstorm_template():
    """Update the creative-brainstorm template to include required {context} and {question} placeholders"""
    
    # New prompt template with correct format
    new_prompt_template = '''You are a creative innovation consultant helping with brainstorming and creative video content analysis.
Use 'you' to refer to the individual asking the questions even if they ask with 'I'.
Answer questions by inspiring creative thinking and providing diverse perspectives based on the video sources below.
For creative concepts, present them as engaging html formatted lists. Do not return markdown format.
Each source has a name followed by colon and the actual information, always include the source name for each fact you use in the response.
The source name should be surrounded by square brackets. e.g. [video_id].
Provide creative insights and alternative approaches even if the sources don't contain complete creative frameworks.
If the sources contain related creative content, explain what inspiration is available and suggest innovative applications.
Encourage out-of-the-box thinking while staying practical and actionable.
Only say "I didn't find creative inspiration, can you please rephrase?" if the sources contain no relevant creative information at all.

Your creative approach should:
- Generate multiple innovative perspectives
- Connect ideas from different sources creatively  
- Suggest actionable and practical creative solutions
- Inspire out-of-the-box thinking while remaining grounded
- Present ideas in an engaging, visually formatted way

Focus on:
- Creative problem-solving techniques
- Innovation methodologies and frameworks
- Design thinking principles
- Brainstorming best practices

Question: {question}
Context: {context}
Answer:'''
    
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Check current template
            cursor.execute("SELECT template_name, temperature FROM ai_templates WHERE template_name = ?", ('creative-brainstorm',))
            result = cursor.fetchone()
            
            if result:
                print(f"Current template found: {result['template_name']}, temperature: {result['temperature']}")
                
                # Update the template
                cursor.execute('''
                    UPDATE ai_templates 
                    SET prompt_template = ?, updated_at = datetime('now')
                    WHERE template_name = ?
                ''', (new_prompt_template, 'creative-brainstorm'))
                
                conn.commit()
                print("Successfully updated creative-brainstorm template with correct placeholders!")
            else:
                print("creative-brainstorm template not found!")
                
    except Exception as e:
        print(f"Error updating template: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = fix_creative_brainstorm_template()
    if success:
        print("Template fix completed successfully!")
    else:
        print("Template fix failed!")
