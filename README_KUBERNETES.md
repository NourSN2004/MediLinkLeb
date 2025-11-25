# MediLink - Healthcare Management System on Kubernetes

Complete microservices-based healthcare platform deployed on Kubernetes with Minikube and NGINX Ingress Controller.

## 🚀 Quick Start

### One-Command Setup

**Run as Administrator for fully automated setup:**
```powershell
.\COMPLETE_SETUP.ps1
```

**Total time:** 10-15 minutes

**Access:** http://medilink.local

That's it! The script handles everything:
- ✅ Minikube cluster setup
- ✅ Docker image builds
- ✅ Microservices deployment
- ✅ Database migrations
- ✅ Ingress configuration
- ✅ Tunnel activation

---

## 📋 Requirements

- Windows 10/11
- PowerShell 5.1+
- Docker Desktop
- kubectl
- Minikube

**Check prerequisites:**
```powershell
.\CHECK_STATUS.ps1
```

---

## 🏗️ Architecture

### Microservices

| Service | Purpose | Port |
|---------|---------|------|
| **API Gateway** | Web UI & request routing | 8000 |
| **Auth Service** | Authentication & user management | 8001 |
| **Doctor Service** | Doctor profiles & management | 8002 |
| **Patient Service** | Patient records & history | 8003 |
| **Pharmacy Service** | Pharmacy operations & staff | 8004 |
| **Scheduling Service** | Appointment scheduling | 8005 |
| **Inventory Service** | Medicine inventory | 8006 |
| **Notification Service** | Email & SMS notifications | 8007 |
| **PostgreSQL** | Database | 5432 |

### Technologies

- **Orchestration:** Kubernetes (Minikube)
- **Ingress:** NGINX Ingress Controller
- **Backend:** Django (Python)
- **Database:** PostgreSQL
- **Containerization:** Docker
- **Server:** Gunicorn

---

## 🎯 Features

### Patient Portal
- Register and manage profile
- View medical history
- View prescriptions
- Browse medicine catalog
- Schedule appointments
- Receive notifications

### Doctor Portal
- Manage profile and credentials
- View today's appointments
- Access full schedule
- Search patient records
- Manage availability
- Create prescriptions

### Pharmacy Portal
- Manage inventory
- Process prescriptions
- Track stock levels
- Manage staff
- View orders

---

## 📖 Documentation

- **[SETUP_GUIDE.md](SETUP_GUIDE.md)** - Complete setup instructions
- **[DEPLOYMENT_SUCCESS.md](DEPLOYMENT_SUCCESS.md)** - Full deployment documentation
- **[ACCESS_GUIDE.md](ACCESS_GUIDE.md)** - Access methods and troubleshooting
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Command reference

---

## 🔧 Common Operations

### Check System Status
```powershell
.\CHECK_STATUS.ps1
```

### View Logs
```powershell
kubectl logs -n medilink deployment/api-gateway --tail=50
```

### Restart Service
```powershell
kubectl rollout restart deployment/api-gateway -n medilink
```

### Access Database
```powershell
kubectl exec -it -n medilink deployment/postgres -- psql -U medilink -d medilink_db
```

### Scale Service
```powershell
kubectl scale deployment api-gateway -n medilink --replicas=6
```

---

## 🌐 Access Methods

### Method 1: Ingress (Production Mode)
**URL:** http://medilink.local

Requires:
- Minikube tunnel running (started by COMPLETE_SETUP.ps1)
- Hosts file entry: `127.0.0.1 medilink.local`

### Method 2: Service Tunnel (Development)
```powershell
.\START_APP.ps1
```
Opens browser to `http://127.0.0.1:xxxxx`

---

## 🧪 Testing

### Create Test Accounts

1. Open http://medilink.local
2. Click "Sign up"
3. Choose role: Patient, Doctor, or Pharmacy
4. Fill in details
5. Auto-login after registration

### Sample Test Data

**Patient:**
- Email: `patient@test.com`
- Password: `Test123!`

**Doctor:**
- Email: `doctor@test.com`
- Password: `Test123!`

**Pharmacy:**
- Email: `pharmacy@test.com`
- Password: `Test123!`

---

## 📊 Project Status

**Status:** ✅ PRODUCTION READY

- 26 pods running
- 9 services deployed
- Ingress configured
- All features functional
- Database operational

---

## 🎓 Academic Project

**Course:** EECE 430 - Software Engineering  
**Institution:** American University of Beirut (AUB)  
**Term:** Fall 2025  

**Learning Objectives:**
- Microservices architecture
- Kubernetes orchestration
- Container deployment
- Service mesh
- API gateway pattern
- Database design
- CI/CD concepts

---

## 🛠️ Development

### Rebuild After Code Changes

```powershell
# Configure Docker
& minikube -p minikube docker-env --shell powershell | Invoke-Expression

# Rebuild service
cd microservices\<service-name>
docker build -t <service-name>:latest .

# Restart deployment
kubectl rollout restart deployment/<service-name> -n medilink
```

### Run Migrations

```powershell
$pod = kubectl get pods -n medilink -l app=auth-service -o jsonpath='{.items[0].metadata.name}'
kubectl exec -n medilink $pod -- python manage.py migrate
```

---

## ⚠️ Important Notes

### Keep Tunnel Running
The minikube tunnel must remain active for http://medilink.local to work. The COMPLETE_SETUP.ps1 script starts the tunnel and keeps it running. Keep that terminal window open.

### Stop and Resume
**Stop tunnel:** Press `Ctrl+C` in the terminal  
**Resume tunnel:** Run `minikube tunnel` as Administrator

### Resource Usage
- **RAM:** 6GB allocated to Minikube
- **CPU:** 4 cores allocated
- **Disk:** 20GB

---

## 🐛 Troubleshooting

### Site Not Accessible
1. Check tunnel: `Get-Process | Where-Object ProcessName -eq "minikube"`
2. Restart tunnel: `minikube tunnel` (as Admin)
3. Verify hosts file has: `127.0.0.1 medilink.local`

### Pods Not Running
```powershell
kubectl get pods -n medilink
kubectl logs -n medilink <pod-name>
kubectl describe pod -n medilink <pod-name>
```

### Out of Resources
```powershell
minikube stop
minikube start --memory=8192 --cpus=4
```

### Clean Restart
```powershell
minikube delete
.\COMPLETE_SETUP.ps1
```

---

## 📞 Support

For issues or questions:
1. Check [SETUP_GUIDE.md](SETUP_GUIDE.md)
2. Run `.\CHECK_STATUS.ps1`
3. Review logs: `kubectl logs -n medilink deployment/<service-name>`

---

## 📄 License

See [LICENSE](LICENSE) file for details.

---

## ✅ Quick Checklist

Before presenting:
- [ ] Run `COMPLETE_SETUP.ps1`
- [ ] All pods in Running state
- [ ] Can access http://medilink.local
- [ ] Can create account
- [ ] Can login
- [ ] All features work
- [ ] Know how to show architecture
- [ ] Know how to scale services
- [ ] Know how to view logs

**Ready to demonstrate!** 🎉
