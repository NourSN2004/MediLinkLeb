# MediLink System Status Check

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  MediLink System Status" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Check Minikube
Write-Host "Checking Minikube..." -ForegroundColor Green
$minikubeStatus = minikube status 2>&1 | Out-String
if ($minikubeStatus -match "Running") {
    Write-Host "  [OK] Minikube is running" -ForegroundColor Green
} else {
    Write-Host "  [FAIL] Minikube is not running" -ForegroundColor Red
}

# Check Pods
Write-Host ""
Write-Host "Checking Pods..." -ForegroundColor Green
$pods = kubectl get pods -n medilink --no-headers 2>$null
$totalPods = ($pods | Measure-Object).Count
$runningPods = ($pods | Select-String "Running" | Measure-Object).Count
Write-Host "  Running: $runningPods/$totalPods pods" -ForegroundColor $(if ($runningPods -eq $totalPods) { "Green" } else { "Yellow" })

# List pods by service
$services = @("api-gateway", "auth-service", "doctor-service", "patient-service", "pharmacy-service", "scheduling-service", "inventory-service", "notification-service", "postgres")
foreach ($service in $services) {
    $servicePods = kubectl get pods -n medilink -l app=$service --no-headers 2>$null
    $count = ($servicePods | Measure-Object).Count
    $running = ($servicePods | Select-String "Running" | Measure-Object).Count
    $status = if ($running -eq $count -and $count -gt 0) { "OK" } else { "WARN" }
    $color = if ($status -eq "OK") { "Green" } else { "Yellow" }
    Write-Host "    $service`: $running/$count running" -ForegroundColor $color
}

# Check Services
Write-Host ""
Write-Host "Checking Services..." -ForegroundColor Green
$services = kubectl get svc -n medilink --no-headers 2>$null
$serviceCount = ($services | Measure-Object).Count
Write-Host "  Services: $serviceCount" -ForegroundColor Green

# Check Ingress
Write-Host ""
Write-Host "Checking Ingress..." -ForegroundColor Green
$ingress = kubectl get ingress -n medilink --no-headers 2>$null
if ($ingress) {
    $address = ($ingress -split '\s+')[3]
    Write-Host "  [OK] Ingress configured" -ForegroundColor Green
    Write-Host "  Address: $address" -ForegroundColor Cyan
} else {
    Write-Host "  [WARN] Ingress not found" -ForegroundColor Yellow
}

# Check Ingress Controller
Write-Host ""
Write-Host "Checking Ingress Controller..." -ForegroundColor Green
$ingressPods = kubectl get pods -n ingress-nginx -l app.kubernetes.io/component=controller --no-headers 2>$null
if ($ingressPods -match "Running") {
    Write-Host "  [OK] NGINX Ingress Controller running" -ForegroundColor Green
} else {
    Write-Host "  [WARN] NGINX Ingress Controller not running" -ForegroundColor Yellow
}

# Check Hosts File
Write-Host ""
Write-Host "Checking Hosts File..." -ForegroundColor Green
$hostsContent = Get-Content "C:\Windows\System32\drivers\etc\hosts" 2>$null
if ($hostsContent -match "medilink.local") {
    Write-Host "  [OK] medilink.local configured in hosts file" -ForegroundColor Green
} else {
    Write-Host "  [WARN] medilink.local not in hosts file" -ForegroundColor Yellow
    Write-Host "  Run START_INGRESS.ps1 as Administrator to add it" -ForegroundColor Yellow
}

# Access Instructions
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Access Instructions" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Method 1 - Direct Service (Recommended for Development):" -ForegroundColor Green
Write-Host "  Run: .\START_APP.ps1" -ForegroundColor White
Write-Host ""
Write-Host "Method 2 - Ingress (Production-like):" -ForegroundColor Green
Write-Host "  Run as Admin: .\START_INGRESS.ps1" -ForegroundColor White
Write-Host "  Then access: http://medilink.local" -ForegroundColor Cyan
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
