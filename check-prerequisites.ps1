# Check if system is ready for Minikube deployment
# Pre-flight check script

$ErrorActionPreference = "Continue"

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "MediLink Minikube Pre-Flight Check" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

$allChecks = $true

# Check 1: Docker Desktop
Write-Host "1. Checking Docker Desktop..." -ForegroundColor Yellow
if (Get-Command docker -ErrorAction SilentlyContinue) {
    $dockerInfo = docker info 2>&1 | Out-String
    if ($dockerInfo -match "Server Version" -or $dockerInfo -match "Server:") {
        Write-Host "   Docker Desktop is running" -ForegroundColor Green
    } else {
        Write-Host "   Docker Desktop is installed but not running" -ForegroundColor Red
        Write-Host "     Please start Docker Desktop" -ForegroundColor Yellow
        $allChecks = $false
    }
} else {
    Write-Host "   Docker Desktop is not installed" -ForegroundColor Red
    Write-Host "     Download from: https://www.docker.com/products/docker-desktop/" -ForegroundColor Yellow
    $allChecks = $false
}

# Check 2: Minikube
Write-Host ""
Write-Host "2. Checking Minikube..." -ForegroundColor Yellow
if (Get-Command minikube -ErrorAction SilentlyContinue) {
    Write-Host "   Minikube is installed" -ForegroundColor Green
    $minikubeVersion = minikube version --short 2>$null
    Write-Host "     Version: $minikubeVersion" -ForegroundColor Gray
} else {
    Write-Host "   Minikube is not installed" -ForegroundColor Red
    Write-Host "     Download from: https://minikube.sigs.k8s.io/docs/start/" -ForegroundColor Yellow
    $allChecks = $false
}

# Check 3: kubectl
Write-Host ""
Write-Host "3. Checking kubectl..." -ForegroundColor Yellow
if (Get-Command kubectl -ErrorAction SilentlyContinue) {
    Write-Host "   kubectl is installed" -ForegroundColor Green
    $kubectlVersion = kubectl version --client --short 2>$null
    if ($kubectlVersion) {
        Write-Host "     Version: $kubectlVersion" -ForegroundColor Gray
    }
} else {
    Write-Host "   kubectl is not installed" -ForegroundColor Red
    Write-Host "     Usually comes with Docker Desktop or Minikube" -ForegroundColor Yellow
    $allChecks = $false
}

# Check 4: PowerShell version
Write-Host ""
Write-Host "4. Checking PowerShell version..." -ForegroundColor Yellow
$psVersion = $PSVersionTable.PSVersion
if ($psVersion.Major -ge 5) {
    Write-Host "   PowerShell $($psVersion.Major).$($psVersion.Minor) is supported" -ForegroundColor Green
} else {
    Write-Host "   PowerShell version too old: $($psVersion.Major).$($psVersion.Minor)" -ForegroundColor Red
    Write-Host "     Please upgrade to PowerShell 5.1 or later" -ForegroundColor Yellow
    $allChecks = $false
}

# Check 5: Required files
Write-Host ""
Write-Host "5. Checking project files..." -ForegroundColor Yellow

$requiredFiles = @(
    "k8s\namespace.yaml",
    "k8s\ingress.yaml",
    "k8s\configmaps\app-config.yaml",
    "k8s\secrets\db-secrets.yaml",
    "k8s\database\postgres-deployment.yaml",
    "docker-compose.yml",
    "scripts\start-minikube.ps1",
    "scripts\build-all.ps1",
    "scripts\deploy.ps1",
    "scripts\run-migrations.ps1"
)

$missingFiles = @()
foreach ($file in $requiredFiles) {
    if (-not (Test-Path $file)) {
        $missingFiles += $file
    }
}

if ($missingFiles.Count -eq 0) {
    Write-Host "   All required files found" -ForegroundColor Green
} else {
    Write-Host "   Missing files:" -ForegroundColor Red
    foreach ($file in $missingFiles) {
        Write-Host "     - $file" -ForegroundColor Red
    }
    $allChecks = $false
}

# Check 6: Microservices
Write-Host ""
Write-Host "6. Checking microservices..." -ForegroundColor Yellow

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

$missingServices = @()
foreach ($service in $services) {
    $servicePath = "microservices\$service"
    $dockerfilePath = "$servicePath\Dockerfile"
    
    if (-not (Test-Path $servicePath)) {
        $missingServices += $service
    } elseif (-not (Test-Path $dockerfilePath)) {
        $missingServices += "$service (no Dockerfile)"
    }
}

if ($missingServices.Count -eq 0) {
    Write-Host "   All 8 microservices found with Dockerfiles" -ForegroundColor Green
} else {
    Write-Host "   Missing or incomplete services:" -ForegroundColor Red
    foreach ($service in $missingServices) {
        Write-Host "     - $service" -ForegroundColor Red
    }
    $allChecks = $false
}

# Check 7: System resources
Write-Host ""
Write-Host "7. Checking system resources..." -ForegroundColor Yellow

# Get available RAM (rough estimate)
try {
    $os = Get-CimInstance Win32_OperatingSystem
    $totalRAM = [math]::Round($os.TotalVisibleMemorySize / 1MB, 2)
    $freeRAM = [math]::Round($os.FreePhysicalMemory / 1MB, 2)
    
    Write-Host "   Total RAM: ${totalRAM}GB" -ForegroundColor Gray
    Write-Host "   Free RAM: ${freeRAM}GB" -ForegroundColor Gray
    
    if ($freeRAM -ge 3) {
        Write-Host "   Sufficient RAM available" -ForegroundColor Green
    } else {
        Write-Host "   Warning: Low RAM (${freeRAM}GB free)" -ForegroundColor Yellow
        Write-Host "     Builds may be slower but should work" -ForegroundColor Gray
    }
} catch {
    Write-Host "   Could not check RAM" -ForegroundColor Yellow
}

# Check 8: Network connectivity
Write-Host ""
Write-Host "8. Checking network connectivity..." -ForegroundColor Yellow
try {
    $netTest = Test-NetConnection -ComputerName google.com -Port 443 -InformationLevel Quiet -WarningAction SilentlyContinue -ErrorAction SilentlyContinue
    if ($netTest) {
        Write-Host "   Network connection available" -ForegroundColor Green
    } else {
        Write-Host "   Warning: Cannot verify network" -ForegroundColor Yellow
        Write-Host "     If you can browse the web, you should be fine" -ForegroundColor Gray
    }
} catch {
    Write-Host "   Warning: Cannot verify network" -ForegroundColor Yellow
    Write-Host "     If you can browse the web, you should be fine" -ForegroundColor Gray
}

# Summary
Write-Host ""
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Pre-Flight Check Summary" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

if ($allChecks) {
    Write-Host "All checks passed!" -ForegroundColor Green
    Write-Host ""
    Write-Host "You are ready to deploy! Run:" -ForegroundColor Yellow
    Write-Host "  .\quick-start-minikube.ps1" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Or step by step:" -ForegroundColor Yellow
    Write-Host "  .\scripts\start-minikube.ps1" -ForegroundColor White
    Write-Host "  .\scripts\build-all.ps1" -ForegroundColor White
    Write-Host "  .\scripts\deploy.ps1" -ForegroundColor White
    Write-Host "  .\scripts\run-migrations.ps1" -ForegroundColor White
    Write-Host ""
    exit 0
} else {
    Write-Host "Some checks failed" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please resolve the issues above before proceeding." -ForegroundColor Yellow
    Write-Host ""
    exit 1
}
