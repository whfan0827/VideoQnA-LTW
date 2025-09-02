_video_indexer_client_pool = {}

def get_video_indexer_client_by_index(config: dict):
    """
    根據 index（帳號）資訊取得對應的 VideoIndexerClient 實例。
    每個 index 只會建立一個 client 實例並重複使用。
    :param config: 必須包含 'AccountName' 作為唯一 key。
    :return: 已認證的 VideoIndexerClient 實例
    """
    account_name = config.get('AccountName')
    if not account_name:
        raise ValueError("config 必須包含 'AccountName' 作為唯一識別 index 的 key")
    if account_name in _video_indexer_client_pool:
        return _video_indexer_client_pool[account_name]
    # 尚未建立，初始化並認證
    client = init_video_indexer_client(config)
    _video_indexer_client_pool[account_name] = client
    return client
from pathlib import Path
import re
import requests
import time
from typing import Optional
from urllib.parse import urlparse
from functools import wraps
from datetime import datetime, timedelta
import threading
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .consts import Consts
from .account_token_provider import get_arm_access_token, get_account_access_token_async, GlobalSessionManager, get_cached_tokens


def auto_retry_auth(max_retries=2):
    """Simplified decorator: Only retry clear connection resets and auth errors"""
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            import time
            for attempt in range(max_retries + 1):
                try:
                    return func(self, *args, **kwargs)
                except requests.exceptions.ConnectionError as e:
                    # Only retry on connection reset (10054) errors  
                    if attempt < max_retries and "10054" in str(e):
                        wait_time = 5  # Fixed 5 second delay instead of exponential backoff
                        print(f"Connection reset detected, retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries + 1})")
                        time.sleep(wait_time)
                    else:
                        print(f"Connection error after {max_retries + 1} attempts: {e}")
                        raise e
                except requests.exceptions.HTTPError as e:
                    # Only retry 401/403 errors with re-authentication
                    if attempt < max_retries and e.response.status_code in [401, 403]:
                        print(f"Authentication error (HTTP {e.response.status_code}), re-authenticating... (attempt {attempt + 1}/{max_retries + 1})")
                        try:
                            self.re_authenticate()
                            time.sleep(2)  # Brief pause after re-auth
                        except Exception as auth_error:
                            print(f"Re-authentication failed: {auth_error}")
                            raise e
                    else:
                        # Don't retry other HTTP errors - let them surface immediately
                        raise e
            return None
        return wrapper
    return decorator


def extract_video_id_from_conflict_message(message) -> Optional[str]:
    ''' Extract the video ID from the message using regex. '''

    match = re.search(r"video id: '([a-zA-Z0-9]+)'", message)
    if match:
        video_id = match.group(1)
        return video_id
    else:
        print("No video ID found")
        return None


class RateLimiter:
    """Rate limiter for Azure Video Indexer API to respect 10 requests/second and 120 requests/minute limits"""
    def __init__(self, requests_per_second=8, requests_per_minute=100):  # Conservative limits
        self.requests_per_second = requests_per_second
        self.requests_per_minute = requests_per_minute
        self.request_times = []
        self.lock = threading.Lock()
    
    def wait_if_needed(self):
        """Wait if necessary to respect rate limits"""
        with self.lock:
            now = datetime.now()
            
            # Clean old requests (older than 1 minute)
            self.request_times = [t for t in self.request_times if now - t < timedelta(minutes=1)]
            
            # Check minute limit
            if len(self.request_times) >= self.requests_per_minute:
                oldest_request = min(self.request_times)
                wait_time = 60 - (now - oldest_request).total_seconds()
                if wait_time > 0:
                    print(f"Rate limit: waiting {wait_time:.1f}s for minute limit")
                    time.sleep(wait_time)
            
            # Check second limit (last second)
            recent_requests = [t for t in self.request_times if now - t < timedelta(seconds=1)]
            if len(recent_requests) >= self.requests_per_second:
                wait_time = 1 - (now - max(recent_requests)).total_seconds()
                if wait_time > 0:
                    print(f"Rate limit: waiting {wait_time:.1f}s for second limit")
                    time.sleep(wait_time)
            
            # Record this request
            self.request_times.append(datetime.now())

class VideoIndexerClient:
    def __init__(self) -> None:
        self.arm_access_token = ''
        self.vi_access_token = ''
        self.account = None
        self.consts = None
        self.rate_limiter = RateLimiter()

    @auto_retry_auth(max_retries=2)  # Reduced retries since we have caching
    def authenticate_async(self, consts:Consts) -> None:
        self.consts = consts
        # Use cached tokens to reduce authentication requests
        self.arm_access_token, self.vi_access_token = get_cached_tokens(self.consts)

    def re_authenticate(self) -> None:
        """Re-authenticate and update access tokens"""
        if self.consts is None:
            raise Exception("Cannot re-authenticate: no initial configuration")
        print("Re-authenticating...")
        # Force new token generation by clearing cache and getting fresh tokens
        from .account_token_provider import TokenCache
        token_cache = TokenCache()
        token_cache.token_expires_at = None  # Clear cache to force new tokens
        self.arm_access_token, self.vi_access_token = get_cached_tokens(self.consts)
        self.account = None  # Reset account information to force re-fetch
        print("Re-authentication completed")

    def get_account_async(self) -> None:
        '''
        Get information about the account with retry mechanism for 10054 errors
        '''
        if self.consts is None:
            raise Exception("Not authenticated. Please call authenticate_async first.")
        if self.account is not None:
            return self.account

        headers = {
            'Authorization': 'Bearer ' + self.arm_access_token,
            'Content-Type': 'application/json'
        }

        url = f'{self.consts.AzureResourceManager}/subscriptions/{self.consts.SubscriptionId}/resourcegroups/' + \
              f'{self.consts.ResourceGroup}/providers/Microsoft.VideoIndexer/accounts/{self.consts.AccountName}' + \
              f'?api-version={self.consts.ApiVersion}'

        # Apply rate limiting before making request
        self.rate_limiter.wait_if_needed()
        
        # Use shared session to reduce connection overhead
        session = GlobalSessionManager.get_session()
        
        # Simple retry similar to original code
        max_attempts = 2
        for attempt in range(max_attempts):
            try:
                response = session.get(url, headers=headers, timeout=30)
                response.raise_for_status()
                
                self.account = response.json()
                print(f'[Account Details] Id:{self.account["properties"]["accountId"]}, Location: {self.account["location"]}')
                return
                
            except requests.exceptions.ConnectionError as e:
                if "10054" in str(e) or "ConnectionResetError" in str(e):
                    if attempt < max_attempts - 1:
                        wait_time = 3  # Fixed wait time for connection resets
                        print(f"Account API connection reset, retrying in {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                raise Exception(f"Failed to get account information. Connection error: {str(e)}")
            except requests.exceptions.Timeout:
                if attempt < max_attempts - 1:
                    print(f"Account API timeout, retrying...")
                    time.sleep(2)
                    continue
                raise Exception(f"Account API timeout after {max_attempts} attempts")
            except Exception as e:
                raise Exception(f"Failed to get account information: {str(e)}")

    def get_account_details(self) -> dict:
        self.get_account_async()
        if self.account is None:
            raise Exception("Account information is not available. Please call get_account_async first.")
        return {"account_id": self.account["properties"]["accountId"], "location": self.account["location"]}

    def upload_url_async(self, video_name: str, video_url: str, excluded_ai: Optional[list[str]] = None,
                         wait_for_index: bool = False, video_description: str = '', privacy='private', 
                         source_language: str = 'auto') -> str:
        '''
        Uploads a video and starts the video index.
        Calls the uploadVideo API (https://api-portal.videoindexer.ai/api-details#api=Operations&operation=Upload-Video)

        :param video_name: The name of the video
        :param video_url: Link to publicly accessed video URL
        :param excluded_ai: The ExcludeAI list to run
        :param wait_for_index: Should this method wait for index operation to complete
        :param video_description: The description of the video
        :param privacy: The privacy mode of the video
        :param source_language: Language for speech recognition ('auto', 'zh-TW', 'en-US', etc.)
        :return: Video Id of the video being indexed, otherwise throws exception
        '''
        if excluded_ai is None:
            excluded_ai = []

        # check that video_url is valid
        parsed_url = urlparse(video_url)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise Exception(f'Invalid video URL: {video_url}')

        if self.consts is None:
            raise Exception("Not authenticated. Please call authenticate_async first.")
        self.get_account_async() # if account is not initialized, get it
        if self.account is None:
            raise Exception("Account information is not available. Please call get_account_async first.")

        url = f'{self.consts.ApiEndpoint}/{self.account["location"]}/Accounts/{self.account["properties"]["accountId"]}/Videos'

        params = {
            'accessToken': self.vi_access_token,
            'name': video_name,
            'description': video_description,
            'privacy': privacy,
            'videoUrl': video_url
        }

        # Add source language for speech recognition
        if source_language and source_language != 'auto':
            params['language'] = source_language
            print(f"Setting language to: {source_language}")

        if len(excluded_ai) > 0:
            params['excludedAI'] = ','.join(excluded_ai)

        # Apply rate limiting for URL upload
        self.rate_limiter.wait_if_needed()
        
        response = requests.post(url, params=params, timeout=60)

        response.raise_for_status()

        video_id = response.json().get('id')
        print(f'Video ID {video_id} was uploaded successfully')

        if wait_for_index:
            self.wait_for_index_async(video_id)

        return video_id

    @auto_retry_auth(max_retries=2)
    def file_upload_async(self, media_path: str | Path, video_name: Optional[str] = None,
                          excluded_ai: Optional[list[str]] = None, video_description: str = '', privacy='private',
                          partition='', source_language: str = 'auto') -> str:
        '''
        Uploads a local file and starts the video index.
        Calls the uploadVideo API (https://api-portal.videoindexer.ai/api-details#api=Operations&operation=Upload-Video)

        :param media_path: The path to the local file
        :param video_name: The name of the video, if not provided, the file name will be used
        :param excluded_ai: The ExcludeAI list to run
        :param video_description: The description of the video
        :param privacy: The privacy mode of the video
        :param partition: The partition of the video
        :return: Video Id of the video being indexed, otherwise throws exception
        '''
        if excluded_ai is None:
            excluded_ai = []

        if isinstance(media_path, str):
            media_path = Path(media_path)

        if video_name is None:
            video_name = media_path.stem

        if not media_path.exists():
            raise Exception(f'Could not find the local file {media_path}')

        if self.consts is None:
            raise Exception("Not authenticated. Please call authenticate_async first.")
        self.get_account_async() # if account is not initialized, get it
        if self.account is None:
            raise Exception("Account information is not available. Please call get_account_async first.")

        url = f'{self.consts.ApiEndpoint}/{self.account["location"]}/Accounts/{self.account["properties"]["accountId"]}/Videos'

        params = {
            'accessToken': self.vi_access_token,
            'name': video_name[:80],  # TODO: Is there a limit on the video name? If so, notice the used and also update `upload_url_async()` accordingly
            'description': video_description,
            'privacy': privacy,
            'partition': partition
        }

        # Add source language for speech recognition
        if source_language and source_language != 'auto':
            params['language'] = source_language
            print(f"Setting language to: {source_language}")

        if len(excluded_ai) > 0:
            params['excludedAI'] = ','.join(excluded_ai)

        # Check file size before upload
        file_size = Path(media_path).stat().st_size
        file_size_mb = file_size / (1024 * 1024)
        if file_size > 2 * 1024 * 1024 * 1024:  # 2GB limit for direct upload
            raise Exception(f"File too large ({file_size_mb:.1f} MB). Use URL upload for files > 2GB")
        
        print(f'Uploading local file ({file_size_mb:.1f} MB) using multipart/form-data post request..')
        
        # Apply rate limiting
        self.rate_limiter.wait_if_needed()
        
        # Use shared session to reduce connection overhead
        session = GlobalSessionManager.get_session()
        
        try:
            with open(media_path, 'rb') as f:
                response = session.post(url, params=params, files={'file': f}, timeout=1800)  # 30 minutes for large files
        except requests.exceptions.ConnectionError as e:
            if "10054" in str(e):
                raise Exception(f"Connection reset (10054). File size: {file_size_mb:.1f} MB. Consider using URL upload for large files or check network connectivity.")
            raise Exception(f"Connection error during upload: {str(e)}")
        except requests.exceptions.Timeout:
            raise Exception(f"Upload timeout for file size {file_size_mb:.1f} MB. Consider using URL upload for large files.")

        if response.status_code == 409:
            video_id = extract_video_id_from_conflict_message(response.json()['Message'])
            if video_id is not None:
                print(f'File {media_path} already exists. Video ID {video_id}. Skipping upload...')
                return video_id

        # Enhanced error handling with detailed diagnostics
        if response.status_code == 200:
            video_id = response.json().get('id')
            print(f'Successfully uploaded file {media_path.name} ({file_size_mb:.1f} MB) -> video_id: {video_id}')
            return video_id
        elif response.status_code == 429:
            raise Exception("Rate limit exceeded (429). Too many requests to Azure Video Indexer API.")
        elif response.status_code == 413:
            raise Exception(f"File too large (413) - {file_size_mb:.1f} MB. Use URL upload for files > 2GB.")
        elif response.status_code >= 500:
            error_details = ""
            try:
                error_response = response.json()
                error_details = f" Response: {error_response}"
            except:
                error_details = f" Response text: {response.text[:200]}..."
            raise Exception(f"Server error ({response.status_code}){error_details}. Please retry later.")
        elif response.status_code >= 400:
            # Client errors - try to get more details
            error_details = ""
            try:
                error_response = response.json()
                if 'message' in error_response:
                    error_details = f" Message: {error_response['message']}"
                elif 'Message' in error_response:
                    error_details = f" Message: {error_response['Message']}"
                else:
                    error_details = f" Response: {error_response}"
            except:
                error_details = f" Response text: {response.text[:200]}..."
            
            raise Exception(f"Upload failed ({response.status_code}){error_details}")
        else:
            # Unexpected success code
            print(f'Unexpected response code {response.status_code} for file upload')
            try:
                video_id = response.json().get('id')
                if video_id:
                    return video_id
                else:
                    raise Exception(f"No video ID in response despite status {response.status_code}")
            except:
                raise Exception(f"Cannot parse response for status {response.status_code}: {response.text[:200]}...")

    def wait_for_index_async(self, video_id: str, language: str = 'English', timeout_sec: Optional[int] = None) -> None:
        '''
        Calls getVideoIndex API in 10 second intervals until the indexing state is 'processed'
        (https://api-portal.videoindexer.ai/api-details#api=Operations&operation=Get-Video-Index).
        Prints video index when the index is complete, otherwise throws exception.

        :param video_id: The video ID to wait for
        :param language: The language to translate video insights
        :param timeout_sec: The timeout in seconds
        '''
        if self.consts is None:
            raise Exception("Not authenticated. Please call authenticate_async first.")
        self.get_account_async() # if account is not initialized, get it
        if self.account is None:
            raise Exception("Account information is not available. Please call get_account_async first.")

        url = f'{self.consts.ApiEndpoint}/{self.account["location"]}/Accounts/{self.account["properties"]["accountId"]}/' + \
            f'Videos/{video_id}/Index'

        params = {
            'accessToken': self.vi_access_token,
            'language': language
        }

        print(f'Checking if video {video_id} has finished indexing...')
        processing = True
        start_time = time.time()
        while processing:
            response = requests.get(url, params=params)

            response.raise_for_status()

            video_result = response.json()
            video_state = video_result.get('state')

            if video_state == 'Processed':
                processing = False
                print(f'The video index has completed. Here is the full JSON of the index for video ID {video_id}: \n{video_result}')
                break
            elif video_state == 'Failed':
                processing = False
                print(f"The video index failed for video ID {video_id}.")
                break

            print(f'The video index state is {video_state}')

            if timeout_sec is not None and time.time() - start_time > timeout_sec:
                print(f'Timeout of {timeout_sec} seconds reached. Exiting...')
                break

            time.sleep(20) # wait 20 seconds before checking again - reduced frequency to avoid rate limits

    def is_video_processed(self, video_id: str) -> bool:
        if self.consts is None:
            raise Exception("Not authenticated. Please call authenticate_async first.")
        self.get_account_async() # if account is not initialized, get it
        if self.account is None:
            raise Exception("Account information is not available. Please call get_account_async first.")

        url = f'{self.consts.ApiEndpoint}/{self.account["location"]}/Accounts/{self.account["properties"]["accountId"]}/' + \
                f'Videos/{video_id}/Index'
        params = {
            'accessToken': self.vi_access_token,
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()

            video_result = response.json()
            video_state = video_result.get('state')
            
            # Log the actual state for debugging
            print(f"Video {video_id} current state: {video_state}")
            
            # Handle different states
            if video_state == 'Processed':
                return True
            elif video_state in ['Failed', 'Unavailable']:
                print(f"Video {video_id} is in a failed/unavailable state: {video_state}")
                
                # Try to get more detailed error information
                failure_details = ""
                if 'failures' in video_result:
                    failure_details = f" Failures: {video_result['failures']}"
                elif 'processingProgress' in video_result:
                    failure_details = f" Progress: {video_result['processingProgress']}"
                elif 'state' in video_result and isinstance(video_result, dict):
                    # Show additional fields that might give clues
                    relevant_fields = {k: v for k, v in video_result.items() 
                                     if k in ['created', 'lastModified', 'processingProgress', 'failures', 'insights']}
                    if relevant_fields:
                        failure_details = f" Additional info: {relevant_fields}"
                
                error_msg = f"Video processing failed or unavailable (state: {video_state}){failure_details}"
                print(f"Detailed error for {video_id}: {error_msg}")
                raise Exception(error_msg)
            else:
                # Still processing (Uploaded, Processing, etc.)
                return False
                
        except requests.exceptions.HTTPError as e:
            # Re-raise HTTP errors with more context
            if e.response.status_code == 404:
                raise Exception(f"Video {video_id} not found (404). It may have been deleted or expired.")
            elif e.response.status_code == 400:
                raise Exception(f"Video {video_id} returned Bad Request (400). The video may be in an invalid state.")
            else:
                raise e

    def get_video_async(self, video_id: str) -> dict:
        '''
        Searches for the video in the account. Calls the searchVideo API
        (https://api-portal.videoindexer.ai/api-details#api=Operations&operation=Search-Videos)
        Prints the video metadata, otherwise throws an exception

        :param video_id: The video ID
        '''
        if self.consts is None:
            raise Exception("Not authenticated. Please call authenticate_async first.")
        self.get_account_async() # if account is not initialized, get it
        if self.account is None:
            raise Exception("Account information is not available. Please call get_account_async first.")

        print(f'Searching videos in account {self.account["properties"]["accountId"]} for video ID {video_id}.')

        url = f'{self.consts.ApiEndpoint}/{self.account["location"]}/Accounts/{self.account["properties"]["accountId"]}/' + \
               f'Videos/{video_id}/Index'

        params = {
            'accessToken': self.vi_access_token
        }

        response = requests.get(url, params=params)

        response.raise_for_status()

        search_result = response.json()
        print(f'Here are the search results: \n{search_result}')
        return search_result

    def generate_prompt_content_async(self, video_id: str) -> None:
        '''
        Calls the promptContent API
        Initiate generation of new prompt content for the video.
        If the video already has prompt content, it will be replaced with the new one.

        :param video_id: The video ID
        '''
        if self.consts is None:
            raise Exception("Not authenticated. Please call authenticate_async first.")
        self.get_account_async() # if account is not initialized, get it
        if self.account is None:
            raise Exception("Account information is not available. Please call get_account_async first.")

        url = f'{self.consts.ApiEndpoint}/{self.account["location"]}/Accounts/{self.account["properties"]["accountId"]}/' + \
              f'Videos/{video_id}/PromptContent'

        headers = {
            "Content-Type": "application/json"
            }

        params = {
            'accessToken': self.vi_access_token
        }

        response = requests.post(url, headers=headers, params=params)

        response.raise_for_status()
        print(f"Prompt content generation for {video_id=} started...")

    def get_prompt_content_async(self, video_id: str, raise_on_not_found: bool = True) -> Optional[dict]:
        '''
        Calls the promptContent API
        Get the prompt content for the video.
        Raises an exception or returns None if the prompt content is not found according to the `raise_on_not_found`.

        :param video_id: The video ID
        :param raise_on_not_found: If True, raises an exception if the prompt content is not found.
        :return: The prompt content for the video, otherwise None
        '''
        if self.consts is None:
            raise Exception("Not authenticated. Please call authenticate_async first.")
        self.get_account_async() # if account is not initialized, get it
        if self.account is None:
            raise Exception("Account information is not available. Please call get_account_async first.")

        url = f'{self.consts.ApiEndpoint}/{self.account["location"]}/Accounts/{self.account["properties"]["accountId"]}/' + \
              f'Videos/{video_id}/PromptContent'

        params = {
            'accessToken': self.vi_access_token
        }

        response = requests.get(url, params=params)
        
        # Handle various error conditions
        if not raise_on_not_found and response.status_code == 404:
            print(f"Prompt content not found for video {video_id} (404)")
            return None
        elif not raise_on_not_found and response.status_code == 400:
            print(f"Prompt content not available for video {video_id} (400 Bad Request). Video may be in an invalid state.")
            return None

        response.raise_for_status()

        return response.json()

    def get_prompt_content(self, video_id: str, timeout_sec: Optional[int] = 60, check_alreay_exists: bool = True) -> dict:
        '''
        Gets the prompt content for the video, waits until the prompt content is ready.
        If the prompt content is not ready within the timeout, it will raise an exception.

        :param video_id: The video ID
        :param timeout_sec: The timeout in seconds
        :param check_already_exists: If True, checks if the prompt content already exists
        :return: The prompt content for the video
        '''

        if check_alreay_exists:
            prompt_content = self.get_prompt_content_async(video_id, raise_on_not_found=False)
            if prompt_content is not None:
                print(f'Prompt content already exists for video ID {video_id}.')
                return prompt_content

        # Defensive check for authentication and account
        if self.consts is None:
            raise Exception("Not authenticated. Please call authenticate_async first.")
        self.get_account_async()
        if self.account is None:
            raise Exception("Account information is not available. Please call get_account_async first.")

        self.generate_prompt_content_async(video_id)

        start_time = time.time()
        while True:
            prompt_content = self.get_prompt_content_async(video_id, raise_on_not_found=False)
            if prompt_content is not None:
                print(f'Prompt content ready for video ID {video_id}.')
                break

            if timeout_sec is not None and time.time() - start_time > timeout_sec:
                print(f'Timeout of {timeout_sec} seconds reached. Exiting...')
                raise TimeoutError(f'Prompt content for video ID {video_id} is not ready within {timeout_sec} seconds.')

            print('Prompt content is not ready yet. Waiting 15 seconds before checking again...')
            time.sleep(15)

        return prompt_content

    def get_collection_prompt_content(self, videos_ids: list[str], timeout_sec: Optional[int] = 300,
                                      check_alreay_exists: bool = True) -> dict:
        '''
        Gets the prompt content for a list of videos, waits until the prompt content is ready.
        If the prompt content is not ready within the timeout, it will raise an exception.

        :param videos_ids: List of video IDs
        :param timeout_sec: The timeout in seconds
        :param check_already_exists: If True, checks if the prompt content already exists
        :return: The prompt content for the videos
        '''
        # Avoid modifying the input while iterating
        videos_ids = videos_ids.copy()

        # Get prompt content for the videos that are already processed
        prompt_content_dict = {}
        if check_alreay_exists:
            for video_id in videos_ids[:]:
                prompt_content = self.get_prompt_content_async(video_id, raise_on_not_found=False)
                if prompt_content is not None:
                    print(f'Prompt content ready for video ID {video_id}.')
                    prompt_content_dict[video_id] = prompt_content
                    videos_ids.remove(video_id)

        # Initiate prompt content generation for the remaining videos
        # First filter out videos that are in Failed/Unavailable state
        valid_videos_for_generation = []
        for video_id in videos_ids[:]:
            try:
                # Check video status before trying to generate PromptContent
                video_info = self.get_video_async(video_id)
                video_state = video_info.get('state', 'Unknown') if video_info else 'Unknown'
                
                if video_state in ['Failed', 'Unavailable']:
                    print(f'Skipping PromptContent generation for video {video_id} - state: {video_state}')
                    videos_ids.remove(video_id)  # Remove from the list to avoid waiting for it
                    continue
                elif video_state != 'Processed':
                    print(f'Video {video_id} is not yet processed (state: {video_state}), will retry later')
                    # Keep it in the list for later retry, but don't try to generate content yet
                    continue
                else:
                    # Video is processed, safe to generate content
                    valid_videos_for_generation.append(video_id)
                    
            except Exception as e:
                print(f'Error checking video status for {video_id}: {e}')
                if "404" in str(e) or "not found" in str(e).lower():
                    print(f'Video {video_id} not found, removing from list')
                    videos_ids.remove(video_id)
                    continue
                else:
                    # For other errors, assume video might be valid and try generation
                    valid_videos_for_generation.append(video_id)
        
        # Only generate content for videos that are confirmed to be processed
        for video_id in valid_videos_for_generation:
            try:
                self.generate_prompt_content_async(video_id)
            except Exception as e:
                print(f'Error initiating PromptContent generation for {video_id}: {e}')
                if "400" in str(e) or "Bad Request" in str(e):
                    print(f'Cannot generate PromptContent for {video_id} - removing from waiting list')
                    if video_id in videos_ids:
                        videos_ids.remove(video_id)

        start_time = time.time()
        while videos_ids:
            video_id = videos_ids[0]
            prompt_content = self.get_prompt_content_async(video_id, raise_on_not_found=False)
            if prompt_content is not None:
                print(f'Prompt content ready for video ID {video_id}.')
                prompt_content_dict[video_id] = prompt_content
                videos_ids.remove(video_id)
                continue

            if timeout_sec is not None and time.time() - start_time > timeout_sec:
                print(f'Timeout of {timeout_sec} seconds reached. Exiting...')
                raise TimeoutError(f'Prompt content for video ID {video_id} is not ready within {timeout_sec} seconds.')

            # Progressive interval: start with 30 seconds, increase gradually
            elapsed_time = time.time() - start_time
            if elapsed_time < 600:  # First 10 minutes
                interval = 30
            elif elapsed_time < 1800:  # 10-30 minutes
                interval = 60
            else:  # After 30 minutes
                interval = 120
                
            print(f'Prompt content for {video_id} is not ready yet. Waiting {interval} seconds before checking again...')
            time.sleep(interval)

        return prompt_content_dict

    def get_insights_widgets_url_async(self, video_id: str, widget_type: str, allow_edit: bool = False) -> None:
        '''
        Calls the getVideoInsightsWidget API
        (https://api-portal.videoindexer.ai/api-details#api=Operations&operation=Get-Video-Insights-Widget)
        It first generates a new access token for the video scope.
        Prints the VideoInsightsWidget URL, otherwise throws exception.

        :param video_id: The video ID
        :param widget_type: The widget type
        :param allow_edit: Allow editing the video insights
        '''
        if self.consts is None:
            raise Exception("Not authenticated. Please call authenticate_async first.")
        self.get_account_async() # if account is not initialized, get it
        if self.account is None:
            raise Exception("Account information is not available. Please call get_account_async first.")

        # generate a new access token for the video scope
        video_scope_access_token = get_account_access_token_async(self.consts, self.arm_access_token,
                                                                  permission_type='Contributor', scope='Video',
                                                                  video_id=video_id)

        print(f'Getting the insights widget URL for video {video_id}')

        params = {
            'widgetType': widget_type,
            'allowEdit': str(allow_edit).lower(),
            'accessToken': video_scope_access_token
        }

        url = f'{self.consts.ApiEndpoint}/{self.account["location"]}/Accounts/{self.account["properties"]["accountId"]}/' + \
              f'Videos/{video_id}/InsightsWidget'

        response = requests.get(url, params=params)

        response.raise_for_status()

        insights_widget_url = response.url
        print(f'Got the insights widget URL: {insights_widget_url}')

    def get_player_widget_url_async(self, video_id: str) -> None:
        '''
        Calls the getVideoPlayerWidget API
        (https://api-portal.videoindexer.ai/api-details#api=Operations&operation=Get-Video-Player-Widget)
        It first generates a new access token for the video scope.
        Prints the VideoPlayerWidget URL, otherwise throws exception

        :param video_id: The video ID
        '''
        if self.consts is None:
            raise Exception("Not authenticated. Please call authenticate_async first.")
        self.get_account_async()
        if self.account is None:
            raise Exception("Account information is not available. Please call get_account_async first.")

        # generate a new access token for the video scope
        video_scope_access_token = get_account_access_token_async(self.consts, self.arm_access_token,
                                                                  permission_type='Contributor', scope='Video',
                                                                  video_id=video_id)

        print(f'Getting the player widget URL for video {video_id}')

        params = {
            'accessToken': video_scope_access_token
        }

        url = f'{self.consts.ApiEndpoint}/{self.account["location"]}/Accounts/{self.account["properties"]["accountId"]}/' + \
              f'Videos/{video_id}/PlayerWidget'

        response = requests.get(url, params=params)

        response.raise_for_status()

        url = response.url
        print(f'Got the player widget URL: {url}')

    def download_captions(self, video_id: str, format: str = 'srt', language: str = 'auto', include_speakers: bool = True) -> bytes:
        '''
        Download caption/subtitle file for a video from Azure Video Indexer
        
        :param video_id: The video ID
        :param format: Caption format ('srt', 'vtt', 'ttml')
        :param language: Language code for captions ('auto' for auto-detect, 'zh-TW', 'zh-CN', 'en-US', etc.)
        :param include_speakers: Whether to include speaker names in captions
        :return: Caption file content as bytes
        '''
        if self.consts is None:
            raise Exception("Not authenticated. Please call authenticate_async first.")
        self.get_account_async()
        if self.account is None:
            raise Exception("Account information is not available. Please call get_account_async first.")

        # Validate format
        supported_formats = ['srt', 'vtt', 'ttml']
        if format.lower() not in supported_formats:
            raise ValueError(f"Unsupported format '{format}'. Supported formats: {', '.join(supported_formats)}")

        # Handle auto language detection
        if language == 'auto':
            print(f'Auto-detecting language for video {video_id}...')
            detected_language = self._detect_video_language(video_id)
            print(f'Detected language: {detected_language}')
            language = detected_language

        print(f'Downloading {format.upper()} captions for video {video_id} in language: {language}')

        # Method 1: Try direct captions endpoint
        url = f'{self.consts.ApiEndpoint}/{self.account["location"]}/Accounts/{self.account["properties"]["accountId"]}/' + \
              f'Videos/{video_id}/Captions'

        params = {
            'accessToken': self.vi_access_token,
            'format': format.capitalize(),  # Azure expects 'Srt', 'Vtt', 'Ttml' (capitalized)
            'language': language
        }
        
        if include_speakers:
            params['includeSpeakers'] = 'true'

        # Apply rate limiting
        self.rate_limiter.wait_if_needed()
        
        # Use shared session to reduce connection overhead
        session = GlobalSessionManager.get_session()
        
        try:
            response = session.get(url, params=params, timeout=60)
            
            if response.status_code == 200:
                content = response.content
                print(f'Successfully downloaded {format.upper()} captions for video {video_id} ({len(content)} bytes)')
                
                # Log first few lines to debug content
                try:
                    content_str = content.decode('utf-8')[:500]  # First 500 chars for debugging
                    print(f'Caption content preview: {repr(content_str)}')
                except:
                    print(f'Caption content is binary, {len(content)} bytes')
                
                # If content is very short, try alternative method
                if len(content) < 100:
                    print(f'Content seems too short ({len(content)} bytes), trying alternative method...')
                    return self._download_captions_via_index(video_id, format, language)
                
                return content
            elif response.status_code == 404:
                # Try alternative method if direct captions endpoint doesn't work
                print(f"Captions endpoint returned 404, trying alternative method...")
                return self._download_captions_via_index(video_id, format, language)
            elif response.status_code == 400:
                raise Exception(f"Bad request for video {video_id}. Video may not be processed or language '{language}' not available")
            elif response.status_code == 401 or response.status_code == 403:
                raise Exception(f"Authentication error ({response.status_code}). Access token may be expired")
            else:
                response.raise_for_status()
                
        except requests.exceptions.ConnectionError as e:
            if "10054" in str(e):
                raise Exception(f"Connection reset during caption download for video {video_id}")
            raise Exception(f"Connection error during caption download: {str(e)}")
        except requests.exceptions.Timeout:
            raise Exception(f"Timeout downloading captions for video {video_id}")
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP error downloading captions for video {video_id}: {e.response.status_code}"
            try:
                error_response = e.response.json()
                if 'message' in error_response:
                    error_msg += f" - {error_response['message']}"
            except:
                pass
            raise Exception(error_msg)

        return response.content

    def _download_captions_via_index(self, video_id: str, format: str, language: str = 'en-US') -> bytes:
        '''
        Alternative method: Extract captions from video index transcript
        '''
        print(f'Trying alternative method: extracting {format.upper()} from video index...')
        
        # Get video index with transcript
        video_index = self.get_video_async(video_id)
        
        if not video_index or 'videos' not in video_index:
            raise Exception(f"Could not get video index for {video_id}")
        
        videos = video_index['videos']
        if not videos:
            raise Exception(f"No video data found in index for {video_id}")
        
        video = videos[0]  # Get first video
        insights = video.get('insights', {})
        transcript = insights.get('transcript', [])
        
        if not transcript:
            raise Exception(f"No transcript found in video index for {video_id}")
        
        print(f'Found {len(transcript)} transcript segments')
        
        # Convert transcript to SRT/VTT format
        if format.lower() == 'srt':
            return self._convert_transcript_to_srt(transcript)
        elif format.lower() == 'vtt':
            return self._convert_transcript_to_vtt(transcript)
        else:
            raise Exception(f"Alternative method only supports SRT and VTT formats, not {format}")

    def _convert_transcript_to_srt(self, transcript) -> bytes:
        '''Convert transcript array to SRT format with proper line breaking and formatting'''
        srt_content = []
        sequence_num = 1
        
        for segment in transcript:
            start_time = self._seconds_to_srt_time(segment.get('start', 0))
            end_time = self._seconds_to_srt_time(segment.get('end', 0))
            text = segment.get('text', '').strip()
            speaker_id = segment.get('speakerId', 0)
            confidence = segment.get('confidence', 0.0)
            
            if text and len(text) > 1:  # Only include meaningful text segments
                # Format speaker information (optional based on confidence)
                speaker_prefix = f"Speaker #{speaker_id + 1}: " if speaker_id is not None else ""
                
                # Break long lines (max 42 characters per line for readability)
                formatted_text = self._break_caption_lines(f"{speaker_prefix}{text}", max_chars=42)
                
                # Only add if we have actual content
                if formatted_text.strip():
                    srt_content.append(f"{sequence_num}\n{start_time} --> {end_time}\n{formatted_text}\n")
                    sequence_num += 1
        
        if not srt_content:
            # Fallback: create a basic caption if no proper segments found
            srt_content.append("1\n00:00:00,000 --> 00:00:05,000\n[No speech detected or transcript unavailable]\n")
        
        content = '\n'.join(srt_content)
        return content.encode('utf-8')

    def _break_caption_lines(self, text: str, max_chars: int = 42, max_lines: int = 2) -> str:
        '''Break long caption text into multiple lines following subtitle best practices'''
        if len(text) <= max_chars:
            return text
        
        # Split by words to avoid breaking mid-word
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            # Check if adding this word would exceed line length
            test_line = f"{current_line} {word}".strip()
            
            if len(test_line) <= max_chars:
                current_line = test_line
            else:
                # Start new line if we haven't reached max lines
                if current_line:
                    lines.append(current_line)
                
                if len(lines) >= max_lines:
                    # If we're at max lines, truncate with ellipsis
                    if len(lines) == max_lines:
                        lines[-1] = lines[-1][:max_chars-3] + "..."
                    break
                
                current_line = word
        
        # Add the last line if it has content and we're under line limit
        if current_line and len(lines) < max_lines:
            lines.append(current_line)
        
        return '\n'.join(lines)

    def _convert_transcript_to_vtt(self, transcript) -> bytes:
        '''Convert transcript array to VTT format with proper formatting'''
        vtt_content = ["WEBVTT", "", "NOTE", "Generated from Azure Video Indexer transcript", ""]
        
        for segment in transcript:
            start_time = self._seconds_to_vtt_time(segment.get('start', 0))
            end_time = self._seconds_to_vtt_time(segment.get('end', 0))
            text = segment.get('text', '').strip()
            speaker_id = segment.get('speakerId', 0)
            confidence = segment.get('confidence', 0.0)
            
            if text and len(text) > 1:  # Only include meaningful text segments
                # Format speaker information
                speaker_prefix = f"Speaker #{speaker_id + 1}: " if speaker_id is not None else ""
                
                # Break long lines for VTT format
                formatted_text = self._break_caption_lines(f"{speaker_prefix}{text}", max_chars=42)
                
                # Only add if we have actual content
                if formatted_text.strip():
                    vtt_content.append(f"{start_time} --> {end_time}")
                    vtt_content.append(formatted_text)
                    vtt_content.append("")  # Empty line between cues
        
        if len(vtt_content) <= 5:  # Only header content, no actual captions
            vtt_content.extend([
                "00:00:00.000 --> 00:00:05.000",
                "[No speech detected or transcript unavailable]",
                ""
            ])
        
        content = '\n'.join(vtt_content)
        return content.encode('utf-8')

    def _seconds_to_srt_time(self, seconds):
        '''Convert seconds to SRT time format (HH:MM:SS,mmm)'''
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        milliseconds = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"

    def _seconds_to_vtt_time(self, seconds):
        '''Convert seconds to VTT time format (HH:MM:SS.mmm)'''
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        milliseconds = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{milliseconds:03d}"

    def _detect_video_language(self, video_id: str) -> str:
        '''
        Detect the primary language of a video by analyzing its insights
        Returns the most likely language code
        '''
        try:
            # Get video insights to detect language
            video_insights = self.get_video_async(video_id)
            
            if not video_insights or 'videos' not in video_insights:
                print(f"Could not get video insights for language detection, defaulting to en-US")
                return 'en-US'
            
            videos = video_insights.get('videos', [])
            if not videos:
                return 'en-US'
            
            video = videos[0]
            insights = video.get('insights', {})
            
            # Check multiple sources for language information
            detected_languages = []
            
            # 1. Check sourceLanguage if available
            source_language = insights.get('sourceLanguage')
            if source_language:
                detected_languages.append(source_language)
            
            # 2. Check transcript languages
            transcript = insights.get('transcript', [])
            if transcript:
                # Look for language info in transcript segments
                for segment in transcript[:10]:  # Check first 10 segments
                    if 'language' in segment:
                        detected_languages.append(segment['language'])
            
            # 3. Analyze transcript text to detect Chinese vs other languages
            if transcript:
                sample_text = ' '.join([seg.get('text', '') for seg in transcript[:5]])
                detected_lang = self._detect_language_from_text(sample_text)
                if detected_lang:
                    detected_languages.append(detected_lang)
            
            # Determine most common language
            if detected_languages:
                from collections import Counter
                language_counts = Counter(detected_languages)
                most_common = language_counts.most_common(1)[0][0]
                
                # Map to standard codes
                language_mapping = {
                    'zh': 'zh-TW',  # Default Chinese to Traditional
                    'zh-Hans': 'zh-CN',
                    'zh-Hant': 'zh-TW',
                    'en': 'en-US',
                    'ja': 'ja-JP',
                    'ko': 'ko-KR',
                    'vi': 'vi-VN',  # Vietnamese
                    'es': 'es-ES',
                    'fr': 'fr-FR',
                    'de': 'de-DE'
                }
                
                return language_mapping.get(most_common, most_common)
            
            # Default fallback
            return 'en-US'
            
        except Exception as e:
            print(f"Error detecting language for video {video_id}: {e}")
            return 'en-US'  # Safe fallback

    def _detect_language_from_text(self, text: str) -> str:
        '''
        Simple text-based language detection
        '''
        if not text or len(text.strip()) < 10:
            return None
        
        # Count Chinese characters (both simplified and traditional)
        chinese_chars = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
        total_chars = len(text.replace(' ', ''))  # Exclude spaces
        
        if total_chars == 0:
            return None
        
        chinese_ratio = chinese_chars / total_chars
        
        if chinese_ratio > 0.3:  # More than 30% Chinese characters
            # Try to distinguish between Traditional and Simplified
            # This is a simple heuristic - Traditional Chinese tends to have more complex characters
            traditional_indicators = ['臺', '學', '國', '時', '會', '來', '說', '對', '們', '這', '個']
            simplified_indicators = ['台', '学', '国', '时', '会', '来', '说', '对', '们', '这', '个']
            
            traditional_score = sum(1 for indicator in traditional_indicators if indicator in text)
            simplified_score = sum(1 for indicator in simplified_indicators if indicator in text)
            
            if traditional_score > simplified_score:
                return 'zh-TW'
            elif simplified_score > traditional_score:
                return 'zh-CN'
            else:
                return 'zh-TW'  # Default to Traditional
        
        # Basic detection for other languages (very simple)
        japanese_chars = sum(1 for char in text if '\u3040' <= char <= '\u309f' or '\u30a0' <= char <= '\u30ff')
        korean_chars = sum(1 for char in text if '\uac00' <= char <= '\ud7af')
        
        if japanese_chars > total_chars * 0.1:
            return 'ja-JP'
        elif korean_chars > total_chars * 0.1:
            return 'ko-KR'
        
        # Default to English for other cases
        return 'en-US'


def init_video_indexer_client(config: dict) -> VideoIndexerClient:
    AccountName = config.get('AccountName')
    ResourceGroup = config.get('ResourceGroup')
    SubscriptionId = config.get('SubscriptionId')

    ApiVersion = '2024-01-01'
    ApiEndpoint = 'https://api.videoindexer.ai'
    AzureResourceManager = 'https://management.azure.com'

    # Validate required config values
    if not AccountName or not ResourceGroup or not SubscriptionId:
        raise ValueError("Missing required config values: AccountName, ResourceGroup, SubscriptionId")
    
    # Create and validate consts
    consts = Consts(ApiVersion, ApiEndpoint, AzureResourceManager, AccountName, ResourceGroup, SubscriptionId)

    # Authenticate

    # Create Video Indexer Client
    client = VideoIndexerClient()

    # Get access tokens (arm and Video Indexer account)
    client.authenticate_async(consts)

    client.get_account_async()

    return client
