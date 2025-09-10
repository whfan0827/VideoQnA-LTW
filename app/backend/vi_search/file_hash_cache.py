"""
File Hash Cache System for avoiding duplicate video uploads to Azure Video Indexer
"""

import hashlib
import json
import time
from pathlib import Path
from typing import Optional, Dict
import logging

from config import AppConfig

logger = logging.getLogger(__name__)

class FileHashCache:
    """
    Local cache system to avoid uploading duplicate video files to Azure Video Indexer.
    Uses MD5 hash of file content to identify duplicates, regardless of filename.
    """
    
    def __init__(self, cache_file: str = None):
        if cache_file is None:
            cache_file = AppConfig.CACHE_FILE_NAME
        self.cache_file = Path(__file__).parent.parent / "data" / cache_file
        self.cache_file.parent.mkdir(exist_ok=True)
        self.cache: Dict[str, dict] = self._load_cache()
        logger.info(f"FileHashCache initialized with {len(self.cache)} cached entries")

    def _load_cache(self) -> Dict[str, dict]:
        """Load existing cache from disk"""
        if not self.cache_file.exists():
            return {}
        
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
                logger.info(f"Loaded file hash cache from {self.cache_file}")
                return cache_data
        except Exception as e:
            logger.warning(f"Failed to load cache file: {e}")
            return {}

    def _save_cache(self):
        """Save current cache to disk"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, indent=2, ensure_ascii=False)
            logger.debug(f"Cache saved to {self.cache_file}")
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")

    def get_file_hash(self, file_path: Path, chunk_size: int = None) -> str:
        """
        Calculate MD5 hash of file content efficiently
        
        Args:
            file_path: Path to the video file
            chunk_size: Size of chunks to read (from env or default 8KB)
            
        Returns:
            MD5 hash string of the file content
        """
        if chunk_size is None:
            chunk_size = AppConfig.FILE_HASH_CHUNK_SIZE
        
        hasher = hashlib.md5()
        
        try:
            with open(file_path, 'rb') as f:
                # Read file in chunks to handle large video files efficiently
                while chunk := f.read(chunk_size):
                    hasher.update(chunk)
            
            file_hash = hasher.hexdigest()
            logger.debug(f"Generated hash {file_hash} for {file_path.name}")
            return file_hash
            
        except Exception as e:
            logger.error(f"Failed to hash file {file_path}: {e}")
            raise

    def get_cached_video_info(self, file_path: Path, validate_with_azure: bool = True) -> Optional[dict]:
        """
        Check if this file (by content hash) has already been processed
        
        Args:
            file_path: Path to the video file
            validate_with_azure: If True, verify the cached video_id exists in Azure Video Indexer
            
        Returns:
            dict with video_id and metadata if found, None if not cached or invalid
        """
        try:
            file_hash = self.get_file_hash(file_path)
            cached_info = self.cache.get(file_hash)
            
            if cached_info:
                video_id = cached_info['video_id']
                logger.info(f"Found cached entry for {file_path.name} -> video_id: {video_id}")
                
                # Validate with Azure Video Indexer if requested
                if validate_with_azure:
                    if self._validate_video_id_exists(video_id):
                        logger.info(f"Cached video_id {video_id} verified in Azure Video Indexer")
                        return cached_info
                    else:
                        logger.warning(f"Cached video_id {video_id} not found in Azure Video Indexer - invalidating cache entry")
                        # Remove the invalid cache entry
                        del self.cache[file_hash]
                        self._save_cache()
                        return None
                else:
                    # Return cached info without validation
                    return cached_info
                
        except Exception as e:
            logger.error(f"Error checking cache for {file_path}: {e}")
            
        return None
    
    def _validate_video_id_exists(self, video_id: str) -> bool:
        """
        Validate that a video_id exists in Azure Video Indexer
        
        Args:
            video_id: The video ID to validate
            
        Returns:
            True if video exists, False otherwise
        """
        try:
            # Import here to avoid circular dependencies
            from vi_search.vi_client.video_indexer_client import init_video_indexer_client
            from dotenv import load_dotenv
            import os
            
            # Load environment variables
            load_dotenv()
            
            # Create config from environment variables
            config = {
                'AccountName': os.getenv('AccountName'),
                'ResourceGroup': os.getenv('ResourceGroup'), 
                'SubscriptionId': os.getenv('SubscriptionId'),
                'AZURE_CLIENT_ID': os.getenv('AZURE_CLIENT_ID'),
                'AZURE_CLIENT_SECRET': os.getenv('AZURE_CLIENT_SECRET'),
                'AZURE_TENANT_ID': os.getenv('AZURE_TENANT_ID')
            }
            
            client = init_video_indexer_client(config)
            
            # Try to get video info - if successful, video exists
            video_info = client.get_video_async(video_id)
            return video_info is not None
            
        except Exception as e:
            # If we get a 404 or similar error, video doesn't exist
            if '404' in str(e) or 'not found' in str(e).lower():
                logger.debug(f"Video {video_id} not found in Azure Video Indexer: {e}")
                return False
            else:
                # For other errors (network issues, auth problems), assume video exists
                # to avoid false negatives due to temporary issues
                logger.warning(f"Could not validate video {video_id} due to error: {e}")
                return True

    def cache_video_info(self, file_path: Path, video_id: str, library_name: str = "", 
                        additional_info: dict = None):
        """
        Cache the video_id and metadata for this file's content
        
        Args:
            file_path: Path to the video file
            video_id: Azure Video Indexer video ID
            library_name: Name of the library this video belongs to
            additional_info: Any additional metadata to store
        """
        try:
            file_hash = self.get_file_hash(file_path)
            
            cache_entry = {
                "video_id": video_id,
                "library_name": library_name,
                "filename": file_path.name,
                "file_size": file_path.stat().st_size,
                "cached_at": time.time(),
                "cached_at_readable": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            if additional_info:
                cache_entry.update(additional_info)
            
            self.cache[file_hash] = cache_entry
            self._save_cache()
            
            logger.info(f"Cached video_id {video_id} for file {file_path.name} (hash: {file_hash})")
            
        except Exception as e:
            logger.error(f"Failed to cache info for {file_path}: {e}")

    def clear_cache(self):
        """Clear all cached entries"""
        self.cache.clear()
        self._save_cache()
        logger.info("File hash cache cleared")

    def get_cache_stats(self) -> dict:
        """Get statistics about the cache"""
        total_entries = len(self.cache)
        total_size = sum(entry.get('file_size', 0) for entry in self.cache.values())
        
        return {
            "total_entries": total_entries,
            "total_file_size_mb": total_size / (1024 * 1024),
            "cache_file_path": str(self.cache_file),
            "cache_exists": self.cache_file.exists()
        }

    def remove_stale_entries(self, max_age_days: int = 30):
        """Remove cache entries older than specified days"""
        cutoff_time = time.time() - (max_age_days * 24 * 60 * 60)
        
        stale_hashes = [
            file_hash for file_hash, info in self.cache.items()
            if info.get('cached_at', 0) < cutoff_time
        ]
        
        for file_hash in stale_hashes:
            del self.cache[file_hash]
        
        if stale_hashes:
            self._save_cache()
            logger.info(f"Removed {len(stale_hashes)} stale cache entries (older than {max_age_days} days)")
        
        return len(stale_hashes)


def get_global_cache() -> FileHashCache:
    """Get the global file hash cache instance"""
    if not hasattr(get_global_cache, '_instance'):
        get_global_cache._instance = FileHashCache()
    return get_global_cache._instance