# MediLink System Verification
Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "   MEDILINK SYSTEM VERIFICATION" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan

# Check containers
Write-Host ""
Write-Host "Checking Microservices Containers..." -ForegroundColor Yellow
docker ps --filter "name=medilink" --format "table {{.Names}}`t{{.Status}}" | Select-String -Pattern "medilink"

# Check gateway
Write-Host ""
Write-Host "Gateway Status:" -ForegroundColor Yellow
docker ps --filter "name=medilink_gateway" --format "{{.Status}}"

# Test static file
Write-Host ""
Write-Host "Testing static CSS..." -ForegroundColor Yellow
try {
    $r = Invoke-WebRequest -Uri "http://localhost:8080/static/css/styles.css" -UseBasicParsing -TimeoutSec 5
    Write-Host "SUCCESS Static CSS loads (HTTP $($r.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host "FAILED Static CSS: $_" -ForegroundColor Red
}

# Test login page
Write-Host ""
Write-Host "Testing login page..." -ForegroundColor Yellow
try {
    $r = Invoke-WebRequest -Uri "http://localhost:8080/" -UseBasicParsing -TimeoutSec 5
    if ($r.Content -like "*Sign in*") {
        Write-Host "SUCCESS Login page loads correctly" -ForegroundColor Green
    }
} catch {
    Write-Host "FAILED Login page: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "Test Credentials:" -ForegroundColor Cyan
Write-Host "  Doctor:   doctor1@medilink.com   / Password123!" -ForegroundColor White
Write-Host "  Patient:  patient1@medilink.com  / Password123!" -ForegroundColor White
Write-Host "  Pharmacy: pharmacy1@medilink.com / Password123!" -ForegroundColor White
Write-Host ""
Write-Host "Access: http://localhost:8080" -ForegroundColor White
Write-Host "================================================================" -ForegroundColor Cyan
