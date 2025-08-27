#!/usr/bin/env python3
"""
Test Azure authentication for Video Indexer
"""
import os
import sys
from dotenv import load_dotenv
from azure.identity import ClientSecretCredential, DefaultAzureCredential

# Fix encoding
if sys.platform == "win32":
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')

def test_azure_auth():
    # Load environment variables
    load_dotenv()
    
    print("=== Testing Azure Authentication ===")
    
    # Get credentials from environment
    client_id = os.getenv('AZURE_CLIENT_ID')
    client_secret = os.getenv('AZURE_CLIENT_SECRET') 
    tenant_id = os.getenv('AZURE_TENANT_ID')
    
    print(f"Client ID: {client_id[:8] + '...' if client_id else 'Not set'}")
    print(f"Client Secret: {'Set' if client_secret else 'Not set'}")
    print(f"Tenant ID: {tenant_id}")
    
    if not all([client_id, client_secret, tenant_id]):
        print("ERROR: Missing required Azure credentials")
        return False
        
    try:
        # Test Service Principal authentication
        print("\n--- Testing Service Principal Authentication ---")
        credential = ClientSecretCredential(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret
        )
        
        # Test getting ARM token
        print("Getting Azure Resource Manager token...")
        scope = "https://management.azure.com/.default"
        token = credential.get_token(scope)
        print(f"SUCCESS: Got ARM token (expires: {token.expires_on})")
        
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to get ARM token - {e}")
        return False

def test_video_indexer_permissions():
    """Test specific Video Indexer permissions"""
    import requests
    from dotenv import load_dotenv
    
    load_dotenv()
    
    subscription_id = os.getenv('AZURE_SUBSCRIPTION_ID')
    resource_group = os.getenv('ResourceGroup')
    account_name = os.getenv('AccountName')
    client_id = os.getenv('AZURE_CLIENT_ID')
    client_secret = os.getenv('AZURE_CLIENT_SECRET') 
    tenant_id = os.getenv('AZURE_TENANT_ID')
    
    try:
        # Get ARM token
        credential = ClientSecretCredential(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret
        )
        token = credential.get_token("https://management.azure.com/.default")
        
        # Test Video Indexer token generation
        print("\n--- Testing Video Indexer Token Generation ---")
        # Try different API versions
        api_versions = ["2024-01-01", "2022-08-01", "2021-10-27-preview"]
        
        for api_version in api_versions:
            print(f"\nTrying API version: {api_version}")
            url = (f"https://management.azure.com/subscriptions/{subscription_id}"
                   f"/resourceGroups/{resource_group}"
                   f"/providers/Microsoft.VideoIndexer/accounts/{account_name}"
                   f"/generateAccessToken?api-version={api_version}")
        
            headers = {
                'Authorization': f'Bearer {token.token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'permissionType': 'Contributor',
                'scope': 'Account'
            }
            
            print(f"URL: {url}")
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=10)
                
                if response.status_code == 200:
                    print(f"SUCCESS: Video Indexer token generated successfully with API version {api_version}")
                    return True
                else:
                    print(f"Failed with status {response.status_code}: {response.text}")
                    
            except Exception as e:
                print(f"Request failed: {e}")
                continue
                
        print("All API versions failed")
        return False
            
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    print("Testing Azure Authentication for Video Indexer...\n")
    
    # Test basic authentication
    auth_success = test_azure_auth()
    
    if auth_success:
        # Test Video Indexer specific permissions
        vi_success = test_video_indexer_permissions()
        
        if vi_success:
            print("\n✅ All tests passed! Azure authentication is working correctly.")
        else:
            print("\n❌ Video Indexer permission test failed. Check service principal permissions.")
    else:
        print("\n❌ Basic authentication failed. Check Azure credentials.")