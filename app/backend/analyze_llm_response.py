#!/usr/bin/env python3
"""
Detailed analysis of the LLM response issue
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

print("=== Detailed LLM Response Analysis ===")

def analyze_retrieval_and_response():
    """Analyze what's being retrieved and why LLM is responding the way it is"""
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        
        from vi_search.prompt_content_db.chroma_db import ChromaDB
        from vi_search.language_models.azure_openai import OpenAI
        from vi_search.utils.ask_templates import ask_templates
        
        # Create components
        prompt_content_db = ChromaDB()
        language_models = OpenAI()
        
        print("✅ Components created successfully")
        
        # Get available databases
        available_dbs = prompt_content_db.get_available_dbs()
        if not available_dbs:
            print("❌ No databases available")
            return False
        
        test_db = available_dbs[0]
        prompt_content_db.set_db(test_db)
        print(f"🎯 Using database: {test_db}")
        
        # Test the exact same query
        test_question = "how to set up YASKAWA GA700"
        print(f"❓ Question: {test_question}")
        
        # Step 1: Get embeddings
        print("\n🔍 Step 1: Getting embeddings for question...")
        embeddings_vector = language_models.get_text_embeddings(test_question)
        print(f"   ✅ Embeddings generated: {len(embeddings_vector)} dimensions")
        
        # Step 2: Vector search
        print("\n📊 Step 2: Performing vector search...")
        docs_by_id, results_content = prompt_content_db.vector_search(embeddings_vector, n_results=3)
        
        print(f"   📈 Found {len(results_content)} results")
        print("\n   📋 Retrieved content:")
        for i, content in enumerate(results_content):
            print(f"   {i+1}. {content}")
            print(f"      (Length: {len(content)} characters)")
            print()
        
        # Step 3: Build the prompt
        print("\n🧠 Step 3: Building the prompt...")
        all_content = "\n".join(results_content)
        
        sys_prompt = ask_templates["default_system_prompt"]
        user_prompt = ask_templates["default_user_template"].format(q=test_question, retrieved=all_content)
        
        print(f"   📝 System prompt length: {len(sys_prompt)} characters")
        print(f"   📝 User prompt length: {len(user_prompt)} characters")
        
        print(f"\n   🎯 Full User Prompt:")
        print("   " + "="*80)
        print(user_prompt)
        print("   " + "="*80)
        
        # Step 4: Get LLM response
        print("\n🤖 Step 4: Getting LLM response...")
        completion = language_models.chat(
            sys_prompt=sys_prompt, 
            user_prompt=user_prompt, 
            temperature=0.7
        )
        
        print(f"   💬 LLM Response: {completion}")
        
        # Step 5: Analysis
        print("\n🔬 Step 5: Analysis...")
        
        # Check if retrieved content actually contains setup information
        setup_keywords = ['setup', 'install', 'configuration', 'connect', 'wiring', 'parameter', 'tuning']
        found_keywords = []
        for keyword in setup_keywords:
            if keyword.lower() in all_content.lower():
                found_keywords.append(keyword)
        
        print(f"   🔍 Setup-related keywords found: {found_keywords}")
        
        # Check content quality
        if len(all_content.strip()) < 100:
            print("   ⚠️ Retrieved content is very short - might not contain enough information")
        
        if 'YASKAWA' in all_content and 'GA700' in all_content:
            print("   ✅ Content contains YASKAWA GA700 references")
        else:
            print("   ❌ Content doesn't contain clear YASKAWA GA700 references")
        
        # Check if content has actual instructional content
        instructional_words = ['step', 'first', 'then', 'next', 'procedure', 'instruction', 'how to']
        found_instructional = []
        for word in instructional_words:
            if word.lower() in all_content.lower():
                found_instructional.append(word)
        
        print(f"   📖 Instructional keywords found: {found_instructional}")
        
        # Try with a less restrictive prompt
        print("\n🧪 Step 6: Testing with less restrictive prompt...")
        relaxed_sys_prompt = """You are an intelligent assistant helping customers with their video questions.
Use 'you' to refer to the individual asking the questions even if they ask with 'I'.
Answer the following question using the data provided in the sources below.
Each source has a name followed by colon and the actual information, always include the source name for each fact you use in the response.
The source name should be surrounded by square brackets. e.g. [video_id].
Provide helpful information even if the sources don't contain complete step-by-step instructions.
If the sources contain related information, explain what information is available and suggest how it might be helpful."""

        relaxed_completion = language_models.chat(
            sys_prompt=relaxed_sys_prompt, 
            user_prompt=user_prompt, 
            temperature=0.7
        )
        
        print(f"   💬 Relaxed LLM Response: {relaxed_completion}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in analysis: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    analyze_retrieval_and_response()
