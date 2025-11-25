$authUrl = "http://localhost:8001"
$doctorUrl = "http://localhost:8002"
$patientUrl = "http://localhost:8003"
$pharmacyUrl = "http://localhost:8004"

function Create-User {
    param($username, $email, $password, $role, $firstName, $lastName)
    
    Write-Host "Creating $role user: $username..." -NoNewline
    
    $body = @{
        email = $email
        name = "$firstName $lastName"
        role = $role
        password = $password
        password_confirm = $password
    } | ConvertTo-Json
    
    try {
        $response = Invoke-RestMethod -Uri "$authUrl/api/auth/register/" -Method Post -Body $body -ContentType "application/json"
        Write-Host " Done." -ForegroundColor Green
        return $response
    } catch {
        Write-Host " Failed." -ForegroundColor Red
        Write-Host $_.Exception.Message
        try {
            $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
            Write-Host $reader.ReadToEnd() -ForegroundColor DarkRed
        } catch {}
        return $null
    }
}

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
        Invoke-RestMethod -Uri "$baseUrl$endpoint" -Method Post -Body $jsonBody -ContentType "application/json" -Headers $headers | Out-Null
        Write-Host "Profile created at $endpoint" -ForegroundColor Green
    } catch {
        if ($_.Exception.Response.StatusCode -ne 400) {
            Write-Host "Profile creation failed: $($_.Exception.Message)" -ForegroundColor Red
            # Print response body if available
            try {
                $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
                Write-Host $reader.ReadToEnd() -ForegroundColor DarkRed
            } catch {}
        } else {
            Write-Host "Profile likely already exists." -ForegroundColor Yellow
        }
    }
}

# 1. Doctor
$docUser = Create-User "doctor1" "doctor1@medilink.com" "Password123!" "doctor" "John" "Smith"
# Even if creation failed (exists), try to login
$token = Get-Token "doctor1@medilink.com" "Password123!"
if ($token) {
    # Need user ID. If we just created, we have it. If not, we need to fetch profile.
    # But we can't fetch profile easily without ID in some services, or /me endpoint.
    # Auth service has /api/auth/profile/
    try {
        $profile = Invoke-RestMethod -Uri "$authUrl/api/auth/profile/" -Headers @{ Authorization = "Bearer $token" }
        $userId = $profile.id
        
        Create-Profile $token $doctorUrl "/api/doctors/" @{
            user_id = $userId
            specialty = "Cardiology"
            license_number = "DOC-001"
        }
        # Add working hours
        Create-Profile $token $doctorUrl "/api/doctors/$userId/working-hours/" @{
            day_of_week = 1
            start_time = "09:00:00"
            end_time = "17:00:00"
        }
    } catch {
        Write-Host "Failed to get user profile: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# 2. Patient
$patUser = Create-User "patient1" "patient1@medilink.com" "Password123!" "patient" "Jane" "Doe"
$token = Get-Token "patient1@medilink.com" "Password123!"
if ($token) {
    try {
        $profile = Invoke-RestMethod -Uri "$authUrl/api/auth/profile/" -Headers @{ Authorization = "Bearer $token" }
        $userId = $profile.id
        
        Create-Profile $token $patientUrl "/api/patients/" @{
            user_id = $userId
            dob = "1990-01-01"
            gender = "F"
            blood_type = "O+"
        }
    } catch {
        Write-Host "Failed to get user profile: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# 3. Pharmacy
$pharmUser = Create-User "pharmacy1" "pharmacy1@medilink.com" "Password123!" "pharmacy" "City" "Pharmacy"
$token = Get-Token "pharmacy1@medilink.com" "Password123!"
if ($token) {
    try {
        $profile = Invoke-RestMethod -Uri "$authUrl/api/auth/profile/" -Headers @{ Authorization = "Bearer $token" }
        $userId = $profile.id
        
        Create-Profile $token $pharmacyUrl "/api/pharmacies/" @{
            user_id = $userId
            address = "123 Main St"
            license_number = "PHARM-001"
        }
    } catch {
        Write-Host "Failed to get user profile: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host "`nTest Users Created:" -ForegroundColor Cyan
Write-Host "1. Doctor:   doctor1@medilink.com / Password123!"
Write-Host "2. Patient:  patient1@medilink.com / Password123!"
Write-Host "3. Pharmacy: pharmacy1@medilink.com / Password123!"
