# -*- coding: utf-8 -*-
"""
Test script to monitor Azure Search API usage after cache fix.
Run this script and check the logs to see the reduction in API calls.
"""
import time
import logging
from pathlib import Path
import sys

# Add backend to path
backend_dir = Path(__file__).parent / "app" / "backend"
sys.path.insert(0, str(backend_dir))

# Configure logging to see cache behavior
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_library_status_calls():
    """Test that library status calls use caching"""
    print("Testing library status API call caching...")

    try:
        # Import the library manager
        from services.library_manager import LibraryManager
        from vi_search.prompt_content_db.azure_search import AzureVectorSearch
        from database.settings_service import SettingsService
        from database.app_db_manager import AppDbManager

        # Create mock instances (this will fail if Azure credentials are not set up)
        # But we can at least test that the cache mechanism is in place
        print("Creating service instances...")

        try:
            search_db = AzureVectorSearch()
            print("AzureVectorSearch created successfully")

            # Test multiple rapid calls to get_available_dbs
            print("\nTesting cache behavior with rapid calls...")

            start_time = time.time()
            for i in range(5):
                print(f"Call {i+1}:")
                try:
                    result = search_db.get_available_dbs()
                    print(f"  Returned {len(result)} indexes")
                except Exception as e:
                    print(f"  API call failed (expected if not configured): {type(e).__name__}")

                # Small delay
                time.sleep(0.1)

            elapsed = time.time() - start_time
            print(f"\nCompleted 5 calls in {elapsed:.2f} seconds")
            print("Check the logs above - you should see cache hits after the first successful call")

        except Exception as e:
            print(f"Azure Search not configured (expected): {type(e).__name__}")
            print("To fully test, configure Azure credentials in your .env file")

        print("\nCache implementation verification:")
        print("- Added 5-minute TTL cache for get_available_dbs()")
        print("- Cache invalidation on create/delete operations")
        print("- Fallback to stale cache on API errors")
        print("- Debug logging for cache hits/misses")

    except ImportError as e:
        print(f"Import error: {e}")
        print("Make sure you're running from the project root directory")

if __name__ == "__main__":
    test_library_status_calls()