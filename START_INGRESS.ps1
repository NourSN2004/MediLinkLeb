# Setup Minikube Tunnel for Ingress Access
# This enables access via http://medilink.local

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  MediLink - Ingress Setup (medilink.local)" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "ERROR: This script must be run as Administrator!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    Write-Host "Then run this script again." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Press any key to exit..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}

Write-Host "Checking Minikube cluster status..." -ForegroundColor Green
$minikubeStatus = minikube status 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Minikube is not running!" -ForegroundColor Red
    Write-Host "Please start Minikube first." -ForegroundColor Yellow
    exit 1
}

Write-Host "Checking hosts file..." -ForegroundColor Green
$hostsFile = "C:\Windows\System32\drivers\etc\hosts"
$hostsContent = Get-Content $hostsFile

# Remove old entry if it exists
$newHostsContent = $hostsContent | Where-Object { $_ -notmatch "medilink.local" }

# Add new entry pointing to 127.0.0.1 (LoadBalancer with tunnel)
$newHostsContent += "`n127.0.0.1`tmedilink.local"

# Write back to hosts file
Set-Content -Path $hostsFile -Value $newHostsContent

Write-Host "  Updated hosts file: 127.0.0.1 medilink.local" -ForegroundColor Green

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Starting Minikube Tunnel" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "IMPORTANT:" -ForegroundColor Red
Write-Host "  - Keep this window open while using the application" -ForegroundColor Yellow
Write-Host "  - Access the application at: http://medilink.local" -ForegroundColor Green
Write-Host "  - Press Ctrl+C to stop the tunnel when done" -ForegroundColor Yellow
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Start minikube tunnel
minikube tunnel
