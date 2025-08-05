#!/usr/bin/env python3
"""
Test what happens with Azure Video Indexer question
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

print("=== Testing Azure Video Indexer Question ===")

def test_azure_vi_question():
    """Test Azure Video Indexer question to see what content is retrieved"""
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        
        from vi_search.prompt_content_db.chroma_db import ChromaDB
        from vi_search.language_models.azure_openai import OpenAI
        
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
        
        # Test the Azure Video Indexer question
        test_question = "What insights are included with Azure AI Video Indexer?"
        print(f"❓ Question: {test_question}")
        
        # Get embeddings and search
        embeddings_vector = language_models.get_text_embeddings(test_question)
        docs_by_id, results_content = prompt_content_db.vector_search(embeddings_vector, n_results=3)
        
        print(f"\n📊 Found {len(results_content)} results")
        
        if results_content:
            print("\n📋 Retrieved content:")
            for i, content in enumerate(results_content):
                print(f"   {i+1}. {content[:200]}...")
                print()
        else:
            print("❌ No content retrieved - this is why you get the generic response!")
        
        # Show what's actually in the database
        print(f"\n📚 Database content summary:")
        collection_data = prompt_content_db.get_collection_data()
        doc_count = len(collection_data['ids']) if collection_data['ids'] else 0
        print(f"   Total documents: {doc_count}")
        
        if doc_count > 0:
            print(f"   Sample documents:")
            for i in range(min(3, doc_count)):
                doc_content = collection_data['documents'][i][:100] + "..." if len(collection_data['documents'][i]) > 100 else collection_data['documents'][i]
                print(f"      - {doc_content}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_azure_vi_question()
