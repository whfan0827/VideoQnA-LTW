#!/usr/bin/env python3
"""
Test script to verify Azure Video Indexer connection with Service Principal authentication
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

print("=== Testing Azure Video Indexer Connection ===")
print(f"Loading .env from: {env_path}")
print(f".env file exists: {env_path.exists()}")

# Check environment variables
required_vars = [
    'AccountName',
    'ResourceGroup', 
    'SubscriptionId',
    'AZURE_CLIENT_ID',
    'AZURE_CLIENT_SECRET',
    'AZURE_TENANT_ID'
]

print("\n=== Environment Variables ===")
for var in required_vars:
    value = os.getenv(var)
    if value:
        # Hide sensitive information
        if 'SECRET' in var or 'KEY' in var:
            print(f"{var}: {'*' * len(value[:4])}{value[-4:] if len(value) > 4 else '*' * len(value)}")
        else:
            print(f"{var}: {value}")
    else:
        print(f"{var}: NOT SET")

print("\n=== Testing Service Principal Authentication ===")
try:
    from azure.identity import ClientSecretCredential
    
    tenant_id = os.getenv('AZURE_TENANT_ID')
    client_id = os.getenv('AZURE_CLIENT_ID')
    client_secret = os.getenv('AZURE_CLIENT_SECRET')
    
    if not all([tenant_id, client_id, client_secret]):
        print("❌ Missing Service Principal credentials")
        sys.exit(1)
    
    # Validate required values are not None
    if tenant_id is None:
        raise ValueError("AZURE_TENANT_ID is None")
    if client_id is None:
        raise ValueError("AZURE_CLIENT_ID is None")
    if client_secret is None:
        raise ValueError("AZURE_CLIENT_SECRET is None")
    
    # Create Service Principal credential
    credential = ClientSecretCredential(
        tenant_id=tenant_id,
        client_id=client_id, 
        client_secret=client_secret
    )
    
    print("✅ Service Principal credential created successfully")
    
    # Test getting ARM token
    print("\n=== Testing ARM Token Generation ===")
    token = credential.get_token("https://management.azure.com/.default")
    
    if token and token.token:
        print("✅ ARM token generated successfully!")
        print(f"   Token expires at: {token.expires_on}")
        print(f"   Token (first 20 chars): {token.token[:20]}...")
    else:
        print("❌ Failed to generate ARM token")
        
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please install required packages: pip install azure-identity")
except Exception as e:
    print(f"❌ Error testing Service Principal: {e}")
    import traceback
    traceback.print_exc()

print("\n=== Testing Account Token Provider ===")
try:
    # Add the parent directory to sys.path to import vi_search modules
    sys.path.insert(0, str(Path(__file__).parent))
    
    from vi_search.vi_client.account_token_provider import get_arm_access_token
    from vi_search.vi_client.consts import Consts
    
    # Create Consts object with environment variables
    consts = Consts(
        ApiVersion="2024-01-01",
        ApiEndpoint="https://api.videoindexer.ai",
        AzureResourceManager="https://management.azure.com",
        AccountName=os.getenv('AccountName', ''),
        ResourceGroup=os.getenv('ResourceGroup', ''),
        SubscriptionId=os.getenv('SubscriptionId', '')
    )
    
    # Test getting access token
    access_token = get_arm_access_token(consts)
    
    if access_token:
        print("✅ Account token provider working!")
        print(f"   Access token (first 20 chars): {access_token[:20]}...")
    else:
        print("❌ Account token provider failed")
        
except Exception as e:
    print(f"❌ Error testing account token provider: {e}")
    import traceback
    traceback.print_exc()

print("\n=== Test Complete ===")
