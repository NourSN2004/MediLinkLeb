# Complete Setup Guide

## 🚀 Quick Start (Automated)

### Option 1: Run as Administrator (Fully Automated)
Right-click PowerShell → Run as Administrator, then:
```powershell
.\COMPLETE_SETUP.ps1
```

This will:
- ✅ Start Minikube cluster
- ✅ Build all Docker images (~5-10 minutes)
- ✅ Deploy all microservices
- ✅ Run database migrations
- ✅ Configure Ingress controller
- ✅ Update hosts file automatically
- ✅ Start minikube tunnel

**Total time:** ~10-15 minutes

After completion, access at: **http://medilink.local**

---

### Option 2: Run as Regular User (Manual Hosts File)
```powershell
.\COMPLETE_SETUP.ps1
```

When prompted, add this line to `C:\Windows\System32\drivers\etc\hosts`:
```
127.0.0.1    medilink.local
```

Then press Enter to continue.

---

### Skip Building (If Images Already Exist)
```powershell
.\COMPLETE_SETUP.ps1 -SkipBuild
```

This saves ~5-10 minutes if you've already built the images.

---

### Force Fresh Start
```powershell
.\COMPLETE_SETUP.ps1 -Force
```

This will restart Minikube even if it's already running.

---

## 📝 What Happens During Setup

1. **Prerequisites Check** - Verifies Docker, kubectl, Minikube installed
2. **Minikube Start** - Starts cluster with 6GB RAM, 4 CPUs
3. **Docker Images** - Builds all 8 microservices (~5-10 min)
4. **Namespace** - Creates `medilink` namespace
5. **Database** - Deploys PostgreSQL and waits for ready
6. **Microservices** - Deploys all services and waits for pods
7. **Migrations** - Runs Django database migrations
8. **Ingress** - Configures Ingress controller and routes
9. **Hosts File** - Updates to point medilink.local to 127.0.0.1
10. **Tunnel** - Starts minikube tunnel for LoadBalancer access
11. **Done!** - Access at http://medilink.local

---

## ⚠️ Important Notes

### Keep Terminal Open
The script ends with `minikube tunnel` running. **Keep this terminal window open** while using the application. Closing it will stop the tunnel and make http://medilink.local inaccessible.

### Stop the Tunnel
When you're done:
- Press `Ctrl+C` in the terminal
- This stops the tunnel but keeps Minikube running

### Resume Access Later
If you stop the tunnel and want to access the app again:
```powershell
minikube tunnel
```

Then open http://medilink.local

---

## 🧪 After Setup

### Create Your First Account
1. Open http://medilink.local
2. Click "Sign up"
3. Choose: Patient, Doctor, or Pharmacy
4. Fill in details and submit
5. You'll be auto-logged in

### Test Different Roles
- **Patient**: View prescriptions, browse medicine, schedule appointments
- **Doctor**: Manage appointments, patient records, availability
- **Pharmacy**: Manage inventory, prescriptions, staff

---

## 🔧 Troubleshooting

### Script Fails During Build
```powershell
# Clean up and try again
minikube delete
.\COMPLETE_SETUP.ps1
```

### Pods Not Ready
Wait a bit longer - initial deployment can take 3-5 minutes for all pods to be ready.

Check status:
```powershell
kubectl get pods -n medilink
```

### medilink.local Not Working
1. Check hosts file has: `127.0.0.1 medilink.local`
2. Check tunnel is running: `Get-Process | Where-Object ProcessName -eq "minikube"`
3. Restart tunnel: `minikube tunnel` (as Admin)

### Out of Memory
If build fails with memory errors:
```powershell
# Stop and increase Minikube memory
minikube stop
minikube start --memory=8192 --cpus=4
.\COMPLETE_SETUP.ps1 -SkipBuild
```

---

## 📊 Check System Status

```powershell
.\CHECK_STATUS.ps1
```

Shows:
- Minikube status
- All pod statuses
- Service status
- Ingress configuration
- Hosts file status

---

## 🎯 For Development

### Rebuild After Code Changes
```powershell
# Configure Docker
& minikube -p minikube docker-env --shell powershell | Invoke-Expression

# Rebuild specific service
cd microservices\<service-name>
docker build -t <service-name>:latest .

# Restart deployment
kubectl rollout restart deployment/<service-name> -n medilink
```

### View Logs
```powershell
kubectl logs -n medilink deployment/api-gateway --tail=50
kubectl logs -n medilink deployment/auth-service --tail=50
```

### Scale Services
```powershell
kubectl scale deployment api-gateway -n medilink --replicas=6
```

---

## 📚 Additional Documentation

- `DEPLOYMENT_SUCCESS.md` - Complete deployment documentation
- `ACCESS_GUIDE.md` - Different ways to access the application
- `QUICK_REFERENCE.md` - Common commands and operations
- `CHECK_STATUS.ps1` - System health check script

---

## ✅ Success Criteria

After running `COMPLETE_SETUP.ps1`, you should see:
- ✅ All pods in Running state
- ✅ Ingress configured
- ✅ Tunnel running
- ✅ Can access http://medilink.local
- ✅ Can create account and login
- ✅ All features working

**If all above are true, you're ready to go!** 🎉
