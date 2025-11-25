# Deploy Jenkins to Kubernetes
# Run this script to set up Jenkins in your Minikube cluster

param(
    [switch]$SkipNamespace = $false
)

$ErrorActionPreference = "Continue"

function Write-Step {
    param([string]$Message)
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')]" -ForegroundColor Gray -NoNewline
    Write-Host " $Message" -ForegroundColor Green
}

function Write-Success {
    param([string]$Message)
    Write-Host "  [OK] $Message" -ForegroundColor Green
}

function Write-Error-Custom {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Jenkins Deployment for MediLink" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Check if Minikube is running
Write-Step "Checking Minikube status..."
$minikubeStatus = minikube status 2>$null | Out-String
if ($minikubeStatus -match "Running") {
    Write-Success "Minikube is running"
} else {
    Write-Error-Custom "Minikube is not running. Please start it first."
    exit 1
}

# Create namespace
if (-not $SkipNamespace) {
    Write-Step "Creating Jenkins namespace..."
    kubectl apply -f k8s/jenkins/namespace.yaml
    Write-Success "Namespace created"
}

# Deploy Jenkins RBAC
Write-Step "Setting up Jenkins permissions..."
kubectl apply -f k8s/jenkins/jenkins-rbac.yaml
Write-Success "RBAC configured"

# Deploy Jenkins PV and PVC
Write-Step "Creating persistent storage..."
kubectl apply -f k8s/jenkins/jenkins-pv.yaml
kubectl apply -f k8s/jenkins/jenkins-pvc.yaml
Write-Success "Storage created"

# Deploy Jenkins
Write-Step "Deploying Jenkins..."
kubectl apply -f k8s/jenkins/jenkins-deployment.yaml
kubectl apply -f k8s/jenkins/jenkins-service.yaml
Write-Success "Jenkins deployed"

# Wait for Jenkins to be ready
Write-Step "Waiting for Jenkins to be ready (this may take 2-3 minutes)..."
$timeout = 180
$elapsed = 0
while ($elapsed -lt $timeout) {
    $podStatus = kubectl get pods -n jenkins -l app=jenkins --no-headers 2>$null | Out-String
    if ($podStatus -match "1/1\s+Running") {
        Write-Success "Jenkins is ready"
        break
    }
    Start-Sleep -Seconds 5
    $elapsed += 5
    Write-Host "." -NoNewline
}
Write-Host ""

if ($elapsed -ge $timeout) {
    Write-Error-Custom "Jenkins failed to start in time"
    Write-Host "Checking pod status:" -ForegroundColor Yellow
    kubectl get pods -n jenkins
    kubectl describe pod -n jenkins -l app=jenkins | Select-String "Error|Warning|Failed" -Context 2
    exit 1
}

# Deploy Jenkins Ingress
Write-Step "Configuring Jenkins Ingress..."
kubectl apply -f k8s/jenkins/jenkins-ingress.yaml
Write-Success "Ingress configured"

# Get initial admin password
Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  Jenkins Deployed Successfully!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""

Write-Step "Getting initial admin password..."
Start-Sleep -Seconds 5
$jenkinsAdmin = kubectl exec -n jenkins deployment/jenkins -- cat /var/jenkins_home/secrets/initialAdminPassword 2>$null

if ($jenkinsAdmin) {
    Write-Host ""
    Write-Host "Initial Admin Password:" -ForegroundColor Yellow
    Write-Host "  $jenkinsAdmin" -ForegroundColor Cyan
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "To get the initial admin password later, run:" -ForegroundColor Yellow
    Write-Host '  kubectl exec -n jenkins deployment/jenkins -- cat /var/jenkins_home/secrets/initialAdminPassword' -ForegroundColor Cyan
    Write-Host ""
}

Write-Host "Access Jenkins at:" -ForegroundColor Yellow
Write-Host "  http://jenkins.medilink.local" -ForegroundColor Cyan
Write-Host ""
Write-Host "IMPORTANT:" -ForegroundColor Yellow
Write-Host "1. Add to hosts file: 127.0.0.1 jenkins.medilink.local" -ForegroundColor White
Write-Host "2. Make sure minikube tunnel is running" -ForegroundColor White
Write-Host ""
Write-Host "Or access via port-forward:" -ForegroundColor Yellow
Write-Host "  kubectl port-forward -n jenkins service/jenkins 8080:8080" -ForegroundColor Cyan
Write-Host "  Then open: http://localhost:8080" -ForegroundColor Cyan
Write-Host ""

# Display status
Write-Host "Jenkins Status:" -ForegroundColor Cyan
kubectl get pods -n jenkins
Write-Host ""
kubectl get svc -n jenkins
Write-Host ""
kubectl get ingress -n jenkins
