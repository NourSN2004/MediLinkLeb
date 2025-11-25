# Quick Fix for medilink.local access
# Run as Administrator

Write-Host "Updating hosts file for medilink.local..." -ForegroundColor Cyan

$hostsFile = "C:\Windows\System32\drivers\etc\hosts"

# Remove old entries
$content = Get-Content $hostsFile | Where-Object { $_ -notmatch "medilink.local" }

# Add new entry
$content += ""
$content += "127.0.0.1`tmedilink.local"

# Write back
Set-Content -Path $hostsFile -Value $content

Write-Host "Hosts file updated successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Now starting minikube tunnel..." -ForegroundColor Cyan
Write-Host "Keep this window open!" -ForegroundColor Yellow
Write-Host ""

# Start tunnel
minikube tunnel
