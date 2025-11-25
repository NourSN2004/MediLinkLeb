# MediLink - Access Guide

## Two Ways to Access the Application

### Method 1: Direct Service Access (Easiest)
Best for development and testing. No special configuration needed.

1. **Run the service tunnel:**
   ```powershell
   .\START_APP.ps1
   ```

2. **Access the application:**
   - Your browser will open automatically
   - URL will be something like: `http://127.0.0.1:50244`
   - Keep the PowerShell window open while using the app

3. **Stop the tunnel:**
   - Press `Ctrl+C` in the PowerShell window

---

### Method 2: Ingress Access (Production-like)
Access via custom domain `http://medilink.local`

1. **Start Minikube tunnel (requires Administrator):**
   ```powershell
   # Right-click PowerShell → Run as Administrator
   .\START_INGRESS.ps1
   ```

2. **Access the application:**
   - Open browser: `http://medilink.local`
   - Keep the PowerShell window open while using the app

3. **Stop the tunnel:**
   - Press `Ctrl+C` in the PowerShell window

**Note:** The Ingress tunnel must remain running for `http://medilink.local` to work.

---

## Test Accounts

### Create Your Own Account
1. Go to the application URL
2. Click "Sign up"
3. Choose your role: Patient, Doctor, or Pharmacy
4. Fill in the registration form

### Test Each User Type

**Patient Account:**
- Sign up as a Patient
- Navigate to:
  - View Medical History
  - View Prescriptions
  - Browse Medicine
  - Schedule Appointment

**Doctor Account:**
- Sign up as a Doctor
- Navigate to:
  - Today's Appointments
  - Full Schedule
  - Patient Search
  - Manage Availability

**Pharmacy Account:**
- Sign up as a Pharmacy
- Navigate to:
  - Inventory Management
  - Prescription Orders
  - Stock Alerts

---

## Troubleshooting

### "Refused to Connect"
- Make sure the tunnel is running (START_APP.ps1 or START_INGRESS.ps1)
- The PowerShell window must stay open

### "Can't access medilink.local"
- Run `START_INGRESS.ps1` as Administrator
- Check that the tunnel is running
- Verify hosts file has entry: `192.168.49.2 medilink.local`

### Service Not Responding
```powershell
# Check all pods are running
kubectl get pods -n medilink

# Restart a specific service if needed
kubectl rollout restart deployment/api-gateway -n medilink
```

### Check Logs
```powershell
# View API Gateway logs
kubectl logs -n medilink deployment/api-gateway --tail=50

# View Auth Service logs
kubectl logs -n medilink deployment/auth-service --tail=50
```

---

## Architecture

- **API Gateway** (Port 8000): Main web interface
- **Auth Service** (Port 8001): User authentication
- **Doctor Service** (Port 8002): Doctor management
- **Patient Service** (Port 8003): Patient records
- **Pharmacy Service** (Port 8004): Pharmacy operations
- **Scheduling Service** (Port 8005): Appointments
- **Inventory Service** (Port 8006): Medicine inventory
- **Notification Service** (Port 8007): Notifications
- **PostgreSQL**: Database

All services are deployed in the `medilink` Kubernetes namespace.
