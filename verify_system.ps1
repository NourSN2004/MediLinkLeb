# Quick System Verification Script
# Run this to verify all services are working

Write-Host "`n" -NoNewline
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "   MEDILINK SYSTEM VERIFICATION" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# Check containers
Write-Host "📦 Checking Microservices Containers..." -ForegroundColor Yellow
$containers = docker ps --filter "name=medilink" --format "{{.Names}}" | Measure-Object -Line
if ($containers.Lines -eq 9) {
    Write-Host "✅ All 9 containers are running" -ForegroundColor Green
} else {
    Write-Host "❌ Expected 9 containers, found $($containers.Lines)" -ForegroundColor Red
}

# Check gateway health
Write-Host "`n🌐 Checking API Gateway..." -ForegroundColor Yellow
$gatewayStatus = docker ps --filter "name=medilink_gateway" --format "{{.Status}}"
if ($gatewayStatus -like "*healthy*") {
    Write-Host "✅ Gateway is healthy and running" -ForegroundColor Green
} else {
    Write-Host "⚠️  Gateway status: $gatewayStatus" -ForegroundColor Yellow
}

# Check for recent errors
Write-Host "`n🔍 Checking for errors in gateway logs..." -ForegroundColor Yellow
$errors = docker logs --tail 100 medilink_gateway 2>&1 | Select-String -Pattern "Traceback|ERROR \[" -Quiet
if (-not $errors) {
    Write-Host "✅ No critical errors found" -ForegroundColor Green
} else {
    Write-Host "⚠️  Some errors detected - check logs with: docker logs medilink_gateway" -ForegroundColor Yellow
}

# Test static file serving
Write-Host "`n🎨 Testing static files..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8080/static/css/styles.css" -UseBasicParsing -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Static CSS file loads successfully" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ Static files not accessible: $_" -ForegroundColor Red
}

# Test login page
Write-Host "`n🔐 Testing login page..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8080/" -UseBasicParsing -TimeoutSec 5
    if ($response.StatusCode -eq 200 -and $response.Content -like "*Sign in*") {
        Write-Host "✅ Login page loads successfully" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ Login page not accessible: $_" -ForegroundColor Red
}

Write-Host "`n═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "   VERIFICATION COMPLETE" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan

Write-Host "`n📋 Test Credentials:" -ForegroundColor Cyan
Write-Host "   Doctor:   doctor1@medilink.com   / Password123!" -ForegroundColor White
Write-Host "   Patient:  patient1@medilink.com  / Password123!" -ForegroundColor White
Write-Host "   Pharmacy: pharmacy1@medilink.com / Password123!" -ForegroundColor White

Write-Host "`n🌐 Access the application:" -ForegroundColor Cyan
Write-Host "   http://localhost:8080" -ForegroundColor White

Write-Host "`n📖 For detailed testing checklist, see:" -ForegroundColor Cyan
Write-Host "   COMPREHENSIVE_TEST_REPORT.md" -ForegroundColor White
Write-Host ""
