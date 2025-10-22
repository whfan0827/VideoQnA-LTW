# VideoQnA-LTW

A Video Q&A application using RAG (Retrieval Augmented Generation) with Azure AI Video Indexer and Azure OpenAI.

## Features

- 🎥 **Video Intelligence**: Automatic video processing with Azure Video Indexer
- 🤖 **AI Q&A**: Ask questions about your videos in natural language
- ⚡ **Smart Caching**: Duplicate detection to avoid reprocessing
- 📊 **Task Management**: Background processing with progress tracking
- 🔍 **Vector Search**: Azure AI Search or ChromaDB support
- 📱 **Modern UI**: React + Fluent UI interface

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Azure subscription (for production) or use test mode (no Azure needed)

### Local Development (Test Mode)

```bash
# 1. Clone repository
git clone https://github.com/yourusername/VideoQnA-LTW.git
cd VideoQnA-LTW

# 2. Backend setup
cd app/backend
python -m venv venv
.\venv\Scripts\Activate.ps1  # Windows
# source venv/bin/activate    # Linux/Mac
pip install -r requirements.txt

# 3. Create .env file (test mode - no Azure needed)
cp .env.example .env
# Edit .env: set LANGUAGE_MODEL=dummy, PROMPT_CONTENT_DB=chromadb

# 4. Start backend
python app.py

# 5. Frontend setup (new terminal)
cd app/frontend
npm install
npm run dev
```

Open http://localhost:5173

### Production Mode (Azure Services)

1. Create Azure resources:
   - Azure Video Indexer account
   - Azure OpenAI service
   - Azure AI Search service

2. Update `.env` with your Azure credentials:
   ```
   LANGUAGE_MODEL=openai
   PROMPT_CONTENT_DB=azure_search
   AZURE_OPENAI_API_KEY=your_key
   AZURE_OPENAI_SERVICE=your_service
   AZURE_SEARCH_SERVICE=your_search
   AZURE_SEARCH_KEY=your_key
   ```

3. Index videos:
   ```bash
   cd app/backend
   python vi_search/prepare_db.py
   ```

## Architecture

```
User → React Frontend → Flask API → Azure Video Indexer
                         ↓
                   Vector Database (Azure AI Search / ChromaDB)
                         ↓
                   Azure OpenAI → Answer with Citations
```

## Project Structure

```
VideoQnA-LTW/
├── app/
│   ├── backend/           # Flask API
│   │   ├── app.py        # Main application
│   │   ├── vi_search/    # RAG core logic
│   │   ├── database/     # SQLite managers
│   │   └── routes/       # API endpoints
│   └── frontend/         # React UI
├── docker-compose.yml    # Docker setup
└── README.md
```

## Environment Variables

Key variables in `.env`:

```bash
# Mode Selection
LANGUAGE_MODEL=dummy|openai        # Use 'dummy' for test, 'openai' for production
PROMPT_CONTENT_DB=chromadb|azure_search

# Azure Video Indexer (production only)
AccountName=your_account
ResourceGroup=your_group
SubscriptionId=your_subscription_id

# Azure OpenAI (production only)
AZURE_OPENAI_SERVICE=your_service
AZURE_OPENAI_API_KEY=your_key

# Azure AI Search (production only)
AZURE_SEARCH_SERVICE=your_service
AZURE_SEARCH_KEY=your_key
```

## Docker Deployment

```bash
# Development
docker-compose up

# Production
docker-compose -f docker-compose.prod.yml up
```

## License

MIT

## Credits

Based on Azure AI Search OpenAI Demo. Enhanced with Azure Video Indexer integration and smart caching.
