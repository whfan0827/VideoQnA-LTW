#!/usr/bin/env python3
"""
Test the improved prompt template
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

print("=== Testing Improved Prompt Template ===")

def test_improved_prompt():
    """Test the complete ask approach with improved prompt"""
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        
        from vi_search.prompt_content_db.chroma_db import ChromaDB
        from vi_search.language_models.azure_openai import OpenAI
        from vi_search.ask import RetrieveThenReadVectorApproach
        
        # Create components
        prompt_content_db = ChromaDB()
        language_models = OpenAI()
        approach = RetrieveThenReadVectorApproach(prompt_content_db, language_models)
        
        print("✅ Ask approach components created successfully")
        
        # Get available databases
        available_dbs = prompt_content_db.get_available_dbs()
        if not available_dbs:
            print("❌ No databases available for testing")
            return False
        
        # Test with the first available database
        test_db = available_dbs[0]
        print(f"🎯 Testing with database: {test_db}")
        
        # Test questions
        test_questions = [
            "how to set up YASKAWA GA700",
            "what is auto tuning in YASKAWA GA700",
            "how to configure motor parameters",
            "what are the initialization steps"
        ]
        
        for question in test_questions:
            print(f"\n❓ Question: {question}")
            
            overrides = {
                "index": test_db,
                "top": 3
            }
            
            # Run the approach
            result = approach.run(question, overrides)
            
            answer = result.get('answer', 'No answer')
            data_points = result.get('data_points', [])
            
            print(f"📊 Data points found: {len(data_points)}")
            print(f"💬 Answer: {answer[:300]}{'...' if len(answer) > 300 else ''}")
            
            # Check if it's still giving the generic "I didn't find" response
            if "I didn't find the answer, can you please rephrase?" in answer:
                print("   ⚠️ Still getting generic response")
            else:
                print("   ✅ Getting helpful response!")
            
            print("-" * 80)
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing improved prompt: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_improved_prompt()
