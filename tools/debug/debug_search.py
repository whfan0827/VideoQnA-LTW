#!/usr/bin/env python3
"""
Debug search issues - Check what content exists in vi-asiadigital-talkshow-index
"""
import os
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "app" / "backend"
sys.path.insert(0, str(backend_path))

from dotenv import load_dotenv
load_dotenv(backend_path / ".env")

def debug_search_issue():
    """Main function to debug search issues"""
    
    # Initialize components
    print("=== Initializing components ===")
    
    search_db = os.environ.get("PROMPT_CONTENT_DB", "azure_search")
    print(f"Using database: {search_db}")
    
    if search_db == "azure_search":
        from vi_search.prompt_content_db.azure_search import AzureVectorSearch
        prompt_content_db = AzureVectorSearch()
    else:
        print(f"Unsupported database type: {search_db}")
        return
    
    # Initialize language model
    lang_model = os.environ.get("LANGUAGE_MODEL", "openai")
    print(f"Using language model: {lang_model}")
    
    if lang_model == "openai":
        from vi_search.language_models.azure_openai import OpenAI
        language_models = OpenAI()
    else:
        print(f"Unsupported language model: {lang_model}")
        return
    
    # Check database
    print("\n=== Checking database ===")
    available_dbs = prompt_content_db.get_available_dbs()
    print(f"Available databases: {available_dbs}")
    
    target_db = "vi-asiadigital-talkshow-index"
    if target_db not in available_dbs:
        print(f"❌ Target database '{target_db}' does not exist!")
        return
    
    print(f"✅ Target database '{target_db}' exists")
    
    # Switch to target database
    prompt_content_db.set_db(target_db)
    print(f"Switched to database: {prompt_content_db.db_name}")
    
    # Test search
    print("\n=== Testing search ===")
    test_queries = [
        "machine instruction index",
        "machine instruction index chinese", 
        "hello",
        "what is",
        "how to"
    ]
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        try:
            # Generate embeddings
            embeddings_vector = language_models.get_text_embeddings(query)
            print(f"  Embeddings vector dimension: {len(embeddings_vector)}")
            
            # Execute search
            docs_by_id, results_content = prompt_content_db.vector_search(embeddings_vector, n_results=5)
            print(f"  Search results count: {len(results_content)}")
            
            # Display result content
            for i, result in enumerate(results_content[:3]):  # Only show first 3
                print(f"  Result {i+1}: {result[:200]}{'...' if len(result) > 200 else ''}")
            
            if not results_content:
                print("  ❌ No search results!")
            
        except Exception as e:
            print(f"  ❌ Search error: {e}")
    
    # Check database statistics
    print("\n=== Database statistics ===")
    try:
        # Try to get some database statistics
        search_client = prompt_content_db.db_handle
        if search_client:
            # Execute empty search to get count
            empty_results = list(search_client.search(search_text="*", top=1))
            print(f"Approximate documents in database: {len(empty_results)} (rough estimate)")
            
            if empty_results:
                doc = empty_results[0]
                print(f"Sample document fields: {list(doc.keys())}")
                print(f"Sample content preview: {str(doc.get('content', 'N/A'))[:200]}...")
        
    except Exception as e:
        print(f"Cannot get database statistics: {e}")

if __name__ == "__main__":
    debug_search_issue()