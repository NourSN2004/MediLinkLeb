# Deploy Ingress Controller
# PowerShell script to deploy and configure Ingress

$ErrorActionPreference = "Continue"

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Deploying Ingress Controller" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Check if minikube is running
$null = minikube status 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Minikube is not running!" -ForegroundColor Red
    Write-Host "Please start Minikube first: .\scripts\start-minikube.ps1" -ForegroundColor Yellow
    exit 1
}

# Check if application is deployed
$pods = kubectl get pods -n medilink --no-headers 2>$null
if (-not $pods) {
    Write-Host "Error: Application is not deployed!" -ForegroundColor Red
    Write-Host "Please deploy the application first: .\scripts\deploy.ps1" -ForegroundColor Yellow
    exit 1
}

Write-Host "Step 1: Enable Ingress addon in Minikube" -ForegroundColor Yellow
minikube addons enable ingress

if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to enable Ingress addon" -ForegroundColor Red
    exit 1
}

Write-Host "Ingress addon enabled" -ForegroundColor Green
Write-Host ""

Write-Host "Step 2: Wait for Ingress controller to be ready" -ForegroundColor Yellow
Write-Host "This may take a minute..." -ForegroundColor Gray

$maxRetries = 30
$retryCount = 0
$ready = $false

while ($retryCount -lt $maxRetries -and -not $ready) {
    Start-Sleep -Seconds 2
    $controllerPod = kubectl get pods -n ingress-nginx -l app.kubernetes.io/component=controller --no-headers 2>$null
    
    if ($controllerPod -and $controllerPod -match "Running") {
        $ready = $true
    }
    
    $retryCount++
    if ($retryCount % 5 -eq 0) {
        Write-Host "  Still waiting... ($retryCount/$maxRetries)" -ForegroundColor Gray
    }
}

if ($ready) {
    Write-Host "Ingress controller is ready" -ForegroundColor Green
} else {
    Write-Host "Warning: Ingress controller may not be fully ready yet" -ForegroundColor Yellow
    Write-Host "  You can check status with: kubectl get pods -n ingress-nginx" -ForegroundColor Gray
}

Write-Host ""

Write-Host "Step 3: Apply Ingress resource" -ForegroundColor Yellow
kubectl apply -f "k8s\ingress.yaml"

if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to apply Ingress resource" -ForegroundColor Red
    exit 1
}

Write-Host "Ingress resource created" -ForegroundColor Green
Write-Host ""

Write-Host "Step 4: Verify Ingress" -ForegroundColor Yellow
Start-Sleep -Seconds 2
kubectl get ingress -n medilink

Write-Host ""
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Ingress Deployment Complete!" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

$minikubeIp = minikube ip

Write-Host "Setup Instructions:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Add to your hosts file (as Administrator):" -ForegroundColor White
Write-Host "   File: C:\Windows\System32\drivers\etc\hosts" -ForegroundColor Gray
Write-Host ""
Write-Host "   Add this line:" -ForegroundColor Gray
Write-Host "   ${minikubeIp}    medilink.local" -ForegroundColor Cyan
Write-Host ""
Write-Host "2. Access the application:" -ForegroundColor White
Write-Host "   http://medilink.local" -ForegroundColor Cyan
Write-Host ""
Write-Host "Alternative (no hosts file edit needed):" -ForegroundColor Yellow
Write-Host "   Use NodePort: http://${minikubeIp}:30080" -ForegroundColor Cyan
Write-Host ""
Write-Host "Test individual services:" -ForegroundColor Yellow
Write-Host "   curl http://medilink.local/api/auth/health/" -ForegroundColor White
Write-Host "   curl http://medilink.local/api/doctors/health/" -ForegroundColor White
Write-Host "   curl http://medilink.local/api/patients/health/" -ForegroundColor White
Write-Host ""
Write-Host "View Ingress details:" -ForegroundColor Yellow
Write-Host "   kubectl describe ingress medilink-ingress -n medilink" -ForegroundColor White
Write-Host ""
Write-Host "View Ingress logs:" -ForegroundColor Yellow
Write-Host "   kubectl logs -n ingress-nginx -l app.kubernetes.io/component=controller -f" -ForegroundColor White
Write-Host ""
Write-Host "For detailed information, see: INGRESS_SETUP_GUIDE.md" -ForegroundColor Gray
Write-Host ""
