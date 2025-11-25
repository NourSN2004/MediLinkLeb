# Run database migrations for MediLink
# PowerShell version

$ErrorActionPreference = "Continue"

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Running Database Migrations" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Check if minikube is running
$null = minikube status 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Minikube is not running!" -ForegroundColor Red
    exit 1
}

# Services that need migrations (in order)
$SERVICES = @(
    "auth-service",
    "doctor-service",
    "patient-service",
    "pharmacy-service",
    "scheduling-service",
    "inventory-service",
    "notification-service"
)

Write-Host "Finding pods..." -ForegroundColor Yellow
Write-Host ""

foreach ($service in $SERVICES) {
    Write-Host "--------------------------------------" -ForegroundColor Cyan
    Write-Host "Running migrations for: $service" -ForegroundColor Yellow
    Write-Host "--------------------------------------" -ForegroundColor Cyan
    
    # Get the first pod for this service
    $pod = kubectl get pods -n medilink -l app=$service -o jsonpath='{.items[0].metadata.name}' 2>$null
    
    if ([string]::IsNullOrEmpty($pod)) {
        Write-Host "No pod found for $service" -ForegroundColor Red
        Write-Host "  Skipping..." -ForegroundColor Yellow
        Write-Host ""
        continue
    }
    
    Write-Host "Using pod: $pod" -ForegroundColor Gray
    
    # Run migrations
    Write-Host "Running: python manage.py migrate" -ForegroundColor Gray
    kubectl exec -n medilink $pod -- python manage.py migrate
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Migrations completed for $service" -ForegroundColor Green
    } else {
        Write-Host "Migrations failed for $service" -ForegroundColor Red
    }
    
    Write-Host ""
}

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Migrations Complete!" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Your application is now ready to use!" -ForegroundColor Green
Write-Host ""
Write-Host "Access the application at:" -ForegroundColor Yellow
$minikubeIp = minikube ip
Write-Host "  http://${minikubeIp}:30080" -ForegroundColor Cyan
Write-Host ""
