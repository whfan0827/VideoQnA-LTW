# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**VideoQnA-LTW** is a production-ready Video Archive Q&A application using the Retrieval Augmented Generation (RAG) pattern with Azure AI Video Indexer data. It features intelligent duplicate detection, background task processing, and supports both Azure cloud services and local development modes.

### Recent Major Improvements (2025)
- ✅ **File Hash Cache System**: MD5-based duplicate detection to prevent redundant uploads
- ✅ **Network Optimization**: Shared session pooling, token caching, reduced connection errors  
- ✅ **Task Management**: Async processing with retry logic, progress tracking, and 7-day cleanup
- ✅ **Rate Limiting Optimization**: Reduced upload delays to 5s with intelligent rate limiting

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

## Project Development Guidelines

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





# Development Guidelines

## Philosophy

### Core Beliefs

- **Incremental progress over big bangs** - Small changes that compile and pass tests
- **Learning from existing code** - Study and plan before implementing
- **Pragmatic over dogmatic** - Adapt to project reality
- **Clear intent over clever code** - Be boring and obvious

### Simplicity Means

- Single responsibility per function/class
- Avoid premature abstractions
- No clever tricks - choose the boring solution
- If you need to explain it, it's too complex

## Process

### 1. Planning & Staging

Break complex work into 3-5 stages. Document in `IMPLEMENTATION_PLAN.md`:

```markdown
## Stage N: [Name]
**Goal**: [Specific deliverable]
**Success Criteria**: [Testable outcomes]
**Tests**: [Specific test cases]
**Status**: [Not Started|In Progress|Complete]
```
- Update status as you progress
- Remove file when all stages are done

### 2. Implementation Flow

1. **Understand** - Study existing patterns in codebase
2. **Test** - Write test first (red)
3. **Implement** - Minimal code to pass (green)
4. **Refactor** - Clean up with tests passing
5. **Commit** - With clear message linking to plan

### 3. When Stuck (After 3 Attempts)

**CRITICAL**: Maximum 3 attempts per issue, then STOP.

1. **Document what failed**:
   - What you tried
   - Specific error messages
   - Why you think it failed

2. **Research alternatives**:
   - Find 2-3 similar implementations
   - Note different approaches used

3. **Question fundamentals**:
   - Is this the right abstraction level?
   - Can this be split into smaller problems?
   - Is there a simpler approach entirely?

4. **Try different angle**:
   - Different library/framework feature?
   - Different architectural pattern?
   - Remove abstraction instead of adding?

## Technical Standards

### Architecture Principles

- **Composition over inheritance** - Use dependency injection
- **Interfaces over singletons** - Enable testing and flexibility
- **Explicit over implicit** - Clear data flow and dependencies
- **Test-driven when possible** - Never disable tests, fix them
- program code and comments must be in English and no emoji, but when chatting with me in terminal please use Traditional Chinese.
- no mock test

### Code Quality

- **Every commit must**:
  - Compile successfully
  - Pass all existing tests
  - Include tests for new functionality
  - Follow project formatting/linting

- **Before committing**:
  - Run formatters/linters
  - Self-review changes
  - Ensure commit message explains "why"

### Error Handling

- Fail fast with descriptive messages
- Include context for debugging
- Handle errors at appropriate level
- Never silently swallow exceptions

## Decision Framework

When multiple valid approaches exist, choose based on:

1. **Testability** - Can I easily test this?
2. **Readability** - Will someone understand this in 6 months?
3. **Consistency** - Does this match project patterns?
4. **Simplicity** - Is this the simplest solution that works?
5. **Reversibility** - How hard to change later?

## Project Integration

### Learning the Codebase

- Find 3 similar features/components
- Identify common patterns and conventions
- Use same libraries/utilities when possible
- Follow existing test patterns

### Tooling

- Use project's existing build system
- Use project's test framework
- Use project's formatter/linter settings
- Don't introduce new tools without strong justification

## Quality Gates

### Definition of Done

- [ ] Tests written and passing
- [ ] Code follows project conventions
- [ ] No linter/formatter warnings
- [ ] Commit messages are clear
- [ ] Implementation matches plan
- [ ] No TODOs without issue numbers

### Test Guidelines

- Test behavior, not implementation
- One assertion per test when possible
- Clear test names describing scenario
- Use existing test utilities/helpers
- Tests should be deterministic

## Important Reminders

**NEVER**:
- Use `--no-verify` to bypass commit hooks
- Disable tests instead of fixing them
- Commit code that doesn't compile
- Make assumptions - verify with existing code

**ALWAYS**:
- Commit working code incrementally
- Update plan documentation as you go
- Learn from existing implementations
- Stop after 3 failed attempts and reassess
