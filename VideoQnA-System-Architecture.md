# VideoQnA-LTW System Architecture Flowchart

## Overview

VideoQnA-LTW is a video Q&A system based on the RAG (Retrieval Augmented Generation) pattern, integrating Azure Video Indexer and Azure AI Search to provide intelligent video content question-answering services.

## System Architecture Flowchart

```mermaid
flowchart TD
    A[User Uploads Video] --> B[System Receives File]
    B --> C[Generate Safe Filename<br/>Chinese→UUID]
    C --> D[Calculate File MD5 Hash]
    D --> E{Check Local Cache<br/>file_hash_cache.json}
    
    %% Duplicate Detection Path (Fast)
    E -->|Found Duplicate| F[⚡ Fast Path<br/>Use Cached video_id]
    F --> G[Get Existing Insights from<br/>Azure Video Indexer]
    G --> H[Generate Vector Embeddings]
    H --> I[Store in Azure AI Search]
    I --> J[Update Local SQLite]
    J --> K[⚡ Complete<br/>< 1 minute]
    
    %% Normal Upload Path (Slow)
    E -->|Not Found| L[🐌 Normal Path<br/>Start Upload Processing]
    L --> M[Upload to Azure Video Indexer]
    M --> N[Wait for AI Analysis<br/>Speech, Video, OCR, etc.]
    N --> O[Analysis Complete<br/>Obtain video_id]
    O --> P[Cache File Hash and video_id<br/>to Local Cache]
    P --> Q[Get Analysis Results (Insights)]
    Q --> R[Segment Processing<br/>Time-based Chunks]
    R --> S[Generate Vector Embeddings<br/>Using Azure OpenAI]
    S --> T[Store in Azure AI Search<br/>Build Search Index]
    T --> U[Update Local SQLite<br/>Video Metadata]
    U --> V[🐌 Complete<br/>8-22 minutes]
    
    %% Database Structure
    K --> W[Data Storage]
    V --> W
    W --> X[Azure AI Search<br/>Vector Search Index]
    W --> Y[Local SQLite<br/>Video Metadata]
    W --> Z[Local Cache<br/>MD5→video_id Mapping]
    
    %% Q&A Query Flow
    AA[User Question] --> BB[Semantic Search<br/>Azure AI Search]
    BB --> CC[Retrieve Relevant Segments]
    CC --> DD[LLM Generate Answer<br/>Azure OpenAI]
    DD --> EE[Return Answer + Video Timestamps]
    
    %% Deletion Flow
    FF[Delete Video] --> GG[Delete Vector Documents from<br/>Azure AI Search]
    GG --> HH[Delete Metadata Records from<br/>Local SQLite]
    HH --> II[Deletion Complete<br/>Irreversible]
    
    %% Style Definitions
    classDef fastPath fill:#90EE90,stroke:#006400,stroke-width:3px
    classDef slowPath fill:#FFB6C1,stroke:#8B0000,stroke-width:2px
    classDef database fill:#87CEEB,stroke:#4682B4,stroke-width:2px
    classDef process fill:#DDA0DD,stroke:#8B008B,stroke-width:2px
    
    class F,G,H,I,J,K fastPath
    class L,M,N,O,P,Q,R,S,T,U,V slowPath
    class W,X,Y,Z database
    class AA,BB,CC,DD,EE,FF,GG,HH,II process
```

## Processing Path Descriptions

### 🟢 Fast Path (Duplicate Detection)
- **Trigger Condition**: System detects files with identical MD5 hash
- **Processing Time**: < 1 minute
- **Key Optimizations**:
  - ✅ Skip upload to Azure Video Indexer
  - ✅ Skip AI analysis wait (5-15 minutes)
  - ✅ Directly use existing insights for vectorization
  - ✅ Significantly save time and Azure service costs

### 🔴 Normal Path (First Upload)
- **Trigger Condition**: Brand new file (MD5 hash not in cache)
- **Processing Time**: 8-22 minutes
- **Complete Process**:
  1. File upload (2-5 minutes)
  2. Azure Video Indexer AI analysis (5-15 minutes)
  3. Result caching and vectorization (1-2 minutes)

### 🔵 Data Storage Architecture
1. **Azure AI Search**
   - Store vector embeddings
   - Provide semantic search functionality
   - Support complex queries and filtering

2. **Local SQLite Database**
   - Video metadata management
   - User interface display
   - Task status tracking

3. **Local File Cache**
   - MD5 hash → video_id mapping
   - File: `app/backend/data/file_hash_cache.json`
   - Enable duplicate detection functionality

### 🟣 Other Core Features
1. **Q&A Query Process**
   - User question → Semantic search → Retrieve relevant segments → LLM generate answer

2. **Video Deletion Mechanism**
   - Dual cleanup: Azure AI Search + Local SQLite
   - Ensure complete removal, irreversible

## Technical Features

### Intelligent Duplicate Detection
- **Content-based**: Uses MD5 hash, unaffected by filename
- **Efficient Caching**: Local JSON file for fast queries
- **Cross-index Reuse**: Same video can be quickly added to different indexes

### Performance Comparison
| Scenario | Processing Time | Description |
|----------|----------------|-------------|
| First Upload | 8-22 minutes | Complete Azure Video Indexer analysis process |
| Duplicate Detection | < 1 minute | Use existing analysis results |
| Q&A Query | 2-5 seconds | Semantic search + LLM generation |
| Video Deletion | 10-30 seconds | Dual cleanup of all storage locations |

### Cost Optimization
- **Avoid Duplicate Analysis**: Save Azure Video Indexer usage quota
- **Rapid Scaling**: Same video can be added to multiple indexes at low cost
- **Smart Caching**: Reduce unnecessary API calls

## Supported Use Cases

✅ **Same Video, Different Indexes**: Complete in seconds  
✅ **Renamed Videos**: System still recognizes duplicates  
✅ **Re-upload After Errors**: Extremely fast completion  
✅ **Multi-environment Deployment**: Dev/Test/Production rapid sync  
✅ **Bulk Video Migration**: Smart deduplication, avoid redundant processing  

## File Structure

### Core Components
```
app/backend/
├── vi_search/
│   ├── file_hash_cache.py          # MD5 caching system
│   ├── prepare_db.py               # Video processing main logic
│   ├── vi_client/                  # Azure Video Indexer client
│   └── prompt_content_db/          # Vector database interface
│       ├── azure_search.py         # Azure AI Search implementation
│       └── chroma_db.py            # ChromaDB implementation (for testing)
├── task_manager.py                 # Asynchronous task management
├── database/
│   └── app_data_manager.py         # SQLite database management
└── data/
    └── file_hash_cache.json        # MD5 cache file
```

### Configuration Files
- `.env` - Environment variable configuration
- `CLAUDE.md` - Project documentation
- `requirements.txt` - Python dependencies

## Environment Configuration

### Azure Service Requirements
- Azure Video Indexer account
- Azure AI Search service
- Azure OpenAI service
- Service Principal authentication

### Local Environment
- Python 3.10+
- SQLite database
- Node.js (frontend)

## Security Considerations

- **Filename Sanitization**: Chinese filenames automatically converted to UUID
- **Access Control**: Azure RBAC integration
- **Data Isolation**: Multiple indexes support different purposes
- **Error Handling**: Comprehensive retry mechanisms and error recovery

---

**Last Updated**: 2025-08-27  
**System Version**: VideoQnA-LTW v2.0  
**Documentation Maintained by**: Claude Code Assistant  