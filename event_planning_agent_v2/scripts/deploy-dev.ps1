# Development Deployment Script for Event Planning Agent v2 (PowerShell)
param(
    [string]$Action = "deploy"
)

# Configuration
$ProjectName = "event-planning-agent-v2"
$ComposeFile = "docker/docker-compose.yml"
$ComposeDevFile = "docker/docker-compose.dev.yml"
$EnvFile = ".env.development"

# Functions
function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

# Check prerequisites
function Test-Prerequisites {
    Write-Info "Checking prerequisites..."
    
    # Check Docker
    try {
        docker --version | Out-Null
    }
    catch {
        Write-Error "Docker is not installed. Please install Docker Desktop first."
        exit 1
    }
    
    # Check Docker Compose
    try {
        docker-compose --version | Out-Null
    }
    catch {
        Write-Error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    }
    
    # Check if Docker daemon is running
    try {
        docker info | Out-Null
    }
    catch {
        Write-Error "Docker daemon is not running. Please start Docker Desktop first."
        exit 1
    }
    
    Write-Success "Prerequisites check passed"
}

# Setup environment
function Initialize-Environment {
    Write-Info "Setting up development environment..."
    
    # Copy development environment file
    if (Test-Path $EnvFile) {
        Copy-Item $EnvFile .env -Force
        Write-Success "Development environment file copied"
    }
    else {
        Write-Warning "Development environment file not found, using default .env"
    }
    
    # Create necessary directories
    $directories = @("logs", "data", "monitoring/grafana/dashboards", "monitoring/grafana/datasources")
    foreach ($dir in $directories) {
        if (!(Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
        }
    }
    
    Write-Success "Environment setup completed"
}

# Pull latest images
function Update-Images {
    Write-Info "Pulling latest Docker images..."
    
    docker-compose -f $ComposeFile -f $ComposeDevFile pull
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Images pulled successfully"
    }
    else {
        Write-Error "Failed to pull images"
        exit 1
    }
}

# Build application
function Build-Application {
    Write-Info "Building application..."
    
    docker-compose -f $ComposeFile -f $ComposeDevFile build --no-cache
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Application built successfully"
    }
    else {
        Write-Error "Failed to build application"
        exit 1
    }
}

# Start services
function Start-Services {
    Write-Info "Starting services..."
    
    # Start infrastructure services first
    docker-compose -f $ComposeFile -f $ComposeDevFile up -d postgres ollama
    
    # Wait for database to be ready
    Write-Info "Waiting for database to be ready..."
    Start-Sleep -Seconds 10
    
    # Start remaining services
    docker-compose -f $ComposeFile -f $ComposeDevFile up -d
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Services started successfully"
    }
    else {
        Write-Error "Failed to start services"
        exit 1
    }
}

# Setup Ollama models
function Initialize-Ollama {
    Write-Info "Setting up Ollama models..."
    
    # Wait for Ollama to be ready
    Start-Sleep -Seconds 15
    
    # Pull required models
    try {
        docker-compose -f $ComposeFile -f $ComposeDevFile exec ollama ollama pull gemma:2b
    }
    catch {
        Write-Warning "Failed to pull gemma:2b model"
    }
    
    try {
        docker-compose -f $ComposeFile -f $ComposeDevFile exec ollama ollama pull tinyllama
    }
    catch {
        Write-Warning "Failed to pull tinyllama model"
    }
    
    Write-Success "Ollama models setup completed"
}

# Run database migrations
function Invoke-Migrations {
    Write-Info "Running database migrations..."
    
    # Wait for API service to be ready
    Start-Sleep -Seconds 20
    
    docker-compose -f $ComposeFile -f $ComposeDevFile exec event-planning-api python -m event_planning_agent_v2.database.setup
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Database migrations completed"
    }
    else {
        Write-Error "Database migrations failed"
        exit 1
    }
}

# Health check
function Test-Health {
    Write-Info "Performing health check..."
    
    # Check API health
    $maxAttempts = 30
    for ($i = 1; $i -le $maxAttempts; $i++) {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 5
            if ($response.StatusCode -eq 200) {
                Write-Success "API is healthy"
                break
            }
        }
        catch {
            if ($i -eq $maxAttempts) {
                Write-Error "API health check failed after $maxAttempts attempts"
                return $false
            }
        }
        Start-Sleep -Seconds 2
    }
    
    # Check database connection
    try {
        docker-compose -f $ComposeFile -f $ComposeDevFile exec postgres pg_isready -U eventuser -d eventdb_dev
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Database is healthy"
        }
        else {
            Write-Error "Database health check failed"
            return $false
        }
    }
    catch {
        Write-Error "Database health check failed"
        return $false
    }
    
    Write-Success "Health check passed"
    return $true
}

# Show service status
function Show-Status {
    Write-Info "Service Status:"
    docker-compose -f $ComposeFile -f $ComposeDevFile ps
    
    Write-Host ""
    Write-Info "Available Services:"
    Write-Host "  🌐 API: http://localhost:8000" -ForegroundColor Cyan
    Write-Host "  📊 API Docs: http://localhost:8000/docs" -ForegroundColor Cyan
    Write-Host "  🗄️  Database: localhost:5432" -ForegroundColor Cyan
    Write-Host "  🤖 Ollama: http://localhost:11434" -ForegroundColor Cyan
    Write-Host "  📈 Prometheus: http://localhost:9090" -ForegroundColor Cyan
    Write-Host "  📊 Grafana: http://localhost:3000 (admin/admin)" -ForegroundColor Cyan
    Write-Host "  🔧 PgAdmin: http://localhost:5050 (admin@eventplanning.dev/admin)" -ForegroundColor Cyan
}

# Cleanup function
function Remove-Services {
    Write-Info "Cleaning up..."
    docker-compose -f $ComposeFile -f $ComposeDevFile down -v --remove-orphans
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Cleanup completed"
    }
}

# Main deployment process
function Start-Deployment {
    Write-Host "🎯 Event Planning Agent v2 - Development Deployment" -ForegroundColor Magenta
    Write-Host "==================================================" -ForegroundColor Magenta
    
    Test-Prerequisites
    Initialize-Environment
    Update-Images
    Build-Application
    Start-Services
    Initialize-Ollama
    Invoke-Migrations
    
    if (Test-Health) {
        Show-Status
        Write-Success "🎉 Development deployment completed successfully!"
        Write-Host ""
        Write-Host "To view logs: docker-compose -f $ComposeFile -f $ComposeDevFile logs -f" -ForegroundColor Yellow
        Write-Host "To stop services: docker-compose -f $ComposeFile -f $ComposeDevFile down" -ForegroundColor Yellow
    }
    else {
        Write-Error "Deployment failed health check"
        exit 1
    }
}

# Handle command line arguments
switch ($Action.ToLower()) {
    "cleanup" {
        Remove-Services
    }
    "status" {
        Show-Status
    }
    "health" {
        Test-Health
    }
    default {
        Start-Deployment
    }
}