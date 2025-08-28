# Hybrid Architecture: Local Files + Azure Blob Storage

This document describes the hybrid video upload architecture that supports both local file uploads and Azure Blob Storage imports.

## Architecture Overview

The VideoQnA-LTW system now supports two video source types:

### 🟢 Local File Upload (Existing)
- **Use Case**: Small-scale uploads, testing, development
- **File Size Limit**: 2GB per file for browser upload
- **Storage**: Local `data/` directory
- **Processing**: Direct upload → Video Indexer → Vector Database

### 🔵 Azure Blob Storage Import (New)
- **Use Case**: Large-scale production deployments
- **File Size Limit**: No practical limit (Azure Blob Storage limit)
- **Storage**: Azure Blob Storage containers
- **Processing**: SAS URL → Video Indexer → Vector Database

## Implementation Details

### Database Schema Changes

New columns added to `video_index` table:
```sql
ALTER TABLE video_index ADD COLUMN source_type TEXT DEFAULT 'local_file';
ALTER TABLE video_index ADD COLUMN blob_url TEXT NULL;
ALTER TABLE video_index ADD COLUMN blob_container TEXT NULL;
ALTER TABLE video_index ADD COLUMN blob_name TEXT NULL;
ALTER TABLE video_index ADD COLUMN blob_metadata TEXT NULL;
```

### Backend Components

#### 1. Blob Storage Service
- **File**: `services/blob_storage_service.py`
- **Features**:
  - List containers and blobs
  - Generate SAS URLs
  - Pattern-based blob selection
  - Metadata-based filtering

#### 2. New API Endpoints
```python
GET  /blob-storage/containers                    # List containers
GET  /blob-storage/containers/{name}/blobs       # List blobs
POST /blob-storage/generate-sas                  # Generate SAS URL
POST /libraries/{name}/import-from-blob          # Import from blob storage
```

#### 3. Task Manager Updates
- Enhanced `TaskInfo` class with `source_type` field
- New `create_blob_import_task()` method
- Support for blob URL processing in existing task pipeline

### Frontend Components

#### 1. Upload Mode Selector
- **Component**: `UploadModeSelector`
- **Purpose**: Choose between local files and blob storage
- **UI**: Radio button selection with descriptions

#### 2. Blob Storage Browser
- **Component**: `BlobStorageBrowser`
- **Features**:
  - Browse containers and blobs
  - Pattern-based selection (e.g., `*.mp4`)
  - File list import
  - Multi-selection support

#### 3. Enhanced Library Management
- **Updated**: `LibraryManagementPanel`
- **Features**:
  - Unified upload interface
  - Source type display in video lists
  - Seamless switching between upload modes

## Configuration

### Environment Variables
```bash
# Azure Blob Storage (Optional)
AZURE_STORAGE_ACCOUNT_NAME=your_storage_account_name
AZURE_STORAGE_ACCOUNT_KEY=your_storage_account_key
# Or use connection string:
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;...
```

### Dependencies
```bash
# Backend
pip install azure-storage-blob==12.23.1

# Frontend (automatically included)
# React components use existing Fluent UI dependencies
```

## Usage Examples

### 1. Import Single Video from Blob
```bash
curl -X POST "/libraries/my-library/import-from-blob" \
-H "Content-Type: application/json" \
-d '{
  "blob_url": "https://storage.blob.core.windows.net/videos/sample.mp4?sv=..."
}'
```

### 2. Import by Pattern
```bash
curl -X POST "/libraries/my-library/import-from-blob" \
-H "Content-Type: application/json" \
-d '{
  "container_name": "videos",
  "blob_path": "training/*.mp4"
}'
```

### 3. Import by File List
```bash
curl -X POST "/libraries/my-library/import-from-blob" \
-H "Content-Type: application/json" \
-d '{
  "container_name": "videos",
  "blob_list": [
    "folder1/video1.mp4",
    "folder2/video2.mp4"
  ]
}'
```

## User Interface

### Upload Mode Selection
The Library Management panel now shows:
1. **Source Selection**: Radio buttons for Local Files vs Azure Blob Storage
2. **Conditional UI**: Different interfaces based on selected source
3. **Unified Processing**: Same task tracking regardless of source

### Video List Display
Enhanced video list with:
- **Source Column**: Shows "Local File" or "Blob Storage"
- **Color Coding**: Blue for blob storage, gray for local files
- **All Existing Features**: Deletion, status tracking, etc.

## Migration Path

### For Existing Deployments
1. **Database Migration**: Run `database/migrate_add_source_type.py`
2. **Environment Setup**: Add blob storage credentials (optional)
3. **Frontend Update**: New build includes hybrid components
4. **Gradual Adoption**: Start with local files, migrate to blob storage over time

### For New Deployments
1. **Choose Architecture**: Local files for testing, blob storage for production
2. **Set Credentials**: Configure appropriate environment variables
3. **Container Setup**: Create blob storage containers as needed
4. **User Training**: Educate users on upload mode selection

## Benefits

### 🔄 Backward Compatibility
- All existing functionality preserved
- Existing videos continue to work
- No breaking changes

### 📈 Scalability
- Handle large video collections
- No local disk space constraints
- Enterprise-grade storage reliability

### 💡 Flexibility
- Choose appropriate method per use case
- Mix local and blob storage videos in same library
- Easy migration between storage types

### 💰 Cost Efficiency
- Blob storage cheaper than local storage at scale
- Shared storage across multiple environments
- Optimized data transfer with SAS URLs

## Security Considerations

### Access Control
- SAS URLs with time-based expiration
- Container-level access policies
- Service principal authentication

### Data Protection
- Azure Storage encryption at rest
- HTTPS-only data transfer
- Network-level access restrictions

## Future Enhancements

### Planned Features
- [ ] Automatic SAS URL renewal
- [ ] Blob metadata tagging
- [ ] Cross-container video migration
- [ ] Batch processing optimization
- [ ] Storage cost analytics

### Integration Possibilities
- [ ] Azure Media Services integration
- [ ] CDN-based video delivery
- [ ] Multi-region blob replication
- [ ] Automated backup strategies

---

**Implementation Status**: Phase 1 Complete ✅  
**Next Phase**: Advanced blob operations and UI enhancements  
**Documentation**: Updated 2025-08-27