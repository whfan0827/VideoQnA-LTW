# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**VideoQnA-LTW** is a production-ready Video Archive Q&A application using the Retrieval Augmented Generation (RAG) pattern with Azure AI Video Indexer data. It features intelligent duplicate detection, background task processing, and supports both Azure cloud services and local development modes.

### Recent Major Improvements (2025)
- ✅ **File Hash Cache System**: MD5-based duplicate detection to prevent redundant uploads
- ✅ **Network Optimization**: Shared session pooling, token caching, reduced connection errors  
- ✅ **Task Management**: Async processing with retry logic and progress tracking
- ✅ **Database Persistence**: SQLite-based task storage with 7-day retention
- ✅ **Performance Optimizations**: Reduced API rate limiting delays from 120s to 5s

## Development Commands

My program and comments must be in English and no emoji, but when chatting with me in terminal please use Traditional Chinese.


### Environment Setup
```powershell
# Check environment prerequisites
.\check_environment.ps1

# Quick start (creates .venv, installs dependencies, builds frontend, starts backend)
.\start_local.ps1
```

### Backend Development
```powershell
cd app\backend
# Always work in virtual environment (.venv in project root or venv in backend)
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:PYTHONPATH = "$(Get-Location)"
python app.py
```

### Frontend Development  
```powershell
cd app\frontend
npm install
npm run build       # Production build (outputs to ../backend/static)
npm run dev         # Development server with proxy to backend
```

### Database Operations
```powershell
cd app\backend
python vi_search\prepare_db.py    # Index videos into vector database
python database\init_db.py        # Initialize SQLite databases
```

## Architecture Overview

### Backend Structure
- **Flask app** (`app.py`): Main application with REST API endpoints
- **vi_search/**: Core RAG functionality
  - `ask.py`: Query processing with RetrieveThenReadVectorApproach
  - `prepare_db.py`: Video indexing pipeline with hash cache integration
  - `file_hash_cache.py`: **NEW** - MD5-based duplicate detection system
  - `prompt_content_db/`: Vector database implementations (Azure Search, ChromaDB)
  - `language_models/`: LLM integrations (Azure OpenAI, dummy for testing)
  - `vi_client/`: Azure Video Indexer API client with optimized networking
- **database/**: SQLite database managers for app data, AI templates, settings
- **services/**: Business logic services  
- **task_manager.py**: **Enhanced** - Background task processing with retry logic

### Frontend Structure
- **React + TypeScript** with Fluent UI components
- **Main components**:
  - `OneShot.tsx`: Main Q&A interface
  - `AIParameterPanel/`: AI model configuration
  - `LibraryManagementPanel/`: Video library management
  - `Answer/`: Response display with video player integration
- **Vite build system** with proxy configuration for backend API calls

### Configuration Modes
- **Test mode**: `LANGUAGE_MODEL=dummy`, `PROMPT_CONTENT_DB=chromadb` (no Azure services needed)
- **Production mode**: `LANGUAGE_MODEL=openai`, `PROMPT_CONTENT_DB=azure_search` (requires Azure credentials)

### Key Data Flow
1. Videos uploaded → Azure Video Indexer → Insights extracted
2. Insights processed → Chunked into sections → Embedded → Stored in vector DB
3. User query → Semantic search → Retrieved sections → LLM generates answer
4. Answer displayed with video timestamps and citations

## Development Guidelines

### Code Requirements (from Copilot instructions)
- Always check for virtual environment before running Python code
- Preserve existing functionality when making changes
- Use English for code and comments, Traditional Chinese for user-facing messages
- Plan changes and get approval before implementing

### Key Files to Understand
- `.env`: Environment configuration (create from template in start_local.ps1)
- `vi_search/constants.py`: Application constants and paths
- `vi_search/utils/ask_templates.py`: Prompt templates for different query types
- `vi_search/file_hash_cache.py`: **NEW** - Duplicate detection implementation
- `app/backend/data/file_hash_cache.json`: Persistent cache storage
- Database schemas in `database/` directory

### Performance Optimizations (2025)
- **Connection Pooling**: `vi_client/account_token_provider.py` - GlobalSessionManager
- **Token Caching**: 50-minute token validity with automatic renewal
- **Rate Limiting**: Optimized from 120s delays to 5s for uploads
- **Error Handling**: 10054 connection error recovery with exponential backoff
- **Duplicate Prevention**: Hash-based file content comparison before upload

### Testing Modes
- **Test Mode**: `LANGUAGE_MODEL=dummy`, `PROMPT_CONTENT_DB=chromadb` (no Azure costs)
- **Production Mode**: `LANGUAGE_MODEL=openai`, `PROMPT_CONTENT_DB=azure_search` 
- Sample videos provided in `data/` directory
- Local ChromaDB for vector storage in test mode

### Deployment Options
- **Local Development**: `.\start_local.ps1` - Full local setup
- **Azure Cloud**: `azd up` and `azd deploy` - Production deployment
- **Docker**: `docker-compose up` - Containerized deployment
- Frontend builds to `app/backend/static` for single-service deployment

### Chinese Language Support
- Chinese filenames automatically converted to UUID-based names
- Full Traditional Chinese UI support
- Code and comments must be in English per project guidelines