#!/usr/bin/env python3
"""
Script to check Azure Video Indexer video processing status
Usage: python check_video_status.py <video_id>
"""

import sys
import os
import json
import requests
from dotenv import load_dotenv

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

from vi_search.vi_client import account_token_provider
from vi_search.vi_client.consts import Consts

def check_video_status(video_id):
    """Check the processing status of a video in Azure Video Indexer"""
    
    # Load environment variables
    load_dotenv()
    
    try:
        # Initialize constants
        print(f"[INFO] Checking status for video ID: {video_id}")
        
        # Get configuration from environment variables
        api_version = os.getenv('VI_API_VERSION', '2024-01-01')
        api_endpoint = os.getenv('VI_API_ENDPOINT', 'https://api.videoindexer.ai')
        azure_resource_manager = os.getenv('AZURE_RESOURCE_MANAGER', 'https://management.azure.com')
        account_name = os.getenv('VI_ACCOUNT_NAME')
        resource_group = os.getenv('VI_RESOURCE_GROUP') 
        subscription_id = os.getenv('VI_SUBSCRIPTION_ID')
        location = os.getenv('VI_LOCATION', 'trial')
        account_id = os.getenv('VI_ACCOUNT_ID')
        
        if not all([account_name, resource_group, subscription_id]):
            print("[ERROR] Missing required environment variables: VI_ACCOUNT_NAME, VI_RESOURCE_GROUP, VI_SUBSCRIPTION_ID")
            print("Available env vars:")
            for key in ['VI_ACCOUNT_NAME', 'VI_RESOURCE_GROUP', 'VI_SUBSCRIPTION_ID', 'VI_LOCATION', 'VI_ACCOUNT_ID']:
                value = os.getenv(key, 'NOT SET')
                print(f"  {key}={value}")
            return
        
        consts = Consts(
            ApiVersion=api_version,
            ApiEndpoint=api_endpoint,
            AzureResourceManager=azure_resource_manager,
            AccountName=account_name,
            ResourceGroup=resource_group,
            SubscriptionId=subscription_id
        )
        # Add location and account_id manually
        consts.Location = location  
        consts.AccountId = account_id
        
        print("[INFO] Getting authentication tokens...")
        
        # Get ARM token
        arm_token = account_token_provider.get_arm_access_token_async(consts)
        if not arm_token:
            print("[ERROR] Failed to get ARM token")
            return
        
        # Get Video Indexer account token
        vi_token = account_token_provider.get_account_access_token_async(consts, arm_token, scope='Account')
        if not vi_token:
            print("[ERROR] Failed to get Video Indexer token")
            return
        
        print("[INFO] Connecting to Azure Video Indexer...")
        
        # Build API URL for getting video index
        # GET https://api.videoindexer.ai/{location}/Accounts/{accountId}/Videos/{videoId}/Index
        api_url = f"https://api.videoindexer.ai/{consts.Location}/Accounts/{consts.AccountId}/Videos/{video_id}/Index"
        
        headers = {
            'Authorization': f'Bearer {vi_token}',
            'Content-Type': 'application/json'
        }
        
        # Add query parameters for detailed information
        params = {
            'accessToken': vi_token,
            'language': 'English',  # Get English metadata
            'includeStreamingUrls': 'false',
            'includeSummarizedInsights': 'false'
        }
        
        print(f"[INFO] Making API call to: {api_url}")
        response = requests.get(api_url, headers=headers, params=params, timeout=30)
        
        if response.status_code == 200:
            video_index = response.json()
            print("[SUCCESS] Video found! Here's the detailed status:")
            print("=" * 60)
            
            # Extract key information
            state = video_index.get('state', 'Unknown')
            processing_progress = video_index.get('processingProgress', 'Unknown')
            
            print(f"Video ID: {video_id}")
            print(f"Processing State: {state}")
            print(f"Processing Progress: {processing_progress}")
            print(f"Created: {video_index.get('created', 'Unknown')}")
            print(f"Last Modified: {video_index.get('lastModified', 'Unknown')}")
            
            # Check if there are any failures
            if 'failures' in video_index and video_index['failures']:
                print("\n[ERROR] Failures found:")
                for failure in video_index['failures']:
                    failure_code = failure.get('code', 'Unknown')
                    failure_message = failure.get('message', 'Unknown error')
                    print(f"   - Code: {failure_code}")
                    print(f"     Message: {failure_message}")
            
            # Check processing details from videos array
            if 'videos' in video_index and video_index['videos']:
                video = video_index['videos'][0]  # Usually there's only one video
                insights = video.get('insights', {})
                
                print(f"\nVideo Details:")
                print(f"   Duration: {video.get('duration', 'Unknown')}")
                print(f"   Source Language: {insights.get('sourceLanguage', 'Unknown')}")
                
                # Check transcript status
                if 'transcript' in insights:
                    transcript_state = insights['transcript'].get('state', 'Unknown')
                    print(f"   Transcript State: {transcript_state}")
                
                # Check processing stages
                if 'processingProgress' in video_index:
                    print(f"\nProcessing Details:")
                    progress = video_index['processingProgress']
                    if isinstance(progress, dict):
                        for stage, percentage in progress.items():
                            print(f"   {stage}: {percentage}%")
                    else:
                        print(f"   Overall: {progress}")
            
            # Show thumbnails info if available
            if 'summarizedInsights' in video_index:
                insights = video_index['summarizedInsights']
                if 'thumbnails' in insights:
                    print(f"\nThumbnails: {len(insights['thumbnails'])} generated")
            
        elif response.status_code == 404:
            print(f"[ERROR] Video with ID '{video_id}' not found")
        elif response.status_code == 401:
            print("[ERROR] Authentication failed - check your tokens")
        elif response.status_code == 403:
            print("[ERROR] Access forbidden - check your permissions")
        else:
            print(f"[ERROR] API call failed with status {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"[ERROR] Error checking video status: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python check_video_status.py <video_id>")
        print("Example: python check_video_status.py 9xfx8xh110")
        sys.exit(1)
    
    video_id = sys.argv[1]
    check_video_status(video_id)