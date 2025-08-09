import requests
import os
import time
from datetime import datetime, timedelta
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from azure.identity import DefaultAzureCredential, ClientSecretCredential

from .consts import Consts


class TokenCache:
    """
    Global token cache to reduce authentication requests and prevent connection exhaustion
    """
    _instance = None
    _lock_time = 0
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TokenCache, cls).__new__(cls)
            cls._instance.arm_token = None
            cls._instance.vi_token = None  
            cls._instance.token_expires_at = None
            cls._instance.consts_hash = None
        return cls._instance
    
    def get_cached_tokens(self, consts):
        """Get cached tokens if they are still valid"""
        current_consts_hash = self._get_consts_hash(consts)
        
        if (self.arm_token and self.vi_token and 
            self.token_expires_at and self.token_expires_at > datetime.now() and
            self.consts_hash == current_consts_hash):
            print("Using cached Azure tokens")
            return self.arm_token, self.vi_token
        return None, None
    
    def cache_tokens(self, consts, arm_token, vi_token, expires_in_seconds=3600):
        """Cache tokens with expiration time"""
        self.arm_token = arm_token
        self.vi_token = vi_token
        # Set expiration to 50 minutes (3000 seconds) to be safe, default token life is 1 hour
        self.token_expires_at = datetime.now() + timedelta(seconds=expires_in_seconds - 600)  
        self.consts_hash = self._get_consts_hash(consts)
        print(f"Cached Azure tokens, expires at: {self.token_expires_at}")
    
    def _get_consts_hash(self, consts):
        """Create a simple hash of the configuration to detect changes"""
        return hash(f"{consts.AccountName}_{consts.SubscriptionId}_{consts.ResourceGroup}")


class GlobalSessionManager:
    """
    Shared session manager to reduce connection overhead and avoid connection pool exhaustion
    """
    _session = None
    _lock = time.time()  # Simple lock mechanism
    
    @classmethod
    def get_session(cls):
        if cls._session is None:
            cls._session = requests.Session()
            # Simple timeout configuration without complex retry logic
            cls._session.timeout = (10, 60)  # (connection_timeout, read_timeout)
        return cls._session


def get_arm_access_token(consts:Consts) -> str:
    '''
    Get an access token for the Azure Resource Manager
    使用 Service Principal 或 DefaultAzureCredential 進行認證

    :param consts: Consts object
    :return: Access token for the Azure Resource Manager
    '''
    # 優先使用 Service Principal 認證
    client_id = os.getenv('AZURE_CLIENT_ID')
    client_secret = os.getenv('AZURE_CLIENT_SECRET')
    tenant_id = os.getenv('AZURE_TENANT_ID')
    
    if client_id and client_secret and tenant_id:
        print("使用 Service Principal 進行認證...")
        credential = ClientSecretCredential(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret
        )
    else:
        print("使用 Default Azure Credential 進行認證...")
        credential = DefaultAzureCredential()
    
    scope = f"{consts.AzureResourceManager}/.default"
    token = credential.get_token(scope)
    return token.token


def get_account_access_token_async(consts, arm_access_token, permission_type='Contributor', scope='Account',
                                   video_id=None):
    '''
    Get an access token for the Video Indexer account

    :param consts: Consts object
    :param arm_access_token: Access token for the Azure Resource Manager
    :param permission_type: Permission type for the access token
    :param scope: Scope for the access token
    :param video_id: Video ID for the access token, if scope is Video. Otherwise, not required
    :return: Access token for the Video Indexer account
    '''

    headers = {
        'Authorization': 'Bearer ' + arm_access_token,
        'Content-Type': 'application/json'
    }

    url = f'{consts.AzureResourceManager}/subscriptions/{consts.SubscriptionId}/resourceGroups/{consts.ResourceGroup}' + \
          f'/providers/Microsoft.VideoIndexer/accounts/{consts.AccountName}/generateAccessToken?api-version={consts.ApiVersion}'

    params = {
        'permissionType': permission_type,
        'scope': scope
    }

    if video_id is not None:
        params['videoId'] = video_id

    # Use shared session to reduce connection overhead
    session = GlobalSessionManager.get_session()
    
    # Simple retry for connection errors only (like original code)
    max_attempts = 2
    for attempt in range(max_attempts):
        try:
            if attempt > 0:
                print(f"Retrying Video Indexer access token request (attempt {attempt + 1})...")

            response = session.post(url, json=params, headers=headers, timeout=(10, 60))

            if response.status_code == 200:
                access_token = response.json().get('accessToken')
                print("Successfully obtained Video Indexer access token")
                return access_token
            elif response.status_code == 409:
                # 檢查是否為 ReadOnlyDisabledSubscription
                try:
                    error_json = response.json()
                    if "ReadOnlyDisabledSubscription" in error_json.get("error", {}).get("code", ""):
                        raise Exception(f"Azure subscription is disabled (read only): {error_json['error']['message']}")
                except Exception:
                    pass
                print("409 Conflict: Waiting 5 seconds before retry...")
                time.sleep(5)
                continue
            else:
                print(f"HTTP error: {response.status_code} - {response.text}")
                response.raise_for_status()

        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            if "10054" in str(e) or "ConnectionResetError" in str(e):
                if attempt < max_attempts - 1:
                    wait_time = 3  # Fixed wait time for connection resets
                    print(f"Connection reset detected, waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                    continue
            print(f"Connection error: {e}")
            if attempt == max_attempts - 1:
                raise

    raise Exception("Failed to get Video Indexer access token")


def get_cached_tokens(consts):
    """
    Get tokens from cache or generate new ones if expired
    This function reduces the number of authentication requests
    """
    token_cache = TokenCache()
    
    # Try to get cached tokens first
    arm_token, vi_token = token_cache.get_cached_tokens(consts)
    if arm_token and vi_token:
        return arm_token, vi_token
    
    # Generate new tokens if cache is empty or expired
    print("Generating new Azure tokens...")
    try:
        arm_token = get_arm_access_token(consts)
        vi_token = get_account_access_token_async(consts, arm_token)
        
        # Cache the new tokens
        token_cache.cache_tokens(consts, arm_token, vi_token)
        
        return arm_token, vi_token
    except Exception as e:
        print(f"Failed to generate new tokens: {e}")
        raise
