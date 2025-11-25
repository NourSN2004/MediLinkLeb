# MediLink on Minikube - Complete Setup

This document provides a complete overview of running the MediLink microservices application on Minikube with Kubernetes.

## Quick Start (TL;DR)

```powershell
# Run everything in one command
.\quick-start-minikube.ps1
```

Or step by step:
```powershell
# 1. Start Minikube
.\scripts\start-minikube.ps1

# 2. Build Docker images
.\scripts\build-all.ps1

# 3. Deploy to Kubernetes
.\scripts\deploy.ps1

# 4. Run migrations
.\scripts\run-migrations.ps1

# 5. Deploy Ingress (optional but recommended)
.\scripts\deploy-ingress.ps1
```

Then access at: `http://<minikube-ip>:30080` or `http://medilink.local` (with Ingress)

## Prerequisites

### Required Software

1. **Docker Desktop** (https://www.docker.com/products/docker-desktop/)
   - Ensure it's running before starting Minikube
   
2. **Minikube** (https://minikube.sigs.k8s.io/docs/start/)
   - Kubernetes in a box for local development
   
3. **kubectl** (comes with Docker Desktop or Minikube)
   - Kubernetes command-line tool

### System Requirements

- **RAM**: 8GB available (12GB+ recommended)
- **CPU**: 4 cores available
- **Disk**: 20GB free space
- **OS**: Windows 10/11 with PowerShell 5.1+

## Project Structure

```
├── k8s/                          # Kubernetes manifests
│   ├── namespace.yaml            # Namespace definition
│   ├── ingress.yaml             # Ingress controller config
│   ├── configmaps/              # Configuration data
│   ├── secrets/                 # Sensitive data
│   ├── database/                # PostgreSQL deployment
│   ├── deployments/             # Service deployments
│   └── services/                # Service networking
├── microservices/               # Service source code
│   ├── api-gateway/
│   ├── auth-service/
│   ├── doctor-service/
│   ├── patient-service/
│   ├── pharmacy-service/
│   ├── scheduling-service/
│   ├── inventory-service/
│   └── notification-service/
└── scripts/                     # Automation scripts
    ├── start-minikube.ps1      # Start Minikube
    ├── build-all.ps1           # Build Docker images
    ├── deploy.ps1              # Deploy to K8s
    ├── run-migrations.ps1      # Run DB migrations
    └── deploy-ingress.ps1      # Setup Ingress
```

## Architecture

### Microservices

The application consists of 8 microservices:

| Service | Port | Purpose |
|---------|------|---------|
| **API Gateway** | 8000 | Main entry point, web UI, request routing |
| **Auth Service** | 8001 | Authentication, authorization, user management |
| **Doctor Service** | 8002 | Doctor profiles, specializations, availability |
| **Patient Service** | 8003 | Patient records, medical history |
| **Pharmacy Service** | 8004 | Pharmacy management, prescriptions |
| **Scheduling Service** | 8005 | Appointment scheduling, calendar |
| **Inventory Service** | 8006 | Medicine inventory, stock management |
| **Notification Service** | 8007 | Email/SMS notifications |

All services:
- Built with Django/Python
- Share a PostgreSQL database
- Communicate via REST APIs
- Include health check endpoints
- Support horizontal scaling

### Kubernetes Resources

- **Namespace**: `medilink` - Isolates all resources
- **Deployments**: 9 (8 services + PostgreSQL)
- **Services**: 9 (ClusterIP for services, NodePort for gateway)
- **ConfigMaps**: Application configuration
- **Secrets**: Database credentials, API keys
- **PersistentVolume**: Database storage
- **Ingress**: External access routing (optional)

## Setup Instructions

### Step 1: Start Minikube

```powershell
.\scripts\start-minikube.ps1
```

**What it does:**
- Starts Minikube with 8GB RAM and 4 CPUs
- Enables Docker driver
- Enables ingress addon
- Enables metrics-server
- Enables dashboard

**Verification:**
```powershell
minikube status
kubectl cluster-info
```

**Expected output:**
```
✓ Minikube started successfully!
Minikube IP: 192.168.49.2
```

### Step 2: Build Docker Images

```powershell
.\scripts\build-all.ps1
```

**What it does:**
- Configures shell to use Minikube's Docker daemon
- Builds Docker images for all 8 services
- Tags images as `<service-name>:latest`
- Images are stored inside Minikube (not locally)

**Build time:** ~5-10 minutes

**Verification:**
```powershell
docker images | Select-String "service|gateway"
```

**Troubleshooting:**
- Error building: Check Dockerfile syntax
- Out of space: Increase disk size or clean up Docker
- Missing files: Ensure requirements.txt exists

### Step 3: Deploy to Kubernetes

```powershell
.\scripts\deploy.ps1
```

**What it does:**
1. Creates `medilink` namespace
2. Applies secrets (DB credentials)
3. Applies configmaps (app configuration)
4. Deploys PostgreSQL with persistent storage
5. Waits for PostgreSQL to be ready
6. Deploys all 8 microservices
7. Waits for all pods to be ready

**Deployment time:** ~5-10 minutes

**Verification:**
```powershell
kubectl get pods -n medilink
kubectl get services -n medilink
```

**Expected output:**
All pods should show `Running` status with `1/1` or `4/4` ready.

### Step 4: Run Database Migrations

```powershell
.\scripts\run-migrations.ps1
```

**What it does:**
- Executes Django migrations on each service
- Creates database tables
- Sets up initial schema

**Verification:**
```powershell
kubectl logs -n medilink -l app=auth-service --tail=50
```

Look for "Applying migrations..." messages.

### Step 5: Deploy Ingress (Optional)

```powershell
.\scripts\deploy-ingress.ps1
```

**What it does:**
- Enables NGINX Ingress controller
- Deploys Ingress resource
- Configures path-based routing

**Additional setup required:**
Edit `C:\Windows\System32\drivers\etc\hosts` as Administrator:
```
192.168.49.2    medilink.local
```

**Verification:**
```powershell
kubectl get ingress -n medilink
curl http://medilink.local
```

## Accessing the Application

### Method 1: NodePort (Easiest)

Get Minikube IP:
```powershell
$ip = minikube ip
Write-Host "Access at: http://${ip}:30080"
```

Open browser to: `http://<minikube-ip>:30080`

### Method 2: Ingress (Production-like)

1. Deploy Ingress controller:
   ```powershell
   .\scripts\deploy-ingress.ps1
   ```

2. Add to hosts file (as Administrator):
   ```
   <minikube-ip>    medilink.local
   ```

3. Access at: `http://medilink.local`

### Method 3: Port Forwarding

```powershell
kubectl port-forward -n medilink service/api-gateway 8080:8000
```

Access at: `http://localhost:8080`

## Testing the Deployment

### Health Checks

Test each service is responding:

```powershell
$minikubeIp = minikube ip
$baseUrl = "http://${minikubeIp}:30080"

# Test main gateway
curl "${baseUrl}/health/"

# Test individual services (via gateway)
curl "${baseUrl}/api/auth/health/"
curl "${baseUrl}/api/doctors/health/"
curl "${baseUrl}/api/patients/health/"
curl "${baseUrl}/api/pharmacy/health/"
```

### With Ingress

```powershell
# Test main app
curl http://medilink.local/

# Test services
curl http://medilink.local/api/auth/health/
curl http://medilink.local/api/doctors/health/
curl http://medilink.local/api/patients/health/
```

### View Logs

```powershell
# All pods
kubectl get pods -n medilink

# Logs for specific service
kubectl logs -f -n medilink -l app=auth-service

# Logs for specific pod
kubectl logs -f -n medilink <pod-name>

# All recent events
kubectl get events -n medilink --sort-by='.lastTimestamp'
```

## Monitoring and Management

### Kubernetes Dashboard

```powershell
minikube dashboard
```

Opens a web-based dashboard showing:
- Pod status and logs
- Resource usage
- Deployments and services
- Events and errors

### Command-Line Monitoring

```powershell
# Watch pods in real-time
kubectl get pods -n medilink -w

# Check resource usage
kubectl top pods -n medilink
kubectl top nodes

# View all resources
kubectl get all -n medilink

# Check endpoints
kubectl get endpoints -n medilink
```

### Scaling Services

```powershell
# Scale up API Gateway
kubectl scale deployment api-gateway -n medilink --replicas=6

# Scale down
kubectl scale deployment api-gateway -n medilink --replicas=2

# View replicas
kubectl get deployment -n medilink
```

### Updating Services

After code changes:

```powershell
# Rebuild specific service
cd microservices\<service-name>
& minikube -p minikube docker-env --shell powershell | Invoke-Expression
docker build -t <service-name>:latest .

# Restart deployment
kubectl rollout restart deployment/<service-name> -n medilink

# Watch rollout
kubectl rollout status deployment/<service-name> -n medilink
```

## Troubleshooting

### Pods Not Starting

```powershell
# Check pod status
kubectl get pods -n medilink

# Describe pod (shows events)
kubectl describe pod -n medilink <pod-name>

# View logs
kubectl logs -n medilink <pod-name>
```

**Common issues:**
- `ImagePullBackOff`: Image not built correctly → Re-run `build-all.ps1`
- `CrashLoopBackOff`: Service failing to start → Check logs
- `Pending`: Insufficient resources → Reduce replicas or increase Minikube resources

### Database Connection Issues

```powershell
# Check PostgreSQL
kubectl get pods -n medilink -l app=postgres
kubectl logs -n medilink -l app=postgres

# Check database secret
kubectl get secret db-secrets -n medilink -o yaml

# Test connection from service
kubectl exec -it -n medilink <service-pod> -- python manage.py dbshell
```

### Ingress Not Working

```powershell
# Check Ingress controller
kubectl get pods -n ingress-nginx

# Check Ingress resource
kubectl describe ingress medilink-ingress -n medilink

# View controller logs
kubectl logs -n ingress-nginx -l app.kubernetes.io/component=controller

# Verify hosts file
Get-Content C:\Windows\System32\drivers\etc\hosts | Select-String "medilink"
```

### Service Communication Issues

```powershell
# Check service endpoints
kubectl get endpoints -n medilink

# Test service from another pod
kubectl exec -it -n medilink <pod-name> -- curl http://auth-service:8001/health/

# Check ConfigMap
kubectl get configmap app-config -n medilink -o yaml
```

### Clean Restart

If everything breaks:

```powershell
# Option 1: Delete namespace (keeps Minikube)
kubectl delete namespace medilink
.\scripts\deploy.ps1
.\scripts\run-migrations.ps1

# Option 2: Full reset
minikube delete
.\quick-start-minikube.ps1
```

## Advanced Topics

### Custom Configuration

Edit `k8s/configmaps/app-config.yaml` to change:
- Debug mode
- Allowed hosts
- Service URLs
- Email settings

Apply changes:
```powershell
kubectl apply -f k8s\configmaps\app-config.yaml
kubectl rollout restart deployment -n medilink --all
```

### Production-like Setup

1. **Enable TLS**:
   - Generate certificates
   - Add to Ingress configuration
   - Use `https://` URLs

2. **Add monitoring**:
   - Deploy Prometheus
   - Deploy Grafana
   - Configure alerts

3. **Add logging**:
   - Deploy ELK stack
   - Configure log aggregation
   - Set up dashboards

4. **Resource limits**:
   - Adjust CPU/memory requests
   - Set proper limits
   - Configure auto-scaling

### Multi-Environment Setup

Create separate namespaces for dev/staging/prod:

```powershell
# Create staging namespace
kubectl create namespace medilink-staging

# Deploy to staging
kubectl apply -f k8s/ -n medilink-staging
```

## Performance Optimization

### Resource Tuning

Adjust resources in deployment files:

```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "250m"
  limits:
    memory: "1Gi"
    cpu: "1000m"
```

### Database Optimization

```powershell
# Increase PostgreSQL resources
# Edit k8s/database/postgres-deployment.yaml

# Restart PostgreSQL
kubectl rollout restart statefulset postgres -n medilink
```

### Caching

Add Redis for caching:
1. Deploy Redis to cluster
2. Update service environment variables
3. Configure Django caching

## Project Demonstration Tips

For your software engineering project:

### 1. Show Architecture

```powershell
# Display all resources
kubectl get all -n medilink

# Show service mesh
kubectl get services -n medilink -o wide
```

### 2. Demonstrate Scaling

```powershell
# Scale up during "high load"
kubectl scale deployment api-gateway -n medilink --replicas=8

# Watch pods being created
kubectl get pods -n medilink -w

# Show load distribution (Ingress logs)
kubectl logs -n ingress-nginx -l app.kubernetes.io/component=controller -f
```

### 3. Demonstrate High Availability

```powershell
# Delete a pod
kubectl delete pod -n medilink -l app=api-gateway --force --grace-period=0

# Show application still works
curl http://medilink.local/

# Show Kubernetes recreated the pod
kubectl get pods -n medilink -l app=api-gateway
```

### 4. Show Monitoring

```powershell
# Open dashboard
minikube dashboard

# Show resource usage
kubectl top pods -n medilink

# Show logs in real-time
kubectl logs -f -n medilink -l app=api-gateway
```

### 5. Demonstrate Updates

```powershell
# Rolling update
kubectl set image deployment/api-gateway api-gateway=api-gateway:v2 -n medilink

# Watch rollout
kubectl rollout status deployment/api-gateway -n medilink

# Zero downtime verified
curl http://medilink.local/ # Still works during update
```

## Useful Commands Reference

### Minikube

```powershell
minikube start                  # Start Minikube
minikube stop                   # Stop Minikube
minikube delete                 # Delete Minikube
minikube status                 # Check status
minikube ip                     # Get IP address
minikube dashboard              # Open dashboard
minikube service list           # List services
minikube ssh                    # SSH into node
minikube logs                   # View logs
```

### kubectl - Pods

```powershell
kubectl get pods -n medilink                    # List pods
kubectl get pods -n medilink -w                 # Watch pods
kubectl get pods -n medilink -o wide            # Detailed view
kubectl describe pod <name> -n medilink         # Pod details
kubectl logs <pod> -n medilink                  # View logs
kubectl logs -f <pod> -n medilink               # Follow logs
kubectl logs <pod> -n medilink --previous       # Previous logs
kubectl exec -it <pod> -n medilink -- /bin/bash # Shell access
kubectl delete pod <pod> -n medilink            # Delete pod
kubectl top pods -n medilink                    # Resource usage
```

### kubectl - Deployments

```powershell
kubectl get deployments -n medilink                  # List deployments
kubectl describe deployment <name> -n medilink       # Deployment details
kubectl scale deployment <name> --replicas=3 -n medilink  # Scale
kubectl rollout restart deployment <name> -n medilink     # Restart
kubectl rollout status deployment <name> -n medilink      # Status
kubectl rollout history deployment <name> -n medilink     # History
kubectl rollout undo deployment <name> -n medilink        # Rollback
```

### kubectl - Services

```powershell
kubectl get services -n medilink              # List services
kubectl get endpoints -n medilink             # List endpoints
kubectl describe service <name> -n medilink   # Service details
kubectl port-forward service/<name> 8080:8000 -n medilink  # Port forward
```

### kubectl - General

```powershell
kubectl get all -n medilink                   # All resources
kubectl get events -n medilink                # Events
kubectl get events -n medilink --sort-by='.lastTimestamp'  # Sorted
kubectl apply -f <file>                       # Apply manifest
kubectl delete -f <file>                      # Delete manifest
kubectl get namespace                         # List namespaces
kubectl describe namespace medilink           # Namespace details
kubectl delete namespace medilink             # Delete namespace
```

## Documentation

- **MINIKUBE_SETUP_GUIDE.md** - Detailed Minikube setup instructions
- **INGRESS_SETUP_GUIDE.md** - Ingress controller configuration
- **KUBERNETES_REFERENCE.md** - Kubernetes concepts and commands
- **README.md** - Main project documentation

## Support and Resources

### Official Documentation

- Kubernetes: https://kubernetes.io/docs/
- Minikube: https://minikube.sigs.k8s.io/docs/
- kubectl: https://kubernetes.io/docs/reference/kubectl/
- Docker: https://docs.docker.com/

### Helpful Commands

```powershell
# View all documentation
Get-ChildItem *.md | Select-Object Name

# Quick help
kubectl --help
minikube --help

# Command-specific help
kubectl get --help
kubectl logs --help
```

## Success Checklist

Before presenting your project:

- [ ] Minikube is running
- [ ] All 8 services deployed
- [ ] All pods showing `Running` status
- [ ] Database migrations completed
- [ ] Application accessible via browser
- [ ] Ingress controller configured
- [ ] Can scale services up/down
- [ ] Can view logs and metrics
- [ ] Dashboard is accessible
- [ ] Know how to troubleshoot issues

## Next Steps

1. ✅ Run application on Minikube
2. ✅ Implement Ingress controller
3. 🔲 Add monitoring (Prometheus/Grafana)
4. 🔲 Add logging (ELK stack)
5. 🔲 Implement CI/CD pipeline
6. 🔲 Add automated testing
7. 🔲 Performance testing
8. 🔲 Security hardening

Good luck with your software engineering project! 🚀

## Questions?

If you encounter issues:
1. Check the logs: `kubectl logs -n medilink <pod-name>`
2. Check events: `kubectl get events -n medilink`
3. Check dashboard: `minikube dashboard`
4. Review the troubleshooting section above
5. Try a clean restart

---

**MediLink** - A microservices-based healthcare management system
