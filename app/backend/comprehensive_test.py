#!/usr/bin/env python3
"""
Comprehensive test script to verify all connections are working properly
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

print("=== Comprehensive Connection Test ===")
print(f"Loading .env from: {env_path}")

def test_openai_embedding():
    """Test OpenAI embedding functionality"""
    print("\n🔍 Testing OpenAI Embedding...")
    try:
        from openai import AzureOpenAI
        
        azure_openai_service = os.getenv('AZURE_OPENAI_SERVICE')
        azure_openai_key = os.getenv('AZURE_OPENAI_API_KEY')
        azure_openai_embeddings_deployment = os.getenv('AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT')
        
        client = AzureOpenAI(
            azure_endpoint=f"https://{azure_openai_service}.openai.azure.com/",
            api_key=azure_openai_key,
            api_version="2024-02-01"
        )
        
        if azure_openai_embeddings_deployment is None:
            raise ValueError("AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT is None")
        
        response = client.embeddings.create(
            input="Test embedding generation",
            model=azure_openai_embeddings_deployment
        )
        
        if response and response.data and len(response.data) > 0:
            print("   ✅ OpenAI embedding generation successful")
            return True
        else:
            print("   ❌ OpenAI embedding generation failed")
            return False
            
    except Exception as e:
        print(f"   ❌ OpenAI embedding error: {e}")
        return False

def test_openai_chat():
    """Test OpenAI chat functionality"""
    print("\n💬 Testing OpenAI Chat...")
    try:
        from openai import AzureOpenAI
        
        azure_openai_service = os.getenv('AZURE_OPENAI_SERVICE')
        azure_openai_key = os.getenv('AZURE_OPENAI_API_KEY')
        azure_openai_chatgpt_deployment = os.getenv('AZURE_OPENAI_CHATGPT_DEPLOYMENT')
        
        client = AzureOpenAI(
            azure_endpoint=f"https://{azure_openai_service}.openai.azure.com/",
            api_key=azure_openai_key,
            api_version="2024-02-01"
        )
        
        if azure_openai_chatgpt_deployment is None:
            raise ValueError("AZURE_OPENAI_CHATGPT_DEPLOYMENT is None")
        
        response = client.chat.completions.create(
            model=azure_openai_chatgpt_deployment,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'Hello, connection test successful!'"}
            ],
            temperature=0.7
        )
        
        if response and response.choices and len(response.choices) > 0:
            content = response.choices[0].message.content
            print(f"   ✅ OpenAI chat successful: {content}")
            return True
        else:
            print("   ❌ OpenAI chat failed")
            return False
            
    except Exception as e:
        print(f"   ❌ OpenAI chat error: {e}")
        return False

def test_service_principal():
    """Test Service Principal authentication"""
    print("\n🔐 Testing Service Principal Authentication...")
    try:
        from azure.identity import ClientSecretCredential
        
        tenant_id = os.getenv('AZURE_TENANT_ID')
        client_id = os.getenv('AZURE_CLIENT_ID')
        client_secret = os.getenv('AZURE_CLIENT_SECRET')
        
        if tenant_id is None:
            raise ValueError("AZURE_TENANT_ID is None")
        if client_id is None:
            raise ValueError("AZURE_CLIENT_ID is None")
        if client_secret is None:
            raise ValueError("AZURE_CLIENT_SECRET is None")
        
        credential = ClientSecretCredential(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret
        )
        
        token = credential.get_token("https://management.azure.com/.default")
        
        if token and token.token:
            print("   ✅ Service Principal authentication successful")
            return True
        else:
            print("   ❌ Service Principal authentication failed")
            return False
            
    except Exception as e:
        print(f"   ❌ Service Principal error: {e}")
        return False

def test_language_model_integration():
    """Test the language model integration"""
    print("\n🧠 Testing Language Model Integration...")
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from vi_search.language_models.azure_openai import OpenAI
        
        lm = OpenAI()
        
        # Test embedding
        embedding = lm.get_text_embeddings("Test integration")
        if not embedding or len(embedding) == 0:
            print("   ❌ Language model embedding failed")
            return False
        
        # Test chat
        response = lm.chat(
            "You are a helpful assistant.",
            "Say 'Integration test successful!'",
            temperature=0.7
        )
        
        if not response:
            print("   ❌ Language model chat failed")
            return False
        
        print(f"   ✅ Language model integration successful: {response}")
        return True
        
    except Exception as e:
        print(f"   ❌ Language model integration error: {e}")
        return False

def test_video_indexer_auth():
    """Test Video Indexer authentication"""
    print("\n🎥 Testing Video Indexer Authentication...")
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from vi_search.vi_client.account_token_provider import get_arm_access_token
        from vi_search.vi_client.consts import Consts
        
        consts = Consts(
            ApiVersion="2024-01-01",
            ApiEndpoint="https://api.videoindexer.ai",
            AzureResourceManager="https://management.azure.com",
            AccountName=os.getenv('AccountName', ''),
            ResourceGroup=os.getenv('ResourceGroup', ''),
            SubscriptionId=os.getenv('SubscriptionId', '')
        )
        
        access_token = get_arm_access_token(consts)
        
        if access_token:
            print("   ✅ Video Indexer authentication successful")
            return True
        else:
            print("   ❌ Video Indexer authentication failed")
            return False
            
    except Exception as e:
        print(f"   ❌ Video Indexer authentication error: {e}")
        return False

def main():
    """Run all tests"""
    print("Starting comprehensive connection tests...\n")
    
    results = {
        "OpenAI Embedding": test_openai_embedding(),
        "OpenAI Chat": test_openai_chat(),
        "Service Principal": test_service_principal(),
        "Language Model Integration": test_language_model_integration(),
        "Video Indexer Auth": test_video_indexer_auth()
    }
    
    print("\n" + "="*50)
    print("📊 TEST RESULTS SUMMARY")
    print("="*50)
    
    passed = 0
    failed = 0
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<25}: {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\nTotal: {passed + failed} tests")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 All tests passed! Your OpenAI embedding and Service Principal authentication are working perfectly!")
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please check the configuration.")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
