# MediLink Microservices - Running Services

## ✅ System Status: ALL SERVICES RUNNING

All microservices are up and operational!

---

## 🌐 Web Interface

**Main Application**: http://localhost:8080

The web interface provides:
- User login and registration (multi-step signup)
- Doctor portal (manage hours, view availability)
- Patient portal (search doctors, view availability)
- Pharmacy portal (manage inventory, staff, medicines)

---

## 🔧 Microservices & Ports

| Service | Port | URL | Status |
|---------|------|-----|--------|
| **API Gateway** | 8080 | http://localhost:8080 | ✅ Running |
| **Auth Service** | 8001 | http://localhost:8001 | ✅ Running |
| **Doctor Service** | 8002 | http://localhost:8002 | ✅ Running |
| **Patient Service** | 8003 | http://localhost:8003 | ✅ Running |
| **Pharmacy Service** | 8004 | http://localhost:8004 | ✅ Running |
| **Scheduling Service** | 8005 | http://localhost:8005 | ✅ Running |
| **Inventory Service** | 8006 | http://localhost:8006 | ✅ Running |
| **Notification Service** | 8007 | http://localhost:8007 | ✅ Running |
| **PostgreSQL Database** | 5432 | localhost:5432 | ✅ Running |

---

## 🏥 Health Check Endpoints

Test service health with these endpoints:

```powershell
# API Gateway
curl http://localhost:8080/health/

# Auth Service
curl http://localhost:8001/health/ready/

# Doctor Service
curl http://localhost:8002/health/ready/

# Patient Service
curl http://localhost:8003/health/ready/

# Pharmacy Service
curl http://localhost:8004/health/ready/

# Scheduling Service
curl http://localhost:8005/health/ready/

# Inventory Service
curl http://localhost:8006/health/ready/

# Notification Service
curl http://localhost:8007/health/ready/
```

---

## 🚀 Docker Commands

### View all running containers
```powershell
docker ps
```

### View logs for a specific service
```powershell
docker logs medilink_gateway
docker logs medilink_auth
docker logs medilink_doctor
docker logs medilink_patient
docker logs medilink_pharmacy
docker logs medilink_scheduling
docker logs medilink_inventory
docker logs medilink_notification
```

### Follow logs in real-time
```powershell
docker logs -f medilink_gateway
```

### Stop all services
```powershell
docker-compose down
```

### Start all services
```powershell
docker-compose up -d
```

### Restart a specific service
```powershell
docker restart medilink_gateway
```

### Rebuild and restart all services
```powershell
docker-compose down
docker-compose build
docker-compose up -d
```

---

## 📊 Database Access

**Connection Details**:
- Host: localhost
- Port: 5432
- Database: medilink_db
- Username: medilink
- Password: medilink_password

### Connect via command line:
```powershell
docker exec -it medilink_postgres psql -U medilink -d medilink_db
```

---

## 🎯 Key Features

### API Gateway (Port 8080)
- Web interface for all user types
- Login/Signup pages
- Role-based dashboards
- Static file serving

### Auth Service (Port 8001)
- User authentication & authorization
- JWT token management
- User registration
- Password reset

### Doctor Service (Port 8002)
- Doctor profile management
- Working hours configuration
- Time-off management
- Availability calculation

### Patient Service (Port 8003)
- Patient profile management
- Medical history
- Search functionality

### Pharmacy Service (Port 8004)
- Pharmacy management
- Staff management
- Location settings

### Scheduling Service (Port 8005)
- Appointment scheduling
- Conflict detection
- Availability queries

### Inventory Service (Port 8006)
- Medicine catalog
- Stock management
- Pharmacy inventory

### Notification Service (Port 8007)
- Email notifications
- Alert management
- Communication handling

---

## 🔍 Troubleshooting

### If a service won't start:
1. Check the logs: `docker logs <container_name>`
2. Restart the service: `docker restart <container_name>`
3. Check database connection: `docker logs medilink_postgres`

### If database has issues:
```powershell
# Restart database
docker restart medilink_postgres

# Check database is healthy
docker ps | Select-String postgres
```

### Complete reset:
```powershell
# Stop and remove all containers and volumes
docker-compose down -v

# Rebuild and start
docker-compose build
docker-compose up -d
```

---

## 📝 Next Steps

1. **Access the web interface**: Navigate to http://localhost:8080
2. **Create an account**: Use the signup flow
3. **Test features**: Try different user roles (doctor, patient, pharmacy)
4. **Monitor logs**: Use `docker logs -f <container_name>` to watch activity
5. **Test APIs**: Each microservice has its own API endpoints

---

## 🎉 Success!

All microservices are running and communicating properly. The system is ready for use and testing!

For more detailed information, see:
- `docker-compose.yml` - Service configuration
- `DEPLOYMENT_GUIDE.md` - Full deployment documentation
- `TESTING_GUIDE.md` - Testing procedures
