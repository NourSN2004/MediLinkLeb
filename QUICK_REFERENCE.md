# MediLink Minikube - Quick Reference Card

## 🚀 Getting Started

### First Time Setup
```powershell
# Check if everything is ready
.\check-prerequisites.ps1

# Run complete setup (recommended)
.\quick-start-minikube.ps1
```

### Manual Setup
```powershell
.\scripts\start-minikube.ps1      # 1. Start Minikube
.\scripts\build-all.ps1           # 2. Build images (5-10 min)
.\scripts\deploy.ps1              # 3. Deploy services (5-10 min)
.\scripts\run-migrations.ps1      # 4. Setup database
.\scripts\deploy-ingress.ps1      # 5. Enable Ingress (optional)
```

## 🌐 Access URLs

### NodePort (Immediate)
```powershell
minikube ip  # Get IP
# Then open: http://<minikube-ip>:30080
```

### Ingress (Production-like)
```
1. Edit: C:\Windows\System32\drivers\etc\hosts (as Admin)
2. Add: <minikube-ip>    medilink.local
3. Open: http://medilink.local
```

### Port Forward
```powershell
kubectl port-forward -n medilink service/api-gateway 8080:8000
# Then open: http://localhost:8080
```

## 📊 Monitoring

### View Status
```powershell
kubectl get pods -n medilink              # All pods
kubectl get services -n medilink          # All services
kubectl get all -n medilink               # Everything
kubectl get pods -n medilink -w           # Watch pods
```

### View Logs
```powershell
kubectl logs -n medilink -l app=api-gateway        # Service logs
kubectl logs -f -n medilink <pod-name>             # Follow logs
kubectl logs -n medilink <pod-name> --previous     # Previous crash
```

### Dashboard
```powershell
minikube dashboard    # Open web dashboard
```

### Resource Usage
```powershell
kubectl top pods -n medilink     # Pod resources
kubectl top nodes                # Node resources
```

## 🔧 Operations

### Scale Services
```powershell
kubectl scale deployment api-gateway -n medilink --replicas=6
kubectl scale deployment api-gateway -n medilink --replicas=2
```

### Restart Service
```powershell
kubectl rollout restart deployment/api-gateway -n medilink
kubectl rollout status deployment/api-gateway -n medilink
```

### Update After Code Changes
```powershell
# Rebuild one service
cd microservices\<service-name>
& minikube -p minikube docker-env --shell powershell | Invoke-Expression
docker build -t <service-name>:latest .

# Restart deployment
kubectl rollout restart deployment/<service-name> -n medilink
```

### Delete and Redeploy
```powershell
kubectl delete namespace medilink     # Delete everything
.\scripts\deploy.ps1                  # Redeploy
.\scripts\run-migrations.ps1          # Re-run migrations
```

## 🔍 Debugging

### Check Pod Issues
```powershell
kubectl describe pod -n medilink <pod-name>
kubectl get events -n medilink
kubectl get events -n medilink --sort-by='.lastTimestamp'
```

### Execute Commands in Pod
```powershell
kubectl exec -it -n medilink <pod-name> -- /bin/bash
kubectl exec -it -n medilink <pod-name> -- python manage.py shell
```

### Test Service Communication
```powershell
kubectl exec -it -n medilink <pod-name> -- curl http://auth-service:8001/health/
```

### Check Endpoints
```powershell
kubectl get endpoints -n medilink
```

## 🛠️ Minikube Commands

### Basic Operations
```powershell
minikube start              # Start
minikube stop               # Stop (preserves data)
minikube delete             # Delete everything
minikube status             # Check status
minikube ip                 # Get IP address
```

### Addons
```powershell
minikube addons list                    # List all addons
minikube addons enable ingress          # Enable Ingress
minikube addons enable metrics-server   # Enable metrics
```

### Access Services
```powershell
minikube service list                          # List services
minikube service api-gateway -n medilink       # Open service in browser
```

### Troubleshooting
```powershell
minikube logs               # View logs
minikube ssh                # SSH into node
minikube docker-env         # Show Docker env
```

## 🔒 Ingress Commands

### Deploy/Remove
```powershell
.\scripts\deploy-ingress.ps1              # Deploy
kubectl delete -f k8s\ingress.yaml        # Remove
```

### Check Status
```powershell
kubectl get ingress -n medilink
kubectl describe ingress medilink-ingress -n medilink
kubectl get pods -n ingress-nginx
```

### View Logs
```powershell
kubectl logs -n ingress-nginx -l app.kubernetes.io/component=controller -f
```

## 🧪 Testing

### Health Checks
```powershell
# Via NodePort
curl http://<minikube-ip>:30080/health/
curl http://<minikube-ip>:30080/api/auth/health/

# Via Ingress
curl http://medilink.local/
curl http://medilink.local/api/auth/health/
curl http://medilink.local/api/doctors/health/
```

### Database Access
```powershell
kubectl exec -it -n medilink <service-pod> -- python manage.py dbshell
```

## 🚨 Common Issues

### Pods Not Starting
```powershell
# Check status
kubectl get pods -n medilink

# View details
kubectl describe pod -n medilink <pod-name>

# Check logs
kubectl logs -n medilink <pod-name>

# Solution: Rebuild images
.\scripts\build-all.ps1
```

### ImagePullBackOff
```
Cause: Image not found in Minikube
Solution: Re-run build-all.ps1
```

### CrashLoopBackOff
```
Cause: Service failing to start
Solution: Check logs, fix code, rebuild
```

### Can't Access Application
```powershell
# Try port forward instead
kubectl port-forward -n medilink service/api-gateway 8080:8000
```

### Minikube Won't Start
```powershell
# Clean restart
minikube delete
.\scripts\start-minikube.ps1
```

## 📋 Service Ports

| Service | Port | Purpose |
|---------|------|---------|
| API Gateway | 8000 | Web UI & routing |
| Auth | 8001 | Authentication |
| Doctor | 8002 | Doctor management |
| Patient | 8003 | Patient records |
| Pharmacy | 8004 | Pharmacy ops |
| Scheduling | 8005 | Appointments |
| Inventory | 8006 | Medicine stock |
| Notification | 8007 | Notifications |
| PostgreSQL | 5432 | Database |

## 🎯 Project Demo Commands

### Show Architecture
```powershell
kubectl get all -n medilink
kubectl get services -n medilink -o wide
```

### Demonstrate Scaling
```powershell
kubectl scale deployment api-gateway -n medilink --replicas=8
kubectl get pods -n medilink -w
```

### Show High Availability
```powershell
# Delete a pod
kubectl delete pod -n medilink -l app=api-gateway --force

# App still works!
curl http://medilink.local/

# Kubernetes auto-recreated it
kubectl get pods -n medilink -l app=api-gateway
```

### Show Load Balancing
```powershell
# Scale up
kubectl scale deployment api-gateway -n medilink --replicas=6

# Watch traffic distribution
kubectl logs -n ingress-nginx -l app.kubernetes.io/component=controller -f
```

### Show Monitoring
```powershell
minikube dashboard
kubectl top pods -n medilink
kubectl logs -f -n medilink -l app=api-gateway
```

## 📚 Documentation Files

- `MINIKUBE_SETUP_SUMMARY.md` - Quick overview
- `MINIKUBE_SETUP_GUIDE.md` - Detailed setup
- `INGRESS_SETUP_GUIDE.md` - Ingress configuration
- `KUBERNETES_COMPLETE_GUIDE.md` - Full reference

## 💡 Tips

1. **Use the dashboard**: `minikube dashboard` for visual monitoring
2. **Watch pods**: Add `-w` flag to watch real-time updates
3. **Follow logs**: Add `-f` flag to stream logs
4. **Quick restart**: `kubectl rollout restart` instead of delete/redeploy
5. **Save time**: Only rebuild changed services, not all 8
6. **Test locally**: Use port-forward for quick access
7. **Check health**: All services have `/health/` endpoints

## ⚡ Keyboard Shortcuts

```powershell
# Aliases you can add to your PowerShell profile
Set-Alias k kubectl
function kgp { kubectl get pods -n medilink }
function kgs { kubectl get services -n medilink }
function klog { kubectl logs -f -n medilink $args }
```

## 🎓 Success Checklist

Before presenting:
- [ ] Minikube running
- [ ] All pods in Running state
- [ ] Can access via browser
- [ ] Ingress working
- [ ] Can scale services
- [ ] Can view logs/metrics
- [ ] Know how to demo features

---

**Quick Help**: Run `.\check-prerequisites.ps1` to verify your setup!
