# MediLink Ingress Controller Setup Guide

This guide explains how to set up and configure an Ingress controller for the MediLink application running on Minikube.

## What is an Ingress Controller?

An Ingress controller is a Kubernetes resource that manages external access to services within a cluster. It provides:

- **Single Entry Point**: One IP/domain for all services
- **Path-based Routing**: Route requests based on URL paths
- **Load Balancing**: Distribute traffic across multiple pods
- **SSL/TLS Termination**: Handle HTTPS certificates
- **Name-based Virtual Hosting**: Multiple domains on one IP

## Prerequisites

Ensure your application is running on Minikube:
```powershell
kubectl get pods -n medilink
```

All pods should be in `Running` status.

## Step 1: Enable Ingress Addon

Minikube includes an NGINX Ingress controller addon:

```powershell
minikube addons enable ingress
```

Verify the ingress controller is running:
```powershell
kubectl get pods -n ingress-nginx
```

You should see pods like:
- `ingress-nginx-controller-xxxxx`
- `ingress-nginx-admission-create-xxxxx`
- `ingress-nginx-admission-patch-xxxxx`

**Wait for the controller to be ready** (may take 1-2 minutes):
```powershell
kubectl wait --namespace ingress-nginx `
  --for=condition=ready pod `
  --selector=app.kubernetes.io/component=controller `
  --timeout=120s
```

## Step 2: Update Service Types

The Ingress controller will route traffic to services, so we need to change the API Gateway service from `NodePort` to `ClusterIP`.

Check current services:
```powershell
kubectl get services -n medilink
```

The API Gateway should already be accessible internally. No changes needed if other services are already `ClusterIP`.

## Step 3: Deploy Ingress Resource

Apply the Ingress configuration:
```powershell
kubectl apply -f k8s\ingress.yaml
```

Verify the Ingress was created:
```powershell
kubectl get ingress -n medilink
```

You should see output like:
```
NAME               CLASS   HOSTS            ADDRESS        PORTS   AGE
medilink-ingress   nginx   medilink.local   192.168.49.2   80      10s
```

Check Ingress details:
```powershell
kubectl describe ingress medilink-ingress -n medilink
```

## Step 4: Configure Local DNS

### Option A: Edit Hosts File (Recommended for Testing)

1. **Open Notepad as Administrator**:
   - Right-click Notepad → "Run as administrator"

2. **Open the hosts file**:
   - File → Open
   - Navigate to: `C:\Windows\System32\drivers\etc\hosts`
   - Change file filter to "All Files (*.*)"

3. **Add this line** (replace with your Minikube IP):
   ```
   192.168.49.2    medilink.local
   ```

4. **Save and close**

Get your Minikube IP:
```powershell
minikube ip
```

### Option B: Use nip.io (No hosts file editing)

Instead of `medilink.local`, you can use `medilink.<MINIKUBE-IP>.nip.io`.

For example, if Minikube IP is `192.168.49.2`:
- URL becomes: `http://medilink.192.168.49.2.nip.io`

To use this approach, update the Ingress:
```powershell
$minikubeIp = minikube ip
kubectl patch ingress medilink-ingress -n medilink --type=json -p="[{`"op`": `"replace`", `"path`": `"/spec/rules/0/host`", `"value`": `"medilink.$minikubeIp.nip.io`"}]"
```

## Step 5: Access the Application

### Via Ingress (Recommended)

Open your browser and navigate to:
```
http://medilink.local
```

or if using nip.io:
```
http://medilink.<MINIKUBE-IP>.nip.io
```

### Via Minikube Tunnel (Alternative)

In a separate PowerShell window (keep it running):
```powershell
minikube tunnel
```

This creates a route to services with LoadBalancer type. Access via:
```
http://medilink.local
```

## Understanding the Ingress Configuration

The `k8s/ingress.yaml` file defines routing rules:

```yaml
spec:
  rules:
  - host: medilink.local
    http:
      paths:
      - path: /                    # Main application
        backend:
          service:
            name: api-gateway
            port: 8000
      
      - path: /api/auth           # Authentication API
        backend:
          service:
            name: auth-service
            port: 8001
      
      - path: /api/doctors        # Doctor management API
        backend:
          service:
            name: doctor-service
            port: 8002
      # ... more services
```

### Routing Logic

- `http://medilink.local/` → API Gateway (main UI)
- `http://medilink.local/api/auth/...` → Auth Service
- `http://medilink.local/api/doctors/...` → Doctor Service
- `http://medilink.local/api/patients/...` → Patient Service
- And so on...

## Testing the Ingress

### 1. Test Main Application
```powershell
curl http://medilink.local
```

### 2. Test Individual Services
```powershell
# Test auth service
curl http://medilink.local/api/auth/health/

# Test doctor service
curl http://medilink.local/api/doctors/health/

# Test patient service
curl http://medilink.local/api/patients/health/
```

### 3. View Ingress Logs
```powershell
kubectl logs -n ingress-nginx -l app.kubernetes.io/component=controller --tail=50 -f
```

### 4. Check Backend Connections
```powershell
kubectl get ingress medilink-ingress -n medilink -o yaml
```

## Advanced Configuration

### Adding SSL/TLS (HTTPS)

1. **Create a self-signed certificate** (for development):
```powershell
# Generate certificate
openssl req -x509 -nodes -days 365 -newkey rsa:2048 `
  -keyout medilink.key -out medilink.crt `
  -subj "/CN=medilink.local/O=MediLink"

# Create Kubernetes secret
kubectl create secret tls medilink-tls `
  --key medilink.key `
  --cert medilink.crt `
  -n medilink
```

2. **Update Ingress to use TLS**:
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: medilink-ingress
  namespace: medilink
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - medilink.local
    secretName: medilink-tls
  rules:
  - host: medilink.local
    # ... rest of configuration
```

3. **Apply the changes**:
```powershell
kubectl apply -f k8s\ingress.yaml
```

4. **Access via HTTPS**:
```
https://medilink.local
```

### Load Balancing

The Ingress controller automatically load balances across multiple pod replicas.

Scale the API Gateway:
```powershell
kubectl scale deployment api-gateway -n medilink --replicas=4
```

Watch the load distribution in Ingress logs:
```powershell
kubectl logs -n ingress-nginx -l app.kubernetes.io/component=controller -f
```

### Rate Limiting

Add rate limiting to prevent abuse:

```yaml
metadata:
  annotations:
    nginx.ingress.kubernetes.io/limit-rps: "10"
    nginx.ingress.kubernetes.io/limit-connections: "5"
```

### Request Size Limits

Already configured in the Ingress file:
```yaml
nginx.ingress.kubernetes.io/proxy-body-size: "50m"
```

This allows uploads up to 50MB.

### Custom Error Pages

Add custom error pages:
```yaml
metadata:
  annotations:
    nginx.ingress.kubernetes.io/custom-http-errors: "404,503"
    nginx.ingress.kubernetes.io/default-backend: custom-error-pages
```

## Monitoring and Debugging

### View Ingress Events
```powershell
kubectl get events -n medilink --field-selector involvedObject.name=medilink-ingress
```

### Check Ingress Controller Status
```powershell
kubectl get pods -n ingress-nginx
kubectl logs -n ingress-nginx -l app.kubernetes.io/component=controller
```

### Validate Ingress Configuration
```powershell
kubectl describe ingress medilink-ingress -n medilink
```

Look for:
- **Rules**: Should list all your paths
- **Backends**: Should show healthy endpoints
- **Events**: Should not show errors

### Test Backend Health
```powershell
kubectl get endpoints -n medilink
```

All services should have IP addresses listed.

### Common Issues

#### 1. 404 Not Found
**Cause**: Path routing misconfigured or service not ready

**Solution**:
```powershell
# Check service endpoints
kubectl get endpoints -n medilink api-gateway

# Check Ingress rules
kubectl describe ingress medilink-ingress -n medilink

# View controller logs
kubectl logs -n ingress-nginx -l app.kubernetes.io/component=controller --tail=50
```

#### 2. 502 Bad Gateway
**Cause**: Backend service is down or not responding

**Solution**:
```powershell
# Check pod status
kubectl get pods -n medilink

# Check pod logs
kubectl logs -n medilink -l app=api-gateway

# Restart deployment
kubectl rollout restart deployment/api-gateway -n medilink
```

#### 3. 503 Service Temporarily Unavailable
**Cause**: No healthy backends available

**Solution**:
```powershell
# Check readiness probes
kubectl describe pod -n medilink <pod-name>

# Check service endpoints
kubectl get endpoints -n medilink
```

#### 4. DNS Not Resolving
**Cause**: Hosts file not updated correctly

**Solution**:
- Verify hosts file entry: `C:\Windows\System32\drivers\etc\hosts`
- Try using IP directly: `http://<MINIKUBE-IP>:30080`
- Use nip.io instead: `http://medilink.<MINIKUBE-IP>.nip.io`

## Cleanup Script

Create a script to apply/remove Ingress:

**deploy-ingress.ps1**:
```powershell
kubectl apply -f k8s\ingress.yaml
Write-Host "Ingress deployed successfully!" -ForegroundColor Green
Write-Host "Access at: http://medilink.local" -ForegroundColor Cyan
```

**remove-ingress.ps1**:
```powershell
kubectl delete -f k8s\ingress.yaml
Write-Host "Ingress removed!" -ForegroundColor Yellow
```

## Production Considerations

For a production environment, consider:

1. **Real Domain**: Register a domain and point it to your cluster
2. **TLS Certificates**: Use Let's Encrypt with cert-manager
3. **Authentication**: Add OAuth2 proxy or similar
4. **Rate Limiting**: Implement proper rate limiting
5. **DDoS Protection**: Use Cloudflare or similar CDN
6. **Monitoring**: Set up Prometheus and Grafana
7. **WAF**: Web Application Firewall for security

## Architecture Diagram

```
Internet
   |
   v
[Ingress Controller (NGINX)]
   |
   +-- / -----------------> [API Gateway Service] -> [API Gateway Pods]
   |
   +-- /api/auth ---------> [Auth Service] -----> [Auth Pods]
   |
   +-- /api/doctors ------> [Doctor Service] ---> [Doctor Pods]
   |
   +-- /api/patients -----> [Patient Service] --> [Patient Pods]
   |
   +-- /api/pharmacy -----> [Pharmacy Service] -> [Pharmacy Pods]
   |
   +-- /api/scheduling ---> [Scheduling Service] -> [Scheduling Pods]
   |
   +-- /api/inventory ----> [Inventory Service] -> [Inventory Pods]
   |
   +-- /api/notifications -> [Notification Service] -> [Notification Pods]
   |
   All Services
   |
   v
[PostgreSQL Database]
```

## Comparison: NodePort vs Ingress

| Feature | NodePort | Ingress |
|---------|----------|---------|
| **Access** | `http://<IP>:30080` | `http://medilink.local` |
| **Ports** | One per service | Single entry point |
| **SSL** | Manual setup | Built-in support |
| **Path Routing** | No | Yes |
| **Load Balancing** | Basic | Advanced |
| **Production Ready** | No | Yes |

## Project Demonstration

For your software engineering project, showcase:

1. **Show Ingress Configuration**:
   ```powershell
   kubectl get ingress -n medilink
   kubectl describe ingress medilink-ingress -n medilink
   ```

2. **Demonstrate Path Routing**:
   - Open `http://medilink.local` (main app)
   - Show `http://medilink.local/api/auth/health/` (auth service)
   - Show `http://medilink.local/api/doctors/health/` (doctor service)

3. **Show Load Balancing**:
   ```powershell
   # Scale up
   kubectl scale deployment api-gateway -n medilink --replicas=6
   
   # Watch traffic distribution
   kubectl logs -n ingress-nginx -l app.kubernetes.io/component=controller -f
   ```

4. **Demonstrate High Availability**:
   ```powershell
   # Delete a pod
   kubectl delete pod -n medilink -l app=api-gateway --force --grace-period=0
   
   # Show application still works (Ingress routes to other pods)
   curl http://medilink.local/health/
   ```

## Success Checklist

- [ ] Ingress addon enabled in Minikube
- [ ] Ingress controller running in `ingress-nginx` namespace
- [ ] Ingress resource created in `medilink` namespace
- [ ] Hosts file updated with `medilink.local`
- [ ] Application accessible via `http://medilink.local`
- [ ] All service paths working (`/api/auth`, `/api/doctors`, etc.)
- [ ] Load balancing working across multiple pods

## Next Steps

After setting up Ingress:
1. Add SSL/TLS certificates
2. Implement authentication at Ingress level
3. Set up monitoring with Prometheus
4. Add rate limiting
5. Configure caching headers
6. Set up logging aggregation

## Useful Commands Reference

```powershell
# Deploy Ingress
kubectl apply -f k8s\ingress.yaml

# View Ingress
kubectl get ingress -n medilink

# Describe Ingress
kubectl describe ingress medilink-ingress -n medilink

# View Ingress controller logs
kubectl logs -n ingress-nginx -l app.kubernetes.io/component=controller -f

# Delete Ingress
kubectl delete -f k8s\ingress.yaml

# Get Minikube IP
minikube ip

# Enable Ingress addon
minikube addons enable ingress

# Disable Ingress addon
minikube addons disable ingress

# Test from command line
curl http://medilink.local
curl http://medilink.local/api/auth/health/
```

Good luck with your Ingress implementation! 🚀
