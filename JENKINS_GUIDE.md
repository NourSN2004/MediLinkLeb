# Jenkins CI/CD for MediLink

Complete CI/CD setup with Jenkins for the MediLink microservices application.

## Quick Start

### Deploy Jenkins

```powershell
.\deploy-jenkins.ps1
```

Or deploy with the complete setup:

```powershell
.\COMPLETE_SETUP.ps1 -IncludeJenkins
```

### Access Jenkins

**Via Ingress (recommended):**
```
http://jenkins.medilink.local
```

Add to `C:\Windows\System32\drivers\etc\hosts`:
```
127.0.0.1 jenkins.medilink.local
```

**Via Port Forward:**
```powershell
kubectl port-forward -n jenkins service/jenkins 8080:8080
```
Then open: http://localhost:8080

---

## Initial Setup

### 1. Get Admin Password

```powershell
kubectl exec -n jenkins deployment/jenkins -- cat /var/jenkins_home/secrets/initialAdminPassword
```

### 2. Configure Jenkins

Run the configuration helper:
```powershell
.\configure-jenkins.ps1
```

Or follow these steps:

1. Open Jenkins in browser
2. Enter admin password
3. Install suggested plugins
4. Create admin user
5. Install additional plugins:
   - Kubernetes Plugin
   - Docker Pipeline
   - Git Plugin

### 3. Create Pipeline Job

1. Click **"New Item"**
2. Name: `MediLink-Pipeline`
3. Type: **Pipeline**
4. Click **OK**

### 4. Configure Pipeline

**Pipeline Configuration:**
- Definition: `Pipeline script from SCM`
- SCM: `Git`
- Repository URL: Your GitHub repo URL
- Branch: `*/main` (or your branch)
- Script Path: `Jenkinsfile`

**Save** and click **"Build Now"**

---

## How It Works

### Intelligent Change Detection

The Jenkinsfile automatically detects which microservices changed:

```groovy
stage('Detect Changes') {
    // Compares current commit with previous
    // Identifies changed microservices
    // Only builds what's needed
}
```

**Examples:**

| Changed Files | Services Built |
|--------------|----------------|
| `microservices/auth-service/views.py` | `auth-service` only |
| `microservices/auth-service/`, `microservices/doctor-service/` | Both services |
| `requirements.txt` or `Dockerfile` | **All services** |
| No changes detected | **All services** (safe default) |

### Pipeline Stages

1. **Detect Changes** - Identifies which services to build
2. **Build Changed Services** - Builds Docker images using Minikube's daemon
3. **Run Tests** - Executes pytest for changed services
4. **Deploy to Kubernetes** - Updates deployments with new images
5. **Run Migrations** - Runs Django migrations if auth-service changed
6. **Verify Deployment** - Checks all pods are running

---

## Architecture

### Jenkins Deployment

```
jenkins namespace
├── jenkins deployment (1 replica)
│   ├── Jenkins LTS image
│   ├── Docker socket mount (for building)
│   └── Persistent volume (10GB)
├── ServiceAccount + RBAC
│   └── Permissions to manage medilink namespace
└── Ingress
    └── jenkins.medilink.local
```

**Resources:**
- Memory: 1Gi request, 2Gi limit
- CPU: 500m request, 1000m limit
- Storage: 10GB persistent volume

### CI/CD Flow

```
GitHub Push
    ↓
Jenkins Webhook (or manual trigger)
    ↓
Detect Changed Services
    ↓
Build Docker Images (Minikube daemon)
    ↓
Run Tests
    ↓
Update Kubernetes Deployments
    ↓
Run Migrations (if needed)
    ↓
Verify Deployment
```

---

## Usage Examples

### Manual Build

1. Go to Jenkins dashboard
2. Click on `MediLink-Pipeline`
3. Click **"Build Now"**
4. Watch console output

### View Build History

- Click on pipeline name
- See list of builds with status
- Click on build number for details

### Console Output

Shows:
- Which services were detected as changed
- Build progress for each service
- Test results
- Deployment status
- Final verification

---

## Management Commands

### View Jenkins Logs

```powershell
kubectl logs -n jenkins deployment/jenkins -f
```

### Restart Jenkins

```powershell
kubectl rollout restart deployment/jenkins -n jenkins
```

### Check Jenkins Status

```powershell
kubectl get all -n jenkins
```

### Delete Jenkins

```powershell
kubectl delete namespace jenkins
```

### Re-deploy Jenkins

```powershell
.\deploy-jenkins.ps1
```

---

## Configuration Files

### Kubernetes Resources

```
k8s/jenkins/
├── namespace.yaml              # jenkins namespace
├── jenkins-rbac.yaml          # ServiceAccount + permissions
├── jenkins-pv.yaml            # Persistent Volume
├── jenkins-pvc.yaml           # Persistent Volume Claim
├── jenkins-deployment.yaml    # Jenkins deployment
├── jenkins-service.yaml       # ClusterIP service
└── jenkins-ingress.yaml       # Ingress route
```

### Pipeline

```
Jenkinsfile                    # Main pipeline definition
```

### Scripts

```
deploy-jenkins.ps1             # Deploy Jenkins to K8s
configure-jenkins.ps1          # Configuration helper
COMPLETE_SETUP.ps1            # Full setup with -IncludeJenkins flag
```

---

## Customization

### Add More Plugins

1. Go to **Manage Jenkins** → **Manage Plugins**
2. Click **Available** tab
3. Search and select plugins
4. Click **Install without restart**

### Modify Pipeline

Edit `Jenkinsfile` to:
- Add custom build steps
- Change test commands
- Add security scanning
- Configure notifications
- Add deployment gates

### Adjust Resources

Edit `k8s/jenkins/jenkins-deployment.yaml`:

```yaml
resources:
  requests:
    memory: "2Gi"    # Increase if needed
    cpu: "1000m"
  limits:
    memory: "4Gi"
    cpu: "2000m"
```

Then apply:
```powershell
kubectl apply -f k8s/jenkins/jenkins-deployment.yaml
```

---

## Troubleshooting

### Jenkins Not Starting

**Check pod status:**
```powershell
kubectl get pods -n jenkins
kubectl describe pod -n jenkins -l app=jenkins
```

**Check logs:**
```powershell
kubectl logs -n jenkins deployment/jenkins
```

### Can't Access Jenkins

**Check Ingress:**
```powershell
kubectl get ingress -n jenkins
```

**Verify hosts file:**
```
127.0.0.1 jenkins.medilink.local
```

**Check tunnel:**
```powershell
Get-Process | Where-Object ProcessName -eq "minikube"
```

### Build Failing

**Common issues:**

1. **Docker daemon not accessible**
   - Jenkins mounts `/var/run/docker.sock`
   - Check Docker is running in Minikube

2. **Kubectl permissions**
   - Jenkins has ServiceAccount with RBAC
   - Check: `kubectl get sa -n jenkins`

3. **Git repository not accessible**
   - Add credentials in Jenkins
   - **Manage Jenkins** → **Credentials**

### Pipeline Not Detecting Changes

**Manual trigger:**
- Click **"Build Now"**
- Pipeline will build all services

**Check Git configuration:**
- Ensure repository URL is correct
- Verify branch name matches

---

## Security Best Practices

### Credentials

Store sensitive data in Jenkins credentials:
1. **Manage Jenkins** → **Credentials**
2. Add credentials (username/password, secret text, etc.)
3. Reference in Jenkinsfile:

```groovy
withCredentials([string(credentialsId: 'my-secret', variable: 'SECRET')]) {
    sh 'echo $SECRET'
}
```

### RBAC

Jenkins ServiceAccount has permissions only for:
- `medilink` namespace (deployments, pods, services)
- Read-only access to other namespaces

To restrict further, edit `k8s/jenkins/jenkins-rbac.yaml`

---

## Integration with GitHub

### Webhook Setup

1. Go to GitHub repository settings
2. Click **Webhooks** → **Add webhook**
3. Payload URL: `http://jenkins.medilink.local/github-webhook/`
4. Content type: `application/json`
5. Events: **Just the push event**
6. Save

Now Jenkins builds automatically on push!

---

## Performance Tips

### Parallel Builds

Modify Jenkinsfile to build services in parallel:

```groovy
stage('Build All Services') {
    parallel {
        stage('Auth') {
            steps { /* build auth */ }
        }
        stage('Doctor') {
            steps { /* build doctor */ }
        }
        // ... more stages
    }
}
```

### Caching

Docker layers are cached in Minikube's daemon, speeding up rebuilds.

### Resource Limits

Adjust Jenkins resources based on load:
- Small projects: 1Gi RAM
- Medium projects: 2Gi RAM
- Large projects: 4Gi+ RAM

---

## Next Steps

1. ✅ Deploy Jenkins
2. ✅ Configure pipeline
3. ✅ Test manual build
4. 🔄 Set up GitHub webhook
5. 🔄 Add automated tests
6. 🔄 Add notifications (email/Slack)
7. 🔄 Add security scanning
8. 🔄 Set up staging environment

---

## Support

For issues:
1. Check Jenkins logs: `kubectl logs -n jenkins deployment/jenkins`
2. Check pipeline console output
3. Verify Minikube is running
4. Ensure Docker daemon is accessible

**Quick health check:**
```powershell
kubectl get all -n jenkins
kubectl get all -n medilink
```
