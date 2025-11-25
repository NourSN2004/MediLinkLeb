# Start MediLink Application
# This script creates a tunnel to access the API Gateway

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Starting MediLink Application" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Creating service tunnel..." -ForegroundColor Green
Write-Host ""
Write-Host "IMPORTANT:" -ForegroundColor Red
Write-Host "  - Keep this window open while using the application" -ForegroundColor Yellow
Write-Host "  - The browser will open automatically with the correct URL" -ForegroundColor Yellow
Write-Host "  - Press Ctrl+C to stop the tunnel when done" -ForegroundColor Yellow
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Start the minikube service tunnel
minikube service api-gateway -n medilink
