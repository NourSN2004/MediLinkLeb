# Build all Docker images for MediLink microservices
# PowerShell version

$ErrorActionPreference = "Continue"

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Building MediLink Microservices" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Check if minikube is running
$minikubeStatus = minikube status 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Minikube is not running!" -ForegroundColor Red
    Write-Host "Please start Minikube first:" -ForegroundColor Yellow
    Write-Host "  .\scripts\start-minikube.ps1" -ForegroundColor White
    exit 1
}

Write-Host "Setting Minikube Docker environment..." -ForegroundColor Yellow
# Set minikube docker environment for PowerShell
& minikube -p minikube docker-env --shell powershell | Invoke-Expression

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Failed to set Minikube Docker environment!" -ForegroundColor Red
    exit 1
}

Write-Host "Using Minikube's Docker daemon" -ForegroundColor Green
Write-Host ""

# Base directory
$BASE_DIR = Split-Path -Parent $PSScriptRoot
$MICROSERVICES_DIR = Join-Path $BASE_DIR "microservices"

# Services to build
$SERVICES = @(
    "auth-service",
    "doctor-service",
    "patient-service",
    "pharmacy-service",
    "scheduling-service",
    "inventory-service",
    "notification-service",
    "api-gateway"
)

$successCount = 0
$failCount = 0
$failedServices = @()

# Build each service
foreach ($service in $SERVICES) {
    Write-Host "--------------------------------------" -ForegroundColor Cyan
    Write-Host "Building $service..." -ForegroundColor Yellow
    Write-Host "--------------------------------------" -ForegroundColor Cyan
    
    $servicePath = Join-Path $MICROSERVICES_DIR $service
    
    if (-not (Test-Path $servicePath)) {
        Write-Host "Service directory not found: $servicePath" -ForegroundColor Red
        $failCount++
        $failedServices += $service
        continue
    }
    
    Push-Location $servicePath
    
    try {
        if (Test-Path "Dockerfile") {
            docker build -t "${service}:latest" .
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "$service built successfully" -ForegroundColor Green
                $successCount++
            } else {
                Write-Host "Failed to build $service" -ForegroundColor Red
                $failCount++
                $failedServices += $service
            }
        } else {
            Write-Host "Dockerfile not found for $service" -ForegroundColor Red
            $failCount++
            $failedServices += $service
        }
    }
    catch {
        Write-Host "Error building $service : $_" -ForegroundColor Red
        $failCount++
        $failedServices += $service
    }
    finally {
        Pop-Location
    }
    
    Write-Host ""
}

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Build Summary" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Successful: $successCount" -ForegroundColor Green
Write-Host "Failed: $failCount" -ForegroundColor $(if ($failCount -gt 0) { "Red" } else { "Green" })

if ($failCount -gt 0) {
    Write-Host ""
    Write-Host "Failed services:" -ForegroundColor Red
    $failedServices | ForEach-Object { Write-Host "  - $_" -ForegroundColor Red }
    Write-Host ""
    Write-Host "Please fix the errors and try again." -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "All images built successfully!" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "List of built images:" -ForegroundColor Yellow
docker images | Select-String -Pattern "(api-gateway|auth-service|doctor-service|patient-service|pharmacy-service|scheduling-service|inventory-service|notification-service)"

Write-Host ""
Write-Host "Next step:" -ForegroundColor Yellow
Write-Host "  Deploy services: .\scripts\deploy.ps1" -ForegroundColor White
Write-Host ""
