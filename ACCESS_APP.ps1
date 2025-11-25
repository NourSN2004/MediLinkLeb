# Access MediLink Application via Minikube Service
# This script opens the API Gateway in your default browser

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  MediLink Application Access" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Opening API Gateway service..." -ForegroundColor Green
Write-Host "This will open your default browser with the application URL" -ForegroundColor Yellow
Write-Host ""
Write-Host "NOTE: This terminal window must stay open!" -ForegroundColor Red
Write-Host "Press Ctrl+C to stop the service tunnel" -ForegroundColor Yellow
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan

minikube service api-gateway -n medilink
