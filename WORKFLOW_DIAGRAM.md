# MediLink CI/CD Workflow Diagrams

---

## 🎯 Complete Development Workflow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    DEVELOPER WORKFLOW                                │
└─────────────────────────────────────────────────────────────────────┘

1. MAKE CHANGES
   ┌──────────────────┐
   │  Edit Code       │
   │  microservices/  │
   │  auth-service/   │
   │  views.py        │
   └────────┬─────────┘
            │
            ↓
2. COMMIT & PUSH
   ┌──────────────────┐
   │  git add .       │
   │  git commit      │
   │  git push        │
   └────────┬─────────┘
            │
            ↓
   ┌────────────────────────────────────┐
   │          GITHUB                    │
   │  Repository: NourSN2004/MediLinkLeb│
   │  Branch: complete-kubernetes-jenkins│
   └────────┬───────────────────────────┘
            │
            ↓
3. JENKINS (3 options)
   ┌─────────────────────────────────────┐
   │ A. Manual: Click "Build Now"        │
   │ B. Polling: Auto-check every 5 min  │
   │ C. Webhook: Instant (needs public)  │
   └────────┬────────────────────────────┘
            │
            ↓
   ┌────────────────────────────────────────────────────┐
   │          JENKINS PIPELINE STAGES                   │
   │                                                    │
   │  ┌──────────────────────────────────────────┐    │
   │  │ 1. Detect Changes                        │    │
   │  │    - Compare with previous commit        │    │
   │  │    - Identify changed services           │    │
   │  │    → auth-service changed                │    │
   │  └──────────────────────────────────────────┘    │
   │                    ↓                              │
   │  ┌──────────────────────────────────────────┐    │
   │  │ 2. Build Changed Services                │    │
   │  │    - cd microservices/auth-service       │    │
   │  │    - docker build -t auth:62f2538        │    │
   │  │    - docker tag auth:62f2538 auth:latest │    │
   │  │    ✅ Image created                       │    │
   │  └──────────────────────────────────────────┘    │
   │                    ↓                              │
   │  ┌──────────────────────────────────────────┐    │
   │  │ 3. Run Tests                             │    │
   │  │    - pytest tests/ (if exists)           │    │
   │  │    ✅ Tests passed                        │    │
   │  └──────────────────────────────────────────┘    │
   │                    ↓                              │
   │  ┌──────────────────────────────────────────┐    │
   │  │ 4. Deploy to Kubernetes                  │    │
   │  │    - kubectl set image deployment/auth   │    │
   │  │    - Rolling update                      │    │
   │  │    ✅ Deployment updated                  │    │
   │  └──────────────────────────────────────────┘    │
   │                    ↓                              │
   │  ┌──────────────────────────────────────────┐    │
   │  │ 5. Run Migrations (if auth changed)      │    │
   │  │    - kubectl exec auth-pod               │    │
   │  │    - python manage.py migrate            │    │
   │  │    ✅ Migrations applied                  │    │
   │  └──────────────────────────────────────────┘    │
   │                    ↓                              │
   │  ┌──────────────────────────────────────────┐    │
   │  │ 6. Verify Deployment                     │    │
   │  │    - kubectl get pods                    │    │
   │  │    - kubectl get ingress                 │    │
   │  │    ✅ All pods running                    │    │
   │  └──────────────────────────────────────────┘    │
   │                                                    │
   │  ✅ BUILD SUCCESS                                  │
   └────────┬───────────────────────────────────────────┘
            │
            ↓
4. KUBERNETES UPDATES
   ┌────────────────────────────────────────┐
   │  Medilink Namespace                    │
   │                                        │
   │  auth-service deployment               │
   │  ├─ Old pod (terminating) ⚠️           │
   │  ├─ New pod #1 ✅ Running              │
   │  ├─ New pod #2 ✅ Running              │
   │  └─ New pod #3 ✅ Running              │
   │                                        │
   │  Zero downtime rolling update! 🎉      │
   └────────┬───────────────────────────────┘
            │
            ↓
5. TEST CHANGES
   ┌──────────────────────────────┐
   │  Open: http://medilink.local │
   │  Test: New feature works!    │
   │  ✅ Deployment successful     │
   └──────────────────────────────┘
```

---

## 🔄 Change Detection Logic

```
Jenkins Checks Git Diff
         │
         ↓
┌────────────────────────────────────────────┐
│  What changed?                             │
└────────────────────────────────────────────┘
         │
         ├─→ microservices/auth-service/views.py
         │   └─→ Build: auth-service only ✅
         │
         ├─→ microservices/auth-service/models.py
         │   microservices/doctor-service/views.py
         │   └─→ Build: auth + doctor services ✅
         │
         ├─→ requirements.txt
         │   └─→ Build: ALL 8 services ✅ (shared dependency)
         │
         ├─→ Dockerfile (root)
         │   └─→ Build: ALL 8 services ✅ (affects all)
         │
         └─→ No changes detected
             └─→ Build: ALL 8 services ✅ (safe default)
```

---

## 🏗️ Kubernetes Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                      YOUR WINDOWS MACHINE                            │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │                     MINIKUBE                                │    │
│  │                                                             │    │
│  │  ┌───────────────────────────────────────────────────┐     │    │
│  │  │          medilink namespace                       │     │    │
│  │  │                                                    │     │    │
│  │  │  ┌──────────────┐  ┌──────────────┐              │     │    │
│  │  │  │ PostgreSQL   │  │ Auth Service │              │     │    │
│  │  │  │              │  │ (3 pods)     │              │     │    │
│  │  │  │ 1 pod        │  └──────────────┘              │     │    │
│  │  │  └──────────────┘                                 │     │    │
│  │  │                                                    │     │    │
│  │  │  ┌──────────────┐  ┌──────────────┐              │     │    │
│  │  │  │ Doctor       │  │ Patient      │              │     │    │
│  │  │  │ Service      │  │ Service      │              │     │    │
│  │  │  │ (3 pods)     │  │ (4 pods)     │              │     │    │
│  │  │  └──────────────┘  └──────────────┘              │     │    │
│  │  │                                                    │     │    │
│  │  │  ┌──────────────┐  ┌──────────────┐              │     │    │
│  │  │  │ Pharmacy     │  │ Scheduling   │              │     │    │
│  │  │  │ Service      │  │ Service      │              │     │    │
│  │  │  │ (2 pods)     │  │ (4 pods)     │              │     │    │
│  │  │  └──────────────┘  └──────────────┘              │     │    │
│  │  │                                                    │     │    │
│  │  │  ┌──────────────┐  ┌──────────────┐              │     │    │
│  │  │  │ Inventory    │  │ Notification │              │     │    │
│  │  │  │ Service      │  │ Service      │              │     │    │
│  │  │  │ (3 pods)     │  │ (2 pods)     │              │     │    │
│  │  │  └──────────────┘  └──────────────┘              │     │    │
│  │  │                                                    │     │    │
│  │  │  ┌──────────────────────────────┐                │     │    │
│  │  │  │ API Gateway (4 pods)         │                │     │    │
│  │  │  │ - Routes requests            │                │     │    │
│  │  │  │ - Load balancing             │                │     │    │
│  │  │  └──────────────────────────────┘                │     │    │
│  │  │                                                    │     │    │
│  │  │  Total: 26 pods                                   │     │    │
│  │  └────────────────────────────────────────────────────┘     │    │
│  │                                                             │    │
│  │  ┌───────────────────────────────────────────────────┐     │    │
│  │  │          jenkins namespace                        │     │    │
│  │  │                                                    │     │    │
│  │  │  ┌──────────────────────────────────────────┐    │     │    │
│  │  │  │ Jenkins (1 pod)                          │    │     │    │
│  │  │  │                                          │    │     │    │
│  │  │  │  ┌────────────────────────────────┐     │    │     │    │
│  │  │  │  │ Capabilities:                  │     │    │     │    │
│  │  │  │  │ ✅ Docker CLI                   │     │    │     │    │
│  │  │  │  │ ✅ kubectl                      │     │    │     │    │
│  │  │  │  │ ✅ Git                          │     │    │     │    │
│  │  │  │  │ ✅ Access to Docker socket     │     │    │     │    │
│  │  │  │  │ ✅ RBAC to deploy to medilink  │     │    │     │    │
│  │  │  │  └────────────────────────────────┘     │    │     │    │
│  │  │  └──────────────────────────────────────────┘    │     │    │
│  │  └────────────────────────────────────────────────────┘     │    │
│  │                                                             │    │
│  │  ┌───────────────────────────────────────────────────┐     │    │
│  │  │          Ingress Controller                       │     │    │
│  │  │                                                    │     │    │
│  │  │  medilink.local → API Gateway                     │     │    │
│  │  │  jenkins.medilink.local → Jenkins                 │     │    │
│  │  └───────────────────────────────────────────────────┘     │    │
│  └────────────────────────────────────────────────────────────┘    │
│                                 ↕                                   │
│                        minikube tunnel                              │
│                                 ↕                                   │
│                         localhost:80                                │
└─────────────────────────────────────────────────────────────────────┘
                                 ↕
                        Your Web Browser
                    http://medilink.local
                    http://jenkins.medilink.local
```

---

## 🔐 Jenkins RBAC Permissions

```
┌──────────────────────────────────────────────┐
│  Jenkins ServiceAccount                      │
│  (jenkins namespace)                         │
└─────────────┬────────────────────────────────┘
              │
              ↓
┌──────────────────────────────────────────────┐
│  ClusterRole: jenkins                        │
│                                              │
│  Can do in medilink namespace:               │
│  ✅ Get/List/Watch/Update:                   │
│     - Pods                                   │
│     - Deployments                            │
│     - Services                               │
│     - ConfigMaps                             │
│     - Secrets                                │
│     - Ingresses (read-only)                  │
│                                              │
│  ✅ Execute commands in pods                 │
│  ✅ Run migrations                           │
│  ✅ Perform rolling updates                  │
│                                              │
│  ❌ Cannot delete namespace                  │
│  ❌ Cannot modify RBAC                       │
└──────────────────────────────────────────────┘
```

---

## 🐳 Docker Build Process

```
Jenkins Pod
    │
    ├─ Mounts: /var/run/docker.sock (from Minikube)
    │
    ↓
┌────────────────────────────────────────────┐
│  Build Process                             │
│                                            │
│  1. git clone from GitHub                  │
│     └─ Get latest code                     │
│                                            │
│  2. cd microservices/auth-service          │
│     └─ Enter service directory             │
│                                            │
│  3. docker build -t auth:62f2538 .         │
│     ├─ FROM python:3.12-slim               │
│     ├─ COPY requirements.txt               │
│     ├─ RUN pip install -r requirements.txt │
│     ├─ COPY . .                            │
│     └─ CMD gunicorn ...                    │
│                                            │
│  4. docker tag auth:62f2538 auth:latest    │
│     └─ Create 'latest' tag                 │
│                                            │
│  ✅ Image stored in Minikube's Docker      │
└────────────────────────────────────────────┘
         │
         ↓
┌────────────────────────────────────────────┐
│  Minikube Docker Daemon                    │
│                                            │
│  Images:                                   │
│  ├─ auth-service:62f2538                   │
│  ├─ auth-service:latest                    │
│  ├─ doctor-service:62f2538                 │
│  ├─ doctor-service:latest                  │
│  └─ ... (all 8 services)                   │
│                                            │
│  Kubernetes pulls from here! 🎯            │
└────────────────────────────────────────────┘
```

---

## 🔄 Rolling Update Process

```
Kubernetes receives update command from Jenkins
    │
    ↓
┌────────────────────────────────────────────────────┐
│  Rolling Update Strategy                           │
│  maxUnavailable: 1                                 │
│  maxSurge: 1                                       │
└────────────────────────────────────────────────────┘
    │
    ↓
Step 1: Create new pod with new image
┌──────────────────────────────────────┐
│  auth-service-old-abc (Running) ✅    │
│  auth-service-old-def (Running) ✅    │
│  auth-service-old-ghi (Running) ✅    │
│  auth-service-new-jkl (Creating) 🔵  │
└──────────────────────────────────────┘
    │
    ↓
Step 2: New pod starts, old pod terminates
┌──────────────────────────────────────┐
│  auth-service-old-abc (Running) ✅    │
│  auth-service-old-def (Running) ✅    │
│  auth-service-old-ghi (Terminating)⚠️│
│  auth-service-new-jkl (Running) ✅    │
└──────────────────────────────────────┘
    │
    ↓
Step 3: Continue rolling update
┌──────────────────────────────────────┐
│  auth-service-old-abc (Running) ✅    │
│  auth-service-old-def (Terminating)⚠️│
│  auth-service-new-jkl (Running) ✅    │
│  auth-service-new-mno (Running) ✅    │
└──────────────────────────────────────┘
    │
    ↓
Step 4: Complete - all pods updated
┌──────────────────────────────────────┐
│  auth-service-new-jkl (Running) ✅    │
│  auth-service-new-mno (Running) ✅    │
│  auth-service-new-pqr (Running) ✅    │
└──────────────────────────────────────┘

✅ Zero downtime deployment complete!
```

---

## ⚡ Automatic Build Options

### Option 1: Manual (Current Default)

```
Developer → Push to GitHub → Open Jenkins UI → Click "Build Now" → Build starts
```

**Delay:** Manual action required
**Pros:** Full control, simple, always works
**Cons:** Requires remembering to build

### Option 2: SCM Polling (Recommended for localhost)

```
Developer → Push to GitHub
                ↓
        (Wait up to 5 minutes)
                ↓
Jenkins checks GitHub (every 5 min)
                ↓
        Detects new commit
                ↓
        Build starts automatically! 🎉
```

**Delay:** 0-5 minutes
**Pros:** Automatic, works with localhost Jenkins
**Cons:** Not instant, polls even when no changes

**Setup:**
```
Jenkins → Job → Configure → Build Triggers
└─ Poll SCM: H/5 * * * *
```

### Option 3: GitHub Webhook (Production)

```
Developer → Push to GitHub → GitHub sends webhook → Jenkins builds instantly! ⚡
```

**Delay:** ~1-3 seconds
**Pros:** Instant, efficient, no polling
**Cons:** Requires public Jenkins URL (not localhost)

---

## 📊 Timeline Comparison

### Manual Build
```
00:00 - Push code
00:05 - Remember to build
00:06 - Open Jenkins
00:07 - Click "Build Now"
00:08 - Build starts
15:00 - Build completes
```
**Total time to deployment:** 15 minutes

### SCM Polling (H/5 * * * *)
```
00:00 - Push code
00:00 to 05:00 - Wait for Jenkins to poll
05:00 - Jenkins detects change
05:01 - Build starts
12:00 - Build completes
```
**Total time to deployment:** 5-12 minutes (automatic!)

### GitHub Webhook
```
00:00 - Push code
00:01 - GitHub webhook triggers Jenkins
00:02 - Build starts
07:00 - Build completes
```
**Total time to deployment:** 7 minutes (instant trigger!)

---

## 🎯 Recommended Setup

**For Development (localhost):**
✅ Use **SCM Polling** (Option 2)
- Set schedule: `H/5 * * * *`
- Automatic builds every 5 minutes
- No external dependencies

**For Production (cloud deployment):**
✅ Use **GitHub Webhook** (Option 3)
- Instant builds on push
- More efficient
- Professional CI/CD experience

**For Learning/Testing:**
✅ Use **Manual** (Option 1)
- Full control
- Understand each step
- Good for debugging

---

## 💡 Key Takeaways

1. **Jenkins is fully integrated** - Can build Docker images and deploy to Kubernetes
2. **Change detection is smart** - Only builds what changed
3. **Zero downtime deployments** - Rolling updates ensure continuous availability
4. **Automatic is better** - Enable SCM polling for hands-free builds
5. **Everything is local** - No cloud services required for development

---

**Want automatic builds?**
```
Jenkins → MediLink-Pipeline → Configure → Build Triggers → Poll SCM
Schedule: H/5 * * * *
Save → Done! 🎉
```
