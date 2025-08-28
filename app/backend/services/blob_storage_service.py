"""
Azure Blob Storage Service for VideoQnA-LTW.
Handles blob operations including listing, SAS URL generation, and metadata management.
"""

import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from urllib.parse import urlparse
import json

try:
    from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
    from azure.core.exceptions import AzureError
    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False
    logging.warning("Azure Storage SDK not available. Blob storage features will be disabled.")

logger = logging.getLogger(__name__)

@dataclass
class BlobInfo:
    """Information about a blob in storage."""
    name: str
    container: str
    size: int
    last_modified: datetime
    content_type: str
    md5_hash: Optional[str] = None
    metadata: Dict[str, str] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class BlobStorageService:
    """Service for managing Azure Blob Storage operations."""
    
    def __init__(self):
        if not AZURE_AVAILABLE:
            raise ImportError("Azure Storage SDK is required for blob storage operations")
        
        self.account_name = os.getenv('AZURE_STORAGE_ACCOUNT_NAME')
        self.account_key = os.getenv('AZURE_STORAGE_ACCOUNT_KEY')
        self.connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
        
        if not self.account_name or not self.account_key:
            if not self.connection_string:
                raise ValueError("Azure Storage credentials not configured. Set AZURE_STORAGE_ACCOUNT_NAME and AZURE_STORAGE_ACCOUNT_KEY or AZURE_STORAGE_CONNECTION_STRING")
        
        try:
            if self.connection_string:
                self.blob_service_client = BlobServiceClient.from_connection_string(self.connection_string)
            else:
                account_url = f"https://{self.account_name}.blob.core.windows.net"
                self.blob_service_client = BlobServiceClient(account_url, credential=self.account_key)
                
            logger.info(f"Initialized blob storage service for account: {self.account_name}")
        except Exception as e:
            logger.error(f"Failed to initialize blob storage service: {e}")
            raise
    
    def list_containers(self) -> List[str]:
        """List all containers in the storage account."""
        try:
            containers = []
            for container in self.blob_service_client.list_containers():
                containers.append(container.name)
            return containers
        except AzureError as e:
            logger.error(f"Failed to list containers: {e}")
            return []
    
    def list_blobs(self, container_name: str, prefix: str = None) -> List[BlobInfo]:
        """
        List blobs in a container.
        
        Args:
            container_name: Name of the container
            prefix: Optional prefix to filter blobs
            
        Returns:
            List of BlobInfo objects
        """
        try:
            container_client = self.blob_service_client.get_container_client(container_name)
            blobs = []
            
            for blob in container_client.list_blobs(name_starts_with=prefix, include=['metadata']):
                # Filter to video files only
                if self._is_video_file(blob.name):
                    blob_info = BlobInfo(
                        name=blob.name,
                        container=container_name,
                        size=blob.size,
                        last_modified=blob.last_modified,
                        content_type=blob.content_settings.content_type if blob.content_settings else 'unknown',
                        md5_hash=blob.content_settings.content_md5.hex() if blob.content_settings and blob.content_settings.content_md5 else None,
                        metadata=blob.metadata or {}
                    )
                    blobs.append(blob_info)
            
            return blobs
        except AzureError as e:
            logger.error(f"Failed to list blobs in container '{container_name}': {e}")
            return []
    
    def list_blobs_by_pattern(self, container_name: str, pattern: str) -> List[BlobInfo]:
        """
        List blobs matching a pattern (supports wildcards).
        
        Args:
            container_name: Name of the container
            pattern: Pattern to match (e.g., "folder/*", "*.mp4")
            
        Returns:
            List of matching BlobInfo objects
        """
        import fnmatch
        
        all_blobs = self.list_blobs(container_name)
        matching_blobs = []
        
        for blob in all_blobs:
            if fnmatch.fnmatch(blob.name, pattern):
                matching_blobs.append(blob)
        
        return matching_blobs
    
    def list_blobs_by_metadata(self, container_name: str, metadata_filter: Dict[str, str]) -> List[BlobInfo]:
        """
        List blobs matching metadata criteria.
        
        Args:
            container_name: Name of the container
            metadata_filter: Dictionary of metadata key-value pairs to match
            
        Returns:
            List of matching BlobInfo objects
        """
        all_blobs = self.list_blobs(container_name)
        matching_blobs = []
        
        for blob in all_blobs:
            if self._metadata_matches(blob.metadata, metadata_filter):
                matching_blobs.append(blob)
        
        return matching_blobs
    
    def generate_sas_url(self, container_name: str, blob_name: str, expiry_hours: int = 24) -> str:
        """
        Generate a SAS URL for a blob.
        
        Args:
            container_name: Name of the container
            blob_name: Name of the blob
            expiry_hours: Hours until the SAS URL expires (default: 24)
            
        Returns:
            SAS URL string
        """
        try:
            expiry_time = datetime.utcnow() + timedelta(hours=expiry_hours)
            
            # Ensure blob_name uses forward slashes for URL compatibility
            normalized_blob_name = str(blob_name).replace('\\', '/')
            
            sas_token = generate_blob_sas(
                account_name=self.account_name,
                container_name=container_name,
                blob_name=normalized_blob_name,
                account_key=self.account_key,
                permission=BlobSasPermissions(read=True),
                expiry=expiry_time
            )
            
            blob_url = f"https://{self.account_name}.blob.core.windows.net/{container_name}/{normalized_blob_name}"
            sas_url = f"{blob_url}?{sas_token}"
            
            logger.info(f"Generated SAS URL for {blob_name}, expires: {expiry_time}")
            return sas_url
            
        except AzureError as e:
            logger.error(f"Failed to generate SAS URL for '{blob_name}': {e}")
            raise
    
    def get_blob_properties(self, container_name: str, blob_name: str) -> Optional[BlobInfo]:
        """
        Get properties and metadata for a specific blob.
        
        Args:
            container_name: Name of the container
            blob_name: Name of the blob
            
        Returns:
            BlobInfo object or None if blob not found
        """
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=container_name, 
                blob=blob_name
            )
            
            properties = blob_client.get_blob_properties()
            
            return BlobInfo(
                name=blob_name,
                container=container_name,
                size=properties.size,
                last_modified=properties.last_modified,
                content_type=properties.content_settings.content_type if properties.content_settings else 'unknown',
                md5_hash=properties.content_settings.content_md5.hex() if properties.content_settings and properties.content_settings.content_md5 else None,
                metadata=properties.metadata or {}
            )
            
        except AzureError as e:
            logger.error(f"Failed to get properties for '{blob_name}': {e}")
            return None
    
    def extract_blob_info_from_url(self, blob_url: str) -> Dict[str, str]:
        """
        Extract container and blob name from a blob URL.
        
        Args:
            blob_url: Full blob URL (with or without SAS token)
            
        Returns:
            Dictionary with 'container', 'blob_name', and 'account_name'
        """
        try:
            parsed_url = urlparse(blob_url)
            path_parts = parsed_url.path.strip('/').split('/')
            
            if len(path_parts) < 2:
                raise ValueError("Invalid blob URL format")
            
            container_name = path_parts[0]
            blob_name = '/'.join(path_parts[1:])
            
            # Extract account name from hostname
            hostname_parts = parsed_url.hostname.split('.')
            account_name = hostname_parts[0] if hostname_parts else None
            
            return {
                'container': container_name,
                'blob_name': blob_name,
                'account_name': account_name
            }
            
        except Exception as e:
            logger.error(f"Failed to parse blob URL '{blob_url}': {e}")
            raise ValueError(f"Invalid blob URL: {blob_url}")
    
    def _is_video_file(self, filename: str) -> bool:
        """Check if a file is a video file based on its extension."""
        video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v'}
        return any(filename.lower().endswith(ext) for ext in video_extensions)
    
    def _metadata_matches(self, blob_metadata: Dict[str, str], filter_metadata: Dict[str, str]) -> bool:
        """Check if blob metadata matches the filter criteria."""
        for key, value in filter_metadata.items():
            if key not in blob_metadata or blob_metadata[key] != value:
                return False
        return True


# Global instance for easy access
blob_storage_service = None

def get_blob_storage_service() -> BlobStorageService:
    """Get or create the global blob storage service instance."""
    global blob_storage_service
    
    if blob_storage_service is None:
        if not AZURE_AVAILABLE:
            raise ImportError("Azure Storage SDK is not available")
        
        try:
            blob_storage_service = BlobStorageService()
        except Exception as e:
            logger.error(f"Failed to initialize blob storage service: {e}")
            raise
    
    return blob_storage_service