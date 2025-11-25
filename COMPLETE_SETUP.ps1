# MediLink Complete Setup Script
# Automates: Minikube start → Build images → Deploy → Ingress setup
# After completion, access at: http://medilink.local

param(
    [switch]$SkipBuild = $false,
    [switch]$Force = $false,
    [switch]$IncludeJenkins = $false
)

$ErrorActionPreference = "Continue"

function Write-Banner {
    param([string]$Message, [string]$Color = "Cyan")
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor $Color
    Write-Host "  $Message" -ForegroundColor $Color
    Write-Host "============================================================" -ForegroundColor $Color
    Write-Host ""
}

function Write-Step {
    param([string]$Message)
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')]" -ForegroundColor Gray -NoNewline
    Write-Host " $Message" -ForegroundColor Green
}

function Write-Error-Custom {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

function Write-Success {
    param([string]$Message)
    Write-Host "  [OK] $Message" -ForegroundColor Green
}

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

Write-Banner "MediLink Kubernetes Deployment - Complete Setup"

Write-Host "This script will:" -ForegroundColor Yellow
Write-Host "  1. Start Minikube cluster" -ForegroundColor White
Write-Host "  2. Build all Docker images (if needed)" -ForegroundColor White
Write-Host "  3. Deploy all microservices" -ForegroundColor White
Write-Host "  4. Run database migrations" -ForegroundColor White
Write-Host "  5. Configure Ingress controller" -ForegroundColor White
Write-Host "  6. Update hosts file (manual step)" -ForegroundColor White
if ($IncludeJenkins) {
    Write-Host "  7. Deploy Jenkins CI/CD" -ForegroundColor White
    Write-Host "  8. Start minikube tunnel" -ForegroundColor White
} else {
    Write-Host "  7. Start minikube tunnel" -ForegroundColor White
}
Write-Host ""
if ($IncludeJenkins) {
    Write-Host "Estimated time: 15-20 minutes" -ForegroundColor Yellow
} else {
    Write-Host "Estimated time: 10-15 minutes" -ForegroundColor Yellow
    Write-Host "Add -IncludeJenkins flag to deploy Jenkins CI/CD" -ForegroundColor Gray
}
Write-Host ""

if (-not $Force) {
    $continue = Read-Host "Continue? (Y/N)"
    if ($continue -ne "Y" -and $continue -ne "y") {
        Write-Host "Setup cancelled." -ForegroundColor Yellow
        exit 0
    }
}

# Step 1: Check Prerequisites
Write-Banner "Step 1: Checking Prerequisites"

Write-Step "Checking Docker..."
try {
    $dockerVersion = docker --version 2>$null
    if ($dockerVersion) {
        Write-Success "Docker installed: $dockerVersion"
    } else {
        Write-Error-Custom "Docker not found. Please install Docker Desktop."
        exit 1
    }
} catch {
    Write-Error-Custom "Docker not running. Please start Docker Desktop."
    exit 1
}

Write-Step "Checking kubectl..."
$kubectlVersion = kubectl version --client 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Success "kubectl installed"
} else {
    Write-Error-Custom "kubectl not found. Please install kubectl."
    exit 1
}

Write-Step "Checking Minikube..."
$minikubeVersion = minikube version --short 2>$null
if ($minikubeVersion) {
    Write-Success "Minikube installed: $minikubeVersion"
} else {
    Write-Error-Custom "Minikube not found. Please install Minikube."
    exit 1
}

# Step 2: Start/Check Minikube
Write-Banner "Step 2: Starting Minikube Cluster"

$minikubeStatus = minikube status 2>$null | Out-String
if ($minikubeStatus -match "Running") {
    Write-Success "Minikube already running"
    
    if ($Force) {
        Write-Step "Force flag set - restarting Minikube..."
        minikube stop
        Start-Sleep -Seconds 3
        minikube start --memory=6144 --cpus=4 --disk-size=20g --driver=docker
    }
} else {
    Write-Step "Starting Minikube (6GB RAM, 4 CPUs, 20GB disk)..."
    minikube start --memory=6144 --cpus=4 --disk-size=20g --driver=docker
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error-Custom "Failed to start Minikube"
        exit 1
    }
    Write-Success "Minikube started"
}

Write-Step "Enabling Ingress addon..."
minikube addons enable ingress
Write-Success "Ingress addon enabled"

# Step 3: Build Docker Images
Write-Banner "Step 3: Building Docker Images"

if ($SkipBuild) {
    Write-Host "Skipping build (--SkipBuild flag set)" -ForegroundColor Yellow
} else {
    Write-Step "Configuring Docker to use Minikube's Docker daemon..."
    & minikube -p minikube docker-env --shell powershell | Invoke-Expression
    
    $services = @(
        "auth-service",
        "doctor-service", 
        "patient-service",
        "pharmacy-service",
        "scheduling-service",
        "inventory-service",
        "notification-service",
        "api-gateway"
    )
    
    $totalServices = $services.Count
    $currentService = 0
    
    foreach ($service in $services) {
        $currentService++
        Write-Step "[$currentService/$totalServices] Building $service..."
        
        Push-Location "microservices\$service"
        docker build -t "${service}:latest" . 2>&1 | Out-Null
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "$service built"
        } else {
            Write-Error-Custom "Failed to build $service"
            Pop-Location
            exit 1
        }
        Pop-Location
    }
    
    Write-Success "All images built successfully"
}

# Step 4: Create Namespace
Write-Banner "Step 4: Setting Up Kubernetes Namespace"

$namespaceExists = kubectl get namespace medilink 2>$null
if (-not $namespaceExists) {
    Write-Step "Creating medilink namespace..."
    kubectl create namespace medilink
    Write-Success "Namespace created"
} else {
    Write-Success "Namespace already exists"
}

# Step 5: Deploy Database
Write-Banner "Step 5: Deploying PostgreSQL Database"

Write-Step "Deploying PostgreSQL..."
kubectl apply -f k8s/database/ -n medilink
Start-Sleep -Seconds 10

Write-Step "Waiting for PostgreSQL to be ready..."
$timeout = 60
$elapsed = 0
$ready = $false
while ($elapsed -lt $timeout) {
    $podStatus = kubectl get pods -n medilink -l app=postgres --no-headers 2>$null | Out-String
    if ($podStatus -match "1/1\s+Running") {
        Write-Success "PostgreSQL is ready"
        $ready = $true
        break
    }
    Start-Sleep -Seconds 5
    $elapsed += 5
    Write-Host "." -NoNewline
}
Write-Host ""

if (-not $ready) {
    Write-Error-Custom "PostgreSQL failed to start in time"
    Write-Host "Checking pod status:" -ForegroundColor Yellow
    kubectl get pods -n medilink -l app=postgres
    kubectl describe pod -n medilink -l app=postgres | Select-String "Error|Warning|Failed" -Context 2
    exit 1
}

# Step 6: Deploy Microservices
Write-Banner "Step 6: Deploying Microservices"

Write-Step "Deploying ConfigMaps..."
kubectl apply -f k8s/configmaps/ -n medilink

Write-Step "Deploying all microservices..."
kubectl apply -f k8s/deployments/ -n medilink
kubectl apply -f k8s/services/ -n medilink

Write-Step "Waiting for all pods to be ready (this may take 2-3 minutes)..."
$timeout = 180
$elapsed = 0
while ($elapsed -lt $timeout) {
    $pods = kubectl get pods -n medilink --no-headers 2>$null
    $totalPods = ($pods | Measure-Object).Count
    $runningPods = ($pods | Select-String "Running" | Measure-Object).Count
    
    Write-Host "`r  Pods: $runningPods/$totalPods ready..." -NoNewline
    
    if ($totalPods -gt 0 -and $runningPods -eq $totalPods) {
        Write-Host ""
        Write-Success "All pods are ready"
        break
    }
    
    Start-Sleep -Seconds 5
    $elapsed += 5
}
Write-Host ""

if ($elapsed -ge $timeout) {
    Write-Host ""
    Write-Host "Warning: Some pods may not be ready yet" -ForegroundColor Yellow
    kubectl get pods -n medilink
}

# Step 7: Run Migrations
Write-Banner "Step 7: Running Database Migrations"

Write-Step "Waiting for auth-service to be ready..."
Start-Sleep -Seconds 10

Write-Step "Running migrations on auth-service..."
$authPod = kubectl get pods -n medilink -l app=auth-service -o jsonpath='{.items[0].metadata.name}' 2>$null
if ($authPod) {
    kubectl exec -n medilink $authPod -- python manage.py migrate 2>&1 | Out-Null
    Write-Success "Migrations completed"
} else {
    Write-Error-Custom "Could not find auth-service pod"
}

# Step 8: Deploy Ingress
Write-Banner "Step 8: Configuring Ingress Controller"

Write-Step "Deploying Ingress resource..."
kubectl apply -f k8s/ingress.yaml

Write-Step "Patching Ingress controller to use LoadBalancer..."
kubectl patch svc ingress-nginx-controller -n ingress-nginx -p '{\"spec\":{\"type\":\"LoadBalancer\"}}' 2>&1 | Out-Null

Start-Sleep -Seconds 5

Write-Step "Waiting for Ingress controller..."
$timeout = 60
$elapsed = 0
while ($elapsed -lt $timeout) {
    $externalIp = kubectl get svc -n ingress-nginx ingress-nginx-controller -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>$null
    if ($externalIp) {
        Write-Success "Ingress controller ready (External IP: $externalIp)"
        break
    }
    Start-Sleep -Seconds 5
    $elapsed += 5
    Write-Host "." -NoNewline
}
Write-Host ""

# Step 9: Hosts File Instructions
Write-Banner "Step 9: Configuring Hosts File"

Write-Host ""
Write-Host "MANUAL STEP REQUIRED:" -ForegroundColor Yellow
Write-Host "To access the application at http://medilink.local, you need to update your hosts file." -ForegroundColor White
if ($IncludeJenkins) {
    Write-Host "Add these lines to C:\Windows\System32\drivers\etc\hosts:" -ForegroundColor White
    Write-Host ""
    Write-Host "127.0.0.1 medilink.local" -ForegroundColor Cyan
    Write-Host "127.0.0.1 jenkins.medilink.local" -ForegroundColor Cyan
} else {
    Write-Host "Add to C:\Windows\System32\drivers\etc\hosts:" -ForegroundColor White
    Write-Host ""
    Write-Host "127.0.0.1 medilink.local" -ForegroundColor Cyan
}
Write-Host ""
$continue = Read-Host "Press Enter after updating hosts file to continue..."

# Optional: Deploy Jenkins
if ($IncludeJenkins) {
    Write-Banner "Step 10: Deploying Jenkins CI/CD"
    
    Write-Step "Deploying Jenkins..."
    & "$PSScriptRoot\deploy-jenkins.ps1" -SkipNamespace
    
    Write-Host ""
    Write-Host "Jenkins deployed! Access at: http://jenkins.medilink.local" -ForegroundColor Green
    Write-Host ""
}

# Display Status
if ($IncludeJenkins) {
    Write-Banner "Step 11: System Status" "Green"
} else {
    Write-Banner "Step 10: System Status" "Green"
}

Write-Step "Checking deployment status..."
Write-Host ""

$pods = kubectl get pods -n medilink --no-headers 2>$null
$totalPods = ($pods | Measure-Object).Count
$runningPods = ($pods | Select-String "Running" | Measure-Object).Count

Write-Host "  Pods: $runningPods/$totalPods running" -ForegroundColor $(if ($runningPods -eq $totalPods) { "Green" } else { "Yellow" })

$services = @("api-gateway", "auth-service", "doctor-service", "patient-service", "pharmacy-service", "scheduling-service", "inventory-service", "notification-service", "postgres")
foreach ($service in $services) {
    $servicePods = kubectl get pods -n medilink -l app=$service --no-headers 2>$null
    $count = ($servicePods | Measure-Object).Count
    $running = ($servicePods | Select-String "Running" | Measure-Object).Count
    $status = if ($running -eq $count -and $count -gt 0) { "OK" } else { "WARN" }
    $color = if ($status -eq "OK") { "Green" } else { "Yellow" }
    Write-Host "    $service`: " -NoNewline
    Write-Host "$running/$count running" -ForegroundColor $color
}

Write-Host ""
$ingress = kubectl get ingress -n medilink --no-headers 2>$null
if ($ingress) {
    Write-Host "  Ingress: Configured" -ForegroundColor Green
} else {
    Write-Host "  Ingress: Not configured" -ForegroundColor Yellow
}

Write-Host ""
$hostsContent = Get-Content "C:\Windows\System32\drivers\etc\hosts" 2>$null
if ($hostsContent -match "medilink.local") {
    Write-Host "  Hosts file: Configured" -ForegroundColor Green
} else {
    Write-Host "  Hosts file: Not configured" -ForegroundColor Yellow
}

if ($IncludeJenkins) {
    Write-Host ""
    $jenkinsPods = kubectl get pods -n jenkins -l app=jenkins --no-headers 2>$null
    $jenkinsRunning = ($jenkinsPods | Select-String "Running" | Measure-Object).Count
    if ($jenkinsRunning -gt 0) {
        Write-Host "  Jenkins: Running" -ForegroundColor Green
    } else {
        Write-Host "  Jenkins: Not running" -ForegroundColor Yellow
    }
}

# Final Step: Start Tunnel
if ($IncludeJenkins) {
    Write-Banner "Step 12: Starting Minikube Tunnel" "Green"
} else {
    Write-Banner "Step 11: Starting Minikube Tunnel" "Green"
}

Write-Host ""
Write-Host "IMPORTANT:" -ForegroundColor Red
Write-Host "  The minikube tunnel must remain running for http://medilink.local to work" -ForegroundColor Yellow
Write-Host "  Keep this window open while using the application" -ForegroundColor Yellow
Write-Host ""
Write-Host "Access the application at:" -ForegroundColor Green
Write-Host "  http://medilink.local" -ForegroundColor Cyan
if ($IncludeJenkins) {
    Write-Host "  http://jenkins.medilink.local" -ForegroundColor Cyan
}
Write-Host ""
Write-Host "Press Ctrl+C to stop the tunnel when done" -ForegroundColor Yellow
Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""

Start-Sleep -Seconds 3

Write-Host "Starting tunnel..." -ForegroundColor Green
minikube tunnel
