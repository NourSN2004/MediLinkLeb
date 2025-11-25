# MediLink Quick Reference Card

---

## 🚀 Fresh Machine Setup (One-Time)

```powershell
# 1. Install prerequisites (Minikube, kubectl, Docker Desktop, Git)

# 2. Clone repo
git clone https://github.com/NourSN2004/MediLinkLeb.git
cd MediLinkLeb
git checkout complete-kubernetes-jenkins

# 3. Start Minikube
minikube start --memory=8192 --cpus=4 --driver=docker
minikube addons enable ingress
minikube tunnel  # Keep open!

# 4. Edit hosts file (as Admin)
# Add: 127.0.0.1 medilink.local jenkins.medilink.local

# 5. Deploy everything
.\COMPLETE_SETUP.ps1 -IncludeJenkins

# 6. Configure Jenkins
# - Get password: kubectl exec -n jenkins deployment/jenkins -- cat /var/jenkins_home/secrets/initialAdminPassword
# - Open: http://jenkins.medilink.local
# - Install suggested plugins + Pipeline plugin
# - Create pipeline job pointing to GitHub repo

# 7. First build
# Click "Build Now" in Jenkins

# Done! 🎉
```

**Time:** ~30-45 minutes

---

## 📅 Daily Workflow

### Morning Startup

```powershell
# Start Minikube (if stopped)
minikube start

# Start tunnel (keep terminal open)
minikube tunnel

# Verify everything
kubectl get pods -n medilink -n jenkins
```

### Making Code Changes

```powershell
# 1. Edit code
code microservices/doctor-service/views.py

# 2. Commit and push
git add .
git commit -m "Your change description"
git push origin complete-kubernetes-jenkins

# 3. Build in Jenkins
# - Open http://jenkins.medilink.local
# - Click "Build Now"
# - Or wait 5 min if polling enabled

# 4. Test changes
# Open http://medilink.local
```

### Evening Shutdown

```powershell
# Stop Minikube (saves state)
minikube stop
```

---

## 🤖 Automatic Builds

### Enable SCM Polling (Recommended)

Jenkins checks GitHub every 5 minutes:

1. Jenkins → MediLink-Pipeline → **Configure**
2. Build Triggers → Check **"Poll SCM"**
3. Schedule: `H/5 * * * *`
4. **Save**

Now push code and wait ~5 minutes - builds automatically! 🎉

---

## 🔍 Quick Status Check

```powershell
# All pods running?
kubectl get pods -n medilink -n jenkins

# Application accessible?
curl http://medilink.local

# Jenkins accessible?
curl http://jenkins.medilink.local

# Minikube healthy?
minikube status

# View recent logs
kubectl logs -n medilink -l app=auth-service --tail=20
```

---

## 📊 What Gets Built?

Jenkins intelligently detects changes:

| You Changed | Jenkins Builds |
|------------|----------------|
| `microservices/auth-service/views.py` | ✅ auth-service only |
| `microservices/auth-service/*` + `doctor-service/*` | ✅ Both services |
| `requirements.txt` or root `Dockerfile` | ✅ All 8 services |
| `Jenkinsfile` or build config | ✅ All 8 services |
| No changes (manual build) | ✅ All 8 services (safe) |

---

## 🛠️ Common Commands

### Kubernetes

```powershell
# Get all resources
kubectl get all -n medilink

# View pod logs
kubectl logs -n medilink <pod-name> --tail=50 -f

# Restart a service
kubectl rollout restart deployment/auth-service -n medilink

# Execute command in pod
kubectl exec -n medilink <pod-name> -- python manage.py shell

# Port forward (bypass ingress)
kubectl port-forward -n medilink service/api-gateway 8000:8000

# Delete everything
kubectl delete namespace medilink
kubectl delete namespace jenkins
```

### Jenkins

```powershell
# Get admin password
kubectl exec -n jenkins deployment/jenkins -- cat /var/jenkins_home/secrets/initialAdminPassword

# View Jenkins logs
kubectl logs -n jenkins deployment/jenkins -f

# Restart Jenkins
kubectl rollout restart deployment/jenkins -n jenkins

# Execute command in Jenkins
kubectl exec -n jenkins deployment/jenkins -- docker ps
```

### Minikube

```powershell
# Start/stop
minikube start
minikube stop
minikube delete  # Complete reset

# Status
minikube status

# Dashboard
minikube dashboard

# SSH into Minikube
minikube ssh

# View Docker images in Minikube
minikube ssh "docker images"

# Increase resources
minikube delete
minikube start --memory=12288 --cpus=6
```

---

## 🐛 Troubleshooting

### Can't Access Application

```powershell
# Check tunnel is running
# Terminal should show: "Tunnel successfully started"

# Restart tunnel if needed
# Ctrl+C to stop, then: minikube tunnel

# Check hosts file
notepad C:\Windows\System32\drivers\etc\hosts
# Should have: 127.0.0.1 medilink.local jenkins.medilink.local
```

### Pod Not Starting

```powershell
# Check pod status
kubectl get pods -n medilink

# View pod details
kubectl describe pod <pod-name> -n medilink

# View logs
kubectl logs <pod-name> -n medilink
```

### Jenkins Build Fails

```powershell
# View console output in Jenkins UI

# Check Docker access
kubectl exec -n jenkins deployment/jenkins -- docker ps

# Check kubectl access
kubectl exec -n jenkins deployment/jenkins -- kubectl get pods -n medilink
```

---

## 📍 Important URLs

- **Application:** http://medilink.local
- **Jenkins:** http://jenkins.medilink.local
- **Minikube Dashboard:** Run `minikube dashboard`

---

## 💡 Pro Tips

1. **Keep tunnel running:** Dedicate one terminal to `minikube tunnel`
2. **Enable SCM polling:** Auto-builds every 5 minutes
3. **Watch build logs:** Jenkins console shows exactly what's happening
4. **Commit often:** Small commits are easier to debug

---

**Quick Health Check:**
```powershell
kubectl get pods -n medilink -n jenkins --no-headers | Select-String "Running" | Measure-Object
# Should show: Count: 27 (26 medilink + 1 jenkins)
```

**If count is 27 and you can access http://medilink.local - you're golden! 🌟**