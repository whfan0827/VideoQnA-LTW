#!/usr/bin/env python3
"""
Test script to check ChromaDB content and vector search functionality
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

print("=== Testing ChromaDB Vector Search ===")

def test_chromadb_content():
    """Test ChromaDB content and availability"""
    print("\n🗃️ Testing ChromaDB Content...")
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from vi_search.prompt_content_db.chroma_db import ChromaDB
        
        # Create ChromaDB instance
        chroma_db = ChromaDB()
        print("✅ ChromaDB instance created successfully")
        
        # Get available databases
        available_dbs = chroma_db.get_available_dbs()
        print(f"📚 Available databases: {available_dbs}")
        
        if not available_dbs:
            print("❌ No databases found! You need to run prepare_db.py first to create vector databases.")
            return False
        
        # Test each database
        for db_name in available_dbs:
            print(f"\n📖 Testing database: {db_name}")
            try:
                # Set the database
                chroma_db.set_db(db_name)
                print(f"   ✅ Successfully connected to database: {db_name}")
                
                # Get collection data to see what's in it
                collection_data = chroma_db.get_collection_data()
                doc_count = len(collection_data['ids']) if collection_data['ids'] else 0
                print(f"   📊 Document count: {doc_count}")
                
                if doc_count > 0:
                    # Show first few documents
                    print(f"   📄 First 3 documents:")
                    for i in range(min(3, doc_count)):
                        doc_id = collection_data['ids'][i]
                        doc_content = collection_data['documents'][i][:100] + "..." if len(collection_data['documents'][i]) > 100 else collection_data['documents'][i]
                        print(f"      [{doc_id}]: {doc_content}")
                
                # Test vector search with a sample query
                print(f"   🔍 Testing vector search...")
                from vi_search.language_models.azure_openai import OpenAI
                lm = OpenAI()
                
                test_query = "how to set up YASKAWA GA700"
                query_embedding = lm.get_text_embeddings(test_query)
                
                docs_by_id, results_content = chroma_db.vector_search(query_embedding, n_results=3)
                
                print(f"   📝 Query: {test_query}")
                print(f"   🎯 Search results found: {len(results_content)}")
                
                if results_content:
                    print(f"   📋 Top 3 results:")
                    for i, result in enumerate(results_content[:3]):
                        print(f"      {i+1}. {result[:150]}...")
                else:
                    print("   ⚠️ No search results found")
                    
            except Exception as e:
                print(f"   ❌ Error testing database {db_name}: {e}")
                import traceback
                traceback.print_exc()
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing ChromaDB: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ask_approach():
    """Test the complete ask approach workflow"""
    print("\n🤖 Testing Complete Ask Approach...")
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
        
        # Test query
        test_question = "how to set up YASKAWA GA700"
        overrides = {
            "index": test_db,
            "top": 3
        }
        
        print(f"❓ Question: {test_question}")
        print(f"⚙️ Overrides: {overrides}")
        
        # Run the approach
        result = approach.run(test_question, overrides)
        
        print(f"✅ Ask approach completed successfully!")
        print(f"📊 Data points found: {len(result.get('data_points', []))}")
        print(f"💬 Answer: {result.get('answer', 'No answer')[:200]}...")
        print(f"🧠 Thoughts: {result.get('thoughts', 'No thoughts')[:200]}...")
        
        # Check if the answer looks like a real response or hardcoded example
        answer = result.get('answer', '')
        if 'Employee Training Video' in answer or 'Overlake' in answer:
            print("⚠️ WARNING: This looks like a hardcoded example response!")
            print("   The system might not be using your vector database correctly.")
            return False
        else:
            print("✅ Response appears to be generated from your vector database")
            return True
        
    except Exception as e:
        print(f"❌ Error testing ask approach: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("Starting ChromaDB and vector search tests...\n")
    
    chromadb_ok = test_chromadb_content()
    ask_approach_ok = test_ask_approach()
    
    print("\n" + "="*50)
    print("📊 TEST RESULTS SUMMARY")
    print("="*50)
    
    results = {
        "ChromaDB Content": chromadb_ok,
        "Ask Approach": ask_approach_ok
    }
    
    passed = 0
    failed = 0
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<20}: {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\nTotal: {passed + failed} tests")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 All tests passed! Your vector database and LLM integration are working correctly!")
    else:
        print(f"\n⚠️ {failed} test(s) failed. There might be issues with your vector database or data.")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
