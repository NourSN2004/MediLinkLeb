# Fresh Machine Setup Guide - MediLink

Complete guide to deploy MediLink from scratch on a new Windows machine.

---

## Prerequisites

### Required Software

1. **Docker Desktop**
   - Download: https://www.docker.com/products/docker-desktop
   - Install and enable Kubernetes
   - Allocate at least 12GB RAM

2. **Minikube**
   ```powershell
   # Install with Chocolatey
   choco install minikube
   
   # Or download from:
   # https://minikube.sigs.k8s.io/docs/start/
   ```

3. **kubectl**
   ```powershell
   # Install with Chocolatey
   choco install kubernetes-cli
   
   # Or install via Minikube
   minikube kubectl -- get pods -A
   ```

4. **Git**
   ```powershell
   choco install git
   ```

5. **PowerShell 5.1 or later** (included with Windows 10/11)

---

## Complete Setup (30-45 minutes)

### Step 1: Clone Repository

```powershell
# Navigate to your desired location
cd "C:\Users\YourName\Documents"

# Clone the repository
git clone https://github.com/NourSN2004/MediLinkLeb.git
cd MediLinkLeb

# Switch to the Kubernetes branch
git checkout complete-kubernetes-jenkins
```

### Step 2: Configure WSL2 Memory (if using WSL2)

Create or edit `C:\Users\YourName\.wslconfig`:

```ini
[wsl2]
memory=12GB
processors=4
```

Then restart WSL:
```powershell
wsl --shutdown
```

### Step 3: Start Minikube

```powershell
# Start Minikube with adequate resources
minikube start --memory=8192 --cpus=4 --driver=docker

# Enable ingress addon
minikube addons enable ingress

# Start tunnel (keep this terminal open)
minikube tunnel
```

> **Important:** Keep the `minikube tunnel` terminal open throughout!

### Step 4: Update Hosts File

Edit `C:\Windows\System32\drivers\etc\hosts` (as Administrator):

```
127.0.0.1 medilink.local
127.0.0.1 jenkins.medilink.local
```

### Step 5: Deploy Everything

```powershell
# Run the complete setup script
.\COMPLETE_SETUP.ps1 -IncludeJenkins

# This will:
# - Create medilink namespace
# - Deploy PostgreSQL database
# - Deploy all 8 microservices
# - Deploy API Gateway
# - Create ingress routes
# - Deploy Jenkins CI/CD
# - Configure RBAC
```

**Wait 5-10 minutes** for all pods to become ready.

### Step 6: Verify Deployment

```powershell
# Check all pods are running
kubectl get pods -n medilink
kubectl get pods -n jenkins

# Should see:
# medilink: 26/26 pods Running
# jenkins: 1/1 pod Running
```

### Step 7: Configure Jenkins

1. **Get Jenkins admin password:**
   ```powershell
   kubectl exec -n jenkins deployment/jenkins -- cat /var/jenkins_home/secrets/initialAdminPassword
   ```

2. **Open Jenkins:** http://jenkins.medilink.local

3. **Initial setup:**
   - Paste admin password
   - Click "Install suggested plugins"
   - Create admin user (username/password)
   - Save and continue

4. **Install Pipeline plugin:**
   - Go to **Manage Jenkins** → **Manage Plugins**
   - Click **Available** tab
   - Search for "Pipeline"
   - Select and click **"Install without restart"**

### Step 8: Create Pipeline Job

1. Click **"New Item"**
2. Enter name: `MediLink-Pipeline`
3. Select **"Pipeline"**
4. Click **OK**

5. **Configure pipeline:**
   - Definition: `Pipeline script from SCM`
   - SCM: `Git`
   - Repository URL: `https://github.com/NourSN2004/MediLinkLeb`
   - Branch: `*/complete-kubernetes-jenkins`
   - Script Path: `Jenkinsfile`

6. Click **Save**

### Step 9: First Build

Click **"Build Now"** to test the pipeline.

Should see all stages succeed:
- ✅ Detect Changes
- ✅ Build Changed Services
- ✅ Run Tests
- ✅ Deploy to Kubernetes
- ✅ Run Migrations
- ✅ Verify Deployment

### Step 10: Access Application

Open http://medilink.local in your browser.

---

## Automated Builds (GitHub Webhook)

### How It Works

Currently: **Manual builds only** - you click "Build Now" in Jenkins.

To enable **automatic builds on GitHub push**:

### Option 1: GitHub Webhook (Requires Public Jenkins)

⚠️ **Problem:** Your Jenkins runs on `localhost` - GitHub can't reach it.

**Solutions:**
1. Use ngrok to expose Jenkins temporarily
2. Deploy Jenkins to a cloud provider
3. Use GitHub Actions instead

### Option 2: Polling SCM (Works with localhost)

Edit the pipeline job in Jenkins:

1. Click **"Configure"**
2. Under **Build Triggers**, check **"Poll SCM"**
3. Schedule: `H/5 * * * *` (check every 5 minutes)
4. Click **Save**

Now Jenkins checks GitHub every 5 minutes for changes!

### Option 3: Manual Trigger (Current Setup)

When you make code changes:

1. Push to GitHub:
   ```powershell
   git add .
   git commit -m "Fix bug in doctor-service"
   git push origin complete-kubernetes-jenkins
   ```

2. Go to Jenkins UI: http://jenkins.medilink.local

3. Click **"Build Now"**

4. Pipeline will:
   - Detect which services changed
   - Build only those services
   - Deploy updates to Kubernetes
   - Run migrations if needed

---

## Change Detection Examples

The Jenkinsfile automatically detects which services changed:

### Example 1: Single Service Change

```powershell
# Edit doctor service
code microservices/doctor-service/views.py

# Commit and push
git add .
git commit -m "Update doctor availability logic"
git push

# Jenkins will build ONLY doctor-service
```

### Example 2: Multiple Services

```powershell
# Edit multiple services
code microservices/auth-service/views.py
code microservices/patient-service/models.py

# Jenkins will build auth-service AND patient-service
```

### Example 3: Shared File Changes

```powershell
# Edit requirements.txt or Dockerfile
code requirements.txt

# Jenkins will build ALL 8 services (safe default)
```

### Example 4: No Code Changes

If you click "Build Now" without code changes:
- Jenkins builds all services as a precaution
- Ensures everything is up-to-date

---

## Daily Workflow

### Starting Your Day

```powershell
# 1. Start Minikube (if stopped)
minikube start

# 2. Start tunnel (new terminal - keep open)
minikube tunnel

# 3. Check everything is running
kubectl get pods -n medilink
kubectl get pods -n jenkins
```

### Making Code Changes

```powershell
# 1. Create a branch
git checkout -b feature/new-feature

# 2. Make your changes
code microservices/doctor-service/views.py

# 3. Test locally (optional)
# ... your local testing ...

# 4. Commit and push
git add .
git commit -m "Add new feature"
git push origin feature/new-feature

# 5. Merge to main branch
# ... via GitHub PR or direct merge ...

# 6. Build in Jenkins
# Go to http://jenkins.medilink.local
# Click "Build Now"

# 7. Verify deployment
# Open http://medilink.local
# Test your changes
```

### Stopping at End of Day

```powershell
# Stop Minikube to free resources
minikube stop

# Everything is saved - just start again next day
```

---

## Troubleshooting

### Minikube Won't Start

```powershell
# Delete and recreate
minikube delete
minikube start --memory=8192 --cpus=4 --driver=docker
minikube addons enable ingress
```

### Jenkins Pod Not Starting

```powershell
# Check logs
kubectl logs -n jenkins deployment/jenkins

# Common issue: memory
# Increase Minikube memory:
minikube delete
minikube start --memory=12288 --cpus=4
```

### Can't Access Applications

```powershell
# Ensure tunnel is running
minikube tunnel

# Check ingress
kubectl get ingress -n medilink
kubectl get ingress -n jenkins

# Verify hosts file has entries
notepad C:\Windows\System32\drivers\etc\hosts
```

### Pipeline Build Fails

```powershell
# Check Jenkins has Docker access
kubectl exec -n jenkins deployment/jenkins -- docker ps

# Check Jenkins can access kubectl
kubectl exec -n jenkins deployment/jenkins -- kubectl get pods -n medilink

# View detailed logs
# Go to Jenkins → Build → Console Output
```

### Database Connection Issues

```powershell
# Check PostgreSQL is running
kubectl get pods -n medilink | Select-String postgres

# Check secrets exist
kubectl get secrets -n medilink

# Restart a service if needed
kubectl rollout restart deployment/auth-service -n medilink
```

---

## Quick Reference

### Essential Commands

```powershell
# Status check
kubectl get all -n medilink
kubectl get all -n jenkins

# View logs
kubectl logs -n medilink -l app=auth-service --tail=50
kubectl logs -n jenkins deployment/jenkins --tail=50

# Restart a service
kubectl rollout restart deployment/auth-service -n medilink

# Delete everything and start over
kubectl delete namespace medilink
kubectl delete namespace jenkins
.\COMPLETE_SETUP.ps1 -IncludeJenkins

# Check Minikube
minikube status
minikube dashboard

# Port forward (if ingress not working)
kubectl port-forward -n medilink service/api-gateway 8000:8000
# Then access: http://localhost:8000
```

### URLs

- **Application:** http://medilink.local
- **Jenkins:** http://jenkins.medilink.local
- **Minikube Dashboard:** `minikube dashboard`

### File Locations

- **Application code:** `microservices/`
- **Kubernetes configs:** `k8s/`
- **Pipeline definition:** `Jenkinsfile`
- **Setup script:** `COMPLETE_SETUP.ps1`
- **Jenkins configs:** `k8s/jenkins/`

---

## Architecture Overview

```
┌─────────────────────────────────────────────┐
│  Your Machine (Windows)                     │
│                                             │
│  ┌────────────────────────────────────┐   │
│  │  Minikube (Kubernetes)             │   │
│  │                                    │   │
│  │  ┌──────────────────────────┐     │   │
│  │  │  medilink namespace      │     │   │
│  │  │  ├── PostgreSQL (1 pod)  │     │   │
│  │  │  ├── Auth (3 pods)       │     │   │
│  │  │  ├── Doctor (3 pods)     │     │   │
│  │  │  ├── Patient (4 pods)    │     │   │
│  │  │  ├── Pharmacy (2 pods)   │     │   │
│  │  │  ├── Scheduling (4 pods) │     │   │
│  │  │  ├── Inventory (3 pods)  │     │   │
│  │  │  ├── Notification (2 pods)│    │   │
│  │  │  └── API Gateway (4 pods)│     │   │
│  │  └──────────────────────────┘     │   │
│  │                                    │   │
│  │  ┌──────────────────────────┐     │   │
│  │  │  jenkins namespace       │     │   │
│  │  │  └── Jenkins (1 pod)     │     │   │
│  │  │      ├── Docker access   │     │   │
│  │  │      ├── kubectl access  │     │   │
│  │  │      └── Git access      │     │   │
│  │  └──────────────────────────┘     │   │
│  │                                    │   │
│  │  Ingress Controller                │   │
│  │  ├── medilink.local → API Gateway │   │
│  │  └── jenkins.medilink.local       │   │
│  └────────────────────────────────────┘   │
│                    ↕                       │
│             minikube tunnel                │
│                    ↕                       │
│              localhost:80                  │
└─────────────────────────────────────────────┘
                     ↕
            Your Web Browser
    http://medilink.local
    http://jenkins.medilink.local
```

---

## CI/CD Flow

```
Developer                     GitHub                    Jenkins                    Kubernetes
    │                           │                         │                            │
    ├─ Edit code                │                         │                            │
    ├─ git commit               │                         │                            │
    ├─ git push ───────────────>│                         │                            │
    │                           │                         │                            │
    ├─ Open Jenkins UI          │                         │                            │
    ├─ Click "Build Now" ──────────────────────────────>│                            │
    │                           │                         │                            │
    │                           │<──── git clone ─────────│                            │
    │                           │                         │                            │
    │                           │                         ├─ Detect changes           │
    │                           │                         ├─ Build Docker images      │
    │                           │                         ├─ Run tests                │
    │                           │                         ├─ Update deployments ─────>│
    │                           │                         │                            ├─ Rolling update
    │                           │                         │                            ├─ New pods start
    │                           │                         │                            ├─ Old pods terminate
    │                           │                         ├─ Run migrations ─────────>│
    │                           │                         ├─ Verify deployment        │
    │                           │                         │<──── pod status ───────────│
    │<──── Build Success ───────────────────────────────────┤                            │
    │                           │                         │                            │
    ├─ Open http://medilink.local                         │                            │
    │<──────────────────────────────────────────────────────────────────────────────────┤
    │                 Updated application running!        │                            │
```

---

## Next Steps

After successful setup:

1. ✅ Application running
2. ✅ Jenkins configured
3. ✅ Pipeline working
4. 🔄 Enable SCM polling (every 5 minutes)
5. 🔄 Add automated tests to microservices
6. 🔄 Set up monitoring (Prometheus/Grafana)
7. 🔄 Configure email notifications for build failures
8. 🔄 Add staging environment
9. 🔄 Set up backup for PostgreSQL data
10. 🔄 Document API endpoints

---

## Support

If you encounter issues:

1. Check this guide's Troubleshooting section
2. Review `JENKINS_GUIDE.md` for Jenkins-specific issues
3. Check `README.md` for application details
4. View pod logs: `kubectl logs -n medilink <pod-name>`
5. Check Jenkins console output for build failures

**Health check command:**
```powershell
Write-Host "Checking MediLink deployment..." -ForegroundColor Cyan
kubectl get pods -n medilink | Select-String "Running" | Measure-Object | Select-Object -ExpandProperty Count
kubectl get pods -n jenkins | Select-String "Running" | Measure-Object | Select-Object -ExpandProperty Count
Write-Host "If you see '26' and '1', everything is running!" -ForegroundColor Green
```

---

**Last updated:** November 25, 2025
**Version:** 1.0 - Complete Kubernetes + Jenkins Setup
