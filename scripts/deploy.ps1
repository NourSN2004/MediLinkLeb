# Deploy MediLink microservices to Kubernetes (Minikube)
# PowerShell version

$ErrorActionPreference = "Continue"

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Deploying MediLink to Kubernetes" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Base directory
$BASE_DIR = Split-Path -Parent $PSScriptRoot
$K8S_DIR = Join-Path $BASE_DIR "k8s"

# Check if minikube is running
$null = minikube status 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Minikube is not running!" -ForegroundColor Red
    Write-Host "Please start Minikube first:" -ForegroundColor Yellow
    Write-Host "  .\scripts\start-minikube.ps1" -ForegroundColor White
    exit 1
}

# Check if kubectl is available
if (-not (Get-Command kubectl -ErrorAction SilentlyContinue)) {
    Write-Host "Error: kubectl is not installed!" -ForegroundColor Red
    Write-Host "Please install kubectl from: https://kubernetes.io/docs/tasks/tools/" -ForegroundColor Yellow
    exit 1
}

Write-Host "Step 1: Create namespace" -ForegroundColor Yellow
kubectl apply -f (Join-Path $K8S_DIR "namespace.yaml")
if ($LASTEXITCODE -ne 0) { exit 1 }
Write-Host "Namespace created" -ForegroundColor Green
Write-Host ""

Write-Host "Step 2: Create secrets and configmaps" -ForegroundColor Yellow
kubectl apply -f (Join-Path $K8S_DIR "secrets")
kubectl apply -f (Join-Path $K8S_DIR "configmaps")
if ($LASTEXITCODE -ne 0) { exit 1 }
Write-Host "Secrets and ConfigMaps created" -ForegroundColor Green
Write-Host ""

Write-Host "Step 3: Deploy PostgreSQL database" -ForegroundColor Yellow
kubectl apply -f (Join-Path $K8S_DIR "database\postgres-pv.yaml")
kubectl apply -f (Join-Path $K8S_DIR "database\postgres-pvc.yaml")
kubectl apply -f (Join-Path $K8S_DIR "database\postgres-deployment.yaml")
kubectl apply -f (Join-Path $K8S_DIR "database\postgres-service.yaml")
if ($LASTEXITCODE -ne 0) { exit 1 }
Write-Host "PostgreSQL deployed" -ForegroundColor Green
Write-Host ""

Write-Host "Waiting for PostgreSQL to be ready..." -ForegroundColor Yellow
Write-Host "This may take a few minutes..." -ForegroundColor Gray
kubectl wait --for=condition=ready pod -l app=postgres -n medilink --timeout=300s
if ($LASTEXITCODE -eq 0) {
    Write-Host "PostgreSQL is ready" -ForegroundColor Green
} else {
    Write-Host "Warning: PostgreSQL might not be fully ready yet" -ForegroundColor Yellow
}
Write-Host ""

Write-Host "Step 4: Deploy backend microservices" -ForegroundColor Yellow
kubectl apply -f (Join-Path $K8S_DIR "deployments")
kubectl apply -f (Join-Path $K8S_DIR "services")
if ($LASTEXITCODE -ne 0) { exit 1 }
Write-Host "Microservices deployed" -ForegroundColor Green
Write-Host ""

Write-Host "Step 5: Waiting for all pods to be ready..." -ForegroundColor Yellow
Write-Host "This may take several minutes..." -ForegroundColor Gray
$waitResult = kubectl wait --for=condition=ready pod --all -n medilink --timeout=600s 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Warning: Some pods may still be starting" -ForegroundColor Yellow
}
Write-Host ""

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Deployment Status" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Pods:" -ForegroundColor Yellow
kubectl get pods -n medilink
Write-Host ""
Write-Host "Services:" -ForegroundColor Yellow
kubectl get services -n medilink
Write-Host ""

$minikubeIp = minikube ip

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Deployment Complete!" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Access Options:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. NodePort Access (Recommended for testing):" -ForegroundColor White
Write-Host "   URL: http://${minikubeIp}:30080" -ForegroundColor Cyan
Write-Host ""
Write-Host "2. Port Forwarding:" -ForegroundColor White
Write-Host "   Run: kubectl port-forward -n medilink service/api-gateway 8080:8000" -ForegroundColor Gray
Write-Host "   URL: http://localhost:8080" -ForegroundColor Cyan
Write-Host ""
Write-Host "3. Minikube Service:" -ForegroundColor White
Write-Host "   Run: minikube service api-gateway -n medilink" -ForegroundColor Gray
Write-Host ""
Write-Host "Useful Commands:" -ForegroundColor Yellow
Write-Host "  View logs: kubectl logs -f -n medilink -l app=<service-name>" -ForegroundColor White
Write-Host "  View pods: kubectl get pods -n medilink" -ForegroundColor White
Write-Host "  Describe pod: kubectl describe pod -n medilink <pod-name>" -ForegroundColor White
Write-Host "  Dashboard: minikube dashboard" -ForegroundColor White
Write-Host ""
Write-Host "Next step:" -ForegroundColor Yellow
Write-Host "  Run migrations: .\scripts\run-migrations.ps1" -ForegroundColor White
Write-Host ""
