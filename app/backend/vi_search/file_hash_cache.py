"""
File Hash Cache System for avoiding duplicate video uploads to Azure Video Indexer
"""

import hashlib
import json
import time
from pathlib import Path
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)

class FileHashCache:
    """
    Local cache system to avoid uploading duplicate video files to Azure Video Indexer.
    Uses MD5 hash of file content to identify duplicates, regardless of filename.
    """
    
    def __init__(self, cache_file: str = "file_hash_cache.json"):
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

    def get_file_hash(self, file_path: Path, chunk_size: int = 8192) -> str:
        """
        Calculate MD5 hash of file content efficiently
        
        Args:
            file_path: Path to the video file
            chunk_size: Size of chunks to read (default 8KB)
            
        Returns:
            MD5 hash string of the file content
        """
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

    def get_cached_video_info(self, file_path: Path) -> Optional[dict]:
        """
        Check if this file (by content hash) has already been processed
        
        Args:
            file_path: Path to the video file
            
        Returns:
            dict with video_id and metadata if found, None if not cached
        """
        try:
            file_hash = self.get_file_hash(file_path)
            cached_info = self.cache.get(file_hash)
            
            if cached_info:
                logger.info(f"Found cached entry for {file_path.name} -> video_id: {cached_info['video_id']}")
                return cached_info
                
        except Exception as e:
            logger.error(f"Error checking cache for {file_path}: {e}")
            
        return None

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