# Docker Version Launch Script
# Run: .\start_docker.ps1

Write-Host "=== VideoQnA-LTW Docker Deployment ===" -ForegroundColor Green

# Check if Docker is installed
Write-Host "`nChecking Docker..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version 2>&1
    Write-Host "✓ Docker: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Docker Desktop first: https://www.docker.com/products/docker-desktop" -ForegroundColor Cyan
    exit 1
}

# Check Docker Compose
try {
    $composeVersion = docker compose version 2>&1
    Write-Host "✓ Docker Compose: $composeVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker Compose is not installed" -ForegroundColor Red
    exit 1
}

# Check if Docker is running
Write-Host "`nChecking Docker service..." -ForegroundColor Yellow
try {
    docker info > $null 2>&1
    Write-Host "✓ Docker service is running" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker service is not running, please start Docker Desktop" -ForegroundColor Red
    exit 1
}

Write-Host "`nSelect run mode:" -ForegroundColor Yellow
Write-Host "1. Test mode (uses mock services, no Azure configuration needed)"
Write-Host "2. Azure mode (requires Azure service configuration)"
Write-Host "3. Development mode (code hot reload)"
Write-Host "4. Stop and clean containers"
Write-Host "5. View logs"
Write-Host "6. Exit"

$choice = Read-Host "Please enter your choice (1-6)"

switch ($choice) {
    "1" {
        Write-Host "`nStarting test mode..." -ForegroundColor Green
        Write-Host "Using mock language model and local vector database" -ForegroundColor Cyan
        
        # Use default docker-compose.yml (configured for test mode)
        docker compose up --build -d
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "`n✓ Services started successfully!" -ForegroundColor Green
            Write-Host "Application URL: http://localhost:5000" -ForegroundColor Cyan
            Write-Host "`nView logs: docker compose logs -f" -ForegroundColor Gray
        } else {
            Write-Host "✗ Startup failed, please check error messages" -ForegroundColor Red
        }
    }
    
    "2" {
        Write-Host "`nStarting Azure mode..." -ForegroundColor Green
        Write-Host "⚠ Azure service information needs to be configured first" -ForegroundColor Yellow
        
        # Check if .env file exists
        if (-not (Test-Path ".env")) {
            Write-Host "Creating .env file..." -ForegroundColor Cyan
            @"
# Azure Service Configuration
LANGUAGE_MODEL=openai
PROMPT_CONTENT_DB=azure_search

# Azure OpenAI
AZURE_OPENAI_API_KEY=your_api_key_here
AZURE_OPENAI_SERVICE=your_service_name
AZURE_OPENAI_CHATGPT_DEPLOYMENT=gpt-4o
AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT=text-embedding-ada-002

# Azure Search
AZURE_SEARCH_SERVICE=your_search_service
AZURE_SEARCH_KEY=your_search_key

# Video Indexer
AccountName=your_vi_account
ResourceGroup=your_resource_group
SubscriptionId=your_subscription_id
"@ | Out-File -FilePath ".env" -Encoding UTF8
            
            Write-Host "✓ .env file created" -ForegroundColor Green
            Write-Host "Please edit the .env file and fill in your Azure service information, then run this script again" -ForegroundColor Yellow
            exit 0
        }
        
        docker compose --env-file .env up --build -d
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "`n✓ Services started successfully!" -ForegroundColor Green
            Write-Host "Application URL: http://localhost:5000" -ForegroundColor Cyan
        } else {
            Write-Host "✗ Startup failed, please check Azure service configuration" -ForegroundColor Red
        }
    }
    
    "3" {
        Write-Host "`nStarting development mode..." -ForegroundColor Green
        Write-Host "Code changes will be automatically reloaded" -ForegroundColor Cyan
        
        # Development mode, mount source code directories
        docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
    }
    
    "4" {
        Write-Host "`nStopping and cleaning containers..." -ForegroundColor Yellow
        docker compose down -v
        docker system prune -f
        Write-Host "✓ Cleanup completed" -ForegroundColor Green
    }
    
    "5" {
        Write-Host "`nViewing service logs..." -ForegroundColor Yellow
        docker compose logs -f
    }
    
    "6" {
        Write-Host "Exit" -ForegroundColor Gray
        exit 0
    }
    
    default {
        Write-Host "Invalid selection" -ForegroundColor Red
        exit 1
    }
}
