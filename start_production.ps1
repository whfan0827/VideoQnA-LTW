# Production deployment script for VideoQnA-LTW
# Run this script to deploy the application in production mode

Write-Host "🚀 VideoQnA-LTW Production Deployment" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Green

# Check prerequisites
Write-Host "`n📋 Checking prerequisites..." -ForegroundColor Yellow

# Check Docker
try {
    $dockerVersion = docker --version
    Write-Host "✓ Docker found: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker not found. Please install Docker Desktop." -ForegroundColor Red
    exit 1
}

# Check Docker Compose
try {
    $composeVersion = docker-compose --version
    Write-Host "✓ Docker Compose found: $composeVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker Compose not found. Please install Docker Compose." -ForegroundColor Red
    exit 1
}

# Check environment file
if (-not (Test-Path ".env.production")) {
    Write-Host "✗ .env.production not found." -ForegroundColor Red
    Write-Host "Please copy .env.production.template to .env.production and configure it." -ForegroundColor Yellow
    
    $createTemplate = Read-Host "Create template now? (y/N)"
    if ($createTemplate -eq "y" -or $createTemplate -eq "Y") {
        Copy-Item ".env.production.template" ".env.production"
        Write-Host "✓ Template created. Please edit .env.production before continuing." -ForegroundColor Green
        Write-Host "Opening .env.production for editing..." -ForegroundColor Cyan
        Start-Process notepad ".env.production"
        Read-Host "Press Enter after configuring .env.production"
    } else {
        exit 1
    }
}

Write-Host "✓ Environment file found" -ForegroundColor Green

# Load environment variables to validate
$envContent = Get-Content ".env.production" | Where-Object { $_ -match "^[^#].*=" }
$requiredVars = @(
    "AZURE_OPENAI_SERVICE",
    "AZURE_OPENAI_API_KEY", 
    "AZURE_CLIENT_ID",
    "AZURE_CLIENT_SECRET"
)

$missingVars = @()
foreach ($var in $requiredVars) {
    $found = $envContent | Where-Object { $_ -match "^$var\s*=" -and $_ -notmatch "=\s*$" }
    if (-not $found) {
        $missingVars += $var
    }
}

if ($missingVars.Count -gt 0) {
    Write-Host "✗ Missing required environment variables:" -ForegroundColor Red
    foreach ($var in $missingVars) {
        Write-Host "  - $var" -ForegroundColor Red
    }
    Write-Host "Please configure these in .env.production" -ForegroundColor Yellow
    exit 1
}

Write-Host "✓ Required environment variables configured" -ForegroundColor Green

# Deployment options
Write-Host "`n🎯 Select deployment option:" -ForegroundColor Yellow
Write-Host "1. Basic deployment (App + Redis)"
Write-Host "2. Full deployment with Nginx (Recommended)"
Write-Host "3. App only (for testing)"

$option = Read-Host "Choose option (1-3)"

$composeFile = "docker-compose.prod.yml"
$envFile = ".env.production"

switch ($option) {
    "1" {
        Write-Host "`n🔧 Starting basic deployment..." -ForegroundColor Cyan
        $services = "videoqna-app redis"
    }
    "2" {
        Write-Host "`n🔧 Starting full deployment with Nginx..." -ForegroundColor Cyan
        $services = "--profile with-nginx"
    }
    "3" {
        Write-Host "`n🔧 Starting app-only deployment..." -ForegroundColor Cyan
        $services = "videoqna-app"
    }
    default {
        Write-Host "Invalid option selected." -ForegroundColor Red
        exit 1
    }
}

# Stop existing containers
Write-Host "`n🛑 Stopping existing containers..." -ForegroundColor Yellow
docker-compose -f $composeFile --env-file $envFile down

# Build images
Write-Host "`n🏗️ Building Docker images..." -ForegroundColor Yellow
docker-compose -f $composeFile --env-file $envFile build --no-cache

if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Build failed!" -ForegroundColor Red
    exit 1
}

# Start services
Write-Host "`n🚀 Starting services..." -ForegroundColor Yellow
if ($services -eq "--profile with-nginx") {
    docker-compose -f $composeFile --env-file $envFile $services up -d
} else {
    docker-compose -f $composeFile --env-file $envFile up -d $services
}

if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Startup failed!" -ForegroundColor Red
    exit 1
}

# Wait for services to be ready
Write-Host "`n⏳ Waiting for services to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Health check
Write-Host "`n🏥 Performing health check..." -ForegroundColor Yellow
$maxRetries = 6
$retryCount = 0

do {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:5000/indexes" -TimeoutSec 10 -UseBasicParsing
        if ($response.StatusCode -eq 200) {
            Write-Host "✓ Application is healthy!" -ForegroundColor Green
            break
        }
    } catch {
        $retryCount++
        if ($retryCount -lt $maxRetries) {
            Write-Host "⏳ Waiting for application to start... (attempt $retryCount/$maxRetries)" -ForegroundColor Yellow
            Start-Sleep -Seconds 10
        }
    }
} while ($retryCount -lt $maxRetries)

if ($retryCount -eq $maxRetries) {
    Write-Host "✗ Health check failed after $maxRetries attempts" -ForegroundColor Red
    Write-Host "Checking logs..." -ForegroundColor Yellow
    docker-compose -f $composeFile --env-file $envFile logs --tail=20 videoqna-app
    exit 1
}

# Show deployment info
Write-Host "`n✅ Deployment completed successfully!" -ForegroundColor Green
Write-Host "`n📊 Service Information:" -ForegroundColor Cyan

$containers = docker-compose -f $composeFile --env-file $envFile ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
Write-Host $containers

if ($option -eq "2") {
    Write-Host "`n🌐 Access URLs:" -ForegroundColor Cyan
    Write-Host "  HTTP:  http://localhost" -ForegroundColor White
    Write-Host "  HTTPS: https://localhost (if SSL configured)" -ForegroundColor White
} else {
    Write-Host "`n🌐 Access URL:" -ForegroundColor Cyan
    Write-Host "  Application: http://localhost:5000" -ForegroundColor White
}

Write-Host "`n📋 Management Commands:" -ForegroundColor Cyan
Write-Host "  View logs:    docker-compose -f $composeFile --env-file $envFile logs -f" -ForegroundColor Gray
Write-Host "  Stop:         docker-compose -f $composeFile --env-file $envFile down" -ForegroundColor Gray
Write-Host "  Restart:      docker-compose -f $composeFile --env-file $envFile restart" -ForegroundColor Gray

Write-Host "`n🎉 Production deployment is ready!" -ForegroundColor Green