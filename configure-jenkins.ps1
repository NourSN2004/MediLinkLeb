# Configure Jenkins - Automated Setup Script
# This script helps configure Jenkins with required plugins and credentials

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Jenkins Configuration Guide" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Step 1: Access Jenkins" -ForegroundColor Yellow
Write-Host "-------------------------------------------------------" -ForegroundColor Gray
Write-Host "URL: http://jenkins.medilink.local" -ForegroundColor White
Write-Host "     (or use port-forward: kubectl port-forward -n jenkins service/jenkins 8080:8080)" -ForegroundColor Gray
Write-Host ""
Write-Host "Get admin password:" -ForegroundColor White
Write-Host '  kubectl exec -n jenkins deployment/jenkins -- cat /var/jenkins_home/secrets/initialAdminPassword' -ForegroundColor Cyan
Write-Host ""

Write-Host "Step 2: Install Required Plugins" -ForegroundColor Yellow
Write-Host "-------------------------------------------------------" -ForegroundColor Gray
Write-Host "During setup, select 'Install suggested plugins', then add:" -ForegroundColor White
Write-Host "  - Kubernetes Plugin" -ForegroundColor Cyan
Write-Host "  - Docker Pipeline" -ForegroundColor Cyan
Write-Host "  - Git Plugin (usually pre-installed)" -ForegroundColor Cyan
Write-Host "  - Pipeline Plugin (usually pre-installed)" -ForegroundColor Cyan
Write-Host ""

Write-Host "Step 3: Create Pipeline Job" -ForegroundColor Yellow
Write-Host "-------------------------------------------------------" -ForegroundColor Gray
Write-Host "1. Click 'New Item'" -ForegroundColor White
Write-Host "2. Enter name: 'MediLink-Pipeline'" -ForegroundColor White
Write-Host "3. Select 'Pipeline' project type" -ForegroundColor White
Write-Host "4. Click 'OK'" -ForegroundColor White
Write-Host ""

Write-Host "Step 4: Configure Pipeline" -ForegroundColor Yellow
Write-Host "-------------------------------------------------------" -ForegroundColor Gray
Write-Host "In Pipeline section:" -ForegroundColor White
Write-Host "  Definition: Pipeline script from SCM" -ForegroundColor Cyan
Write-Host "  SCM: Git" -ForegroundColor Cyan
Write-Host "  Repository URL: [Your GitHub repo URL]" -ForegroundColor Cyan
Write-Host "  Branch: */main (or your branch)" -ForegroundColor Cyan
Write-Host "  Script Path: Jenkinsfile" -ForegroundColor Cyan
Write-Host ""

Write-Host "Step 5: Configure Kubernetes Access" -ForegroundColor Yellow
Write-Host "-------------------------------------------------------" -ForegroundColor Gray
Write-Host "Jenkins already has access via ServiceAccount" -ForegroundColor White
Write-Host "The Jenkinsfile uses kubectl commands directly" -ForegroundColor White
Write-Host ""

Write-Host "Step 6: Test the Pipeline" -ForegroundColor Yellow
Write-Host "-------------------------------------------------------" -ForegroundColor Gray
Write-Host "1. Click 'Build Now' in your pipeline" -ForegroundColor White
Write-Host "2. Watch the console output" -ForegroundColor White
Write-Host "3. Pipeline will detect changed services and build only those" -ForegroundColor White
Write-Host ""

Write-Host "============================================================" -ForegroundColor Green
Write-Host "  Quick Commands" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Get Jenkins password:" -ForegroundColor Yellow
Write-Host '  kubectl exec -n jenkins deployment/jenkins -- cat /var/jenkins_home/secrets/initialAdminPassword' -ForegroundColor Cyan
Write-Host ""
Write-Host "Port forward to Jenkins:" -ForegroundColor Yellow
Write-Host "  kubectl port-forward -n jenkins service/jenkins 8080:8080" -ForegroundColor Cyan
Write-Host ""
Write-Host "View Jenkins logs:" -ForegroundColor Yellow
Write-Host "  kubectl logs -n jenkins deployment/jenkins -f" -ForegroundColor Cyan
Write-Host ""
Write-Host "Restart Jenkins:" -ForegroundColor Yellow
Write-Host "  kubectl rollout restart deployment/jenkins -n jenkins" -ForegroundColor Cyan
Write-Host ""

# Prompt to open port-forward
$response = Read-Host "Would you like to start port-forward now? (Y/N)"
if ($response -eq "Y" -or $response -eq "y") {
    Write-Host ""
    Write-Host "Starting port-forward on http://localhost:8080..." -ForegroundColor Green
    Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
    Write-Host ""
    kubectl port-forward -n jenkins service/jenkins 8080:8080
}
