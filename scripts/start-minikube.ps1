# Start Minikube with appropriate resources for MediLink
# PowerShell version

$ErrorActionPreference = "Continue"

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Starting Minikube for MediLink" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Check if minikube is installed
if (-not (Get-Command minikube -ErrorAction SilentlyContinue)) {
    Write-Host "Error: Minikube is not installed!" -ForegroundColor Red
    Write-Host "Please install Minikube from: https://minikube.sigs.k8s.io/docs/start/" -ForegroundColor Yellow
    exit 1
}

# Check if Docker is running
$dockerInfo = docker info 2>&1 | Out-String
if (-not ($dockerInfo -match "Server Version" -or $dockerInfo -match "Server:")) {
    Write-Host "Error: Docker is not running!" -ForegroundColor Red
    Write-Host "Please start Docker Desktop and try again." -ForegroundColor Yellow
    exit 1
}

# Check if minikube is already running
$null = minikube status 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "Minikube is already running!" -ForegroundColor Green
    minikube status
    Write-Host ""
    Write-Host "Minikube IP: $(minikube ip)" -ForegroundColor Cyan
    exit 0
}

Write-Host "Starting Minikube with:" -ForegroundColor Yellow
Write-Host "  - Memory: 6GB" -ForegroundColor White
Write-Host "  - CPUs: 4" -ForegroundColor White
Write-Host "  - Driver: docker" -ForegroundColor White
Write-Host "  - Disk: 20GB" -ForegroundColor White
Write-Host ""
Write-Host "This may take a few minutes..." -ForegroundColor Yellow
Write-Host ""

minikube start --memory=6144 --cpus=4 --driver=docker --disk-size=20g

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "Error: Failed to start Minikube!" -ForegroundColor Red
    Write-Host "Try running: minikube delete" -ForegroundColor Yellow
    Write-Host "Then run this script again." -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "Minikube started successfully!" -ForegroundColor Green
Write-Host ""

minikube status

Write-Host ""
Write-Host "Minikube IP: $(minikube ip)" -ForegroundColor Cyan
Write-Host ""

# Enable necessary addons
Write-Host "Enabling required addons..." -ForegroundColor Yellow
minikube addons enable ingress
minikube addons enable metrics-server
minikube addons enable dashboard

Write-Host ""
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Minikube Ready!" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Build images: .\scripts\build-all.ps1" -ForegroundColor White
Write-Host "  2. Deploy services: .\scripts\deploy.ps1" -ForegroundColor White
Write-Host "  3. Run migrations: .\scripts\run-migrations.ps1" -ForegroundColor White
Write-Host ""
Write-Host "Useful commands:" -ForegroundColor Yellow
Write-Host "  - View dashboard: minikube dashboard" -ForegroundColor White
Write-Host "  - Get IP: minikube ip" -ForegroundColor White
Write-Host "  - Stop Minikube: minikube stop" -ForegroundColor White
Write-Host "  - Delete Minikube: minikube delete" -ForegroundColor White
Write-Host ""
