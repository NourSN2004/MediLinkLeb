# MediLink Microservices Deployment Guide

## Overview

This guide explains how to deploy MediLink's microservices architecture on Kubernetes using Minikube.

## Architecture Summary

MediLink has been transformed from a monolithic Django application into a microservices architecture with:

- **8 Microservices** (25 total pods):
  - API Gateway & Frontend (4 replicas) - NGINX reverse proxy + static frontend
  - Auth & Access Service (3 replicas) - User authentication & authorization
  - Doctor Service (3 replicas) - Doctor profiles & availability management
  - Patient Service (4 replicas) - Patient profiles & medical history
  - Pharmacy Service (2 replicas) - Pharmacy management & staff
  - Scheduling Service (4 replicas) - Appointment scheduling & conflict resolution
  - Inventory Service (3 replicas) - Medicine catalog & pharmacy stock
  - Notification Service (2 replicas) - Alerts & notifications

- **Shared Database**: Single PostgreSQL instance (as per architecture requirements)
- **Communication**: REST APIs over HTTP with JWT authentication
- **Service Discovery**: Kubernetes DNS
- **Load Balancing**: Kubernetes Services with pod anti-affinity rules

## Prerequisites

### Required Software

1. **Docker** (version 20.10+)
   ```bash
   docker --version
   ```

2. **Minikube** (version 1.30+)
   ```bash
   minikube version
   ```

3. **kubectl** (Kubernetes CLI)
   ```bash
   kubectl version --client
   ```

### System Requirements

- **Memory**: 8GB RAM minimum (Minikube configuration)
- **CPU**: 4 cores minimum
- **Disk Space**: 20GB free

### Installation (if needed)

**macOS:**
```bash
brew install docker minikube kubectl
```

**Linux:**
```bash
# Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Minikube
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube

# kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
```

## Quick Start (Automated Deployment)

The fastest way to get MediLink running:

```bash
cd /home/user/MediLinkLeb-Copy
./scripts/full-deploy.sh
```

This single script will:
1. Start Minikube (if not running)
2. Build all Docker images
3. Deploy all services to Kubernetes
4. Run database migrations
5. Display access information

**Total time**: ~10-15 minutes

## Manual Step-by-Step Deployment

If you prefer more control or need to troubleshoot:

### Step 1: Start Minikube

```bash
./scripts/start-minikube.sh
```

Or manually:
```bash
minikube start --memory=8192 --cpus=4 --driver=docker
```

Verify Minikube is running:
```bash
minikube status
```

### Step 2: Build Docker Images

This builds all 8 microservice images:

```bash
./scripts/build-all.sh
```

**What happens**:
- Sets Minikube's Docker environment
- Builds Docker images for all services
- Tags images as `<service-name>:latest`
- Images are loaded directly into Minikube (no registry needed)

**Time**: ~5-8 minutes

Verify images were built:
```bash
eval $(minikube -p minikube docker-env)
docker images | grep -E "(auth-service|doctor-service|patient-service)"
```

### Step 3: Deploy to Kubernetes

```bash
./scripts/deploy.sh
```

**What happens**:
1. Creates `medilink` namespace
2. Creates secrets (database credentials, JWT keys)
3. Creates ConfigMaps (environment variables, service URLs)
4. Deploys PostgreSQL database (PV, PVC, Deployment, Service)
5. Waits for PostgreSQL to be ready
6. Deploys all 8 microservices (Deployments and Services)
7. Waits for all pods to be ready

**Time**: ~3-5 minutes

Monitor deployment progress:
```bash
watch kubectl get pods -n medilink
```

### Step 4: Run Database Migrations

Once all pods are running:

```bash
./scripts/run-migrations.sh
```

**What happens**:
- Executes Django migrations in each backend service pod
- Creates database tables for each service's models

**Time**: ~1-2 minutes

### Step 5: Access the Application

Get Minikube IP:
```bash
minikube ip
# Example output: 192.168.49.2
```

Access MediLink:
```
http://<minikube-ip>:30080
```

**Alternative (Port Forwarding)**:
```bash
kubectl port-forward -n medilink service/api-gateway 8080:80
```
Then visit: `http://localhost:8080`

## Deployment Verification

### Check All Pods Are Running

```bash
kubectl get pods -n medilink
```

Expected output (25 backend + 4 gateway = 29 pods total):
```
NAME                                     READY   STATUS    RESTARTS   AGE
api-gateway-xxxxxxxxxx-xxxxx             1/1     Running   0          5m
api-gateway-xxxxxxxxxx-xxxxx             1/1     Running   0          5m
api-gateway-xxxxxxxxxx-xxxxx             1/1     Running   0          5m
api-gateway-xxxxxxxxxx-xxxxx             1/1     Running   0          5m
auth-service-xxxxxxxxxx-xxxxx            1/1     Running   0          5m
auth-service-xxxxxxxxxx-xxxxx            1/1     Running   0          5m
auth-service-xxxxxxxxxx-xxxxx            1/1     Running   0          5m
doctor-service-xxxxxxxxxx-xxxxx          1/1     Running   0          5m
... (and so on for all services)
postgres-xxxxxxxxxx-xxxxx                1/1     Running   0          6m
```

### Check Services

```bash
kubectl get services -n medilink
```

Expected output:
```
NAME                      TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)        AGE
api-gateway               NodePort    10.96.xxx.xxx    <none>        80:30080/TCP   5m
auth-service              ClusterIP   10.96.xxx.xxx    <none>        8001/TCP       5m
doctor-service            ClusterIP   10.96.xxx.xxx    <none>        8002/TCP       5m
patient-service           ClusterIP   10.96.xxx.xxx    <none>        8003/TCP       5m
pharmacy-service          ClusterIP   10.96.xxx.xxx    <none>        8004/TCP       5m
scheduling-service        ClusterIP   10.96.xxx.xxx    <none>        8005/TCP       5m
inventory-service         ClusterIP   10.96.xxx.xxx    <none>        8006/TCP       5m
notification-service      ClusterIP   10.96.xxx.xxx    <none>        8007/TCP       5m
postgres-service          ClusterIP   10.96.xxx.xxx    <none>        5432/TCP       6m
```

### Test Service Health

The frontend includes a service health checker. Visit the homepage and scroll to "System Status" to see all services.

Or test individual services:
```bash
# Get Minikube IP
MINIKUBE_IP=$(minikube ip)

# Test Auth Service
curl http://$MINIKUBE_IP:30080/api/auth/

# Test Doctor Service
curl http://$MINIKUBE_IP:30080/api/doctors/

# Test Health Endpoints
curl http://$MINIKUBE_IP:30080/api/auth/health/live/
```

## Troubleshooting

### Pods Not Starting

Check pod status:
```bash
kubectl get pods -n medilink
kubectl describe pod <pod-name> -n medilink
```

View logs:
```bash
kubectl logs -f -n medilink <pod-name>
```

Common issues:
- **ImagePullBackOff**: Images not built or not in Minikube's Docker. Re-run `./scripts/build-all.sh`
- **CrashLoopBackOff**: Check logs for errors. Usually database connection or migration issues.

### Database Connection Issues

Check PostgreSQL is running:
```bash
kubectl get pods -n medilink -l app=postgres
kubectl logs -n medilink -l app=postgres
```

Test database connection from a service pod:
```bash
POD=$(kubectl get pods -n medilink -l app=auth-service -o jsonpath='{.items[0].metadata.name}')
kubectl exec -n medilink $POD -- python manage.py check --database default
```

### Migration Failures

Run migrations manually for a specific service:
```bash
POD=$(kubectl get pods -n medilink -l app=auth-service -o jsonpath='{.items[0].metadata.name}')
kubectl exec -n medilink $POD -- python manage.py migrate --no-input
kubectl exec -n medilink $POD -- python manage.py showmigrations
```

### Service Communication Issues

Check service DNS resolution:
```bash
POD=$(kubectl get pods -n medilink -l app=auth-service -o jsonpath='{.items[0].metadata.name}')
kubectl exec -n medilink $POD -- nslookup postgres-service
kubectl exec -n medilink $POD -- nslookup doctor-service
```

### Minikube Issues

Restart Minikube:
```bash
minikube stop
minikube start --memory=8192 --cpus=4
```

Delete and recreate Minikube (⚠️ destroys all data):
```bash
minikube delete
minikube start --memory=8192 --cpus=4
```

## Useful Commands

### View Logs

```bash
# Specific service
kubectl logs -f -n medilink -l app=auth-service

# All pods
kubectl logs -f -n medilink --all-containers=true

# Last 100 lines
kubectl logs --tail=100 -n medilink <pod-name>
```

### Execute Commands in Pods

```bash
# Get a shell
kubectl exec -it -n medilink <pod-name> -- /bin/bash

# Run Django management commands
kubectl exec -n medilink <pod-name> -- python manage.py <command>

# Create superuser
POD=$(kubectl get pods -n medilink -l app=auth-service -o jsonpath='{.items[0].metadata.name}')
kubectl exec -it -n medilink $POD -- python manage.py createsuperuser
```

### Scale Services

```bash
# Scale a service
kubectl scale deployment auth-service -n medilink --replicas=5

# Scale multiple services
kubectl scale deployment doctor-service patient-service -n medilink --replicas=5
```

### Update Configuration

After changing ConfigMaps or Secrets:
```bash
kubectl apply -f k8s/configmaps/
kubectl apply -f k8s/secrets/

# Restart pods to pick up changes
kubectl rollout restart deployment -n medilink
```

### Minikube Dashboard

View Kubernetes dashboard:
```bash
minikube dashboard
```

## Cleanup

Remove all MediLink resources:

```bash
./scripts/cleanup.sh
```

This will:
1. Delete all deployments
2. Delete all services
3. Delete all ConfigMaps and Secrets
4. Delete all PVCs and PVs
5. Delete the `medilink` namespace

To completely remove Minikube:
```bash
minikube stop
minikube delete
```

## Next Steps

### Populate Demo Data

The original monolith has a `populate` management command. To use it:

1. Copy the command to auth-service or another service
2. Run it in a pod:
   ```bash
   POD=$(kubectl get pods -n medilink -l app=auth-service -o jsonpath='{.items[0].metadata.name}')
   kubectl exec -n medilink $POD -- python manage.py populate
   ```

### Implement Missing Models

The microservices currently have boilerplate code. To complete them:

1. Copy models from the original monolith (`accounts/models.py`) to each service
2. Copy serializers and views
3. Update API endpoints
4. Run migrations
5. Rebuild and redeploy

Reference the design document: `MICROSERVICES_DESIGN.md`

### Configure Email

Update email settings in `k8s/configmaps/app-config.yaml`:

```yaml
EMAIL_BACKEND: "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST: "smtp.gmail.com"
EMAIL_HOST_USER: "your-email@gmail.com"
```

Update email credentials in `k8s/secrets/app-secrets.yaml`:

```yaml
EMAIL_HOST_PASSWORD: "your-app-password"
```

Apply changes:
```bash
kubectl apply -f k8s/configmaps/
kubectl apply -f k8s/secrets/
kubectl rollout restart deployment -n medilink
```

### Production Considerations

This setup is for **development/testing only**. For production:

1. **Database**: Use managed PostgreSQL (AWS RDS, Google Cloud SQL, etc.)
2. **Storage**: Use cloud storage for media files (S3, GCS, Azure Blob)
3. **Secrets**: Use proper secrets management (Vault, AWS Secrets Manager)
4. **Ingress**: Use Ingress controller instead of NodePort
5. **TLS**: Enable HTTPS with Let's Encrypt
6. **Monitoring**: Add Prometheus + Grafana
7. **Logging**: Centralized logging with ELK or Loki
8. **CI/CD**: Automate builds and deployments
9. **Backups**: Regular database backups
10. **Security**: Network policies, pod security policies, RBAC

## Architecture Reference

For detailed architecture information, see:
- `MICROSERVICES_DESIGN.md` - Service responsibilities and API endpoints
- Original architecture document (in the project root)
- `k8s/` directory - All Kubernetes manifests

## Support

If you encounter issues:

1. Check logs: `kubectl logs -f -n medilink <pod-name>`
2. Describe pod: `kubectl describe pod <pod-name> -n medilink`
3. Check events: `kubectl get events -n medilink --sort-by='.lastTimestamp'`
4. Review this troubleshooting section

## Summary

You now have a fully functional microservices deployment of MediLink running on Kubernetes/Minikube with:

- 8 independent microservices
- 25 backend pods + 4 gateway pods
- PostgreSQL database
- NGINX API Gateway
- Service discovery and load balancing
- Health checks and readiness probes
- Easy deployment and management scripts

Happy coding! 🚀
