# Quick Start Script for MediLink on Minikube
# This script runs all steps in sequence

$ErrorActionPreference = "Continue"

Write-Host ""
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "  MediLink Minikube Quick Start" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "This script will:" -ForegroundColor Yellow
Write-Host "  1. Start Minikube" -ForegroundColor White
Write-Host "  2. Build Docker images" -ForegroundColor White
Write-Host "  3. Deploy to Kubernetes" -ForegroundColor White
Write-Host "  4. Run database migrations" -ForegroundColor White
Write-Host "  5. Deploy Ingress controller" -ForegroundColor White
Write-Host ""
Write-Host "Estimated time: 15-20 minutes" -ForegroundColor Gray
Write-Host ""

$continue = Read-Host "Continue? (Y/N)"
if ($continue -ne "Y" -and $continue -ne "y") {
    Write-Host "Cancelled." -ForegroundColor Yellow
    exit 0
}

Write-Host ""
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "  Step 1/5: Starting Minikube" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

& ".\scripts\start-minikube.ps1"
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed at Step 1!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Press any key to continue to Step 2..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

Write-Host ""
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "  Step 2/5: Building Docker Images" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

& ".\scripts\build-all.ps1"
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed at Step 2!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Press any key to continue to Step 3..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

Write-Host ""
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "  Step 3/5: Deploying to Kubernetes" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

& ".\scripts\deploy.ps1"
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed at Step 3!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Press any key to continue to Step 4..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

Write-Host ""
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "  Step 4/5: Running Database Migrations" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

& ".\scripts\run-migrations.ps1"
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed at Step 4!" -ForegroundColor Red
    Write-Host "You can try running migrations manually later." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Press any key to continue to Step 5..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

Write-Host ""
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "  Step 5/5: Deploying Ingress" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Applying Ingress configuration..." -ForegroundColor Yellow
kubectl apply -f "k8s\ingress.yaml"

if ($LASTEXITCODE -eq 0) {
    Write-Host "Ingress deployed successfully!" -ForegroundColor Green
} else {
    Write-Host "Warning: Ingress deployment had issues" -ForegroundColor Yellow
    Write-Host "You can deploy it manually later with: kubectl apply -f k8s\ingress.yaml" -ForegroundColor Gray
}

Write-Host ""
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "  Setup Complete!" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

$minikubeIp = minikube ip

Write-Host "Your application is ready!" -ForegroundColor Green
Write-Host ""
Write-Host "Access Options:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. NodePort (Immediate):" -ForegroundColor White
Write-Host "   http://${minikubeIp}:30080" -ForegroundColor Cyan
Write-Host ""
Write-Host "2. Ingress (Recommended):" -ForegroundColor White
Write-Host "   First, add this to your hosts file (as Administrator):" -ForegroundColor Gray
Write-Host "   C:\Windows\System32\drivers\etc\hosts" -ForegroundColor Gray
Write-Host ""
Write-Host "   Add this line:" -ForegroundColor Gray
Write-Host "   ${minikubeIp}    medilink.local" -ForegroundColor Cyan
Write-Host ""
Write-Host "   Then access: http://medilink.local" -ForegroundColor Cyan
Write-Host ""
Write-Host "3. Port Forward:" -ForegroundColor White
Write-Host "   kubectl port-forward -n medilink service/api-gateway 8080:8000" -ForegroundColor Gray
Write-Host "   Then: http://localhost:8080" -ForegroundColor Cyan
Write-Host ""
Write-Host "Useful Commands:" -ForegroundColor Yellow
Write-Host "  kubectl get pods -n medilink              # View all pods" -ForegroundColor White
Write-Host "  kubectl logs -f -n medilink -l app=<name> # View logs" -ForegroundColor White
Write-Host "  minikube dashboard                        # Open dashboard" -ForegroundColor White
Write-Host "  minikube stop                             # Stop Minikube" -ForegroundColor White
Write-Host ""
Write-Host "For detailed guides, see:" -ForegroundColor Yellow
Write-Host "  - MINIKUBE_SETUP_GUIDE.md" -ForegroundColor White
Write-Host "  - INGRESS_SETUP_GUIDE.md" -ForegroundColor White
Write-Host ""
Write-Host "Good luck with your project!" -ForegroundColor Green
Write-Host ""
