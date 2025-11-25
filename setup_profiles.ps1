# Create profiles for existing test users
$authUrl = "http://localhost:8001"
$doctorUrl = "http://localhost:8002"
$patientUrl = "http://localhost:8003"
$pharmacyUrl = "http://localhost:8004"

function Get-Token {
    param($email, $password)
    
    $body = @{
        email = $email
        password = $password
    } | ConvertTo-Json
    
    try {
        $response = Invoke-RestMethod -Uri "$authUrl/api/auth/login/" -Method Post -Body $body -ContentType "application/json"
        return $response.tokens.access
    } catch {
        Write-Host "Login failed for $email" -ForegroundColor Red
        return $null
    }
}

function Create-Profile {
    param($token, $baseUrl, $endpoint, $body)
    
    try {
        $headers = @{ Authorization = "Bearer $token" }
        $jsonBody = $body | ConvertTo-Json
        $response = Invoke-RestMethod -Uri "$baseUrl$endpoint" -Method Post -Body $jsonBody -ContentType "application/json" -Headers $headers
        Write-Host " Profile created at $endpoint" -ForegroundColor Green
        return $response
    } catch {
        if ($_.Exception.Response.StatusCode -eq 400) {
            Write-Host "  Profile already exists." -ForegroundColor Yellow
        } else {
            Write-Host "  Profile creation failed: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
}

Write-Host "`n=== Setting up test user profiles ===" -ForegroundColor Cyan

# 1. Doctor
Write-Host "`n1. Doctor (doctor1@medilink.com):" -ForegroundColor Yellow
$token = Get-Token "doctor1@medilink.com" "Password123!"
if ($token) {
    $profile = Invoke-RestMethod -Uri "$authUrl/api/auth/me/" -Headers @{ Authorization = "Bearer $token" }
    $userId = $profile.id
    
    Create-Profile $token $doctorUrl "/api/doctors/" @{
        user_id = $userId
        specialty = "Cardiology"
        license_number = "DOC001"
    }
    
    Create-Profile $token $doctorUrl "/api/doctors/$userId/working-hours/" @{
        day_of_week = 1
        start_time = "09:00:00"
        end_time = "17:00:00"
    }
    
    Create-Profile $token $doctorUrl "/api/doctors/$userId/working-hours/" @{
        day_of_week = 3
        start_time = "09:00:00"
        end_time = "17:00:00"
    }
}

# 2. Patient
Write-Host "`n2. Patient (patient1@medilink.com):" -ForegroundColor Yellow
$token = Get-Token "patient1@medilink.com" "Password123!"
if ($token) {
    $profile = Invoke-RestMethod -Uri "$authUrl/api/auth/me/" -Headers @{ Authorization = "Bearer $token" }
    $userId = $profile.id
    
    Create-Profile $token $patientUrl "/api/patients/" @{
        user_id = $userId
        dob = "1990-01-01"
        gender = "F"
        blood_type = "O+"
        national_id = "PAT001"
    }
}

# 3. Pharmacy
Write-Host "`n3. Pharmacy (pharmacy1@medilink.com):" -ForegroundColor Yellow
$token = Get-Token "pharmacy1@medilink.com" "Password123!"
if ($token) {
    $profile = Invoke-RestMethod -Uri "$authUrl/api/auth/me/" -Headers @{ Authorization = "Bearer $token" }
    $userId = $profile.id
    
    Create-Profile $token $pharmacyUrl "/api/pharmacies/" @{
        user_id = $userId
        address = "123 Main Street, Beirut"
        license_number = "PHARM001"
        phone = "+9611234567"
    }
}

Write-Host "`n==================================================" -ForegroundColor Green
Write-Host "         Test Users Ready for Login              " -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Web Interface: http://localhost:8080" -ForegroundColor Cyan
Write-Host ""
Write-Host "Login Credentials:" -ForegroundColor Yellow
Write-Host "  1. Doctor:   doctor1@medilink.com   / Password123!" -ForegroundColor White
Write-Host "  2. Patient:  patient1@medilink.com  / Password123!" -ForegroundColor White
Write-Host "  3. Pharmacy: pharmacy1@medilink.com / Password123!" -ForegroundColor White
Write-Host ""
