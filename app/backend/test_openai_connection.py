#!/usr/bin/env python3
"""
Test script to verify OpenAI embedding connection with Service Principal authentication
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

print("=== Testing OpenAI Embedding Connection ===")
print(f"Loading .env from: {env_path}")
print(f".env file exists: {env_path.exists()}")

# Check environment variables
required_vars = [
    'AZURE_OPENAI_SERVICE',
    'AZURE_OPENAI_API_KEY', 
    'AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT',
    'AZURE_CLIENT_ID',
    'AZURE_CLIENT_SECRET',
    'AZURE_TENANT_ID'
]

print("\n=== Environment Variables ===")
for var in required_vars:
    value = os.getenv(var)
    if value:
        # Hide sensitive information
        if 'KEY' in var or 'SECRET' in var:
            print(f"{var}: {'*' * len(value[:4])}{value[-4:] if len(value) > 4 else '*' * len(value)}")
        else:
            print(f"{var}: {value}")
    else:
        print(f"{var}: NOT SET")

print("\n=== Testing Azure OpenAI Connection ===")
try:
    from openai import AzureOpenAI
    
    azure_openai_service = os.getenv('AZURE_OPENAI_SERVICE')
    azure_openai_key = os.getenv('AZURE_OPENAI_API_KEY')
    azure_openai_embeddings_deployment = os.getenv('AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT')
    
    if not all([azure_openai_service, azure_openai_key, azure_openai_embeddings_deployment]):
        print("❌ Missing required Azure OpenAI configuration")
        sys.exit(1)
    
    # Create Azure OpenAI client
    client = AzureOpenAI(
        azure_endpoint=f"https://{azure_openai_service}.openai.azure.com/",
        api_key=azure_openai_key,
        api_version="2024-02-01"
    )
    
    print(f"✅ Azure OpenAI client created successfully")
    print(f"   Service: {azure_openai_service}")
    print(f"   Endpoint: https://{azure_openai_service}.openai.azure.com/")
    print(f"   Embeddings Deployment: {azure_openai_embeddings_deployment}")
    
    # Test embedding generation
    print("\n=== Testing Embedding Generation ===")
    test_text = "This is a test sentence for embedding generation."
    
    # Ensure model is not None
    if azure_openai_embeddings_deployment is None:
        raise ValueError("AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT is None")
    
    response = client.embeddings.create(
        input=test_text,
        model=azure_openai_embeddings_deployment
    )
    
    if response and response.data and len(response.data) > 0:
        embedding = response.data[0].embedding
        print(f"✅ Embedding generated successfully!")
        print(f"   Text: {test_text}")
        print(f"   Embedding dimensions: {len(embedding)}")
        print(f"   First 5 values: {embedding[:5]}")
        print(f"   Usage: {response.usage}")
    else:
        print("❌ Failed to generate embedding - empty response")
        
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please install required packages: pip install openai python-dotenv")
except Exception as e:
    print(f"❌ Error testing OpenAI connection: {e}")
    import traceback
    traceback.print_exc()

print("\n=== Testing Language Model Integration ===")
try:
    from vi_search.language_models.azure_openai import OpenAI
    
    # Create language model instance
    lm = OpenAI()
    print("✅ Language model instance created successfully")
    
    # Test embedding method
    test_text = "Hello world, this is a test"
    embedding = lm.get_text_embeddings(test_text)
    
    if embedding and len(embedding) > 0:
        print(f"✅ Language model embeddings working!")
        print(f"   Input text: {test_text}")
        print(f"   Embedding dimensions: {len(embedding)}")
        print(f"   First 5 values: {embedding[:5]}")
    else:
        print("❌ Language model embeddings failed")
        
    # Test chat functionality
    print("\n=== Testing Chat Functionality ===")
    sys_prompt = "You are a helpful assistant."
    user_prompt = "Say hello in a friendly way."
    
    response = lm.chat(sys_prompt, user_prompt, temperature=0.7)
    
    if response:
        print(f"✅ Chat functionality working!")
        print(f"   System prompt: {sys_prompt}")
        print(f"   User prompt: {user_prompt}")
        print(f"   Response: {response}")
    else:
        print("❌ Chat functionality failed")
        
except Exception as e:
    print(f"❌ Error testing language model: {e}")
    import traceback
    traceback.print_exc()

print("\n=== Test Complete ===")
