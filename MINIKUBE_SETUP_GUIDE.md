# MediLink Minikube Setup Guide

This guide will help you run the MediLink application on Minikube, simulating a Kubernetes environment for your software engineering project.

## Prerequisites

Before starting, ensure you have the following installed:

1. **Docker Desktop** - Download from https://www.docker.com/products/docker-desktop/
   - Make sure Docker is running before proceeding
   
2. **Minikube** - Download from https://minikube.sigs.k8s.io/docs/start/
   - Follow the Windows installation instructions
   
3. **kubectl** - Usually comes with Docker Desktop or Minikube
   - Verify with: `kubectl version --client`

## Quick Start

Run these commands in PowerShell from the project root directory:

```powershell
# 1. Start Minikube
.\scripts\start-minikube.ps1

# 2. Build Docker images
.\scripts\build-all.ps1

# 3. Deploy to Kubernetes
.\scripts\deploy.ps1

# 4. Run database migrations
.\scripts\run-migrations.ps1
```

## Detailed Steps

### Step 1: Start Minikube

```powershell
.\scripts\start-minikube.ps1
```

This script will:
- Start Minikube with 8GB RAM and 4 CPUs
- Enable required addons (ingress, metrics-server, dashboard)
- Configure Docker driver
- Display the Minikube IP address

**Expected Output:**
```
✓ Minikube started successfully!
Minikube IP: 192.168.49.2
```

**Troubleshooting:**
- If Minikube fails to start, try: `minikube delete` then run the script again
- Ensure Docker Desktop is running
- Check you have enough system resources (8GB RAM available)

### Step 2: Build Docker Images

```powershell
.\scripts\build-all.ps1
```

This script will:
- Configure your terminal to use Minikube's Docker daemon
- Build Docker images for all 8 microservices
- Tag images appropriately for Kubernetes deployment

**Expected Output:**
```
✓ auth-service built successfully
✓ doctor-service built successfully
...
All images built successfully!
```

**Build Time:** Approximately 5-10 minutes depending on your system

**Troubleshooting:**
- If a service fails to build, check the Dockerfile in `microservices/<service-name>/`
- Ensure all requirements.txt files are present
- Check Docker Desktop has enough disk space

### Step 3: Deploy to Kubernetes

```powershell
.\scripts\deploy.ps1
```

This script will:
1. Create the `medilink` namespace
2. Apply secrets and configmaps
3. Deploy PostgreSQL database
4. Deploy all 8 microservices
5. Wait for pods to be ready

**Expected Output:**
```
✓ Namespace created
✓ Secrets and ConfigMaps created
✓ PostgreSQL deployed
✓ PostgreSQL is ready
✓ Microservices deployed
Deployment Complete!
```

**Deployment Time:** Approximately 5-10 minutes

**Verify Deployment:**
```powershell
kubectl get pods -n medilink
```

All pods should show `Running` status with `1/1` or `4/4` ready containers.

### Step 4: Run Database Migrations

```powershell
.\scripts\run-migrations.ps1
```

This script will:
- Execute Django migrations on each service
- Create database tables and schema
- Populate initial data if configured

**Expected Output:**
```
✓ Migrations completed for auth-service
✓ Migrations completed for doctor-service
...
Your application is now ready to use!
```

## Accessing the Application

### Method 1: NodePort (Recommended)

Get your Minikube IP:
```powershell
minikube ip
```

Access the application at: `http://<MINIKUBE-IP>:30080`

Example: `http://192.168.49.2:30080`

### Method 2: Port Forwarding

In a separate PowerShell window:
```powershell
kubectl port-forward -n medilink service/api-gateway 8080:8000
```

Then access: `http://localhost:8080`

### Method 3: Minikube Service Command

```powershell
minikube service api-gateway -n medilink
```

This will automatically open your browser to the correct URL.

## Useful Commands

### Monitoring

```powershell
# View all pods
kubectl get pods -n medilink

# Watch pods in real-time
kubectl get pods -n medilink -w

# View services
kubectl get services -n medilink

# View logs for a specific service
kubectl logs -f -n medilink -l app=auth-service

# View logs for a specific pod
kubectl logs -f -n medilink <pod-name>

# Open Kubernetes dashboard
minikube dashboard
```

### Debugging

```powershell
# Describe a pod (shows events and errors)
kubectl describe pod -n medilink <pod-name>

# Execute commands in a pod
kubectl exec -it -n medilink <pod-name> -- /bin/bash

# Check pod resource usage
kubectl top pods -n medilink
```

### Management

```powershell
# Restart a deployment
kubectl rollout restart deployment/<service-name> -n medilink

# Scale a deployment
kubectl scale deployment/<service-name> -n medilink --replicas=2

# Delete all resources
kubectl delete namespace medilink

# Stop Minikube (preserves state)
minikube stop

# Start Minikube again
minikube start

# Completely remove Minikube
minikube delete
```

## Architecture Overview

The application consists of 8 microservices:

1. **auth-service** (Port 8001) - Authentication and authorization
2. **doctor-service** (Port 8002) - Doctor management
3. **patient-service** (Port 8003) - Patient management
4. **pharmacy-service** (Port 8004) - Pharmacy operations
5. **scheduling-service** (Port 8005) - Appointment scheduling
6. **inventory-service** (Port 8006) - Medicine inventory
7. **notification-service** (Port 8007) - Notifications
8. **api-gateway** (Port 8000) - Main entry point & web interface

All services share a PostgreSQL database and communicate via internal Kubernetes services.

## Next Steps: Ingress Controller

After successfully running the application, you can implement an Ingress controller for better routing. See `INGRESS_SETUP.md` for details.

## Troubleshooting

### Pods Not Starting

```powershell
# Check pod status
kubectl get pods -n medilink

# Check events
kubectl get events -n medilink --sort-by='.lastTimestamp'

# Describe failing pod
kubectl describe pod -n medilink <pod-name>
```

Common issues:
- **ImagePullBackOff**: Images weren't built correctly. Re-run `.\scripts\build-all.ps1`
- **CrashLoopBackOff**: Service is failing to start. Check logs with `kubectl logs`
- **Pending**: Insufficient resources. Try reducing replicas in deployment files

### Database Connection Issues

```powershell
# Check PostgreSQL status
kubectl get pods -n medilink -l app=postgres

# View PostgreSQL logs
kubectl logs -n medilink -l app=postgres

# Test database connection from a service
kubectl exec -it -n medilink <service-pod> -- python manage.py dbshell
```

### Resource Issues

```powershell
# Check Minikube resources
minikube status

# Increase resources (requires restart)
minikube delete
minikube start --memory=10240 --cpus=6
```

### Clean Restart

If things go wrong, start fresh:

```powershell
# Delete everything
kubectl delete namespace medilink
minikube stop
minikube delete

# Start over
.\scripts\start-minikube.ps1
.\scripts\build-all.ps1
.\scripts\deploy.ps1
.\scripts\run-migrations.ps1
```

## Configuration Files

### Kubernetes Manifests

- `k8s/namespace.yaml` - Namespace definition
- `k8s/configmaps/` - Configuration data
- `k8s/secrets/` - Sensitive data (passwords, keys)
- `k8s/database/` - PostgreSQL deployment
- `k8s/deployments/` - Service deployments
- `k8s/services/` - Service networking

### Docker

- `docker-compose.yml` - Docker Compose reference
- `microservices/*/Dockerfile` - Service Docker images

## Performance Tips

1. **Build Once**: Docker images persist in Minikube. You only need to rebuild when code changes.

2. **Parallel Builds**: The build script builds services sequentially. For faster builds, you could modify it to build in parallel.

3. **Resource Allocation**: Adjust deployment replicas based on your system:
   ```powershell
   kubectl scale deployment/api-gateway -n medilink --replicas=2
   ```

4. **Persistent Data**: Database data is stored in Persistent Volumes and survives pod restarts.

## Development Workflow

1. Make code changes to a service
2. Rebuild only that service:
   ```powershell
   cd microservices/<service-name>
   & minikube -p minikube docker-env --shell powershell | Invoke-Expression
   docker build -t <service-name>:latest .
   ```
3. Restart the deployment:
   ```powershell
   kubectl rollout restart deployment/<service-name> -n medilink
   ```
4. Watch logs for errors:
   ```powershell
   kubectl logs -f -n medilink -l app=<service-name>
   ```

## Project Demonstration Tips

For your software engineering project presentation:

1. **Show the Architecture**:
   ```powershell
   kubectl get all -n medilink
   ```

2. **Demonstrate Scaling**:
   ```powershell
   kubectl scale deployment/api-gateway -n medilink --replicas=6
   kubectl get pods -n medilink -w
   ```

3. **Show Health Checks**:
   ```powershell
   kubectl describe pod -n medilink <pod-name> | Select-String -Pattern "Liveness|Readiness"
   ```

4. **Monitor Resources**:
   ```powershell
   kubectl top pods -n medilink
   kubectl top nodes
   ```

5. **Use the Dashboard**:
   ```powershell
   minikube dashboard
   ```

## Support

If you encounter issues:
1. Check the logs: `kubectl logs -f -n medilink <pod-name>`
2. Check events: `kubectl get events -n medilink`
3. Review the Kubernetes dashboard: `minikube dashboard`
4. Verify Docker is running: `docker ps`
5. Check Minikube status: `minikube status`

## Success Checklist

- [ ] Minikube started successfully
- [ ] All 8 Docker images built
- [ ] All pods showing `Running` status
- [ ] Database migrations completed
- [ ] Application accessible via browser
- [ ] All services returning healthy status

Good luck with your project! 🚀
